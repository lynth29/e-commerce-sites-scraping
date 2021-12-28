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
from helpers.logging import *
from helpers.write import *
from helpers.read import *
from scraping.vinmart import *
from scraping.coop import *

class Run():

    def __init__(self):
        # Driver
        self.driver = ChromeDriver().normal_driver()
        # Classes
        self.vin = Vinmart(self.driver)
        self.coop = Coop(self.driver)

    def daily_crawl(self, site):
        """Main workhorse function. Support functions defined below"""
        # Scrape
        try:
            log.info('Scraper started')
            # Select mart
            log.info('Start selecting shipping location')
            self.vin.choose_location() if site == "vinmart" else self.coop.choose_location()
            log.info('Selected Hanoi')
            # Get categories directories
            CATEGORIES_PAGES = self.vin.get_category_list() if site == "vinmart" else self.coop.get_category_list()
            log.info('Found ' + str(len(CATEGORIES_PAGES)) + ' categories')
            # Read each categories pages and scrape for data
            for cat in track(CATEGORIES_PAGES,
                             description = "[green]Scraping...",
                             total = len(CATEGORIES_PAGES)):
                self.vin.scrap_data(cat) if site == "vinmart" else self.coop.scrap_data(cat)
        except Exception as e:
            log.exception('Got exception, scraper stopped')
            log.info(type(e).__name__ + str(e))
        # Compress scraped data
        CSV_write("vinmart").compress_csv() if site == "vinmart" else CSV_write("coop").compress_csv()
        # Unzip CSV
        CSV_read("vinmart").unzip_csv() if site == "vinmart" else CSV_read("coop").unzip_csv()
        # Clean data
        self.vin.cleaning_data() if site == "vinmart" else self.coop.cleaning_data()
        log.info('Finished. Hibernating until next day...')

if __name__ == '__main__':
    run = Run()
    sites = ["vinmart", "coop"]
    for site in sites:
        run.daily_crawl(site)
