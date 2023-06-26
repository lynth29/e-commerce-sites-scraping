#!/usr/bin/python3
# -*- coding: utf-8 -*-

# Import essential libraries
# Work with files and folders
import sys
import os

sys.path.append(".")
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Import modules
from helpers.read import *
from helpers.write import *
from helpers.crawl import *

# Parameters
SITE_NAME = "cocoshop"
PATH_CSV = os.path.join(PROJECT_PATH, "csv", SITE_NAME)


# Define class
class Cocoshop:
    def __init__(self):
        # Parameters
        self.BASE_URL = "https://cocoshop.vn"
        self.session = Session().session
        self.DATE = str(datetime.date.today())
        self.OBSERVATION = 0
        # Classes
        self.wr = CSV_write("cocoshop")

    def get_category_list(self) -> list:
        """Get list of relative categories directories from thitruongsi.com"""
        # Send request to home_api
        home_res = self.session.get(self.BASE_URL)
        home_soup = BeautifulSoup(home_res.content, features="lxml")
        cat_bar = home_soup.find('ul', class_='vertical-menu-list').find_all('li')
        # Create an empty list to store categories' information
        page_list = []
        for cat in cat_bar:
            child_cat = cat.find_all('h4')
            if len(child_cat) > 0:
                for l2 in child_cat:
                    next_page = {}
                    next_page["cat_l1"] = cat.find('a', class_='parent')['title']
                    next_page["cat_l2"] = l2.find('a')["title"]
                    next_page["href"] = l2.find('a')["href"]
                    page_list.append(next_page)
            else:
                next_page = {}
                next_page["cat_l1"] = cat.find('a', class_='parent')['title']
                next_page["cat_l2"] = ""
                next_page["href"] = cat["href"]
                page_list.append(next_page)
        return page_list

    def scrap_data(self, cat: dict):
        """Get item data from a category page and self.write to csv"""
        print(f"Crawling {cat['cat_l2']}")
        # Get soup
        cat_res = self.session.get(self.BASE_URL + cat['href'])
        cat_soup = BeautifulSoup(cat_res.content, features="lxml")
        # Get page number
        page_holder = cat_soup.find('ul', class_='pagination')
        page = page_holder.find_all('li')[-2].text.strip()
        # Get all products by going through each page
        items_list = []
        for i in range(page):
            if i >= 1:
                cat_res = self.session.get(f"{cat['href']}page-{str(i+1)}/")
                cat_soup = BeautifulSoup(cat_res.content, features="lxml")
            items = cat_soup.find_all('div', class_='col-sm-12 col-md-6')
            items_list.extend(items)
        print("Found " + str(len(items_list)) + " products")
        # Get information of each item
        for item in items_list:
            try:
                row = {}
                # Get soup
                prod_res = self.session.get(item)
                prod_soup = BeautifulSoup(prod_res.content, features="lxml")
                # Product name
                name = prod_soup.find('h1', attrs={'id': 'titlepro2'}).text.strip()
                row["product_name"] = name
                alt_name = ""
                row["alt_name"] = alt_name
                # Price
                price = int(prod_soup.find('span', class_='money').text.split('đ')[0].replace('.', ''))
                row["price"] = price
                # Brand
                try:
                    brand = prod_soup.find('strong', text=re.compile('Thương hiệu')).next_sibling.replace('\xa0','')
                except TypeError:
                    brand = ""
                row["brand"] = brand
                # Barcode
                barcode = prod_soup.find('li', attrs={'id': 'titlecode2'}).find('strong').text.strip()
                row["barcode"] = barcode
                # Image
                image = prod_soup.find('img', class_='cloudzoom')['src']
                image = self.BASE_URL + image
                row["image"] = image
                # Volume
                try:
                    volume = prod_soup.find('strong', text=re.compile('Trọng lượng')).next_sibling.replace('\xa0','')
                except TypeError:
                    volume = ""
                row["volume"] = volume
                # Others
                row["cat_l1"] = cat["cat_l1"]
                row["cat_l2"] = cat["cat_l2"]
                row["href"] = item
                self.OBSERVATION += 1
                self.wr.write_data(row)
                time.sleep(1)
            except Exception as e:
                print("Error on " + str(item))
                print(type(e).__name__ + str(e))
                pass
