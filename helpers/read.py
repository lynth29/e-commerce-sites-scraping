#!/usr/bin/python3
# -*- coding: utf-8 -*-

# Import essential libraries
## Work with files and folders
import os
import sys
from zipfile import ZipFile
from pathlib import Path
import datetime

sys.path.append(".")
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Parameters
PROJECT_PATH = Path(__file__).absolute().parents[1]

# Define classes
class CSV_read:
    def __init__(self, site_name: str):
        # Set output
        self.SITE_NAME = site_name
        self.PATH_CSV = os.path.join(PROJECT_PATH, "csv", self.SITE_NAME)
        # Set date
        self.DATE = str(datetime.date.today())

    def unzip_csv(self):
        """Unzip .csv files"""
        if not os.path.exists(self.PATH_CSV):
            os.makedirs(self.PATH_CSV)
        os.chdir(self.PATH_CSV)
        try:
            with ZipFile(self.SITE_NAME + "_" + self.DATE + "_csv.zip", "a") as zip_csv:
                zip_csv.extractall(self.PATH_CSV)
        except Exception as e:
            print("Error when compressing csv")
            print(type(e).__name__ + str(e))
        os.chdir(PROJECT_PATH)
