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
import selenium.webdriver.support.ui as ui
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium import webdriver
from bs4 import BeautifulSoup
from time import sleep
import signal

# Parameters
SITE_NAME = "shopeevn"
BASE_URL = "https://shopee.vn"
PROJECT_PATH = re.sub("/py$", "", os.getcwd())
PATH_HTML = PROJECT_PATH + "/html/" + SITE_NAME + "/"
PATH_CSV = PROJECT_PATH + "/csv/" + SITE_NAME + "/"
PATH_LOG = PROJECT_PATH + "/log/"
DATE = str(datetime.date.today())
OBSERVATION = 0
CHROME_DRIVER = PROJECT_PATH + "/bin/chromedriver"

# Selenium options
OPTIONS = Options()
# OPTIONS.add_argument("--headless")
OPTIONS.add_argument("start-maximized")
OPTIONS.add_argument("--disable-extensions")
OPTIONS.add_argument("--no-sandbox")
OPTIONS.add_argument("--disable-dev-shm-usage")
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
    CATEGORIES_PAGES = listing
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
                log.debug("Downloaded: %s", file_name)
                return(True)
            except:
                attempts += 1
                log.warning("Try again" + file_name)
        else:
            log.error("Cannot download %s", file_name)
            return(False)
    else:
        log.debug("Already downloaded %s", file_name)
        return(True)

listing = [{'relativelink': '/Thời-Trang-Nam-cat.78',
  'directlink': 'https://shopee.vn/Thời-Trang-Nam-cat.78',
  'name': '_Thời-Trang-Nam-cat.78',
  'label': 'Thời Trang Nam'},
 {'relativelink': '/Thời-Trang-Nữ-cat.77',
  'directlink': 'https://shopee.vn/Thời-Trang-Nữ-cat.77',
  'name': '_Thời-Trang-Nữ-cat.77',
  'label': 'Thời Trang Nữ'},
 {'relativelink': '/Điện-Thoại-Phụ-Kiện-cat.84',
  'directlink': 'https://shopee.vn/Điện-Thoại-Phụ-Kiện-cat.84',
  'name': '_Điện-Thoại-Phụ-Kiện-cat.84',
  'label': 'Điện Thoại & Phụ Kiện'},
 {'relativelink': '/Mẹ-Bé-cat.163',
  'directlink': 'https://shopee.vn/Mẹ-Bé-cat.163',
  'name': '_Mẹ-Bé-cat.163',
  'label': 'Mẹ & Bé'},
 {'relativelink': '/Thiết-Bị-Điện-Tử-cat.2365',
  'directlink': 'https://shopee.vn/Thiết-Bị-Điện-Tử-cat.2365',
  'name': '_Thiết-Bị-Điện-Tử-cat.2365',
  'label': 'Thiết Bị Điện Tử'},
 {'relativelink': '/Nhà-Cửa-Đời-Sống-cat.87',
  'directlink': 'https://shopee.vn/Nhà-Cửa-Đời-Sống-cat.87',
  'name': '_Nhà-Cửa-Đời-Sống-cat.87',
  'label': 'Nhà Cửa & Đời Sống'},
 {'relativelink': '/Máy-tính-Laptop-cat.13030',
  'directlink': 'https://shopee.vn/Máy-tính-Laptop-cat.13030',
  'name': '_Máy-tính-Laptop-cat.13030',
  'label': 'Máy tính & Laptop'},
 {'relativelink': '/Sức-Khỏe-Sắc-Đẹp-cat.160',
  'directlink': 'https://shopee.vn/Sức-Khỏe-Sắc-Đẹp-cat.160',
  'name': '_Sức-Khỏe-Sắc-Đẹp-cat.160',
  'label': 'Sức Khỏe & Sắc Đẹp'},
 {'relativelink': '/Máy-ảnh-Máy-quay-phim-cat.13033',
  'directlink': 'https://shopee.vn/Máy-ảnh-Máy-quay-phim-cat.13033',
  'name': '_Máy-ảnh-Máy-quay-phim-cat.13033',
  'label': 'Máy ảnh - Máy quay phim'},
 {'relativelink': '/Giày-Dép-Nữ-cat.161',
  'directlink': 'https://shopee.vn/Giày-Dép-Nữ-cat.161',
  'name': '_Giày-Dép-Nữ-cat.161',
  'label': 'Giày Dép Nữ'},
 {'relativelink': '/Đồng-Hồ-cat.9607',
  'directlink': 'https://shopee.vn/Đồng-Hồ-cat.9607',
  'name': '_Đồng-Hồ-cat.9607',
  'label': 'Đồng Hồ'},
 {'relativelink': '/Túi-Ví-cat.162',
  'directlink': 'https://shopee.vn/Túi-Ví-cat.162',
  'name': '_Túi-Ví-cat.162',
  'label': 'Túi Ví'},
 {'relativelink': '/Giày-Dép-Nam-cat.2429',
  'directlink': 'https://shopee.vn/Giày-Dép-Nam-cat.2429',
  'name': '_Giày-Dép-Nam-cat.2429',
  'label': 'Giày Dép Nam'},
 {'relativelink': '/Phụ-Kiện-Thời-Trang-cat.80',
  'directlink': 'https://shopee.vn/Phụ-Kiện-Thời-Trang-cat.80',
  'name': '_Phụ-Kiện-Thời-Trang-cat.80',
  'label': 'Phụ Kiện Thời Trang'},
 {'relativelink': '/Thiết-Bị-Điện-Gia-Dụng-cat.2353',
  'directlink': 'https://shopee.vn/Thiết-Bị-Điện-Gia-Dụng-cat.2353',
  'name': '_Thiết-Bị-Điện-Gia-Dụng-cat.2353',
  'label': 'Thiết Bị Điện Gia Dụng'},
 {'relativelink': '/Bách-Hoá-Online-cat.9824',
  'directlink': 'https://shopee.vn/Bách-Hoá-Online-cat.9824',
  'name': '_Bách-Hoá-Online-cat.9824',
  'label': 'Bách Hoá Online'},
 {'relativelink': '/Thể-Thao-Du-Lịch-cat.9675',
  'directlink': 'https://shopee.vn/Thể-Thao-Du-Lịch-cat.9675',
  'name': '_Thể-Thao-Du-Lịch-cat.9675',
  'label': 'Thể Thao & Du Lịch'},
 {'relativelink': '/Voucher-Dịch-vụ-cat.12938',
  'directlink': 'https://shopee.vn/Voucher-Dịch-vụ-cat.12938',
  'name': '_Voucher-Dịch-vụ-cat.12938',
  'label': 'Voucher & Dịch vụ'},
 {'relativelink': '/Ô-tô-xe-máy-xe-đạp-cat.12494',
  'directlink': 'https://shopee.vn/Ô-tô-xe-máy-xe-đạp-cat.12494',
  'name': '_Ô-tô-xe-máy-xe-đạp-cat.12494',
  'label': 'Ô tô - xe máy - xe đạp'},
 {'relativelink': '/Đồ-Chơi-cat.13242',
  'directlink': 'https://shopee.vn/Đồ-Chơi-cat.13242',
  'name': '_Đồ-Chơi-cat.13242',
  'label': 'Đồ Chơi'},
 {'relativelink': '/Giặt-giũ-Chăm-sóc-nhà-cửa-cat.17101',
  'directlink': 'https://shopee.vn/Giặt-giũ-Chăm-sóc-nhà-cửa-cat.17101',
  'name': '_Giặt-giũ-Chăm-sóc-nhà-cửa-cat.17101',
  'label': 'Giặt giũ & Chăm sóc nhà cửa'},
 {'relativelink': '/Thời-Trang-Trẻ-Em-cat.16770',
  'directlink': 'https://shopee.vn/Thời-Trang-Trẻ-Em-cat.16770',
  'name': '_Thời-Trang-Trẻ-Em-cat.16770',
  'label': 'Thời Trang Trẻ Em'},
 {'relativelink': '/Sản-Phẩm-Khác-cat.91',
  'directlink': 'https://shopee.vn/Sản-Phẩm-Khác-cat.91',
  'name': '_Sản-Phẩm-Khác-cat.91',
  'label': 'Sản Phẩm Khác'}]

