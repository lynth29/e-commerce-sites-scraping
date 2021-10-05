# Import essential libraries
import sys
import os
import glob
from zipfile import ZipFile
import time
import datetime
import schedule
import re
import csv
import random
import logging
import pandas as pd
import numpy as np
from pathlib import Path
from rich.logging import RichHandler
from rich.progress import track
from urllib.request import urlopen
import selenium.webdriver.support.ui as ui
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.wait import WebDriverWait
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import TimeoutException
from selenium import webdriver
from bs4 import BeautifulSoup
from time import sleep
import signal


# Parameters
SITE_NAME = "vinmart"
BASE_URL = "https://winmart.vn"
PROJECT_PATH = Path(__file__).absolute().parents[1]
PATH_HTML = os.path.join(PROJECT_PATH, "html", SITE_NAME)
PATH_CSV = os.path.join(PROJECT_PATH, "csv", SITE_NAME)
PATH_LOG = os.path.join(PROJECT_PATH, "log")
CLEAN_CSV = os.path.join(PROJECT_PATH, "clean_csv", SITE_NAME)
DATE = str(datetime.date.today())
OBSERVATION = 0
CHROME_DRIVER = os.path.join(PROJECT_PATH, "bin/chromedriver")

# Selenium options
OPTIONS = Options()
OPTIONS.add_argument("start-maximized")
OPTIONS.add_argument("--no-sandbox")
# OPTIONS.add_argument('--headless')
OPTIONS.add_argument('--disable-gpu')
BROWSER = webdriver.Chrome(executable_path=CHROME_DRIVER,
                               options=OPTIONS)

# Setting up logging
logging.basicConfig(
    level="INFO",
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(rich_tracebacks=True)]
)

log = logging.getLogger("rich")


# Defining main functions
def main():
    # Select mart
    log.info('Start selecting shipping location')
    choose_location(BASE_URL)
    log.info('Selected Hanoi')
    try:
        daily_task()
    except Exception as e:
        log.exception('Got exception, scraper stopped')
        log.info(type(e).__name__ + str(e))
    # Compress data and html files
    compress_csv()
    compress_html()
    unzip_csv()
    cleaning_data()
    log.info('Finished. Hibernating until next day...')

def daily_task():
    """Main workhorse function. Support functions defined below"""
    global CATEGORIES_PAGES
    global BROWSER
    global DATE
    global OBSERVATION
    log.info('Scraper started')
    # Refresh date
    DATE = str(datetime.date.today())
    OBSERVATION = 0
    # Download topsite and get categories directories
    base_file_name = "All_cat_" + DATE + ".html"
    fetch_html(BASE_URL, base_file_name, PATH_HTML, attempts_limit=1000)
    html_file = open(PATH_HTML + '/' + base_file_name).read()
    log.info('Start getting categories')
    CATEGORIES_PAGES = get_category_list(html_file)
    log.info('Found ' + str(len(CATEGORIES_PAGES)) + ' categories')
    # Read each categories pages and scrape for data
    for cat in track(CATEGORIES_PAGES,
                     description = "[green]Scraping...",
                     total = len(CATEGORIES_PAGES)):
        cat_file = "cat_" + cat['name'] + "_" + DATE + ".html"
        download = fetch_html(cat['directlink'], cat_file, PATH_HTML)
        scrap_data(cat)
    # Close browser
    # BROWSER.close()
    # BROWSER.service.process.send_signal(signal.SIGTERM)
    # BROWSER.quit()


def choose_location(url):
    global BROWSER
    BROWSER.maximize_window()
    BROWSER.get(url)
    try:
        wait = WebDriverWait(BROWSER, 60).until(EC.element_to_be_clickable((By.XPATH, "//span[contains(text(),'TP. Hà Nội')]")))
    except TimeoutException:
        pass
    sleep(2)
    city = BROWSER.find_element_by_xpath("//span[contains(text(),'TP. Hà Nội')]").click() # Hà Nội
    sleep(2)
    district = BROWSER.find_element_by_xpath("//span[contains(text(),'Q. Hai Bà Trưng')]").click() # Hai Bà Trưng
    sleep(2)
    ward = BROWSER.find_element_by_xpath("//span[contains(text(),'P. Minh Khai')]").click() # Minh Khai

