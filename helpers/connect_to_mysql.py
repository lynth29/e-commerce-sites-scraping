# !/usr/bin/python3
# -*- coding: utf-8 -*-

# Import essential libraries
import sqlalchemy
from sqlalchemy_utils import database_exists, create_database

class ConnectMySQL:
    
    def __init__(self) -> None:
        self.host = "10.24.103.21"
        self. port = "3306"
        self.user = "commondb_admin"
        self.password = "RB8cFmN3sxLBTAnMbk8P"
        self.db = "common_database"
    
    def create_sql_engine(self):
        # load credentials and connect to database
        try:
            engine = sqlalchemy.create_engine(f'mysql+pymysql://{self.user}:{self.password}@{self.host}:{self.port}/{self.db}')
        except:
            raise Exception('Could not connect to host. Please check your credentials or internet connection.')

        # Create database if it does not exist.
        if not database_exists(engine.url):
            create_database(engine.url)
        else:
            # Connect the database if exists.
            engine.connect()
        return engine