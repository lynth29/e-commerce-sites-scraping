#!/usr/bin/python3
# -*- coding: utf-8 -*-

# Import essential libraries
## Work with files and folders
import sys
import os
from pathlib import Path
## Work with time
import time
import datetime
from time import sleep
## Handle data
import re
import random
import pandas as pd
import numpy as np

# Parameters
SITE_NAME = "coop"
PROJECT_PATH = Path(__file__).absolute().parents[1]
PATH_CSV = os.path.join(PROJECT_PATH, "csv", SITE_NAME)
PATH_LOG = os.path.join(PROJECT_PATH, "log")
CLEAN_CSV = os.path.join(PROJECT_PATH, "clean_csv", SITE_NAME)

# Import other functions
sys.path.append('.')
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from helpers.crawl import *
from helpers.logging import *
from helpers.write import *
from helpers.read import *

# Define class

class Coop:

    def __init__(self, driver):
        # Parameters
        self.BROWSER = driver
        self.BASE_URL = "https://cooponline.vn"
        self.DATE = str(datetime.date.today())
        self.OBSERVATION = 0
        # Scroll options
        self.SCROLL_PAUSE_TIME = 5
        # Classes
        self.wr = CSV_write("coop")

    def choose_location(self):
        """Choose shopping location on cooponline.vn"""
        # Access url
        self.BROWSER.get(self.BASE_URL)
        sleep(2)
        # Choose mart
        mart = Select(self.BROWSER.find_element_by_xpath("(//select)[2]"))
        mart.select_by_index(1) # Tan Phong
        sleep(2)
        # Click button
        self.BROWSER.find_element_by_xpath("(//button)[2]").click()

    def disable_sub(self):
        """Disable subscription popup"""
        try:
            wait = WebDriverWait(self.BROWSER, 60).until(EC.presence_of_element_located((By.ID, "onesignal-slidedown-dialog")))
            sleep(2)
            self.BROWSER.find_element_by_xpath("//button[contains(@class, 'align-right secondary')]").click()
        except TimeoutException:
            pass

    def get_category_list(self):
        """Get list of relative categories directories from the top page"""
        # Access to browser
        self.BROWSER.get(self.BASE_URL)
        sleep(5)
        # Get soup
        toppage_soup = BeautifulSoup(self.BROWSER.page_source, "lxml")
        # Get categories
        categories_bar = [toppage_soup.findAll("ul", {'class': 'megamenu'})]
        categories_bar = [item for sublist in categories_bar for item in sublist]
        categories_bar = [categories_bar[1]]
        categories_tag = [cat.findAll('li') for cat in categories_bar]
        categories_tag = [item for sublist in categories_tag for item in sublist]
        categories = [cat.find_all('a') for cat in categories_tag]
        categories = [item for sublist in categories for item in sublist]
        categories = categories[2:]
        # Create an empty list to store categories' information
        page_list = []
        for cat in categories:
            next_page = {}
            link = re.sub(".+cooponline\\.vn", "", cat['href'])
            next_page['relativelink'] = link
            next_page['directlink'] = self.BASE_URL + link
            name = re.sub("/|\\?.=", "_", link)
            next_page['name'] = re.sub("_production","", name)
            next_page['label'] = re.sub("\n                                                                                                            |\n","",cat.text)
            page_list.append(next_page)
        # Remove duplicates
        page_list = [dict(t) for t in set(tuple(i.items()) for i in page_list)]
        return page_list

    def scrap_data(self, cat):
        """Get item data from a category page and self.write to csv"""
        # Access
        self.BROWSER.get(cat['directlink'])
        # Get all products appeared by scrolling
        # Wait to load elements
        wait = WebDriverWait(self.BROWSER, 60)
        try:
            wait.until(EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'product-image-container second_img')]")))
            scrape_test = self.BROWSER.find_elements_by_xpath("//div[contains(@class, 'product-image-container second_img')]")
            if scrape_test:
                log.info("There are elements!")
            else:
                log.info("Cannnot find the elements!")
        except TimeoutException:
            log.info("Timeout!")
            pass
        # Get soup
        soup = BeautifulSoup(self.BROWSER.page_source, 'lxml')
        # Get category name
        cat_name = soup.find('h3', {'class':'title-category'})
        attempts_limit = 5
        if cat_name == None:
            attempts = 0
            while attempts < attempts_limit:
                try:
                    cat_name = cat_name.text
                except:
                    attempts += 1
                    log.warning("Try getting cat_name again")
            else:
                log.error(f"Cannot download get cat_name")
                cat_name = ""
        else:
            cat_name = cat_name.text
        # Click see_more button as many as possible
        while True:
            try:
                see_more = self.BROWSER.find_element_by_xpath("//button[contains(@class, 'btn-success')]")
                self.BROWSER.execute_script("arguments[0].click();", see_more)
            except IGNORED_EXCEPTIONS:
                log.info('Clicked all see_more button as much as possible in ' + cat_name + ' category.')
                break
        # Scraping product's data
        try:
            soup = BeautifulSoup(self.BROWSER.page_source, 'lxml')
            sleep(10)
            # Get all products' holders
            list = soup.find_all('div', {'class': 'product-item-container'})
            log.info('Found ' + str(len(list)) + ' products')
            # Get main category and sub-category
            directory = soup.find_all('span', {'property': 'name'})
            if len(directory) != 1:
                subdir = directory[1].text.strip()
            else:
                subdir = directory[0].text.strip()
            # Scraping data
            for item in list:
                row = {}
                # Name
                if item.find('h4', {'class':'title_product_lmh'}) != None:
                    good_name = item.find('h4', {'class':'title_product_lmh'}).text
                    row['good_name'] = good_name
                else:
                    None
                # Price
                if item.find('span', class_='price-new') != None:
                    price = item.find('span', class_='price-new').text.strip()
                    price = price.split('đ')[0]
                    price = price.strip()
                    row['price'] = price
                else:
                    None
                # Old price
                if item.find('span', class_='price-old') != None:
                    old_price = item.find('span', class_='price-old').text.strip()
                    old_price = old_price.split('đ')[0]
                    old_price = old_price.strip()
                    row['old_price'] = old_price
                else:
                    None
                # ID
                if item.find('a', {'target':'_self'}) != None:
                    item_id = item.find('a', {'target':'_self'}).get('href')
                    item_id = re.sub(".+products/|/","",item_id)
                    row['id'] = item_id
                # Sub category
                row['parent_category'] = subdir
                # Category
                row['category'] = cat['label']
                # Date
                row['date'] = self.DATE
                self.OBSERVATION += 1
                self.wr.write_data(row)
            log.info('Finished scraping ' + cat_name + ' category.')
        except Exception as e:
            log.error("Error on " + self.BROWSER.current_url)
            log.info(type(e).__name__ + str(e))
            pass

    def cleaning_data(self):
        # Import CSV file
        os.chdir(PATH_CSV)
        raw = pd.read_csv(SITE_NAME + '_' + self.DATE + '.csv')
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
        if raw.old_price.isnull().any():
            raw.old_price = raw.old_price.fillna(0)
            raw.old_price = np.where(raw.old_price == 0, raw.price, raw.old_price)
        log.info('Have a look at the dtypes after converting:')
        log.info(raw.info())
        os.remove(SITE_NAME + '_' + self.DATE + '.csv')

        # Export to new CSV
        os.chdir(PROJECT_PATH)
        os.chdir(CLEAN_CSV)
        raw.to_csv(SITE_NAME + '_' + self.DATE + '_clean.csv')
        log.info('Finished cleaning data')
