import os

import dotenv
import requests

dotenv.load_dotenv()

MEILI_URL = os.getenv("MEILI_URL", "http://localhost:7700/")
MEILI_AUTH_KEY = os.getenv("MEILI_AUTH_KEY")


headers = {"Authorization": f"Bearer {MEILI_AUTH_KEY}"}
payload = {
    "description": "Full access key",
    "actions": ["*"],
    "indexes": ["*"],
    "expiresAt": None,
}

response = requests.post(f"{MEILI_URL}/keys", headers=headers, json=payload)

if response.status_code == 201:
    print("New API Key:", response.json()["key"])
else:
    print(f"Error: {response.status_code}, {response.text}")
