# support_api.py
import os
import requests

SERVICE_KEY = os.getenv("PUBLIC_DATA_KEY")
BASE = "https://api.odcloud.kr/api/gov24/v3"

# 1. 목록 조회 (keyword 기반)
def fetch_service_list(keyword: str = "") -> list:
    url = f"{BASE}/serviceList"
    params = {
        "page": 1,
        "perPage": 100,
        "serviceKey": SERVICE_KEY
    }
    res = requests.get(url, params=params)
    res.raise_for_status()
    data = res.json().get("data", [])
    return [d for d in data if keyword in d.get("서비스명", "")]

# 2. 상세정보 조회 (서비스ID 필요)
def fetch_service_detail(service_id: str) -> dict:
    url = f"{BASE}/serviceDetail"
    params = {
        "serviceKey": SERVICE_KEY,
        "srvcId": service_id
    }
    res = requests.get(url, params=params)
    res.raise_for_status()
    return res.json().get("data", {})

# 3. 민감정보 포함 상세 (보통 비공개, optional)
def fetch_service_detail_auth(service_id: str) -> dict:
    url = f"{BASE}/serviceDetailAuth"
    params = {
        "serviceKey": SERVICE_KEY,
        "srvcId": service_id
    }
    res = requests.get(url, params=params)
    res.raise_for_status()
    return res.json().get("data", {})
