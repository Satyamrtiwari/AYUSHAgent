# agents/icd_client.py
import os
import time
import requests
import re
from dotenv import load_dotenv
from pathlib import Path

# Load env vars from repo root
ENV_PATH = Path(__file__).resolve().parents[4] / ".env"
if ENV_PATH.exists():
    load_dotenv(ENV_PATH)
else:
    load_dotenv()

ICD_CLIENT_ID = os.getenv("ICD_CLIENT_ID")
ICD_CLIENT_SECRET = os.getenv("ICD_CLIENT_SECRET")
ICD_TOKEN_URL = os.getenv("ICD_TOKEN_URL")
ICD_SEARCH_URL = os.getenv("ICD_SEARCH_URL")
ICD_API_VERSION = os.getenv("ICD_API_VERSION", "v2")

DEFAULT_TIMEOUT = 10  # seconds

def clean_html(text):
    """Remove WHO HTML tags like <em class='found'>."""
    if not text:
        return ""
    return re.sub(r"<.*?>", "", text)

def extract_description(entity):
    """
    Extract description from ICD API entity.
    Checks matchingPVs for description text.
    """
    if not entity:
        return None
    
    # Check matchingPVs (property values that matched the search)
    matching_pvs = entity.get("matchingPVs", [])
    if matching_pvs and len(matching_pvs) > 0:
        # Get the first matching property value's label
        desc_raw = matching_pvs[0].get("label", "")
        if desc_raw:
            return clean_html(desc_raw)
    
    # Fallback: check other description fields
    desc = entity.get("definition", "") or entity.get("description", "")
    if desc:
        return clean_html(desc)
    
    return None

class ICD11Client:
    def __init__(self):
        self._token = None
        self._expires = 0

    def _fetch_token(self):
        if not ICD_CLIENT_ID or not ICD_CLIENT_SECRET or not ICD_TOKEN_URL:
            raise EnvironmentError("ICD11 credentials or token URL not configured")
        data = {
            "grant_type": "client_credentials",
            "client_id": ICD_CLIENT_ID,
            "client_secret": ICD_CLIENT_SECRET,
            "scope": "icdapi_access"
        }
        print(f"🔑 Fetching ICD API token from {ICD_TOKEN_URL}")
        r = requests.post(ICD_TOKEN_URL, data=data, timeout=DEFAULT_TIMEOUT)
        r.raise_for_status()
        js = r.json()
        self._token = js.get("access_token")
        self._expires = time.time() + js.get("expires_in", 3600)
        print(f"✅ ICD API token obtained (expires in {js.get('expires_in', 3600)}s)")

    def _token_ok(self):
        return self._token and time.time() < self._expires - 30

    def search(self, query):
        """
        Returns list of dicts with code, title, description, and raw data.
        Uses POST with form-data (as per WHO API requirements).
        """
        try:
            if not self._token_ok():
                self._fetch_token()

            headers = {
                "Authorization": f"Bearer {self._token}",
                "API-Version": ICD_API_VERSION,
                "Accept-Language": "en",
                "Accept": "application/json",
                "Content-Type": "application/x-www-form-urlencoded"  # Important: form-data
            }
            
            # Use POST with form-data (as in your test script)
            body = {
                "q": query,
                "chapterFilter": "mms"
            }
            
            print(f"🔍 Searching ICD-11 API for: '{query}'")
            r = requests.post(ICD_SEARCH_URL, headers=headers, data=body, timeout=DEFAULT_TIMEOUT)

            if r.status_code == 401:
                # try refreshing once
                print("🔄 Token expired, refreshing...")
                self._fetch_token()
                headers["Authorization"] = f"Bearer {self._token}"
                r = requests.post(ICD_SEARCH_URL, headers=headers, data=body, timeout=DEFAULT_TIMEOUT)

            r.raise_for_status()
            data = r.json()
            ents = data.get("destinationEntities", [])
            out = []
            for e in ents[:10]:  # Get more results to allow better prioritization
                title = clean_html(e.get("title", ""))
                code = e.get("theCode")
                description = extract_description(e)
                
                if code and title:
                    out.append({
                        "code": code,
                        "title": title,
                        "description": description,  # Add description
                        "raw": e
                    })
            print(f"✅ ICD API returned {len(out)} results for '{query}'")
            return out
        except requests.RequestException as e:
            # network or http error — log and return empty
            print(f"❌ ICD API request failed for '{query}': {str(e)}")
            return []
        except EnvironmentError as e:
            # credentials missing — log and return empty
            print(f"❌ ICD API credentials missing: {str(e)}")
            return []
        except Exception as e:
            # unexpected error — log and return empty
            print(f"❌ ICD API unexpected error for '{query}': {str(e)}")
            return []
