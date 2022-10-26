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
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import requests

# Handle selenium exeptions
import selenium.webdriver.support.ui as ui
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import SessionNotCreatedException, TimeoutException, NoSuchElementException, StaleElementReferenceException, ElementClickInterceptedException
IGNORED_EXCEPTIONS = (NoSuchElementException, StaleElementReferenceException, TimeoutException, ElementClickInterceptedException)
class ChromeDriver:

    def normal_driver(self):
        """
        Create normal chrome webdriver with some options
        """

        op = webdriver.ChromeOptions()
        # Run browser in headless mode
        op.add_argument('--headless')
        op.add_argument('--no-sandbox')
        # Set window size to maximized mode
        op.add_argument("--start-maximized")
        # Overcome limited resource problems
        op.add_argument("--disable-dev-shm-usage")
        op.add_argument("--disable-gpu")
        # Disable infobars
        op.add_argument("--disable-infobars")
        # Disable extensions
        op.add_argument("--disable-extensions")

        # Create driver 
        driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=op)
        return driver
