# Install essential libraries
import pandas as pd
import numpy as np
import os
from zipfile import ZipFile
import time
import datetime
import csv
import logging
import re
from rich.logging import RichHandler
from rich.progress import track

# Parameters
SITE_NAME = "vinmart"
PROJECT_PATH = re.sub("/py$", "", os.getcwd())
PATH_CSV = PROJECT_PATH + "/csv/" + SITE_NAME + "/"
CLEAN_CSV = PROJECT_PATH + '/clean_csv/'
DATE = str(datetime.date.today())
ZIP_NAME = SITE_NAME + '_' + DATE + '_csv.zip'
OBSERVATION = 0

# Setting up logging
logging.basicConfig(
    level="INFO",
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(rich_tracebacks=True)]
)

log = logging.getLogger("rich")

# Unzip
def unzip_csv():
    """Unzip .csv files"""
    if not os.path.exists(PATH_CSV):
        os.makedirs(PATH_CSV)
    os.chdir(PATH_CSV)
    try:
        with ZipFile(SITE_NAME + '_' + DATE + '_csv.zip', 'a') as zip_csv:
            zip_csv.extractall(PATH_CSV)
        log.info(f"Unziping {str(OBSERVATION+1)} item(s)")
    except Exception as e:
        log.error('Error when compressing csv')
        log.info(type(e).__name__ + str(e))
    os.chdir(PROJECT_PATH)

unzip_csv()

# Import CSV file
raw = pd.read_csv(PATH_CSV + SITE_NAME + '_' + DATE + '.csv')
log.info('Imported CSV file to a dataframe')

# Summarize the dataframe
log.info('The dataframe has a shape as:')
log.info(raw.shape)
log.info('Have a look at the dtypes:')
log.info(raw.info())
log.info('Are there any null value?:')
log.info(raw.isnull().any())

# Convert dtypes
raw.price = raw.price.str.replace('.','').astype(float)
raw.old_price = raw.old_price.str.replace('.','').astype(float)
raw.old_price = raw.old_price.fillna(0)
raw.old_price = np.where(raw.old_price == 0, raw.price, raw.old_price)
raw.date = pd.to_datetime(raw.date)
log.info('Have a look at the dtypes after converting:')
log.info(raw.info())

# Export to new CSV
raw.to_csv(CLEAN_CSV + SITE_NAME + '_' + DATE + '_hn_clean.csv')
os.remove(PATH_CSV + SITE_NAME + '_' + DATE + '.csv')
log.info('Finished cleaning data')
