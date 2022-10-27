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
SITE_NAME = "bachhoaxanh"
PATH_CSV = os.path.join(PROJECT_PATH, "csv", SITE_NAME)

# Define class
class BachHoaXanh:

    def __init__(self, driver):
        # Parameters
        self.BROWSER = driver
        self.BASE_URL = "https://www.bachhoaxanh.com"
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
        categories_bar = toppage_soup.find_all('li', attrs={"class":"CateItem"})
        # Create an empty list to store categories' information
        page_list = []
        for cat in categories_bar:
            parent_cat = cat.find('div', class_="nav-parent").text.strip()
            child_cats = cat.find_all('div', class_='parent')
            for child in child_cats:
                # Check whether lv3 categories exist or not
                child_res = requests.get(self.BASE_URL + child.find('a')['href'])
                child_soup = BeautifulSoup(child_res.content, features="lxml")
                lv3_categories = child_soup.find_all('div', class_='groupfeature')
                # If none set l3 as blank
                if len(lv3_categories) == 0:
                    row = {}
                    row["cat_l1"] = parent_cat
                    row["cat_l2"] = child.text.strip()
                    row["cat_l3"] = ""
                    row["href"] = child.find('a')['href']
                    page_list.append(row)
                else:
                    for child_cat in lv3_categories:
                        row = {}
                        row["cat_l1"] = parent_cat
                        row["cat_l2"] = child.text.strip()
                        row["cat_l3"] = child_cat.find('h2').text.strip()
                        row["href"] = child_cat.find('a')['href']
                        page_list.append(row)
        # Remove duplicates
        page_list = [dict(t) for t in set(tuple(i.items()) for i in page_list)]
        return page_list

    def scrap_data(self, cat):
        """Get item data from a category page and self.write to csv"""
        # Access
        self.BROWSER.get(self.BASE_URL + cat['href'])
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
