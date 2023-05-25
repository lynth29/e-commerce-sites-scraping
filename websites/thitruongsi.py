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
        # API
        self.shop_info_api = "https://m.thitruongsi.com/endpoint/v1/user/api{}"
        self.shop_feeds_api = "https://m.thitruongsi.com/endpoint/v1/feed/feed/shop:{}"
        self.price_ask_api = (
            "https://m.thitruongsi.com/endpoint/v2/rfq/api/rfqs.json?limit={}"
        )
        # Classes
        self.wr = CSV_write("thitruongsi")

    def get_category_list(self) -> list:
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

    def scrap_data(self, cat: dict):
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
        try:
            items_list = random.choices(items_list, k=100)
        except IndexError:
            items_list = random.choices(items_list, k=len(items_list))
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
                shop_href = shop_section.find("a")["href"]
                row["shop_href"] = shop_href
                # Connect to shop api
                shop_res = self.session.get(self.shop_info_api.format(shop_href))
                shop_js = shop_res.json()["data"]["shop"]
                shop_name = shop_js["name"]
                row["shop_name"] = shop_name
                shop_id = shop_js["id"]
                row["shop_id"] = shop_id
                shop_address = shop_js["shop_province"]["name"]
                row["shop_address"] = shop_address
                if shop_section.find("img") != None:
                    shop_subs = shop_section.find("img")["alt"]
                else:
                    shop_subs = "Free"
                row["shop_subs"] = shop_subs
                shop_join = datetime.datetime.strptime(
                    shop_js["created_at"], "%Y-%m-%dT%H:%M:%S%z"
                )
                row["shop_join"] = shop_join
                shop_prods = shop_js["total_products"]
                row["shop_prods"] = shop_prods
                try:
                    shop_followers = shop_js["total_following"]
                except IndexError:
                    shop_followers = 0
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
 
    def create_shop_db(self, product_data) -> list:
        shop_df = pd.read_csv(product_data)
        shop_df = shop_df[
            [
                "shop_name",
                "shop_id",
                "shop_address",
                "shop_subs",
                "shop_join",
                "shop_prods",
                "shop_followers",
                "shop_href",
            ]
        ]
        shop_df = shop_df.drop_duplicates("shop_id")
        shop_db = shop_df.to_dict("records")
        return shop_db
 
    def scrap_feeds(
        self,
        shop: dict,
        start_time: str = None,
        end_time: str = None,
        days_diff: int = None,
    ) -> list:
        """Crawling feeds from shop"""
        print(f"Scraping feeds of shop {shop['shop_name']}")
        # Define time range
        if end_time != None:
            end_time = datetime.datetime.strptime(end_time, "%Y%m%d")
        else:
            end_time = datetime.datetime.today()
        if start_time != None:
            start_time = datetime.datetime.strptime(start_time, "%Y%m%d")
        elif days_diff != None:
            start_time = end_time - datetime.timedelta(days=days_diff)
        # Access to shop_feed_api
        res = self.session.get(self.shop_feeds_api.format(shop["shop_id"]))
        feeds_data = res.json()
        # Create a while loop to crawling feeds within time range
        all_posts = []
        while True:
            try:
                posts = feeds_data["activities"]
                for post in posts:
                    post_date = datetime.datetime.strptime(
                        post["created_at"], "%Y-%m-%dT%H:%M:%S.%fZ"
                    )
                    if start_time < post_date < end_time:
                        row = {}
                        row["content"] = post["caption"]
                        row["like"] = post["reactions"]["like"]
                        row["comment"] = post["reactions"]["comment"]
                        row["reach"] = post["reach"]
                        row["date"] = post_date
                        row["shop"] = shop["shop_name"]
                        row["shop_id"] = shop["shop_id"]
                        all_posts.append(row)
                oldest_post_time = datetime.datetime.strptime(
                    feeds_data["activities"][-1]["created_at"], "%Y-%m-%dT%H:%M:%S.%fZ"
                )
                if (start_time != None) & (oldest_post_time < start_time):
                    break
                next_page = self.session.get(feeds_data["paging"]["previous"])
                feeds_data = next_page.json()
            except KeyError:
                print(shop["shop_name"], shop["shop_id"])
                break
            except IndexError:
                print(
                    f"Shop {shop['shop_name']} doesn't update anything on their feeds."
                )
                break
        return all_posts

    def create_feeds_db(
        self,
        shop_db: list,
        start_time: str = None,
        end_time: str = None,
        days_diff: int = None,
    ):
        feeds_db = []
        for shop in shop_db:
            feeds_db.extend(
                self.scrap_feeds(
                    shop, start_time=start_time, end_time=end_time, days_diff=days_diff
                )
            )
        feeds_df = pd.DataFrame(feeds_db)
        feeds_df.to_csv("feeds_db.csv", index=False)

    def scrap_price_ask(
        self,
        limit: int = 100,
        start_time: str = None,
        end_time: str = None,
        days_diff: int = None,
    ) -> list:
        # Define time range
        if end_time != None:
            end_time = datetime.datetime.strptime(end_time, "%Y%m%d")
        else:
            end_time = datetime.datetime.today()
        if start_time != None:
            start_time = datetime.datetime.strptime(start_time, "%Y%m%d")
        elif days_diff != None:
            start_time = end_time - datetime.timedelta(days=days_diff)
        # Access to shop_feed_api
        while True:
            res = self.session.get(self.price_ask_api.format(limit))
            quotation = res.json()["rfqs"]
            oldest_quote_time = datetime.datetime.strptime(
                quotation[-1]["created_at"], "%Y-%m-%dT%H:%M:%S.%fZ"
            )
            if oldest_quote_time >= start_time:
                limit += 100
            else:
                break
        print(f"There are total {len(quotation)} quotations from {start_time} to {end_time} with limit as {limit}")
        # Create a while loop to crawling feeds within time range
        all_quotations = []
        for q in quotation:
            quote_date = datetime.datetime.strptime(
                q["created_at"], "%Y-%m-%dT%H:%M:%S.%fZ"
            )
            if start_time < quote_date < end_time:
                row = {}
                row["id"] = q["id"]
                row["title"] = q["title"]
                row["l1"] = q["category_lv1_title"]
                row["l2"] = q["category_lv2_title"]
                row["quote_count"] = q["quote_count"]
                all_quotations.append(row)
        return all_quotations

    def create_quotation_db(
        self,
        limit: int = 100,
        start_time: str = None,
        end_time: str = None,
        days_diff: int = None,
    ):
        all_quotation = self.scrap_price_ask(
            limit=limit, start_time=start_time, end_time=end_time, days_diff=days_diff
        )
        quotation_df = pd.DataFrame(all_quotation)
        quotation_df = quotation_df.drop_duplicates("id")
        quotation_df.to_csv("quotation_db.csv", index=False)
