# agents/abdm_client.py
import os
import time
import requests
from dotenv import load_dotenv

load_dotenv()

ABDM_CLIENT_ID = os.getenv("ABDM_CLIENT_ID")
ABDM_CLIENT_SECRET = os.getenv("ABDM_CLIENT_SECRET")
ABDM_TOKEN_URL = os.getenv("ABDM_TOKEN_URL")
ABDM_FHIR_BASE = os.getenv("ABDM_FHIR_BASE")

DEFAULT_TIMEOUT = 10  # seconds

class ABDMClient:
    def __init__(self):
        self._token = None
        self._expires = 0

    def _fetch_token(self):
        if not ABDM_CLIENT_ID or not ABDM_CLIENT_SECRET or not ABDM_TOKEN_URL:
            raise EnvironmentError("ABDM credentials or token URL not configured")
        data = {
            "client_id": ABDM_CLIENT_ID,
            "client_secret": ABDM_CLIENT_SECRET,
            "grant_type": "client_credentials"
        }
        r = requests.post(ABDM_TOKEN_URL, data=data, timeout=DEFAULT_TIMEOUT)
        r.raise_for_status()
        js = r.json()
        self._token = js.get("access_token")
        self._expires = time.time() + js.get("expires_in", 3600)

    def _token_ok(self):
        return self._token and time.time() < self._expires - 30

    def push_condition(self, fhir_json):
        if not ABDM_FHIR_BASE:
            raise EnvironmentError("ABDM FHIR base URL not configured")
        try:
            if not self._token_ok():
                self._fetch_token()

            headers = {"Authorization": f"Bearer {self._token}", "Content-Type": "application/fhir+json"}
            url = f"{ABDM_FHIR_BASE.rstrip('/')}/Condition"
            r = requests.post(url, json=fhir_json, headers=headers, timeout=DEFAULT_TIMEOUT)

            if r.status_code == 401:
                self._fetch_token()
                headers["Authorization"] = f"Bearer {self._token}"
                r = requests.post(url, json=fhir_json, headers=headers, timeout=DEFAULT_TIMEOUT)

            r.raise_for_status()
            return r.json()
        except requests.RequestException as e:
            # network/http error
            raise
        except EnvironmentError:
            # credentials missing
            raise
