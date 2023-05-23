#!/usr/bin/python3
# -*- coding: utf-8 -*-

# Import essential libraries
# Work with files and folders
import sys
import os

sys.path.append(".")
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Import modules
from helpers.read import *
from helpers.write import *
from helpers.crawl import *

# Parameters
SITE_NAME = "topcv"
PATH_CSV = os.path.join(PROJECT_PATH, "csv", SITE_NAME)


# Define class
class TopCV:
    def __init__(self):
        # Parameters
        self.BASE_URL = "https://topcv.vn"
        self.session = Session().session
        self.DATE = str(datetime.date.today())
        self.OBSERVATION = 0
        self.jobs = [
            "UIUX Designer",
            "UXUI Designer",
            "Marketing Executive",
            "Marketing Planner",
            "Marketing Strategy",
            "Content Writer",
            "Frontend Developer",
            "Backend Developer",
            "Blockchain Engineer",
            "Blockchain Engineering",
            "Blockchain Developer",
            "Smart Contract Developer",
        ]
        # Classes
        self.wr = CSV_write("topcv")

    def get_category_list(self) -> list:
        page_list = []
        for j in self.jobs:
            row = {}
            row["name"] = j
            row[
                "href"
            ] = f"{self.BASE_URL}/tim-viec-lam-{j.replace(' ','-')}-tai-ha-noi-kl1"
            page_list.append(row)
        return page_list

    def scrap_data(self, cat: dict):
        """Get item data from a category page and self.write to csv"""
        # Get all products
        print(f"Crawling {cat['name']}")
        res = self.session.get(cat["href"])
        soup = BeautifulSoup(res.content, "lxml")
        # Find page number
        try:
            page_num = (
                soup.find("ul", class_="pagination").find_all("li")[-2].text.strip()
            )
        except AttributeError:
            page_num = 1
        # Get all products
        jobs_list = []
        for i in range(int(page_num)):
            if i > 1:
                res = self.session.get(f"{cat['href']}?page={i}")
                soup = BeautifulSoup(res.content, "lxml")
            if i != 1:
                jobs = soup.find_all("div", {"data-box": "BoxSearchResult"})
                jobs_list.extend(jobs)
        print("Found " + str(len(jobs_list)) + " jobs")
        # Get information of each item
        for j in jobs_list:
            try:
                row = {}
                row["job_name"] = j.find("h3").text.strip()
                row["company"] = j.find("a", class_="company").text.strip()
                row["href"] = j.find("a")["href"]
                # Get inner info
                res_job = requests.get(row["href"])
                soup_job = BeautifulSoup(res_job.content, "lxml")
                # Summary
                info_section = soup_job.find("div", class_="box-main")
                info_section = info_section.find_all("div", class_="box-item")
                info = {
                    i.find("strong").text.strip(): i.find("span").text.strip()
                    for i in info_section
                }
                try:
                    row["salary"] = info["Mức lương"]
                except KeyError:
                    row["salary"] = ""
                try:
                    row["type"] = info["Hình thức làm việc"]
                except KeyError:
                    row["type"] = ""
                try:
                    row["level"] = info["Cấp bậc"]
                except KeyError:
                    row["level"] = ""
                try:
                    row["gender"] = info["Giới tính"]
                except KeyError:
                    row["gender"] = ""
                try:
                    row["exp"] = info["Kinh nghiệm"]
                except KeyError:
                    row["exp"] = ""
                # Address
                if soup_job.find("div", class_="box-address") != None:
                    row["address"] = (
                        soup_job.find("div", class_="box-address")
                        .find("div")
                        .text.strip()
                    )
                else:
                    row["address"] = ""
                # Requirements and Benefits
                re_section = soup_job.find("div", class_="job-data")
                re_title = re_section.find_all("h3")[:-1]
                re_title = [i.text.strip() for i in re_title]
                re_content = re_section.find_all("div", class_="content-tab")
                re_content = [i.text.strip() for i in re_content]
                require = dict(zip(re_title, re_content))
                try:
                    row["description"] = require["Mô tả công việc"]
                except KeyError:
                    row["description"] = ""
                try:
                    row["requirements"] = require["Yêu cầu ứng viên"]
                except KeyError:
                    row["requirements"] = ""
                try:
                    row["benefits"] = require["Quyền lợi"]
                except KeyError:
                    row["benefits"] = ""
                self.OBSERVATION += 1
                self.wr.write_data(row)
                time.sleep(1)
            except Exception as e:
                print("Error on " + j.find("a")["href"])
                print(type(e).__name__ + str(e))
                pass
        # except Exception:
        #     print(item.find('a')['href'], Exception)
