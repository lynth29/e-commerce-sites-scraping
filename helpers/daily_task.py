#!/usr/bin/python3
# -*- coding: utf-8 -*-

# Import essential libraries
## Work with files and folders
import sys
import os
from pathlib import Path

# Import other functions
sys.path.append(".")
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from helpers.crawl import *

# from helpers.logging import *
from helpers.write import *
from helpers.read import *
# FMCG
from websites.winmart import *
from websites.coop import *
from websites.bachhoaxanh import *
from websites.fujimart import *
# Mom and baby
from websites.bibomart import *
from websites.concung import *
from websites.kidsplaza import *
# Cosmetics
from websites.hasaki import *
from websites.cocoshop import *
# Others
from websites.thitruongsi import *
from websites.topcv import *


class Run:
    def __init__(self, list_of_sites: list):
        self.list_of_sites = list_of_sites
        # Driver
        self.driver = ChromeDriver().normal_driver()
        # Classes
        # FMCG
        self.win = (
            Winmart(ChromeDriver().show_driver())
            if "win" in self.list_of_sites
            else None
        )
        self.coop = Coop(self.driver) if "coop" in self.list_of_sites else None
        self.bachhoaxanh = (
            BachHoaXanh(self.driver) if "bachhoaxanh" in self.list_of_sites else None
        )
        self.fujimart = (
            FujiMart(self.driver) if "fujimart" in self.list_of_sites else None
        )
        # Mom and baby
        self.bibomart = BiboMart() if "bibomart" in self.list_of_sites else None
        self.concung = ConCung() if "concung" in self.list_of_sites else None
        self.kidsplaza = (
            KidsPlaza(self.driver) if "kidsplaza" in self.list_of_sites else None
        )
        # Cosmetics
        self.hasaki = Hasaki() if "hasaki" in self.list_of_sites else None
        self.cocoshop = Cocoshop() if "cocoshop" in self.list_of_sites else None
        # Others
        self.thitruongsi = (
            ThiTruongSi() if "thitruongsi" in self.list_of_sites else None
        )
        self.topcv = (
            TopCV() if "topcv" in self.list_of_sites else None
        )

    def daily_crawl(self, site: str):
        """Main workhorse function. Support functions defined below"""
        # Scrape
        # try:
        print("Scraper started")
        # Select mart
        print("Start selecting shipping location")
        if site == "coop":
            # self.coop.choose_location()
            self.coop.disable_sub()
        # Get categories directories
        # FMCG
        if site == "winmart":
            CATEGORIES_PAGES = self.win.get_category_list()
        elif site == "coop":
            CATEGORIES_PAGES = self.coop.get_category_list()
        elif site == "bachhoaxanh":
            CATEGORIES_PAGES = self.bachhoaxanh.get_category_list()
        elif site == "fujimart":
            CATEGORIES_PAGES = self.fujimart.get_category_list()
        # Mom and baby
        elif site == "bibomart":
            CATEGORIES_PAGES = self.bibomart.get_category_list()
        elif site == "concung":
            CATEGORIES_PAGES = self.concung.get_category_list()
        elif site == "kidsplaza":
            CATEGORIES_PAGES = self.kidsplaza.get_category_list()
        # Cosmetics
        elif site == "hasaki":
            CATEGORIES_PAGES = self.hasaki.get_category_list()
        elif site == "cocoshop":
            CATEGORIES_PAGES = self.cocoshop.get_category_list()
        # Others
        elif site == "thitruongsi":
            CATEGORIES_PAGES = self.thitruongsi.get_category_list()
        elif site == "topcv":
            CATEGORIES_PAGES = self.topcv.get_category_list()
        print("Found " + str(len(CATEGORIES_PAGES)) + " categories")
        # Read each categories pages and scrape for data
        for cat in CATEGORIES_PAGES:
            # FMCG
            if site == "winmart":
                self.win.scrap_data(cat)
            elif site == "coop":
                self.coop.scrap_data(cat)
            elif site == "bachhoaxanh":
                self.bachhoaxanh.scrap_data(cat)
            elif site == "fujimart":
                self.fujimart.scrap_data(cat)
            # Mom and baby
            elif site == "bibomart":
                self.bibomart.scrap_data(cat)
            elif site == "concung":
                self.concung.scrap_data(cat)
            elif site == "kidsplaza":
                self.kidsplaza.scrap_data(cat)
            # Cosmetics
            elif site == "hasaki":
                self.hasaki.scrap_data(cat)
            elif site == "cocoshop":
                self.cocoshop.scrap_data(cat)
            # Others
            elif site == "thitruongsi":
                self.thitruongsi.scrap_data(cat)
            elif site == "topcv":
                self.topcv.scrap_data(cat)
        # except Exception as e:
        #     print("Got exception, scraper stopped")
        #     print(type(e).__name__ + str(e))
        # Compress scraped data
        CSV_write(site).compress_csv()
        print("Finished. Hibernating until next day...")


if __name__ == "__main__":
    num_of_sites = int(input("How many sites you would like to crawl?: "))
    sites = []
    for i in range(num_of_sites):
        sites.append(str(input("Which site then: ")))
    
    run = Run(sites)
    for site in sites:
        run.daily_crawl(site)