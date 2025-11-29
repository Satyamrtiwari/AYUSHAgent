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
ICD_TOKEN_URL = os.getenv("ICD_TOKEN_URL", "https://icdaccessmanagement.who.int/connect/token")
# Use the correct search URL matching the working ICD_api_key.py script
# Force the correct URL (matching user's working script)
ICD_SEARCH_URL = "https://id.who.int/icd/release/11/2024-01/mms/search"
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
        Uses POST with form-data (exactly matching the working ICD_api_key.py script).
        """
        try:
            # Verify credentials and URL are loaded
            if not ICD_CLIENT_ID or not ICD_CLIENT_SECRET:
                print(f"❌ ICD API credentials missing: CLIENT_ID={bool(ICD_CLIENT_ID)}, CLIENT_SECRET={bool(ICD_CLIENT_SECRET)}")
                return []
            
            if not ICD_SEARCH_URL:
                print(f"❌ ICD_SEARCH_URL not configured")
                return []
            
            if not self._token_ok():
                self._fetch_token()

            headers = {
                "Authorization": f"Bearer {self._token}",
                "API-Version": ICD_API_VERSION,
                "Accept-Language": "en",
                "Accept": "application/json",
                "Content-Type": "application/x-www-form-urlencoded"  # Important: form-data (not JSON)
            }
            
            # Use POST with form-data (exactly as in working ICD_api_key.py)
            body = {
                "q": query,
                "chapterFilter": "mms"
            }
            
            print(f"🔍 Searching ICD-11 API for: '{query}'")
            print(f"   URL: {ICD_SEARCH_URL}")
            r = requests.post(ICD_SEARCH_URL, headers=headers, data=body, timeout=DEFAULT_TIMEOUT)

            if r.status_code == 401:
                # Token expired - refresh once
                print("🔄 Token expired, refreshing...")
                self._fetch_token()
                headers["Authorization"] = f"Bearer {self._token}"
                r = requests.post(ICD_SEARCH_URL, headers=headers, data=body, timeout=DEFAULT_TIMEOUT)

            if r.status_code != 200:
                print(f"❌ ICD Search error {r.status_code}: {r.text[:200]}")
                return []

            data = r.json()
            
            # Debug: Check what the API actually returned
            if not data:
                print(f"⚠️ ICD API returned empty JSON for '{query}'")
                return []
            
            ents = data.get("destinationEntities", [])
            
            # Debug: Log raw response structure
            if not ents:
                print(f"⚠️ ICD API returned 0 results for '{query}'")
                print(f"   Response keys: {list(data.keys())}")
                if "destinationEntities" in data:
                    print(f"   destinationEntities type: {type(data['destinationEntities'])}")
                return []
            
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
            import traceback
            print(traceback.format_exc())
            return []
