import glob
import json
import os
import random

import dotenv
import langdetect
import pandas as pd
from meilisearch import Client

dotenv.load_dotenv()

DATA_DIR = "data"
DATA_FILE = "research_papers.json"
INDEX_NAME = "documents"
MEILI_URL = os.getenv("MEILI_URL", "http://localhost:7700/")
MEILI_API_KEY = os.getenv("MEILI_API_KEY")

keywords_dict = {
    "ML_papers": "Machine Learning",
    "IP_papers": "Image Processing",
    "OD_papers": "Object Detection",
    "CV_papers": "Computer Vision",
    "IOT_papers": "Internet Of Things",
    "A_papers": "Antenna",
    "SC_papers": "Science",
    "M_papers": "Maths",
    "D_papers": "Deep Learning",
    "S_papers": "Statistics",
    "NLP_papers": "Natural Language Processing",
    "LLM_papers": "Large Language Models",
    "AI_papers": "Artificial Intelligence",
    "NN_papers": "Neural Networks",
    "T_papers": "Transformers",
    "QC_papers": "Quantum Computing",
    "C_papers": "Cryptography",
    "B_papers": "Blockchain",
    "GT_papers": "Graph Theory",
    "CC_papers": "Cloud Computing",
}


def is_english(text):
    try:
        if text and langdetect.detect(text) == "en":
            return True
    except Exception:
        pass

    return False


dataframes = []
for file in glob.glob(f"{DATA_DIR}/*.csv"):
    keyword = os.path.splitext(os.path.basename(file))[0]
    df = pd.read_csv(file)

    df["keyword"] = keywords_dict.get(keyword, "Unknown")
    df = df.where(pd.notnull(df), None)

    for col in ["title", "abstract"]:
        if col in df.columns:
            df = df[df[col].apply(lambda x: is_english(x))]

    dataframes.append(df)

merged_data = pd.concat(dataframes, ignore_index=True)
merged_data["year"] = merged_data.apply(lambda _: random.randint(1995, 2024), axis=1)

if "id" not in merged_data.columns:
    merged_data["id"] = merged_data.index

documents = merged_data.to_dict(orient="records")

with open(f"{DATA_DIR}/{DATA_FILE}", "w") as f:
    json.dump(documents, f, indent=2)

# with open(f"{DATA_DIR}/{DATA_FILE}", "r") as f:
#     documents = json.load(f)

client = Client(MEILI_URL, MEILI_API_KEY)

try:
    client.get_index(INDEX_NAME)
    client.delete_index(INDEX_NAME)
    print(f"Index '{INDEX_NAME}' deleted.")
except Exception:
    print(f"Index '{INDEX_NAME}' does not exist. Creating a new one.")

client.create_index(uid=INDEX_NAME, options={"primaryKey": "id"})
print(f"Index '{INDEX_NAME}' created.")

index = client.index(INDEX_NAME)
index.update_settings(
    {
        "searchableAttributes": ["title", "abstract", "keyword", "authors"],
        "filterableAttributes": ["keyword", "authors", "year"],
        "sortableAttributes": ["date", "popularity", "year"],
        "displayedAttributes": [
            "id",
            "title",
            "authors",
            "type",
            "abstract",
            "link",
            "paperlink",
            "keyword",
            "year",
        ],
        "typoTolerance": {
            "enabled": True,
            "minWordSizeForTypos": {
                "oneTypo": 5,
                "twoTypos": 9,
            },
            "disableOnWords": ["AI", "NLP"],
            "disableOnAttributes": ["keyword"],
        },
        "rankingRules": ["typo", "words", "proximity", "attribute", "exactness"],
        "synonyms": {
            "AI": ["Artificial Intelligence", "Machine Learning"],
            "ML": ["Machine Learning"],
            "NLP": ["Natural Language Processing"],
            "LLM": ["Large Language Models"],
            "B": ["Blockchain"],
            "CC": ["Cloud Computing"],
            "GT": ["Graph Theory"],
            "QC": ["Quantum Computing"],
        },
        "stopWords": ["the", "and", "or", "but", "of", "in", "on", "with"],
        "distinctAttribute": "id",
    }
)

index.add_documents(documents)
print(f"Added {len(documents)} documents to the index '{INDEX_NAME}'.")
