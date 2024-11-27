import csv
import hashlib
import os
import random
import re
import time

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

options = Options()
options.add_argument("--headless")
options.add_argument("--no-sandbox")
driver = webdriver.Chrome()

DATA_DIR = "data"


def generate_hash_id(paper):
    unique_string = f"{paper['title']}_{paper['authors']}_{paper['link']}"
    return hashlib.md5(unique_string.encode("utf-8")).hexdigest()


def load_author_names(filename="authors_scraped.txt"):
    if not os.path.exists(filename):
        return set()

    with open(filename, "r", encoding="utf-8") as file:
        return set(line.strip() for line in file)


def save_author_name(author_name, filename="authors_scraped.txt"):
    with open(filename, "a", encoding="utf-8") as file:
        file.write(f"{author_name}\n")


def extract_year(citation: str) -> int:
    try:
        match = re.search(r"\b(19|20)\d{2}\b", citation)
        if match:
            return int(match.group(0))

    except Exception as e:
        print(f"Error extracting year: {e}")

    return None


def get_author_papers(paper_link, papers):
    driver.get(paper_link)
    time.sleep(random.uniform(2, 4))

    title = driver.find_element(By.CSS_SELECTOR, "#gsc_oci_title").text
    try:
        type = driver.find_element(By.CSS_SELECTOR, ".gsc_vcd_title_ggt").text
    except Exception:
        type = "nan"

    # print(paper_link)
    fields = driver.find_elements(By.CSS_SELECTOR, ".gs_scl")

    paper_details = {}
    for field in fields:
        try:
            key = field.find_element(By.CSS_SELECTOR, ".gsc_oci_field").text
            value = field.find_element(By.CSS_SELECTOR, ".gsc_oci_value").text
            paper_details[key] = value
        except Exception as e:
            print(f"Error parsing field: {e}")

    authors = paper_details.get("Authors", "N/A")
    abstract = paper_details.get("Description", "N/A")
    year = extract_year(paper_details.get("Publication date", "N/A"))
    try:
        link = driver.find_element(
            By.CSS_SELECTOR, ".gsc_oci_title_link"
        ).get_attribute("href")
    except Exception:
        link = "nan"

    try:
        paperlinkcont = driver.find_element(By.CSS_SELECTOR, ".gsc_oci_title_ggi")
        paperlink_a = paperlinkcont.find_element(By.TAG_NAME, "a")
        paperlink = paperlink_a.get_attribute("href")
    except Exception:
        paperlink = "nan"

    papers.append(
        {
            "title": title,
            "authors": authors,
            "type": type,
            "abstract": abstract,
            "link": link,
            "paperlink": paperlink,
            "year": year,
        }
    )


def scrape_author_papers(author_link, author_name, papers):
    scraped_authors = load_author_names()

    if author_name in scraped_authors:
        print(f"Skipping {author_name} as their papers are already scraped.")
        return

    save_author_name(author_name)

    driver.get(author_link)
    time.sleep(random.uniform(2, 4))

    while True:
        try:
            show_more_button = driver.find_element(
                By.XPATH, "//button[contains(text(), 'Show more')]"
            )
            show_more_button.click()
            time.sleep(random.uniform(2, 4))
        except Exception:
            print("Show More button is no longer available")
            break

    results = driver.find_elements(By.CSS_SELECTOR, ".gsc_a_tr")
    paper_links = []
    for result in results:
        try:
            paper_link = result.find_element(
                By.CSS_SELECTOR, ".gsc_a_at"
            ).get_attribute("href")
            paper_links.append(paper_link)
        except Exception as e:
            print(f"Error parsing author citings: {e}")

    for paper_link in paper_links:
        get_author_papers(paper_link, papers)


