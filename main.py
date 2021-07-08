#!/usr/bin/env python3

# Import essential libraries
import os
import sys
from pathlib import Path
import logging
from rich.logging import RichHandler
from rich.progress import track

# Import modules
from scraping import vinmart
from scraping import coop
from post_scrape import upload

# Define paths
PROJECT_PATH = os.getcwd()
SITES_LIST = [f.name for f in os.scandir(PROJECT_PATH + '/html')]

# Setting up logging
logging.basicConfig(
    level="INFO",
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(rich_tracebacks=True)]
)

log = logging.getLogger("rich")

# UI
# log.info(f"Please choose a site to start scraping:")
log.info("We will start scraping these sites.")
for idx, site in enumerate(SITES_LIST, start=0):
    if site.startswith('.'):
        continue
    log.info(f"{idx}. {site}")
# INPUT = str(input("Chosen site: "))

# Define main function
def main():
    try:
        # if INPUT == 'vinmart':
        log.info("Start scraping vinmart.vn")
        vinmart.main()
        # if INPUT == 'coop':
        log.info("Start scraping cooponline.vn")
        coop.main()
        os.chdir(PROJECT_PATH)
        log.info(f"Proceed to upload to Google Drive.")
        upload.main()
    except Exception as e:
        log.info(type(e).__name__ + str(e))
if __name__ == "__main__":
    main()
