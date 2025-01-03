from datetime import datetime
from pathlib import Path
from urllib.parse import urljoin

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


URL = "https://www.clubforgrowth.org/scorecards/app/"


def extract(page_source, **additional_info):

    soup = BeautifulSoup(page_source, "html.parser")
    table = soup.find("table", {"class": "full-scorecard"})

    headers = [th.get_text(strip=True) for th in table.select("thead th")]
    rows = [tr.select("td") for tr in table.select("tbody tr.scorecard-row")]

    extracted = []

    for row in rows:
        id_link = row[3].a.get("href")
        sig_candidate_id = id_link.split("/")[-2]

        extracted.append(
            dict(zip(headers, [c.get_text(strip=True) for c in row]))
            | {"sig_candidate_id": sig_candidate_id}
            | additional_info
        )

    return extracted


def get_years(page_source):
    soup = BeautifulSoup(page_source, "html.parser")
    year_select = soup.find("select", {"name": "yr"})
    year_options = [int(o["value"]) for o in year_select.find_all("option")]
    return year_options


def extract_files(files: list):

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
            f"{'-' if any(additional_info) else ''}{timestamp}.html"
        ),
        "w",
    ) as f:
        f.write(str(soup))


def main(filename: str, export_path: Path, html_path: Path = None, year: int = None):

    if html_path:
        html_files = filter(
            lambda f: f.name.endswith(".html"),
            (export_path / html_path).iterdir(),
        )
        records_extracted = extract_files(
            sorted(html_files, key=lambda x: x.stat().st_ctime)
        )
        return records_extracted

    chrome_service = Service()
    chrome_options = Options()
    chrome_options.add_argument("incognito")
    chrome_options.add_argument("headless")
    chrome_driver = webdriver.Chrome(service=chrome_service, options=chrome_options)

    chrome_driver.get(URL)

    # close overlay
    ActionChains(chrome_driver).send_keys(Keys.ESCAPE).perform()

    if year:
        if year not in get_years(chrome_driver.page_source):
            print("Year does not exists.")
            return []
        else:
            chrome_driver.get(urljoin(URL, f"?yr={year}"))

    save_html(
        chrome_driver.page_source,
        export_path / "HTML_FILES",
        filename,
        str(year) if year else "",
    )
    extracted = extract(chrome_driver.page_source)
    records_extracted = dict(enumerate(extracted))

    return records_extracted
