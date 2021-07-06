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
from selenium.common.exceptions import StaleElementReferenceException
from selenium import webdriver
from bs4 import BeautifulSoup
from time import sleep
import signal


# Parameters
SITE_NAME = "coop"
BASE_URL = "https://cooponline.vn"
PROJECT_PATH = Path(__file__).absolute().parents[1]
PATH_HTML = os.path.join(PROJECT_PATH, "html", SITE_NAME)
PATH_CSV = os.path.join(PROJECT_PATH, "csv", SITE_NAME)
PATH_LOG = os.path.join(PROJECT_PATH, "log")
CLEAN_CSV = os.path.join(PROJECT_PATH, "clean_csv", SITE_NAME)
DATE = str(datetime.date.today())
OBSERVATION = 0
CHROME_DRIVER = os.path.join(PROJECT_PATH, "bin/chromedriver")
IGNORED_EXCEPTIONS = (NoSuchElementException,StaleElementReferenceException)

# Selenium options
OPTIONS = Options()
OPTIONS.add_argument("start-maximized")
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
    log.info('Start selecting mart')
    choose_mart(BASE_URL)
    log.info('Selected CoopXtra Mart in Tan Phong, District 7')
    disable_sub()
    log.info('Disable popup alert')
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
    CATEGORIES_PAGES = get_category_list(html_file)
    log.info('Found ' + str(len(CATEGORIES_PAGES)) + ' categories')
    # Read each categories pages and scrape for data
    for cat in track(CATEGORIES_PAGES,
                     description = "[green]Scraping...",
                     total = len(CATEGORIES_PAGES)):
        cat_file = "cat_" + cat['name'] + "_" + DATE + ".html"
        download = fetch_html(cat['directlink'], cat_file, PATH_HTML)
        if download:
            scrap_data(cat)
    # Close browser
    BROWSER.close()
    BROWSER.service.process.send_signal(signal.SIGTERM)
    BROWSER.quit()


def choose_mart(url):
    global BROWSER
    BROWSER.get(url)
    wait = WebDriverWait(BROWSER, 10)
    sleep(1)
    mart = Select(BROWSER.find_element_by_xpath("(//select)[2]"))
    mart.select_by_index(1) # Tan Phong
    sleep(2)
    BROWSER.find_element_by_xpath("(//button)[2]").click()

def disable_sub():
    global BROWSER
    wait = WebDriverWait(BROWSER, 20).until(EC.presence_of_element_located((By.ID, "onesignal-slidedown-dialog")))
    sleep(2)
    BROWSER.find_element_by_xpath("//button[contains(@class, 'align-right secondary')]").click()

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
                log.warning("Try again" + file_name)
        else:
            log.error(f"Cannot download {file_name}")
            return(False)
    else:
        log.debug(f"Already downloaded {file_name}")
        return(True)
    os.chdir(PROJECT_PATH)

def get_category_list(top_html):
    """Get list of relative categories directories from the top page"""
    page_list = []
    toppage_soup = BeautifulSoup(BROWSER.page_source, "lxml")
    categories_bar = [toppage_soup.findAll("ul", {'class': 'megamenu'})]
    categories_bar = [item for sublist in categories_bar for item in sublist]
    categories_bar = [categories_bar[1]]
    categories_tag = [cat.findAll('li') for cat in categories_bar]
    categories_tag = [item for sublist in categories_tag for item in sublist]
    categories = [cat.find_all('a') for cat in categories_tag]
    categories = [item for sublist in categories for item in sublist]
    categories = categories[2:]
    for cat in categories:
        next_page = {}
        link = re.sub(".+cooponline\\.vn", "", cat['href'])
        next_page['relativelink'] = link
        next_page['directlink'] = BASE_URL + link
        name = re.sub("/|\\?.=", "_", link)
        next_page['name'] = re.sub("_production","", name)
        next_page['label'] = re.sub("\n                                                                                                            |\n","",cat.text)
        page_list.append(next_page)
    # Remove duplicates
    page_list = [dict(t) for t in set(tuple(i.items()) for i in page_list)]
    return(page_list)

