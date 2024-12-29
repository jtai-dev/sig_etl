from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse, urljoin

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import NoSuchElementException

from tqdm import trange


URL = "https://cdfactioncouncil.org/scorecard_legislator/"


def extract(page_source, **additional_info):

    soup = BeautifulSoup(page_source, "html.parser")
    articles = soup.select("div#posts-container article.post")

    extracted = []

    for article in articles:

        name = article.select_one("div.rep-name")
        grade_title = article.select_one("div.grade-title")
        grade = article.select_one("a.grade")
        info = article.select_one("div.legislator-data")

        extracted.append(
            {
                "name": name.get_text(strip=True),
                (
                    grade_title.get_text(strip=True) if grade_title else "Grade"
                ): grade.get_text(strip=True),
                "info": info.get_text(strip=True, separator=";"),
            }
            | additional_info
        )

    return extracted


def extract_files(files: list[Path]):

    extracted = []

    for file in files:

        with open(file, "r") as f:
            extracted += extract(f.read())

    records_extracted = dict(enumerate(extracted))

    return records_extracted


def save_html(
    page_source,
    filepath: Path,
    filename: str,
    *additional_info,
):

    filepath.mkdir(exist_ok=True)

    soup = BeautifulSoup(page_source, "html.parser")
    timestamp = datetime.strftime(datetime.now(), "%Y-%m-%d-%H%M%S-%f")

    with open(
        filepath
        / (
            f"{filename}_{'-'.join(map(str, additional_info))}"
            f"{'-' if additional_info else ''}{timestamp}.html"
        ),
        "w",
    ) as f:
        f.write(str(soup))


def main(filename: str, export_path: Path, html_path: Path = None):

    # if html_path:
    #     html_files = filter(
    #         lambda f: f.name.endswith(".html"),
    #         (export_path / html_path).iterdir(),
    #     )
    #     records_extracted = extract_files(
    #         sorted(html_files, key=lambda x: x.stat().st_ctime)
    #     )
    #     return records_extracted

    chrome_service = Service()
    chrome_options = Options()
    chrome_options.add_argument("incognito")
    chrome_options.add_argument("headless")
    chrome_driver = webdriver.Chrome(service=chrome_service, options=chrome_options)

    chrome_driver.get(URL)

    # close overlay
    ActionChains(chrome_driver).send_keys(Keys.ESCAPE).perform()

    pages = chrome_driver.find_elements(By.CSS_SELECTOR, "div.pagination a.inactive")

    last_page_link = urlparse(pages[-1].get_attribute("href"))

    page_query = last_page_link.query.rpartition("=")[0]
    last_page = last_page_link.query.rpartition("=")[-1]

    extracted = []

    for i in trange(1, int(last_page) + 1):
        chrome_driver.get(urljoin(URL, f"?{page_query}={i}"))
        save_html(
            chrome_driver.page_source,
            export_path / "HTML_FILES",
            filename,
        )
        extracted += extract(chrome_driver.page_source)

    records_extracted = dict(enumerate(extracted))

    return records_extracted