def scrap_data(cat):
    """Get item data from a category page and write to csv"""
    global OBSERVATION
    soup = BeautifulSoup(BROWSER.page_source, 'lxml')
    page_count = 100
    log.info('Shopee limited the number of scraped items to 1500 items per category.')
    try:
        i = 0
        while i < int(page_count):
            list = soup.find_all('div', class_='shopee-search-item-result__item')
            for item in list:
                row = {}
                item_id = item.find('a')
                if item_id != None:
                    item_id = item_id.get('href').strip()
                    item_id = item_id.split('-i.')
                    item_id = item_id[len(item_id)-1]
                    item_id = item_id.strip()
                    row['id'] = item_id
                if item.find('div', class_='yQmmFK _1POlWt _36CEnF') != None:
                    good_name = item.find('div', class_='yQmmFK _1POlWt _36CEnF').text.strip()
                    row['good_name'] = good_name
                else:
                    good_name = None
                if item.find('span', class_='_29R_un') != None:
                    price = item.find('span', class_='_29R_un').text.strip()
                    row['price'] = price
                else:
                    price = None
                if item.find('div', class_='WTFwws _3f05Zc _3_-SiN') != None:
                    old_price = item.find('div', class_='WTFwws _3f05Zc _3_-SiN').text.strip()
                    old_price = old_price.split('₫')[1]
                    old_price = old_price.strip()
                    row['old_price'] = old_price
                else:
                    old_price = None
                if item.find('div', class_='_2CWevj') != None:
                    location = item.find('div', class_='_2CWevj').text.strip()
                    row['location'] = location
                else:
                    location = None
                row['category'] = cat['label']
                row['date'] = DATE
                OBSERVATION += 1
                write_data(row)
            i += 1
    except Exception as e:
        log.error("Error on " + BROWSER.current_url)
        log.info(type(e).__name__ + str(e))
        pass


def write_data(item_data):
    """Write an item data as a row in csv. Create new file if needed"""
    fieldnames = ['good_name', 'price', 'old_price', 'id', 'location',
                  'category', 'date']
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
        log.info("Compressing %s item(s)", str(OBSERVATION))
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
