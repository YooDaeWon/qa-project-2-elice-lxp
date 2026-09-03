import os
import requests
from dotenv import load_dotenv

load_dotenv()

r = requests.post(
    "https://dev-qatrack-account-api.dev.elicer.io/login/pw",
    json={"login_id": os.getenv("ST_ID"), "password": os.getenv("ST_PW")},
)
token = r.json()["access_token"]
headers = {
    "Authorization": f"Bearer {token}",
    "x-elice-org-name-short": "academy",
}

g = requests.get(
    "https://dev-qatrack-api.dev.elicer.io/org/academy/board/article/get/",
    params={"board_article_id": 9874},
    headers=headers,
)
print(g.status_code)
print(g.text[:1500])