def fetch_html(url, file_name, path, attempts_limit=5):
    """Fetch and download a html with provided path and file names"""
    if not os.path.exists(path):
        os.makedirs(path)
    os.chdir(path)
    if os.path.isfile(file_name) is False:
        attempts = 0
        while attempts < attempts_limit:
            try:
                BROWSER.get(url)
                element = BROWSER.find_element_by_xpath("/html")
                html_content = element.get_attribute("innerHTML")
                with open(file_name, "w") as f:
                    f.write(html_content)
                log.debug(f"Downloaded: {file_name}")
                return(True)
            except:
                attempts += 1
                log.warning('Try again to download ' + file_name)
        else:
            log.error(f"Cannot download {file_name}")
            log.warning('Will pass downloading ' + file_name)
            return(False)
    else:
        log.debug(f"Already downloaded {file_name}")
        return(True)
    os.chdir(PROJECT_PATH)

def multiple_replace(dict, text):
  # Create a regular expression  from the dictionary keys
  regex = re.compile("(%s)" % "|".join(map(re.escape, dict.keys())))
  # For each match, look-up corresponding value in dictionary
  return regex.sub(lambda mo: dict[mo.string[mo.start():mo.end()]], text)

def get_category_list(top_html):
    """Get list of relative categories directories from the top page"""
    page_list = []
    BROWSER.get(BASE_URL)
    sleep(5)
    toppage_soup = BeautifulSoup(BROWSER.page_source, "lxml")
    categories_bar = [toppage_soup.findAll("a", {'class': 'menu-name'})]
    categories = [item for sublist in categories_bar for item in sublist]
    for cat in categories:
        next_page = {}
        link = cat.get('href')
        next_page['relativelink'] = link
        next_page['directlink'] = BASE_URL + link
        next_page['name'] = cat.text
        next_page['label'] = cat.text
        page_list.append(next_page)
    # Remove duplicates
    return(page_list)

def scrap_data(cat):
    """Get item data from a category page and write to csv"""
    global OBSERVATION
    global BROWSER
    try:
        # Get all products appeared by scrolling

        BROWSER.get(cat['directlink'])

        SCROLL_PAUSE_TIME = 5

        # Get scroll height
        last_height = BROWSER.execute_script("return document.body.scrollHeight")
        while True:
            # Scroll down to bottom
            BROWSER.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            # Wait to load page
            sleep(SCROLL_PAUSE_TIME)
            # Calculate new scroll height and compare with last scroll height
            new_height = BROWSER.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height

        # Get all products
        soup = BeautifulSoup(BROWSER.page_source, 'lxml')
        list = soup.find_all('div', {'class':'product-card-two__Card-sc-1lvbgq2-0 cbXSsN product-card'})
        log.info('Found ' + str(len(list)) + ' products')
        for item in list:
            row = {}
            # Product name
            if item.find('h2', {'class':'product-card-two__Title-sc-1lvbgq2-4 ifcsNx'}) != None:
                good_name = item.find('h2', {'class':'product-card-two__Title-sc-1lvbgq2-4 ifcsNx'}).text.strip()
                row['good_name'] = good_name
            else:
                None
            # Price
            if item.find('div', {'class':'product-card-two__Price-sc-1lvbgq2-6 cDiKnb'}) != None:
                price = item.find('div', {'class':'product-card-two__Price-sc-1lvbgq2-6 cDiKnb'}).text.strip()
                price = price.split('₫')[0]
                price = price.strip()
                row['price'] = price
            else:
                None
            # Old price
            if item.find('div', {'class':'product-card-two__SalePrice-sc-1lvbgq2-7 fEocCD'}) != None:
                old_price = item.find('div', {'class':'product-card-two__SalePrice-sc-1lvbgq2-7 fEocCD'}).text.strip()
                old_price = old_price.split('₫')[0]
                old_price = old_price.strip()
                row['old_price'] = old_price
            else:
                None
            # Item_id
            if item.find('a', {'class': ''}) != None:
                item_id = item.find('a', {'class': ''}).get('href').strip()
                item_id = item_id.split('--')
                item_id = item_id[len(item_id)-1]
                item_id = item_id.strip()
                row['id'] = item_id
            # Category
            row['category'] = cat['label']
            row['date'] = DATE
            OBSERVATION += 1
            write_data(row)
    except Exception as e:
        log.error("Error on " + BROWSER.current_url)
        log.info(type(e).__name__ + str(e))
        pass

