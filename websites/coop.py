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
SITE_NAME = "coop"
PATH_CSV = os.path.join(PROJECT_PATH, "csv", SITE_NAME)

# Define class
class Coop:

    def __init__(self, driver):
        # Parameters
        self.BROWSER = driver
        self.BASE_URL = "https://cooponline.vn"
        self.DATE = str(datetime.date.today())
        self.OBSERVATION = 0
        # Define wait
        self.wait = WebDriverWait(self.BROWSER, 10)
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
        district = Select(self.BROWSER.find_element(By.XPATH, "(//select)[2]"))
        district.select_by_index(1)  # 01
        sleep(2)
        ward = Select(self.BROWSER.find_element(By.XPATH, "(//select)[3]"))
        ward.select_by_index(1)  # Ben Thanh
        sleep(2)
        mart = Select(self.BROWSER.find_element(By.XPATH, "(//select)[4]"))
        mart.select_by_index(1)  # Tan Phong
        sleep(2)
        # Click button
        self.BROWSER.find_element(By.XPATH, "//button[contains(text(), 'Xác nhận')]").click()
        sleep(2)

    def disable_sub(self):
        """Disable subscription popup"""
        try:
            self.wait.until(
                EC.presence_of_element_located((By.ID, "slidedown-footer")))
            self.BROWSER.find_element(By.XPATH, "//button[contains(@id, 'onesignal-slidedown-cancel-button')]").click()
        except TimeoutException:
            pass

    def get_category_list(self):
        """Get list of relative categories directories from the top page"""
        # Access to browser
        self.BROWSER.get(self.BASE_URL)
        sleep(5)
        # Get soup
        toppage_soup = BeautifulSoup(self.BROWSER.page_source, features="lxml")
        # Get categories
        categories_bar = toppage_soup.find("ul", {'class': 'megamenu'}).find_all('li')
        # Create an empty list to store categories' information
        page_list = []
        for cat in categories_bar:
            cat_l1 = cat.find('a').text.strip()
            cat_l2s = cat.find_all('div', class_="menu")
            for child_cat in cat_l2s:
                cat_l2 = child_cat.find('a', class_="main-menu").text.strip()
                cat_l3s = child_cat.find_all('a', class_=None)
                for grandchild_cat in cat_l3s:
                    row = {}
                    row['cat_l1'] = cat_l1
                    row['cat_l2'] = cat_l2
                    row['cat_l3'] = grandchild_cat.text.strip()
                    row['href'] = grandchild_cat['href']
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
        # Click see_more button as many as possible
        while True:
            try:
                # Wait
                self.wait.until(
                    EC.presence_of_element_located((By.XPATH, "//span[contains(text(), ' Xem tiếp . . .')]")))
                see_more = self.BROWSER.find_element(By.XPATH, "/span[contains(text(), ' Xem tiếp . . .')]")
                see_more.click()
            except IGNORED_EXCEPTIONS:
                print(
                    'Clicked all see_more button as much as possible in ' + cat['cat_l3'] + ' category.')
                break
        # Scraping product's data
        # try:
        soup = BeautifulSoup(self.BROWSER.page_source, features='lxml')
        sleep(10)
        # Get all products' holders
        list = soup.find_all('div', {'class': 'product-item-container'})
        print('Found ' + str(len(list)) + ' products')
        # Scraping data
        for item in list:
            row = {}
            row['cat_l1'] = cat['cat_l1']
            row['cat_l2'] = cat['cat_l2']
            row['cat_l3'] = cat['cat_l3']
            # Name
            product_name = item.find('div', class_='caption').find('a').text.strip()
            row['product_name'] = product_name
            # Brand
            href = item.find('a')['href']
            prod_res = requests.get(href)
            prod_soup = BeautifulSoup(prod_res.content, features="lxml")
            try:
                brand_holder = prod_soup.find('h4').find('a')
                row['brand'] = brand_holder.text.strip()
            except AttributeError:
                row['brand'] = ""
            row['href'] = href
            # # Price
            # if item.find('span', class_='price-new col-xs-12') != None:
            #     price = item.find('span', class_='price-new col-xs-12').text.strip()
            #     price = price.split('đ')[0].strip()
            #     price = price.replace(',',"")
            #     row['price'] = int(price)
            # else:
            #     None
            # # Old price
            # if item.find('span', class_='price-old') != None:
            #     old_price = item.find(
            #         'span', class_='price-old').text.strip()
            #     old_price = old_price.split('đ')[0].strip()
            #     old_price = old_price.replace(',',"")
            #     row['old_price'] = int(old_price)
            # else:
            #     None
            self.OBSERVATION += 1
            self.wr.write_data(row)
        print('Finished scraping ' + cat['cat_l3'] + ' category.')
        # except Exception as e:
        #     print("Error on " + self.BROWSER.current_url)
        #     print(type(e).__name__ + str(e))
        #     pass
