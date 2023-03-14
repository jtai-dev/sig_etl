# This is the webscraping script for Business & Industry Political Education Committee, sig_id = 1216

import sys
import pandas

from selenium import webdriver
from selenium.webdriver.chrome.service import Service

from bs4 import BeautifulSoup
from datetime import datetime
from pathlib import Path


FILENAME = f"_MA_BIPEC_Ratings"
TIMESTAMP = datetime.strftime(datetime.now(), '%Y-%m-%d')

METHODOLOGY = {'glyphicon-ok': '+', 
               'glyphicon-remove': '-'}

OFFICES = ['house', 'senate']


def extract(driver:webdriver.Chrome, file:str=None):

    if file:
        soup = BeautifulSoup(file, 'html.parser')
    else:
        soup = BeautifulSoup(driver.page_source, 'html.parser')
    
    table = soup.find('table', {'id': 'example'})
    office = driver.current_url.split('=')[-1]

    headers = []

    for th in table.thead.find_all('th'):
        if th.span:
            th.span.clear()
        headers.append(th.text)

    rows = [tr.find_all('td') for tr in table.tbody.find_all('tr')]

    extracted = []
    
    for row in rows:
        bipec_id = row[1].a['href'].split('=')[-1]
        
        translate_rating = lambda x: METHODOLOGY[x.span['class'][-1]] if x.span else x.text

        extracted.append({'bipec_id': bipec_id} |
                        dict(zip(headers[:4], map(lambda x: x.text.strip(), row[:4]))) | 
                        {'office': office} |
                        dict(zip(headers[4:], map(translate_rating, row[4:])))
                        )
    return extracted


def download_page(driver:webdriver.Chrome):

    soup = BeautifulSoup(driver.page_source, 'html.parser')
    office = driver.current_url.split('=')[-1]

    HTML_FILES.mkdir(exist_ok=True)

    with open(HTML_FILES / f"{FILENAME}_{office}-{TIMESTAMP}.html", 'w') as f:
        f.write(soup.prettify())


def extract_from_file(files:list):
    
    extracted  = []

    for file in files:

        with open(file, 'r') as f:
            file_contents = f.read()
        
        extracted += extract(driver=None, file=file_contents)
    
    EXTRACT_FILES.mkdir(exist_ok=True)

    df = pandas.DataFrame.from_records(extracted)
    df.to_csv(EXTRACT_FILES / f"{FILENAME}-Extract_{TIMESTAMP}.csv", index=False)


def main():
    
    chrome_service = Service('chromedriver')
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument('incognito')
    chrome_options.add_argument('headless')
    chrome_driver = webdriver.Chrome(service=chrome_service, options=chrome_options)

    extracted = []

    for office in OFFICES:
        chrome_driver.get(f"{URL}/?c={office}")
        
        download_page(chrome_driver)
        extracted += extract(chrome_driver)

    EXTRACT_FILES.mkdir(exist_ok=True)

    df = pandas.DataFrame.from_records(extracted)
    df.to_csv(EXTRACT_FILES / f"{FILENAME}-Extract_{TIMESTAMP}.csv", index=False)


if __name__ == "__main__":
    _, EXPORT_DIR, URL, FILES = sys.argv

    EXPORT_DIR = Path(EXPORT_DIR)
    HTML_FILES = EXPORT_DIR / "HTML_FILES"
    EXTRACT_FILES = EXPORT_DIR / "EXTRACT_FILES"
    
    if FILES:
        extract_from_file(FILES)
    else:
        main()
