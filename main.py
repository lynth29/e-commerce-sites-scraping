#!/usr/bin/env python3

# Import essential libraries
import os
import sys

# Import modules
from helpers.daily_task import *
from post_scrape import upload

# Define paths
PROJECT_PATH = os.getcwd()
SITES_LIST = [f.name for f in os.scandir(PROJECT_PATH + "/csv")]

# UI
# log.info(f"Please choose a site to start scraping:")
log.info("We will start scraping these sites.")
for idx, site in enumerate(SITES_LIST, start=0):
    if site.startswith("."):
        continue
    log.info(f"{idx}. {site}")

# Define main function
def main():
    try:
        # Scrape
        run = Run()
        for site in SITES_LIST:
            run.daily_crawl(site)
        # upload
        os.chdir(PROJECT_PATH)
        log.info(f"Proceed to upload to Google Drive.")
        upload.main()
    except Exception as e:
        log.info(type(e).__name__ + str(e))


if __name__ == "__main__":
    main()
