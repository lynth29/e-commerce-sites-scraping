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
SITE_NAME = "winmart"
PATH_CSV = os.path.join(PROJECT_PATH, "csv", SITE_NAME)


# Define class
class Winmart:
    def __init__(self, driver):
        # Parameters
        self.BROWSER = driver
        self.BASE_URL = "https://winmart.vn"
        self.DATE = str(datetime.date.today())
        self.OBSERVATION = 0
        self.wait = WebDriverWait(self.BROWSER, 10)
        # Scroll options
        self.SCROLL_PAUSE_TIME = 5
        # Classes
        self.wr = CSV_write("winmart")

    def choose_location(self):
        """Choose shopping location on winmart.vn"""
        # Access url
        self.BROWSER.get(self.BASE_URL)
        try:
            self.wait.until(
                EC.element_to_be_clickable(
                    (By.XPATH, "//span[contains(text(),'TP. Hà Nội')]")
                )
            )
        except TimeoutException:
            pass
        # Choose city
        city = self.BROWSER.find_element(
            By.XPATH, "//span[contains(text(),'TP. Hà Nội')]"
        ).click()  # Hà Nội
        sleep(2)
        # Choose district
        district = self.BROWSER.find_element(
            By.XPATH, "//span[contains(text(),'Q. Hai Bà Trưng')]"
        ).click()  # Hai Bà Trưng
        sleep(2)
        # Choose ward
        ward = self.BROWSER.find_element(
            By.XPATH, "//span[contains(text(),'P. Minh Khai')]"
        ).click()  # Minh Khai

    def get_category_list(self):
        """Get list of relative categories directories from winmart.vn"""
        # Access to browser
        self.BROWSER.get(self.BASE_URL)
        sleep(5)
        # Get soup
        toppage_soup = BeautifulSoup(self.BROWSER.page_source, "lxml")
        # Get categories
        categories_bar = toppage_soup.find_all("li", {"class": "menu-item"})
        # Create an empty list to store categories' information
        page_list = []
        for cat in categories_bar:
            cat_l1 = cat.find("a").text.strip()
            child_cats = cat.find_all("li", class_="sub-menu-item")
            if len(child_cats) > 0:
                for child in child_cats:
                    next_page = {}
                    next_page["cat_l1"] = cat_l1
                    next_page["cat_l2"] = child.find("a").text.strip()
                    next_page["cat_l3"] = ""
                    next_page["href"] = child.find("a")["href"]
                    page_list.append(next_page)
            else:
                next_page = {}
                next_page["cat_l1"] = cat_l1
                next_page["cat_l2"] = ""
                next_page["cat_l3"] = ""
                next_page["href"] = cat.find("a")["href"]
                page_list.append(next_page)
        return page_list

    def scrap_data(self, cat):
        """Get item data from a category page and self.write to csv"""
        # try:
        # Get all products appeared by scrolling
        self.BROWSER.get(self.BASE_URL + cat["href"])
        # Get scroll height
        last_height = self.BROWSER.execute_script("return document.body.scrollHeight")
        while True:
            # Scroll down to bottom
            self.BROWSER.execute_script(
                "window.scrollTo(0, document.body.scrollHeight);"
            )
            # Wait to load page
            sleep(self.SCROLL_PAUSE_TIME)
            # Calculate new scroll height and compare with last scroll height
            new_height = self.BROWSER.execute_script(
                "return document.body.scrollHeight"
            )
            if new_height == last_height:
                break
            last_height = new_height
        # Get all products
        soup = BeautifulSoup(self.BROWSER.page_source, "lxml")
        list = soup.find_all(
            "div", {"class": "product-card-two__Card-sc-1lvbgq2-0 fABVCu product-card"}
        )
        print("Found " + str(len(list)) + " products")
        for item in list:
            row = {}
            # Product name
            row["product_name"] = (
                item.find("h6").text.strip() if item.find("h6") != None else None
            )
            # # Price
            # if item.find('div', {'class': 'product-card-two__Price-sc-1lvbgq2-6 hrPTUd'}) != None:
            #     price = item.find(
            #         'div', {'class': 'product-card-two__Price-sc-1lvbgq2-6 hrPTUd'}).text.strip()
            #     price = price.split('\xa0₫')[0]
            #     price = price.replace('.','')
            #     row['price'] = int(price)
            # else:
            #     None
            # # Old price
            # if item.find('div', {'class': 'product-card-two__SalePrice-sc-1lvbgq2-7 djkQAj'}) != None:
            #     old_price = item.find(
            #         'div', {'class': 'product-card-two__SalePrice-sc-1lvbgq2-7 djkQAj'}).text.strip()
            #     old_price = old_price.split('\xa0₫')[0]
            #     old_price = old_price.replace('.','')
            #     row['old_price'] = int(old_price)
            # else:
            #     None
            # Category
            row["cat_l1"] = cat["cat_l1"]
            row["cat_l2"] = cat["cat_l2"]
            row["cat_l3"] = cat["cat_l3"]
            row["brand"] = ""
            row["href"] = self.BASE_URL + item.find("a")["href"]
            self.OBSERVATION += 1
            self.wr.write_data(row)
        # except Exception as e:
        #     print("Error on " + self.BROWSER.current_url)
        #     print(type(e).__name__ + str(e))
        #     pass
