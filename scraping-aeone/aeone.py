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
from selenium import webdriver
from bs4 import BeautifulSoup
from time import sleep
import signal


# Parameters
SITE_NAME = "aeoneshop"
BASE_URL = "https://aeoneshop.com"
PROJECT_PATH = re.sub("/py$", "", os.getcwd())
PATH_HTML = PROJECT_PATH + "/html/" + SITE_NAME + "/"
PATH_CSV = PROJECT_PATH + "/csv/" + SITE_NAME + "/"
PATH_LOG = PROJECT_PATH + "/log/"
DATE = str(datetime.date.today())
OBSERVATION = 0
CHROME_DRIVER = PROJECT_PATH + "/bin/chromedriver"

# Selenium options
OPTIONS = Options()
OPTIONS.add_argument("start-maximized")
OPTIONS.add_argument('--headless')
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
    try:
        daily_task()
    except Exception as e:
        log.exception('Got exception, scraper stopped')
        log.info(type(e).__name__ + str(e))
    # Compress data and html files
    compress_csv()
    compress_html()
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
    html_file = open(PATH_HTML + base_file_name).read()
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

#def choose_location(url):
    #global BROWSER
    #BROWSER.get(url)
    #wait = ui.WebDriverWait(BROWSER, 10)
    #sleep(1)
    #city = Select(BROWSER.find_element_by_id('select_city'))
    #city.select_by_index(1) # Hanoi
    #sleep(2)
    #district = Select(BROWSER.find_element_by_id('select_district'))
    #district.select_by_index(1) # Ba Dinh
    #sleep(2)
    #BROWSER.find_element_by_xpath("//button[text()='Đồng ý']").click()
    #wait

def fetch_html(url, file_name, path, attempts_limit=5):
    """Fetch and download a html with provided path and file names"""
    if not os.path.exists(path):
        os.makedirs(path)
    if os.path.isfile(path + file_name) is False:
        attempts = 0
        while attempts < attempts_limit:
            try:
                BROWSER.get(url)
                element = BROWSER.find_element_by_xpath("/html")
                html_content = element.get_attribute("innerHTML")
                with open(path + file_name, "w") as f:
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

def get_category_list(top_html):
    """Get list of relative categories directories from the top page"""
    page_list = []
    toppage_soup = BeautifulSoup(BROWSER.page_source, "lxml")
    categories = toppage_soup.findAll("li", {'class': re.compile('menu-item')})
    categories_tag = [cat.findAll('a') for cat in categories]
    categories_tag = [item for sublist in categories_tag for item in sublist]
    for cat in categories_tag:
        next_page = {}
        link = re.sub(".+aeoneshop\\.com", "", cat['href'])
        next_page['relativelink'] = link
        next_page['directlink'] = BASE_URL + link
        next_page['name'] = re.sub("/|\\?.=", "_", link)
        next_page['label'] = re.sub("\\n|\t+", "", cat.text)
        page_list.append(next_page)
    # Remove javascript links
    page_list = [i for i in page_list if not (i['name'] == 'javascript:void(0);')]
    return(page_list)

def scrap_data(cat):
    """Get item data from a category page and write to csv"""
    global OBSERVATION
    global BROWSER
    BROWSER.get(cat['directlink'])
    wait = ui.WebDriverWait(BROWSER, 60)
    soup = BeautifulSoup(BROWSER.page_source, 'lxml')
    wait
    if soup.find('li', {'id':'level_1'}) != None:
        cat_name = soup.find('li', {'id':'level_1'}).text
    else:
        cat_name = 'No name'
    page_count = soup.find_all('a', class_='page-node')
    if len(page_count) == 0:
        page_count = 1
    else:
        page_count = page_count[-1]
        page_count = page_count.text.strip()
    log.info(cat_name + ' category has ' + str(page_count) + ' pages')
    try:
        i = 0
        while i < int(page_count):
            if i != 0:
                try:
                    element = BROWSER.find_element_by_xpath("//*[contains(@class, 'pull-right')]")
                    BROWSER.execute_script("arguments[0].click();", element)
                except NoSuchElementException:
                    pass
                wait
                soup = BeautifulSoup(BROWSER.page_source, 'lxml')
                sleep(10)
                list = soup.find_all('div', class_='product-block')
                log.info('We are on ' + str(i+1) + ' page')
            if i == 0:
                soup = BeautifulSoup(BROWSER.page_source, 'lxml')
                wait
                list = soup.find_all('div', class_='product-block')
                log.info('We are on ' + str(i+1) + ' page')
            log.info('Found ' + str(len(list)) + ' products')
            for item in list:
                row = {}
                if item.find('h3', class_='pro-name') != None:
                    good_name = item.find('h3', class_='pro-name').a.get('title').strip()
                    row['good_name'] = good_name
                else:
                    None
                if item.find('span', class_='priceMin') != None:
                    price = item.find('span', class_='priceMin').text.strip()
                    price = price.split('₫')[0]
                    price = price.strip()
                    row['price'] = price
                else:
                    None
                if item.find('del', {'class':'compare-price'}) != None:
                    old_price = item.find('del', {'class':'compare-price'}).text.strip()
                    old_price = old_price.split('₫')[0]
                    old_price = old_price.strip()
                    row['old_price'] = old_price
                else:
                    None
                if item.find('div', class_='product-gift-icon') != None:
                    item_id = item.find('div', class_='product-gift-icon').get('product-id').strip()
                    row['id'] = item_id
                else:
                    None
                row['category'] = cat['label']
                row['date'] = DATE
                OBSERVATION += 1
                write_data(row)
            log.info('Finished scraping ' + str(i+1) + ' page')
            i += 1
    except Exception as e:
        log.error("Error on " + BROWSER.current_url)
        log.info(type(e).__name__ + str(e))
        pass

def write_data(item_data):
    """Write an item data as a row in csv. Create new file if needed"""
    fieldnames = ['good_name', 'price', 'old_price', 'id', 'category', 'date']
    file_exists = os.path.isfile(PATH_CSV + SITE_NAME + "_" + DATE + ".csv")
    if not os.path.exists(PATH_CSV):
        os.makedirs(PATH_CSV)
    with open(PATH_CSV + SITE_NAME + "_" + DATE + ".csv", "a") as f:
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

main()
