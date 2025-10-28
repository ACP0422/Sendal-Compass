import requests, os, time

GHL_BASE = "https://services.leadconnectorhq.com"
CLIENT_ID = os.getenv("GHL_CLIENT_ID")
CLIENT_SECRET = os.getenv("GHL_CLIENT_SECRET")
REFRESH_TOKEN = os.getenv("GHL_REFRESH_TOKEN")

token_cache = {"access_token": None, "expires_at": 0}

def get_access_token():
    now = time.time()
    if token_cache["access_token"] and now < token_cache["expires_at"]:
        return token_cache["access_token"]

    url = f"{GHL_BASE}/oauth/token"
    data = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "grant_type": "refresh_token",
        "refresh_token": REFRESH_TOKEN,
    }
    r = requests.post(url, data=data)
    r.raise_for_status()
    token = r.json()
    token_cache["access_token"] = token["access_token"]
    token_cache["expires_at"] = now + token["expires_in"] - 60
    return token["access_token"]
