#!/usr/bin/python3
# -*- coding: utf-8 -*-

# Import essential libraries
## Work with files and folders
import sys
import os
from pathlib import Path

# Import other functions
sys.path.append('.')
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from helpers.crawl import *
# from helpers.logging import *
from helpers.write import *
from helpers.read import *
from websites.winmart import *
from websites.coop import *
from websites.bachhoaxanh import *
from websites.fujimart import *
from websites.bibomart import *

class Run():

    def __init__(self):
        # Driver
        self.driver = ChromeDriver().normal_driver()
        # Classes
        self.win = Winmart(self.driver)
        self.coop = Coop(self.driver)
        self.bachhoaxanh = BachHoaXanh(self.driver)
        self.fujimart = FujiMart(self.driver)
        self.bibomart = BiboMart()

    def daily_crawl(self, site):
        """Main workhorse function. Support functions defined below"""
        # Scrape
        try:
            print('Scraper started')
            # Select mart
            print('Start selecting shipping location')
            if site == "coop":
                # self.coop.choose_location()
                self.coop.disable_sub()
            # Get categories directories
            if site == "winmart":
                CATEGORIES_PAGES = self.win.get_category_list()
            elif site == "coop":
                CATEGORIES_PAGES = self.coop.get_category_list()
            elif site == "bachhoaxanh":
                CATEGORIES_PAGES = self.bachhoaxanh.get_category_list()
            elif site == "fujimart":
                CATEGORIES_PAGES = self.fujimart.get_category_list()
            elif site == "bibomart":
                CATEGORIES_PAGES = self.bibomart.get_category_list()
            print('Found ' + str(len(CATEGORIES_PAGES)) + ' categories')
            # Read each categories pages and scrape for data
            for cat in CATEGORIES_PAGES:
                if site == "winmart":
                    self.win.scrap_data(cat)
                elif site == "coop":
                    self.coop.scrap_data(cat)
                elif site == "bachhoaxanh":
                    self.bachhoaxanh.scrap_data(cat)
                elif site == "fujimart":
                    self.fujimart.scrap_data(cat)
                elif site == "bibomart":
                    self.bibomart.scrap_data(cat)
        except Exception as e:
            print('Got exception, scraper stopped')
            print(type(e).__name__ + str(e))
        # Compress scraped data
        CSV_write(site).compress_csv()
        print('Finished. Hibernating until next day...')

if __name__ == '__main__':
    run = Run()
    sites = ["bibomart"]
    for site in sites:
        run.daily_crawl(site)
