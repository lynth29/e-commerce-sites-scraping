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
SITE_NAME = "hasaki"
PATH_CSV = os.path.join(PROJECT_PATH, "csv", SITE_NAME)


# Define class
class Hasaki:
    def __init__(self):
        # Parameters
        self.BASE_URL = "https://hasaki.vn"
        self.session = Session().session
        self.DATE = str(datetime.date.today())
        self.OBSERVATION = 0
        # API
        self.home_api = "https://hasaki.vn/wap/v2/master/?page=newHeaderHome"
        self.listing_api = "https://hasaki.vn/wap/v2/catalog/category/get-listing-product?cat={}&p={}&product_list_limit=12&&more_data=1&lstType=1&lstId=0"
        self.product_api = "https://hasaki.vn/wap/v2/product/detail?id={}"
        # Classes
        self.wr = CSV_write("hasaki")

    def get_category_list(self) -> list:
        """Get list of relative categories directories from hasaki.vn"""
        # Send request to home_api
        home_res = self.session.get(self.home_api)
        home_json = home_res.json()
        cat_bar = home_json["cate_menu"]
        # Create an empty list to store categories' information
        page_list = []
        for cat in cat_bar:
            if cat["name"] != "Mỹ Phẩm High-End":
                if "child" in cat.keys():
                    cat_child = cat["child"]
                    for l2 in cat_child:
                        if "child" in l2.keys():
                            cat_grandchild = l2["child"]
                            for l3 in cat_grandchild:
                                next_page = {}
                                next_page["cat_l1"] = cat["name"]
                                next_page["cat_l2"] = l2["name"]
                                next_page["cat_l3"] = l3["name"]
                                next_page["id"] = l3["id"]
                                next_page["href"] = l3["url"]
                                page_list.append(next_page)
                        else:
                            next_page = {}
                            next_page["cat_l1"] = cat["name"]
                            next_page["cat_l2"] = l2["name"]
                            next_page["cat_l3"] = ""
                            next_page["id"] = l2["id"]
                            next_page["href"] = l2["url"]
                            page_list.append(next_page)
                else:
                    next_page = {}
                    next_page["cat_l1"] = cat["name"]
                    next_page["cat_l2"] = ""
                    next_page["cat_l3"] = ""
                    next_page["id"] = cat["id"]
                    next_page["href"] = cat["url"]
                    page_list.append(next_page)
        # pd.DataFrame(page_list).to_csv('test.csv')
        return page_list

    def scrap_data(self, cat: dict):
        """Get item data from a category page and self.write to csv"""
        # Get all products
        print(f"Crawling {cat['cat_l2']}")
        i = 1
        items_list = []
        while True:
            res = self.session.get(self.listing_api.format(cat["id"], i))
            listing = res.json()["listing"]
            if len(listing) > 0:
                for sku in listing:
                    prod_id = sku["id"]
                    items_list.append(prod_id)
                i += 1
            else:
                break
        print("Found " + str(len(items_list)) + " products")
        # Get information of each item
        for item in items_list:
            try:
                # Send request to product_api
                prod_res = self.session.get(self.product_api.format(item))
                prod_json = prod_res.json()
                row = {}
                # Product name
                name = prod_json["name"]
                row["product_name"] = name
                # Image
                try:
                    image = prod_json["gallery"][-2]
                except IndexError:
                    image = ""
                row["image"] = image
                # Category
                row["cat_l0"] = "Mỹ phẩm"
                row["cat_l1"] = cat["cat_l1"]
                row["cat_l2"] = cat["cat_l2"]
                row["cat_l3"] = cat["cat_l3"]
                # Barcode
                barcode = prod_json["attribute_show"][0]["val"]
                row["barcode"] = barcode
                # Brand
                brand = prod_json["brand"]["name"]
                row["brand"] = brand
                # Manufacturer
                manu = prod_json["attribute_show"][3]["val"]
                row["manufacturer"] = manu if manu != False else ""
                # Attribute
                try:
                    attribute_list = prod_json["attribute"]
                    attribute_list = attribute_list["items"]
                except TypeError:
                    attribute_list = ""
                if attribute_list != "":
                    attr_check = [a["code"] for a in attribute_list]
                    # Capacity
                    if "capacity" in attr_check:
                        for i in attribute_list:
                            if i["code"] == "capacity":
                                for o in i["options"]:
                                    id_list = [l["id"] for l in o["products"]]
                                    if item in id_list:
                                        row["capacity"] = o["long_label"]
                                        break
                    else:
                        row["capacity"] = ""
                    # Effect
                    if "effect" in attr_check:
                        for i in attribute_list:
                            if i["code"] == "effect":
                                for o in i["options"]:
                                    id_list = [l["id"] for l in o["products"]]
                                    if item in id_list:
                                        row["effect"] = o["long_label"]
                                        break
                    else:
                        row["effect"] = ""
                else:
                    row["capacity"] = ""
                    row["effect"] = ""
                price = prod_json["price"]
                row["price"] = price
                # Source
                row["source"] = "hasaki.vn"
                # Link
                row["href"] = prod_json["url"]
                self.OBSERVATION += 1
                self.wr.write_data(row)
                time.sleep(1)
            except Exception as e:
                print("Error on " + str(item))
                print(type(e).__name__ + str(e))
                pass
