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
from websites.vinmart import *
from websites.coop import *
from websites.bachhoaxanh import *

class Run():

    def __init__(self):
        # Driver
        self.driver = ChromeDriver().normal_driver()
        # Classes
        self.vin = Vinmart(self.driver)
        self.coop = Coop(self.driver)
        self.bachhoaxanh = BachHoaXanh(self.driver)

    def daily_crawl(self, site):
        """Main workhorse function. Support functions defined below"""
        # Scrape
        try:
            print('Scraper started')
            # Select mart
            print('Start selecting shipping location')
            if site == "vinmart":
                self.vin.choose_location()
            elif site == "coop":
                self.coop.choose_location()
            # Get categories directories
            if site == "vinmart":
                CATEGORIES_PAGES = self.vin.get_category_list()
            elif site == "coop":
                CATEGORIES_PAGES = self.coop.get_category_list()
            elif site == "bachhoaxanh":
                CATEGORIES_PAGES = self.bachhoaxanh.get_category_list()
            print('Found ' + str(len(CATEGORIES_PAGES)) + ' categories')
            # Read each categories pages and scrape for data
            for cat in CATEGORIES_PAGES):
                if site == "vinmart":
                    self.vin.scrap_data(cat)
                elif site == "coop":
                    self.coop.scrap_data(cat)
                elif site == "bachhoaxanh":
                    self.bachhoaxanh.scrap_data(cat)
        except Exception as e:
            print('Got exception, scraper stopped')
            print(type(e).__name__ + str(e))
        # Compress scraped data
        CSV_write(site).compress_csv()
        print('Finished. Hibernating until next day...')

if __name__ == '__main__':
    run = Run()
    sites = ["bachhoaxanh"]
    for site in sites:
        run.daily_crawl(site)
