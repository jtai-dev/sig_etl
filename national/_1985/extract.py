import re
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse, urljoin

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from tqdm import tqdm


URL = "https://grades.numbersusa.com/"
CANDIDATE_URL_PATTERN = (
    r"^https://(?P<domain>[^/]+)/gradecard/(?P<candidate_id>\d+)/(?P<session>\d+)/$"
)


def extract(page_source, **additional_info):

    soup = BeautifulSoup(page_source, "html.parser")

    info_container = soup.find("div", {"class": "rep-info-container"})
    info_text = info_container.get_text(strip=True, separator=";")

    nav_container = soup.find("div", {"class": "tab-nav-container"})
    score_containers = nav_container.find_all("a", {"class", "nav-link"})

    def get_score(x):
        score_parts = x.get_text(strip=True).split(":")
        score_type = score_parts[0].strip() if score_parts else ""
        score_value = score_parts[1].strip() if len(score_parts) > 1 else ""
        return score_type.strip(), score_value.strip()

    name, office, state_district, *_ = info_text.split(";")

    return (
        {"name": name, "office": office, "state_district": state_district}
        | dict(map(get_score, score_containers))
        | additional_info
    )


def get_sig_candidate_id(page_source):
    soup = BeautifulSoup(page_source, "html.parser")
    headshot = soup.find("div", {"class": "rep-headshot"})
    image_src = headshot.img["src"]
    sig_candidate_id = image_src.rpartition("/")[-1].rstrip(".jpg")
    return sig_candidate_id


def extract_files(files: list):

    extracted = []

    for file in tqdm(files):
        with open(file, "r") as f:
            page_source = f.read()
            extracted.append(
                extract(page_source, sig_candidate_id=get_sig_candidate_id(page_source))
            )

    records_extracted = dict(enumerate(extracted))

    return records_extracted


def get_cpage_urls(page_source):
    soup = BeautifulSoup(page_source, "html.parser")
    rows = soup.find_all("row", {"class": "rep-link"})

    def clean(x):
        return x.lstrip("go(')").rstrip("');")

    return [urlparse(urljoin(URL, clean(row["onclick"]))) for row in rows]


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


def main(filename, export_path: Path, html_path: Path = None):

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

    search_button = chrome_driver.find_element(By.XPATH, "//input[@value='Search']")
    search_button.click()

    cpage_urls = get_cpage_urls(chrome_driver.page_source)

    extracted = []

    for url in tqdm(cpage_urls):
        chrome_driver.get(url.geturl())
        url_extract = re.match(CANDIDATE_URL_PATTERN, url.geturl())
        save_html(
            chrome_driver.page_source,
            export_path / "HTML_FILES",
            filename,
            url_extract.group(
                "candidate_id",
            ),
        )
        extracted.append(
            extract(
                chrome_driver.page_source,
                sig_candidate_id=url_extract.group("candidate_id"),
            )
        )

    records_extracted = dict(enumerate(extracted))
    return records_extracted
