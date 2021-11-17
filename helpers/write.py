#!/usr/bin/python3
# -*- coding: utf-8 -*-

# Import essential libraries
## Work with files and folders
import os
import glob
from zipfile import ZipFile
from pathlib import Path
import datetime
import sys
sys.path.append('.')
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
## Write to data
import csv
import pandas as pd

# Import logging
from helpers.logging import *

# Parameters
PROJECT_PATH = Path(__file__).absolute().parents[1]

# Define classes
class CSV_write:

    def __init__(self, site_name):
        # Set output
        self.SITE_NAME = site_name
        self.PATH_CSV = os.path.join(PROJECT_PATH, "csv", self.SITE_NAME)
        # Set date
        self.DATE = str(datetime.date.today())
        # Set fieldnames
        self.fieldnames = ['good_name', 'price', 'old_price', 'id', 'parent_category', 'category', 'date']

    def write_data(self, item_data):
        """Write an item data as a row in csv. Create new file if needed"""
        file_exists = os.path.isfile(self.PATH_CSV + '/' + self.SITE_NAME + "_" + self.DATE + ".csv")
        if not os.path.exists(self.PATH_CSV):
            os.makedirs(self.PATH_CSV)
        with open(self.PATH_CSV + '/' + self.SITE_NAME + "_" + self.DATE + ".csv", "a") as f:
            writer = csv.DictWriter(f, self.fieldnames)
            if not file_exists:
                writer.writeheader()
            writer.writerow(item_data)

    def compress_csv(self):
        """Compress downloaded .csv files"""
        if not os.path.exists(self.PATH_CSV):
            os.makedirs(self.PATH_CSV)
        os.chdir(self.PATH_CSV)
        try:
            zip_csv = ZipFile(self.SITE_NAME + '_' + self.DATE + '_csv.zip', 'a')
            for file in glob.glob("*" + self.DATE + "*" + "csv"):
                zip_csv.write(file)
                os.remove(file)
        except Exception as e:
            log.error('Error when compressing csv')
            log.info(type(e).__name__ + str(e))
        os.chdir(PROJECT_PATH)
