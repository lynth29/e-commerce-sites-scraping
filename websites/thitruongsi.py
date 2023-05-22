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
SITE_NAME = "thitruongsi"
PATH_CSV = os.path.join(PROJECT_PATH, "csv", SITE_NAME)


# Define class
class ThiTruongSi:
    def __init__(self):
        # Parameters
        self.BASE_URL = "https://thitruongsi.com"
        self.session = Session().session
        self.DATE = str(datetime.date.today())
        self.OBSERVATION = 0
        # Classes
        self.wr = CSV_write("thitruongsi")

    def get_category_list(self):
        """Get list of relative categories directories from thitruongsi.com"""
        # Get category level 1 dictionary
        cat_l1_dict = self.session.get(
            "https://thitruongsi.com/endpoint/v2/product/categories.json?level=1"
        ).json()
        cat_l1_list = cat_l1_dict["categories"]
        cat_l1_bar = {str(cat["category_id"]): cat["title"] for cat in cat_l1_list}
        # Get category level 2 dictionary
        cat_l2_dict = self.session.get(
            "https://thitruongsi.com/endpoint/v2/product/categories.json?level=2"
        ).json()
        cat_l2_list = cat_l2_dict["categories"]
        cat_l2_bar = {str(cat["category_id"]): cat["title"] for cat in cat_l2_list}
        cat_l2_parent = {str(cat["category_id"]): cat["p_id"] for cat in cat_l2_list}
        # Create an empty list to store categories' information
        page_list = []
        for cat in cat_l2_list:
            next_page = {}
            try:
                next_page["cat_l1"] = cat_l1_bar[str(cat["p_id"])]
            except KeyError:
                try:
                    next_page["cat_l1"] = cat_l1_bar[
                        str(cat_l2_parent[str(cat["p_id"])])
                    ]
                except KeyError:
                    next_page["cat_l1"] = ""
            next_page["cat_l2"] = cat["title"]
            next_page["href"] = str(cat["category_id"]) + "-" + cat["slug"]
            page_list.append(next_page)
        return page_list

    def scrap_data(self, cat):
        """Get item data from a category page and self.write to csv"""
        # Get all products
        print(f"Crawling {cat['cat_l2']}")
        res = self.session.get(f"{self.BASE_URL}/category/child/{cat['href']}.html")
        soup = BeautifulSoup(res.content, "lxml")
        # Find page number
        total_prods = (
            soup.find("div", class_="bg-fff rounded p-2 mb-2")
            .find("strong")
            .text.strip()
        )
        page_num = int(int(total_prods) / 40 + 1)
        # Get all products
        items_list = []
        for i in range(1, page_num + 1):
            if i > 1:
                res = self.session.get(
                    f"{self.BASE_URL}/category/child/{cat['href']}.html/?&limit=40&offset={40*(i-1)}&page={i}"
                )
                soup = BeautifulSoup(res.content, "lxml")
            items = soup.find("div", class_="pr-0 col-sm-8 col-md-9 col-lg-10")
            items = items.find_all("div", class_="item")
            items_list.extend(items)
        print("Found " + str(len(items_list)) + " products")
        # Get information of each item
        for item in items_list:
            try:
                row = {}
                # Product name
                row["product_name"] = item.find("a", class_="css-rrtwm0").text.strip()
                row["href"] = item.find("a")["href"]
                # Get inner information
                prod_res = self.session.get(f"{self.BASE_URL}{row['href']}")
                prod_soup = BeautifulSoup(prod_res.content, "lxml")
                price_section = prod_soup.find("div", class_="pricing-section mb-4")
                if (
                    prod_soup.find("div", class_="jsx-1704392005 multiple-prices")
                    != None
                ):
                    multi_price_section = prod_soup.find(
                        "div", class_="jsx-1704392005 multiple-prices"
                    ).find_all("div")
                    price_1 = int(
                        multi_price_section[1]
                        .text.strip()
                        .split("đ")[0]
                        .replace(",", "")
                        .replace(".", "")
                        .replace("x", "0")
                    )
                    price_2 = int(
                        multi_price_section[4]
                        .text.strip()
                        .split("đ")[0]
                        .replace(",", "")
                        .replace(".", "")
                        .replace("x", "0")
                    )
                    row["price_2"] = price_2
                    if len(multi_price_section) > 7:
                        price_3 = int(
                            multi_price_section[7]
                            .text.strip()
                            .split("đ")[0]
                            .replace(",", "")
                            .replace(".", "")
                            .replace("x", "0")
                        )
                        row["price_3"] = price_3
                    else:
                        row["price_3"] = ""
                else:
                    price_1 = int(
                        price_section.find("span")
                        .text.strip()
                        .split("đ")[0]
                        .replace(",", "")
                        .replace("x", "0")
                        .replace(".", "")
                    )
                    row["price_2"] = ""
                    row["price_3"] = ""
                row["price_1"] = price_1
                # Get shop information
                shop_section = prod_soup.find(
                    "div", class_="border rounded css-1il6ewt"
                )
                shop_name = shop_section.find("a").text.strip()
                row["shop_name"] = shop_name
                shop_href = shop_section.find("a")["href"]
                row["shop_href"] = shop_href
                shop_address = shop_section.find(
                    "div", class_="css-16yk86w"
                ).text.strip()
                row["shop_address"] = shop_address
                if shop_section.find("img") != None:
                    shop_subs = shop_section.find("img")["alt"]
                else:
                    shop_subs = "Free"
                row["shop_subs"] = shop_subs
                shop_stats = shop_section.find("div", class_="css-y4fsjf")
                shop_stats = shop_stats.find_all("span")
                shop_join = shop_stats[1].text.strip()
                row["shop_join"] = shop_join
                shop_prods = int(shop_stats[3].text.strip().replace(",", ""))
                row["shop_prods"] = shop_prods
                try:
                    shop_rep_rate = [
                        int(shop_stats[id + 1].text.strip().split("%")[0]) / 100
                        for id, i in enumerate(shop_stats)
                        if i.text.strip() == "Tỷ lệ phản hồi"
                    ][0]
                except IndexError:
                    shop_rep_rate = 0
                try:
                    shop_followers = [
                        int(shop_stats[id + 1].text.strip().replace(",", ""))
                        for id, i in enumerate(shop_stats)
                        if i.text.strip() == "Người theo dõi"
                    ][0]
                except IndexError:
                    shop_followers = 0
                row["shop_rep_rate"] = shop_rep_rate
                row["shop_followers"] = shop_followers
                row["cat_l1"] = cat["cat_l1"]
                row["cat_l2"] = cat["cat_l2"]
                self.OBSERVATION += 1
                self.wr.write_data(row)
                time.sleep(1)
            except Exception as e:
                print("Error on " + item.find("a")["href"])
                print(type(e).__name__ + str(e))
                pass
            # except Exception:
            #     print(item.find('a')['href'], Exception)