def scrap_data(cat):
    """Get item data from a category page and write to csv"""
    global OBSERVATION
    soup = BeautifulSoup(BROWSER.page_source, 'lxml')
    wait = WebDriverWait(BROWSER, 60)
    try:
        wait.until(EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'product-image-container second_img')]")))
        scrape_test = BROWSER.find_elements_by_xpath("//div[contains(@class, 'product-image-container second_img')]")
        if scrape_test:
            log.info("There are elements!")
        else:
            log.info("Cannnot find the elements!")
    except TimeoutException:
        log.info("Timeout!")
        pass
    cat_name = soup.find('h3', {'class':'title-category'}).text
    while True:
        try:
            see_more = BROWSER.find_element_by_xpath("//button[contains(@class, 'btn-success')]")
            BROWSER.execute_script("arguments[0].click();", see_more)
        except IGNORED_EXCEPTIONS:
            log.info('Clicked all see_more button as much as possible in ' + cat_name + ' category.')
            break
    try:
        soup = BeautifulSoup(BROWSER.page_source, 'lxml')
        sleep(10)
        list = soup.find_all('div', {'class': 'product-item-container'})
        log.info('Found ' + str(len(list)) + ' products')
        directory = soup.find_all('span', {'property': 'name'})
        if len(directory) != 1:
            subdir = directory[1].text.strip()
        else:
            subdir = directory[0].text.strip()
        for item in list:
            row = {}
            if item.find('h4', {'class':'title_product_lmh'}) != None:
                good_name = item.find('h4', {'class':'title_product_lmh'}).text
                row['good_name'] = good_name
            else:
                None
            if item.find('span', class_='price-new') != None:
                price = item.find('span', class_='price-new').text.strip()
                price = price.split('đ')[0]
                price = price.strip()
                row['price'] = price
            else:
                None
            if item.find('span', class_='price-old') != None:
                old_price = item.find('span', class_='price-old').text.strip()
                old_price = old_price.split('đ')[0]
                old_price = old_price.strip()
                row['old_price'] = old_price
            else:
                None
            if item.find('a', {'target':'_self'}) != None:
                item_id = item.find('a', {'target':'_self'}).get('href')
                item_id = re.sub(".+products/|/","",item_id)
                row['id'] = item_id
            row['parent_category'] = subdir
            row['category'] = cat['label']
            row['date'] = DATE
            OBSERVATION += 1
            write_data(row)
        log.info('Finished scraping ' + cat_name + ' category.')
    except Exception as e:
        log.error("Error on " + BROWSER.current_url)
        log.info(type(e).__name__ + str(e))
        pass

def write_data(item_data):
    """Write an item data as a row in csv. Create new file if needed"""
    fieldnames = ['good_name', 'price', 'old_price', 'id', 'parent_category', 'category', 'date']
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
    ## Price
    if raw.price.str.contains('Đang cập nhật').any():
        raw.price = np.where(raw.price == 'Đang cập nhật', 0, raw.price)
    if raw.price.str.contains('.').any():
        raw.price = raw.price.str.replace('.','', regex=True)
    if raw.price.str.contains(',').any():
        raw.price = raw.price.str.replace(',','', regex=True)
    raw.price = raw.price.astype(float)
    ## Old price
    if raw.old_price.str.contains('.').any():
        raw.old_price = raw.old_price.str.replace('.','', regex=True)
    if raw.old_price.str.contains(',').any():
        raw.old_price = raw.old_price.str.replace(',','', regex=True)
    raw.old_price = raw.old_price.astype(float)    ### Handle null values
    if raw.old_price.isnull().any():
        raw.old_price = raw.old_price.fillna(0)
        raw.old_price = np.where(raw.old_price == 0, raw.price, raw.old_price)
    log.info('Have a look at the dtypes after converting:')
    log.info(raw.info())
    os.remove(SITE_NAME + '_' + DATE + '.csv')

    # Export to new CSV
    os.chdir(PROJECT_PATH)
    os.chdir(CLEAN_CSV)
    raw.to_csv(SITE_NAME + '_' + DATE + '_clean.csv')
    log.info('Finished cleaning data')

if __name__ == '__main__':
    main()
