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
SITE_NAME = "concung"
PATH_CSV = os.path.join(PROJECT_PATH, "csv", SITE_NAME)

# Define class
class ConCung:
    def __init__(self):
        # Parameters
        self.BASE_URL = "https://concung.com"
        self.headers = {
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36 Edg/107.0.1418.42"
        }
        self.OBSERVATION = 0
        self.wr = CSV_write("concung")

    def get_category_list(self) -> list:
        """Get list of relative categories directories from the top page"""
        # Access to browser
        res = requests.get(self.BASE_URL, headers=self.headers)
        # Get soup
        toppage_soup = BeautifulSoup(res.content, features="lxml")
        # Get categories
        categories_bar = toppage_soup.find(
            "ul",
            class_="menu-main container pb-3 font-12 d-flex border border-top-0 pl-3",
        )
        categories_bar = categories_bar.find_all(
            "li", class_=re.compile(r"menu-1 has-submenu")
        )
        # Create an empty list to store categories' information
        page_list = []
        for cat in categories_bar:
            cat_l1 = cat.find("a", recursive=False).text.strip()
            # Get holders that have sub sections
            sub_secs = cat.find_all("ul", class_="menu-child")
            for sub in sub_secs:
                # Get all child cats in sub sections
                child_cats = sub.find_all("li", class_="menu-2")
                # Run through each child cat to find grandchild cat
                for child in child_cats:
                    child_cat = child.find(class_="position-relative")
                    # Not sữa bột, bỉm tã
                    if child_cat != None:
                        cat_l2 = child_cat.text.strip()
                        granchild_cats = child.find_all("li", class_="menu-3")
                        # Have grandchild cats
                        if len(granchild_cats) > 0:
                            for grandchild in granchild_cats:
                                row = {}
                                row["cat_l1"] = cat_l1
                                row["cat_l2"] = cat_l2
                                row["cat_l3"] = grandchild.text.strip()
                                row["href"] = grandchild.find("a")["href"]
                                page_list.append(row)
                        # No grandchild cats
                        else:
                            row = {}
                            row["cat_l1"] = cat_l1
                            row["cat_l2"] = cat_l2
                            row["cat_l3"] = ""
                            try:  # Ignoring child cats which are cat title
                                row["href"] = child.find("a")["href"]
                                page_list.append(row)
                            except TypeError:
                                pass
                    # Sữa bột, bỉm tã
                    else:
                        row = {}
                        row["cat_l1"] = cat_l1
                        row["cat_l2"] = cat_l2
                        cat_l3 = child.find("a").get("title")
                        row["cat_l3"] = (
                            cat_l3
                            if cat_l3 != None
                            else re.sub(r"\s", "", child.find("a").text.strip())
                        )
                        row["href"] = child.find("a")["href"]
                        page_list.append(row)
        # Remove duplicates
        page_list = [i for i in page_list if i["cat_l2"] not in ("Thương hiệu") and i["cat_l3"] != ""]
        page_list = [dict(t) for t in set(tuple(i.items()) for i in page_list)]
        return page_list

    def scrap_data(self, cat: dict):
        """Get item data from a category page and self.write to csv"""
        # Define cat_name
        cat_name = cat["cat_l3"] if cat["cat_l3"] != "" else cat["cat_l2"]
        # Access
        res = requests.get(cat["href"], headers=self.headers)
        # Get soup
        soup = BeautifulSoup(res.content, features="lxml")
        # Get page numbers
        page_holder = soup.find("ul", class_="pagination")
        if page_holder != None:
            page_num = len(page_holder.find_all("li")) - 1
        else:
            page_num = 1
        # Get all product holders
        all_products = []
        for page in range(1, page_num + 1):
            if page != 1:
                res_page = requests.get(res.url + "?p=" + str(page), headers=self.headers)
                soup = BeautifulSoup(res_page.content, features="lxml")
            products = soup.find_all("div", class_="product-item")
            all_products.extend(products)
        print("Found " + str(len(all_products)) + " products in " + cat_name)
        # Scraping data
        for item in all_products:
            row = {}
            row["cat_l1"] = cat["cat_l1"]
            row["cat_l2"] = cat["cat_l2"]
            row["cat_l3"] = cat["cat_l3"]
            # Name
            row["product_name"] = item.find("h4").text.strip()
            # Brand
            href = item.find("a")["href"]
            prod_res = requests.get(href, headers=self.headers)
            prod_soup = BeautifulSoup(prod_res.content, features="lxml")
            try:
                brand_holder = prod_soup.find("tbody").find(string="Thương hiệu").find_parents("tr")
                if len(brand_holder) > 0:
                    row["brand"] = brand_holder[0].find("a").text.strip()
                else:
                    row["brand"] = ""
            except AttributeError:
                row["brand"] = ""
            row["href"] = href
            self.OBSERVATION += 1
            self.wr.write_data(row)
        print("Finished scraping " + cat_name + " category.")
