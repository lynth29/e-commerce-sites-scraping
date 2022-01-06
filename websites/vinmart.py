#!/usr/bin/python3
# -*- coding: utf-8 -*-

# Import essential libraries
# Work with files and folders
import sys
import os
sys.path.append('.')
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Parameters
SITE_NAME = "vinmart"
PATH_CSV = os.path.join(PROJECT_PATH, "csv", SITE_NAME)
PATH_LOG = os.path.join(PROJECT_PATH, "log")
CLEAN_CSV = os.path.join(PROJECT_PATH, "clean_csv", SITE_NAME)

# Import modules
from helpers.read import *
from helpers.write import *
from helpers.logging import *
from helpers.crawl import *

# Define class
class Vinmart:

    def __init__(self, driver):
        # Parameters
        self.BROWSER = driver
        self.BASE_URL = "https://winmart.vn"
        self.DATE = str(datetime.date.today())
        self.OBSERVATION = 0
        # Scroll options
        self.SCROLL_PAUSE_TIME = 5
        # Classes
        self.wr = CSV_write("vinmart")

    def choose_location(self):
        """Choose shopping location on winmart.vn"""
        # Access url
        self.BROWSER.get(self.BASE_URL)
        try:
            wait = WebDriverWait(self.BROWSER, 60).until(EC.element_to_be_clickable(
                (By.XPATH, "//span[contains(text(),'TP. Hà Nội')]")))
        except TimeoutException:
            pass
        sleep(2)
        # Choose city
        city = self.BROWSER.find_element_by_xpath(
            "//span[contains(text(),'TP. Hà Nội')]").click()  # Hà Nội
        sleep(2)
        # Choose district
        district = self.BROWSER.find_element_by_xpath(
            "//span[contains(text(),'Q. Hai Bà Trưng')]").click()  # Hai Bà Trưng
        sleep(2)
        # Choose ward
        ward = self.BROWSER.find_element_by_xpath(
            "//span[contains(text(),'P. Minh Khai')]").click()  # Minh Khai

    def get_category_list(self):
        """Get list of relative categories directories from winmart.vn"""
        # Access to browser
        self.BROWSER.get(self.BASE_URL)
        sleep(5)
        # Get soup
        toppage_soup = BeautifulSoup(self.BROWSER.page_source, "lxml")
        # Get categories
        categories_bar = [toppage_soup.findAll("a", {'class': 'menu-name'})]
        categories = [item for sublist in categories_bar for item in sublist]
        # Create an empty list to store categories' information
        page_list = []
        for cat in categories:
            next_page = {}
            link = cat.get('href')
            next_page['relativelink'] = link
            next_page['directlink'] = self.BASE_URL + link
            next_page['name'] = cat.text
            next_page['label'] = cat.text
            page_list.append(next_page)
        return page_list

    def scrap_data(self, cat):
        """Get item data from a category page and self.write to csv"""
        try:
            # Get all products appeared by scrolling
            self.BROWSER.get(cat['directlink'])

            # Get scroll height
            last_height = self.BROWSER.execute_script(
                "return document.body.scrollHeight")
            while True:
                # Scroll down to bottom
                self.BROWSER.execute_script(
                    "window.scrollTo(0, document.body.scrollHeight);")
                # Wait to load page
                sleep(self.SCROLL_PAUSE_TIME)
                # Calculate new scroll height and compare with last scroll height
                new_height = self.BROWSER.execute_script(
                    "return document.body.scrollHeight")
                if new_height == last_height:
                    break
                last_height = new_height

            # Get all products
            soup = BeautifulSoup(self.BROWSER.page_source, 'lxml')
            list = soup.find_all(
                'div', {'class': 'product-card-two__Card-sc-1lvbgq2-0 EvJvz product-card'})
            log.info('Found ' + str(len(list)) + ' products')
            for item in list:
                row = {}
                # Product name
                if item.find('h2', {'class': 'product-card-two__Title-sc-1lvbgq2-4 dokUNv'}) != None:
                    good_name = item.find(
                        'h2', {'class': 'product-card-two__Title-sc-1lvbgq2-4 dokUNv'}).text.strip()
                    row['good_name'] = good_name
                else:
                    None
                # Price
                if item.find('div', {'class': 'product-card-two__Price-sc-1lvbgq2-6 bMEYxB'}) != None:
                    price = item.find(
                        'div', {'class': 'product-card-two__Price-sc-1lvbgq2-6 bMEYxB'}).text.strip()
                    price = price.split('₫')[0]
                    price = price.strip()
                    row['price'] = price
                else:
                    None
                # Old price
                if item.find('div', {'class': 'product-card-two__SalePrice-sc-1lvbgq2-7 iZguIh'}) != None:
                    old_price = item.find(
                        'div', {'class': 'product-card-two__SalePrice-sc-1lvbgq2-7 iZguIh'}).text.strip()
                    old_price = old_price.split('₫')[0]
                    old_price = old_price.strip()
                    row['old_price'] = old_price
                else:
                    None
                # Item_id
                if item.find('a', {'class': ''}) != None:
                    item_id = item.find('a', {'class': ''}).get('href').strip()
                    item_id = item_id.split('--')
                    item_id = item_id[len(item_id) - 1]
                    item_id = item_id.strip()
                    row['id'] = item_id
                # Category
                row['parent_category'] = ''
                row['category'] = cat['label']
                row['date'] = self.DATE
                self.OBSERVATION += 1
                self.wr.write_data(row)
        except Exception as e:
            log.error("Error on " + self.BROWSER.current_url)
            log.info(type(e).__name__ + str(e))
            pass

    def cleaning_data():
        """Clean scraped data from winmart.vn"""
        # Import CSV file
        os.chdir(PATH_CSV)
        raw = pd.read_csv(SITE_NAME + '_' + self.DATE + '.csv')
        log.info('Imported CSV file to a dataframe')

        # Summarize the dataframe
        log.info(
            f"The dataframe has {raw.shape[0]} rows and {raw.shape[1]} columns.")
        log.info('Have a look at the dtypes:')
        log.info(raw.info())
        log.info('Are there any null value?:')
        log.info(raw.isnull().any())

        # Convert dtypes
        # Date
        raw.date = self.DATE
        raw.date = pd.to_datetime(raw.date)
        log.info('Finished converting Date.')
        # Price
        if raw.price.astype(str).str.contains('Đang cập nhật').any():
            raw.price = np.where(raw.price == 'Đang cập nhật', 0, raw.price)
            log.info('Finished handling Đang cập nhật')
        # Multiple price with 1000
        raw.price = raw.price * 1000
        log.info('Finished handling float dot in price')
        # Old price
        raw.old_price = raw.old_price * 1000
        log.info('Finished handling float dot in old_price')
        if raw.old_price.isnull().any():
            raw.old_price = raw.old_price.fillna(0)
            raw.old_price = np.where(
                raw.old_price == 0, raw.price, raw.old_price)
            log.info('Finished copy price to old_price')
        log.info('Have a look at the dtypes after converting:')
        log.info(raw.info())
        os.remove(SITE_NAME + '_' + self.DATE + '.csv')

        # Export to new CSV
        os.chdir(PROJECT_PATH)
        os.chdir(CLEAN_CSV)
        raw.to_csv(SITE_NAME + '_' + self.DATE + '_hn_clean.csv')
        log.info('Finished cleaning data')
