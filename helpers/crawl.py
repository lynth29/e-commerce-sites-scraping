#!/usr/bin/python3
# -*- coding: utf-8 -*-

# Import libraries
# Work with files and folders
import os
from pathlib import Path
import platform
# Work with time
import time
import datetime
from time import sleep
# Handle data
import re
import random
import pandas as pd
import numpy as np

# Crawl
from selenium import webdriver
from seleniumrequests.request import RequestMixin
from bs4 import BeautifulSoup
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from urllib.request import urlopen

# Handle selenium exeptions
import selenium.webdriver.support.ui as ui
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import SessionNotCreatedException, TimeoutException, NoSuchElementException, StaleElementReferenceException
IGNORED_EXCEPTIONS = (NoSuchElementException, StaleElementReferenceException)

# Parameters
PROJECT_PATH = Path(__file__).absolute().parents[1]
CHROME_DRIVER = os.path.join(PROJECT_PATH, "bin")


class ChromeDriver:

    def normal_driver(self):
        """
        Create normal chrome webdriver with some options
        """

        op = webdriver.ChromeOptions()
        # Show chromnium browser or not
        # op.add_argument('--headless')
        # Set window size to maximium when using headless to avoid losing or not showing up elements
        op.add_argument("--window-size=1920,1080")
        # 6 arguments to optimize speed when loading
        op.add_argument('--no-sandbox')
        op.add_argument("start-maximized")
        op.add_argument("--disable-extensions")
        op.add_argument("--disable-gpu")
        op.add_argument("--disable-dev-shm-usage")
        op.add_argument("--enable-javascript")

        # Create a driver based on chromedriver exe file and options
        if platform.machine() == "arm64":
            driver = webdriver.Chrome(executable_path="{}/chromedriver_mac64_m1".format(CHROME_DRIVER), options=op)
        # Must use appropriate chromedriver version with Chrome version (89.0 vs 89.0)
        return driver
