import requests
from app.core.config import settings


BASE_URL = "https://api.football-data.org/v4"


def fetch_matches():
    url = f"{BASE_URL}/matches"

    headers = {
        "X-Auth-Token": settings.FOOTBALL_DATA_API_KEY
    }

    response = requests.get(url, headers=headers, timeout=10)

    print("요청 URL:", url)
    print("상태 코드:", response.status_code)

    response.raise_for_status()

    return response.json()