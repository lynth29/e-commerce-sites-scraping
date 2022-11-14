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
SITE_NAME = "bibomart"
PATH_CSV = os.path.join(PROJECT_PATH, "csv", SITE_NAME)

# Define class
class BiboMart:

    def __init__(self, driver):
        # Parameters
        self.BROWSER = driver
        self.BASE_URL = "https://bibomart.com.vn"
        self.OBSERVATION = 0
        # Define wait
        self.wait = WebDriverWait(self.BROWSER, 10)
        # Scroll options
        self.SCROLL_PAUSE_TIME = 5
        # Classes
        self.wr = CSV_write("bibomart")

    def get_category_list(self):
        """Get list of relative categories directories from the top page"""
        # Access to browser
        res = requests.get(self.BASE_URL)
        # Get soup
        toppage_soup = BeautifulSoup(res.content, features="lxml")
        # Get categories
        categories_bar = toppage_soup.find_all('li', class_='menu megamenu-item has-child has-content')
        # Create an empty list to store categories' information
        page_list = []
        for cat in categories_bar:
            parent_cat = cat.find('a').text.strip()
            parent_href = cat.find('a')['href']
            parent_res = requests.get(parent_href)
            parent_soup = BeautifulSoup(parent_res.content, features="lxml")
            child_cats = parent_soup.find('ul', class_='cate-1').find_all('li')
            for child in child_cats:
                # Check whether lv3 categories exist or not
                child_res = requests.get(child.find('a')['href'])
                child_soup = BeautifulSoup(child_res.content, features="lxml")
                try:
                    grandchild_cats = child_soup.find('ul', class_='cate-2').find_all('li')
                    for grandchild in grandchild_cats:
                        row = {}
                        row["cat_l1"] = parent_cat
                        row["cat_l2"] = child.text.strip()
                        row["cat_l3"] = grandchild.text.strip()
                        row["href"] = grandchild.find('a')['href']
                        page_list.append(row)
                except AttributeError:
                    row = {}
                    row["cat_l1"] = parent_cat
                    row["cat_l2"] = child.text.strip()
                    row["cat_l3"] = ""
                    row["href"] = child.find('a')['href']
                    page_list.append(row)
        # Remove duplicates
        page_list = [dict(t) for t in set(tuple(i.items()) for i in page_list)]
        return page_list

    def scrap_data(self, cat):
        """Get item data from a category page and self.write to csv"""
        # Access
        self.BROWSER.get(cat['href'])
        # Get soup
        soup = BeautifulSoup(self.BROWSER.page_source, 'lxml')
        # Define cat_name
        cat_name = cat["cat_l3"] if cat["cat_l3"] != "" else cat["cat_l2"]
        # Click see_more button as many as possible
        while True:
            try:
                # Wait
                self.wait.until(
                    EC.presence_of_element_located((By.XPATH, "//a[@class='viewmore']")))
                see_more = self.BROWSER.find_element(By.XPATH, "//a[@class='viewmore']")
                see_more.click()
                sleep(1)
            except IGNORED_EXCEPTIONS:
                print(
                    'Clicked all see_more button as much as possible in ' + cat_name + ' category.')
                break
        # Scraping product's data
        soup = BeautifulSoup(self.BROWSER.page_source, 'lxml')
        # Get all products' holders
        products = soup.find('ul', class_='cate')
        list = products.find_all('li')[:-1]
        print('Found ' + str(len(list)) + ' products')
        # Scraping data
        for item in list:
            row = {}
            row['cat_l1'] = cat['cat_l1']
            row['cat_l2'] = cat['cat_l2']
            row['cat_l3'] = cat['cat_l3']
            # Name
            row['product_name'] = item.find('h3').text.strip() if item.find('h3') != None else None
            self.OBSERVATION += 1
            self.wr.write_data(row)
        print('Finished scraping ' + cat_name + ' category.')