def fetch_random_papers(query, num_pages=2, start_page=0):
    base_url = "https://scholar.google.com/scholar?hl=en&q="
    query_list = query.split(" ")
    base_url += "+".join(query_list)

    driver.get(base_url)
    time.sleep(random.uniform(2, 4))

    papers = []
    author_links = []
    for _ in range(start_page):
        try:
            next_button = driver.find_element(By.LINK_TEXT, "Next")
            next_button.click()
            time.sleep(random.uniform(2, 4))
        except Exception as e:
            print("No more pages or error navigating to the next page:", e)
            break

    for _ in range(num_pages):
        results = driver.find_elements(By.CSS_SELECTOR, ".gs_r.gs_or.gs_scl")
        for result in results:
            try:
                title = result.find_element(By.CSS_SELECTOR, ".gs_rt").text
                try:
                    type = result.find_element(By.CSS_SELECTOR, ".gs_ct1").text
                except Exception:
                    try:
                        type = result.find_element(By.CSS_SELECTOR, ".gs_ctg2").text
                    except Exception:
                        type = "nan"

                if type != "nan" and type in title:
                    title = title.replace(type, "")

                authors_x = result.find_element(By.CSS_SELECTOR, ".gs_a").text
                authors = authors_x.split(" - ")[0]
                date = "N/A"

                if len(authors_x.split(" - ")[1]) > 2:
                    date = extract_year(authors_x.split(" - ")[1])

                abstract = result.find_element(By.CSS_SELECTOR, ".gs_rs").text
                heading_element = result.find_element(By.CSS_SELECTOR, ".gs_rt")
                anchor_tag = heading_element.find_element(By.TAG_NAME, "a")
                link = anchor_tag.get_attribute("href")

                try:
                    paperlinkcont = result.find_element(By.CSS_SELECTOR, ".gs_or_ggsm")
                    paperlink_a = paperlinkcont.find_element(By.TAG_NAME, "a")
                    paperlink = paperlink_a.get_attribute("href")
                except Exception:
                    paperlink = "nan"

                author_flag = False
                try:
                    authors_link = result.find_element(By.CSS_SELECTOR, ".gs_a")
                    # print(authors_link)
                    authors_a = authors_link.find_elements(By.TAG_NAME, "a")
                    for author_a in authors_a:
                        author_flag = True
                        author_name = author_a.text
                        author_link = author_a.get_attribute("href")
                        if author_link not in author_links:
                            author_links.append((author_name, author_link))
                except Exception:
                    author_flag = False

                if not author_flag:
                    papers.append(
                        {
                            "title": title,
                            "authors": authors,
                            "type": type,
                            "abstract": abstract,
                            "link": link,
                            "paperlink": paperlink,
                            "year": date,
                        }
                    )
            except Exception as e:
                print(f"Error parsing result: {e}")

        try:
            next_button = driver.find_element(By.LINK_TEXT, "Next")
            next_button.click()
            time.sleep(random.uniform(2, 4))
        except Exception as e:
            print("No more pages or error navigating to the next page:", e)
            break

    for author_name, author_link in author_links:
        scrape_author_papers(author_link, author_name, papers)

    return papers


def save_data_to_csv(papers, query):
    fieldnames = [
        "id",
        "title",
        "authors",
        "type",
        "abstract",
        "link",
        "paperlink",
        "year",
    ]

    filename = f"{''.join([word[0].upper() for word in query.split()])}_papers.csv"
    existing_ids = set()

    if os.path.exists(filename):
        with open(filename, mode="r", newline="", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            for row in reader:
                existing_ids.add(row["id"])

    with open(filename, mode="a", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        if file.tell() == 0:
            writer.writeheader()
        for paper in papers:
            paper_id = generate_hash_id(paper)
            if paper_id not in existing_ids:
                paper_with_id = {
                    "id": paper_id,
                    **paper,
                }
                writer.writerow(paper_with_id)
                existing_ids.add(paper_id)


if __name__ == "__main__":
    TOPICS = [
        "Machine Learning",
        "Image Processing",
        "Object Detection",
        "Computer Vision",
        "Internet Of Things",
        "Antenna",
        "Science",
        "Maths",
        "Deeplearning",
        "Statistics",
        "Natural Language Processing",
        "Large Language Models",
        "Artificial Intelligence",
        "Neural Networks",
        "Transformers",
        "Quantum Computing",
        "Cryptography",
        "Blockchain",
        "Graph Theory",
        "Cloud Computing",
    ]

    for query in TOPICS:
        start_page = 0
        num_pages = 10
        papers = fetch_random_papers(query, num_pages, start_page)
        save_data_to_csv(papers, query)

    driver.quit()