def write_data(item_data):
    """Write an item data as a row in csv. Create new file if needed"""
    fieldnames = ['good_name', 'price', 'old_price', 'id', 'category', 'date']
    file_exists = os.path.isfile(PATH_CSV + '/' + SITE_NAME + "_" + DATE + ".csv")
    if not os.path.exists(PATH_CSV):
        os.makedirs(PATH_CSV)
    with open(PATH_CSV + '/' + SITE_NAME + "_" + DATE + ".csv", "a") as f:
        writer = csv.DictWriter(f, fieldnames)
        if not file_exists:
            writer.writeheader()
        writer.writerow(item_data)

def compress_csv():
    """Compress downloaded .csv files"""
    if not os.path.exists(PATH_CSV):
        os.makedirs(PATH_CSV)
    os.chdir(PATH_CSV)
    try:
        zip_csv = ZipFile(SITE_NAME + '_' + DATE + '_csv.zip', 'a')
        for file in glob.glob("*" + DATE + "*" + "csv"):
            zip_csv.write(file)
            os.remove(file)
        log.info(f"Compressing {str(OBSERVATION)} item(s)")
    except Exception as e:
        log.error('Error when compressing csv')
        log.info(type(e).__name__ + str(e))
    os.chdir(PROJECT_PATH)

def compress_html():
    """Compress downloaded .html files"""
    if not os.path.exists(PATH_HTML):
        os.makedirs(PATH_HTML)
    os.chdir(PATH_HTML)
    try:
        zip_csv = ZipFile(SITE_NAME + '_' + DATE + '_html.zip', 'a')
        for file in glob.glob("*" + DATE + "*" + "html"):
            zip_csv.write(file)
            os.remove(file)
        log.info("Compressing HTML files")
    except Exception as e:
        log.error('Error when compressing html')
        log.info(type(e).__name__ + str(e))
    os.chdir(PROJECT_PATH)

def unzip_csv():
    """Unzip .csv files"""
    if not os.path.exists(PATH_CSV):
        os.makedirs(PATH_CSV)
    os.chdir(PATH_CSV)
    try:
        with ZipFile(SITE_NAME + '_' + DATE + '_csv.zip', 'a') as zip_csv:
            zip_csv.extractall(PATH_CSV)
        log.info(f"Unziping {str(OBSERVATION+1)} item(s)")
    except Exception as e:
        log.error('Error when compressing csv')
        log.info(type(e).__name__ + str(e))
    os.chdir(PROJECT_PATH)

def cleaning_data():
    # Import CSV file
    os.chdir(PATH_CSV)
    raw = pd.read_csv(SITE_NAME + '_' + DATE + '.csv')
    log.info('Imported CSV file to a dataframe')

    # Summarize the dataframe
    log.info(f"The dataframe has {raw.shape[0]} rows and {raw.shape[1]} columns.")
    log.info('Have a look at the dtypes:')
    log.info(raw.info())
    log.info('Are there any null value?:')
    log.info(raw.isnull().any())

    # Convert dtypes
    ## Date
    raw.date = str(datetime.date.today())
    raw.date = pd.to_datetime(raw.date)
    log.info('Finished converting Date.')
    ## Price
    if raw.price.astype(str).str.contains('Đang cập nhật').any():
        raw.price = np.where(raw.price == 'Đang cập nhật', 0, raw.price)
        log.info('Finished handling Đang cập nhật')
    ## Multiple price with 1000
    raw.price = raw.price * 1000
    log.info('Finished handling float dot in price')
    ## Old price
    raw.old_price = raw.old_price * 1000
    log.info('Finished handling float dot in old_price')
    if raw.old_price.isnull().any():
        raw.old_price = raw.old_price.fillna(0)
        raw.old_price = np.where(raw.old_price == 0, raw.price, raw.old_price)
        log.info('Finished copy price to old_price')
    log.info('Have a look at the dtypes after converting:')
    log.info(raw.info())
    os.remove(SITE_NAME + '_' + DATE + '.csv')

    # Export to new CSV
    os.chdir(PROJECT_PATH)
    os.chdir(CLEAN_CSV)
    raw.to_csv(SITE_NAME + '_' + DATE + '_hn_clean.csv')
    log.info('Finished cleaning data')

if __name__ == '__main__':
    main()
