#!/usr/bin/python3
# -*- coding: utf-8 -*-

# Import essential libraries
# Work with files and folders
import sys
import os
sys.path.append('.')
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import modules
from helpers.read import *
from helpers.write import *
from helpers.crawl import *

# Parameters
SITE_NAME = "fujimart"
PATH_CSV = os.path.join(PROJECT_PATH, "csv", SITE_NAME)

# Define class
class FujiMart:

    def __init__(self, driver):
        # Parameters
        self.BROWSER = driver
        self.BASE_URL = "https://www.fujimart.vn"
        self.OBSERVATION = 0
        # Define wait
        self.wait = WebDriverWait(self.BROWSER, 10)
        # Scroll options
        self.SCROLL_PAUSE_TIME = 5
        # Classes
        self.wr = CSV_write("bachhoaxanh")

    def get_category_list(self):
        """Get list of relative categories directories from the top page"""
        # Access to browser
        res = requests.get(self.BASE_URL)
        # Get soup
        toppage_soup = BeautifulSoup(res.content, features="lxml")
        # Get categories
        categories_bar = toppage_soup.find('ul', class_='multi-level').find_all('a')
        # Create an empty list to store categories' information
        page_list = []
        for cat in categories_bar:
            row = {}
            row["cat_l1"] = cat.text.strip()
            row["cat_l2"] = ""
            row["cat_l3"] = ""
            row["href"] = cat['href']
            page_list.append(row)
        # Remove duplicates
        page_list = [dict(t) for t in set(tuple(i.items()) for i in page_list)]
        return page_list

    def scrap_data(self, cat):
        """Get item data from a category page and self.write to csv"""
        # Access
        res = requests.get(cat['href'] + "?limit=100")
        # Get soup
        soup = BeautifulSoup(res.content, features='lxml')
        # Get pages num
        try:
            pages_num = len(soup.find('ul', class_="pagination").find_all('li'))
        except AttributeError:
            pages_num = 1
        # Get all products
        all_products = []
        for i in range(pages_num):
            if i > 0:
                res = requests.get(cat['href'] + "?limit=100&page=" + str(i+1))
                soup = BeautifulSoup(res.content, features="lxml")
            products = soup.find_all('div', class_='product-thumb')
            all_products.extend(products)
        print('Found ' + str(len(all_products)) + ' products')
        # Scraping data
        for item in all_products:
            row = {}
            row['cat_l1'] = cat['cat_l1']
            row['cat_l2'] = cat['cat_l2']
            row['cat_l3'] = cat['cat_l3']
            # Name
            row['product_name'] = item.find('h4').text.strip() if item.find('h4') != None else None
            self.OBSERVATION += 1
            self.wr.write_data(row)
        print('Finished scraping ' + cat_name + ' category.')
