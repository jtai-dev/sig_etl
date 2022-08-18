# This is the webscraping script for National Parks Conservation Association (NPCA), sig_id=922

import os
import pandas
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import NoSuchElementException
from tqdm import tqdm
from bs4 import BeautifulSoup


MAIN_URL = "https://nationalparksaction.org/online-scorecard/"
SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))


def extract_candidate_urls(soup):
    container = soup.find('div', {'id': 'legislators-container'})
    urls = [card.a['href'] for card in container.find_all('div', {'class': 'card'})]

    return urls


def extract(driver):
    soup = BeautifulSoup(driver.page_source, 'html.parser')

    npca_id = driver.current_url.split('/')[-1]
    name = soup.find('div', {'class': 'legislator-name'})
    office_party, state_district = soup.find('div', {'class': 'legislator-sub-head'}).text.strip().split(',')
    score = soup.find('p', {'class': 'legislator-detail-score'}).span

    record = {'NPCA_id': npca_id,
              'name': name.text.strip() if name else None, 
              'office (party)': office_party.strip() if office_party else None, 
              'state-district': state_district.strip() if state_district else None,
              'sig_rating': score.text.strip() if score else None}

    with open(f'_NA_NPCA_Ratings_{npca_id}.html', 'w') as f:
        f.write(soup.prettify())

    return record


def download_page(driver):
    if not os.path.isdir(f"{SCRIPT_DIR}/Ratings"):
        os.mkdir(f"{SCRIPT_DIR}/Ratings")

    candidate_id = driver.current_url.split('/')[-1]
    soup = BeautifulSoup(driver.page_source, 'html.parser')

    with open(f"{SCRIPT_DIR}/Ratings/Ratings_{candidate_id}.html", 'w') as f:
        f.write(soup.prettify())


def main():
    chrome_service = Service('chromedriver')
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument('incognito')
    # chrome_options.add_argument('headless')

    driver = webdriver.Chrome(service=chrome_service, options=chrome_options)

    driver.get(MAIN_URL)

    try:
        WebDriverWait(driver,10).until(EC.presence_of_element_located((By.ID, "legislators-container")))
        
    except TimeoutException:
        print("Cannot find Legislator Container. Quitting...")
        exit()


    while True:
        try:
            pagination = driver.find_element(By.XPATH, "//div[@class='pagination pure-u-md-1 pure-u-lg-3-4']/a")

            if pagination:
                pagination.click()
            else:
                break

        except NoSuchElementException:
            break

    soup = BeautifulSoup(driver.page_source, 'html.parser')

    records = []

    for url in tqdm(extract_candidate_urls(soup)):
        driver.get(MAIN_URL + url)
        records.append(extract(driver))
        download_page(driver)

    df = pandas.DataFrame.from_records(records)
    df.to_csv('_NA_NPCA_Ratings-Extract.csv', index=False)

if __name__ == '__main__':
    main()