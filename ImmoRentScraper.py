from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException, ElementClickInterceptedException

import pandas as pd
from datetime import date
import time
import json
from glob import glob
from tqdm import tqdm
from random import randint
import logging


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S')


class ImmoRentScraper:
    def __init__(self, url, output_path="data/immo24/rent"):
        self.url = url
        self.data_folder = output_path
        self.links_folder = f"{output_path}/links"
        self.raw_folder = f"{output_path}/raw"
        self.driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()))
        self.service = None
        self.options = None
        self.links = []
        self.data = []
        self.driver.get(url)
        self.driver.maximize_window()
        time.sleep(3)

    def extract_expose_links(self):
        links = []
        all_list = self.driver.find_elements(By.CLASS_NAME, "slick-track")
        for l in all_list:
            link = l.find_element(By.TAG_NAME, "a").get_attribute("href")
            if "expose" in link:
                links.append(link)
        return links

    @staticmethod
    def n_click(button):
        while True:
            try:
                button.click()
            except StaleElementReferenceException:
                break

    def click_all_buttons(self):
        for button in self.driver.find_elements(By.CLASS_NAME, "padding-left-none"):
            self.n_click(button)

    def extract_project_links(self):
        links = []
        self.click_all_buttons()
        all_list = self.driver.find_elements(By.CLASS_NAME, "grouped-listing-image-frame")
        for l in all_list:
            links.append(l.get_attribute("href"))
        return links

    def extract_page_links(self):
        links = self.extract_expose_links() + self.extract_project_links()
        return links

    def extract_all_links(self):
        total_n_pages = int(self.driver.find_elements(By.CLASS_NAME, "p-items")[-2].text)
        for p in range(total_n_pages):
            time.sleep(2)
            current_n_page = int(self.driver.find_element(By.CLASS_NAME, "p-active").text)
            links = self.extract_page_links()
            self.links += links
            logging.info(
                f"Current page: {current_n_page}, Total pages:{total_n_pages}, Number of Links: {len(links)}, Total links: {len(self.links)}"
            )
            try:
                next_page = self.driver.find_element(By.XPATH, "//*[@aria-label='Next page']")
                next_page.click()
            except ElementClickInterceptedException:
                time.sleep(4)
            if p == total_n_pages:
                break

    def get_company(self):
        try:
            return self.driver.find_element(By.XPATH, "//*[@data-qa='company-name']").text
        except NoSuchElementException:
            try:
                private = self.driver.find_element(By.CLASS_NAME, "brandLogoPrivate_dnns4")
                if private:
                    return "private"
            except NoSuchElementException:
                return ""

    def get_label_elements(self, data):
        label_elements = self.driver.find_elements(By.XPATH, "//dt[contains(@class, 'label')]")
        for l in label_elements:
            v_key = l.get_attribute("class").split()[0][:-6]
            data[l.text] = self.driver.find_element(By.CLASS_NAME, v_key).text
        return data

    def get_description_elements(self, data):
        description_elements = self.driver.find_elements(By.XPATH, "//h4[contains(@class, 'label')]")
        for l in description_elements:
            v_key = l.get_attribute("class").split()[0][:-6]
            try:
                data[l.text] = self.driver.find_element(By.CLASS_NAME, v_key).text
            except NoSuchElementException:
                data[l.text] = ""
        return data

    def extract_data_from_url(self, url):
        data = {}
        self.driver.get(url)
        data["URL"] = url
        data["Title"] = self.driver.find_element(By.ID, "expose-title").text
        data["Address"] = self.driver.find_element(By.CLASS_NAME, "address-block").text
        data["Company"] = self.get_company()
        data = self.get_label_elements(data)
        data = self.get_description_elements(data)
        return data

    def extract_all_data(self, links):
        for link in tqdm(links):
            try:
                self.data.append(self.extract_data_from_url(link))
                time.sleep(randint(2, 5))
            except NoSuchElementException:
                logging.info(f"Could not extract data from: {link}")
                time.sleep(60)

    def save_new_links(self, links):
        today = date.today().strftime("%Y%m%d")
        path = f"{self.links_folder}/links_{today}.json"
        with open(path, "w") as f:
            json.dump(links, f)

    def load_history_links(self):
        paths = f"{self.links_folder}/*.json"
        links = []
        for path in tqdm(glob(paths)):
            with open(path, "r") as f:
                links += json.load(f)
        return links

    def save_new_data(self):
        today = date.today().strftime("%Y%m%d")
        path = f"{self.raw_folder}/data_{today}.csv"
        df = pd.DataFrame(self.data)
        df.to_csv(path, index=False)

    @staticmethod
    def load_links(path):
        with open(path, "r") as f:
            links = json.load(f)
        return links

    @staticmethod
    def save_links(path, links):
        with open(path, "w") as f:
            json.dump(links, f)

    @staticmethod
    def save_data(path, data):
        df = pd.DataFrame(data)
        df.to_csv(path, index=False)
