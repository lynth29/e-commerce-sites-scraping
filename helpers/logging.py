#!/usr/bin/python3
# -*- coding: utf-8 -*-

# Import libraries
## Work with logging
from rich.logging import RichHandler
from rich.progress import track
import logging
import signal

# Setting up logging
logging.basicConfig(
    level="INFO",
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(rich_tracebacks=True)]
)

log = logging.getLogger("rich")
