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
SITE_NAME = "kidsplaza"
PATH_CSV = os.path.join(PROJECT_PATH, "csv", SITE_NAME)

# Define class
class KidsPlaza:
    def __init__(self, driver):
        # Parameters
        self.BROWSER = driver
        self.BASE_URL = "https://www.kidsplaza.vn"
        self.OBSERVATION = 0
        # Define wait
        self.wait = WebDriverWait(self.BROWSER, 10)
        # Scroll options
        self.SCROLL_PAUSE_TIME = 5
        # Classes
        self.wr = CSV_write("kidsplaza")

    def get_category_list(self):
        """Get list of relative categories directories from the top page"""
        # Access to browser
        self.BROWSER.get(self.BASE_URL)
        # Get soup
        toppage_soup = BeautifulSoup(self.BROWSER.page_source, features="lxml")
        # Get categories
        categories_bar = toppage_soup.find("ul", attrs={"role": "menu"}).find_all(
            "li", attrs={"role": "presentation"}
        )
        # Create an empty list to store categories' information
        page_list = []
        for cat in categories_bar:
            # Get cat level1
            parent_cat = cat.find("a").text.strip()
            # Get all cat level2
            child_cats = cat.find_all("li", class_="level1")
            for child in child_cats:
                # Get cat level2
                cat_l2 = child.find("a").text.strip()
                # Check whether lv3 categories exist or not
                child_check = child.find("ul")
                # If exists
                if child_check != None:
                    # Access to child cat
                    self.BROWSER.get(child.find("a")["href"])
                    sleep(2)
                    sub_soup = BeautifulSoup(self.BROWSER.page_source, features="lxml")
                    grandchild_cats = sub_soup.find("div", class_="list-category")
                    grandchild_cats = grandchild_cats.find_all("a")
                    for grandchild in grandchild_cats:
                        row = {}
                        row["cat_l1"] = parent_cat
                        row["cat_l2"] = cat_l2
                        row["cat_l3"] = grandchild.text.strip()
                        row["href"] = grandchild["href"]
                        page_list.append(row)
                # If none set cat_l3 as blank
                else:
                    row = {}
                    row["cat_l1"] = parent_cat
                    row["cat_l2"] = cat_l2
                    row["cat_l3"] = ""
                    row["href"] = child.find("a")["href"]
                    page_list.append(row)
        # Remove duplicates
        page_list = [dict(t) for t in set(tuple(i.items()) for i in page_list)]
        return page_list

    def scrap_data(self, cat):
        """Get item data from a category page and self.write to csv"""
        # Define cat_name
        cat_name = cat["cat_l3"] if cat["cat_l3"] != "" else cat["cat_l2"]
        # Access
        res = requests.get(cat["href"])
        # Get soup
        soup = BeautifulSoup(res.content, features="lxml")
        # Get page numbers
        page_holder = soup.find("ul", attrs={"aria-labelledby": "paging-label"})
        if page_holder != None:
            page_num = len(page_holder.find_all("li")) - 1
        else:
            page_num = 1
        # Get all product holders
        all_products = []
        for page in range(1, page_num + 1):
            if page != 1:
                res_page = requests.get(res.url + "?p=" + str(page))
                soup = BeautifulSoup(res_page.content, features="lxml")
            products_holder = soup.find(
                "ol", class_="products list items product-items"
            )
            products = products_holder.find_all(
                "div", attrs={"data-container": "product-grid"}
            )
            all_products.extend(products)
        print("Found " + str(len(all_products)) + " products in " + cat_name)
        # Scraping data
        for item in all_products:
            row = {}
            row["cat_l1"] = cat["cat_l1"]
            row["cat_l2"] = cat["cat_l2"]
            row["cat_l3"] = cat["cat_l3"]
            # Name
            row["product_name"] = item.find("h3").text.strip()
            # Brand
            href = item.find("a")["href"]
            prod_res = requests.get(href)
            prod_soup = BeautifulSoup(prod_res.content, features="lxml")
            try:
                brand_holder = prod_soup.find("div", class_="product attribute brand")
                if len(brand_holder) > 0:
                    row["brand"] = brand_holder.find(class_="value").text.strip()
                else:
                    row["brand"] = ""
            except AttributeError:
                row["brand"] = ""
            row["href"] = href
            self.OBSERVATION += 1
            self.wr.write_data(row)
        print("Finished scraping " + cat_name + " category.")
