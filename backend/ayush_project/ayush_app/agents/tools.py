import csv
from functools import lru_cache
from pathlib import Path
import uuid
from datetime import datetime

BASE = Path(__file__).resolve().parents[1]
CSV_PATH = BASE/"data"/"seed_mappings.csv"


PRIORITY_CODES = {
    "visarpa": "1C13",  # Clinical priority override
    "udara roga": "MB41",
}


@lru_cache()
def _load_seed_rows():
    if not CSV_PATH.exists(): 
        return []
    with open(CSV_PATH) as f:
        return list(csv.DictReader(f))


def _variant_keys(value):
    """
    Generate comparison keys for a term, including content inside parentheses.
    Example: "Shvitra (Shwetakustha)" -> {"shvitra (shwetakustha)", "shvitra", "shwetakustha"}
    """
    base = (value or "").lower().strip()
    keys = {base, base.replace(" ", "")}
    if "(" in base and ")" in base:
        prefix = base.split("(", 1)[0].strip()
        suffix = base.split("(", 1)[1].split(")", 1)[0].strip()
        if prefix:
            keys.add(prefix)
            keys.add(prefix.replace(" ", ""))
        if suffix:
            keys.add(suffix)
            keys.add(suffix.replace(" ", ""))
    return {k for k in keys if k}


def deterministic_lookup(term):
    """
    Lookup AYUSH term in seed mappings with synonym awareness.
    Returns metadata so upstream callers can trigger manual review when multiple
    deterministic matches exist (e.g., 'Shwasa' vs 'Shwasa (Tamaka Shwasa)').
    """
    rows = _load_seed_rows()
    t = (term or "").lower().strip()
    if not t:
        return None

    matches = []
    for row in rows:
        row_term = row.get("ayush_term", "")
        if not row_term:
            continue
        keys = _variant_keys(row_term)
        if t in keys:
            match_entry = {
                "ayush_term": row_term,
                "icd_code": row.get("icd_code"),
                "icd_title": row.get("icd_title"),
                "match_type": "exact" if row_term.lower().strip() == t else "alias"
            }
            matches.append(match_entry)

    if not matches:
        return None

    # Prefer explicit priorities → exact match → first match
    primary = None
    priority_code = PRIORITY_CODES.get(t)
    if priority_code:
        primary = next((m for m in matches if m["icd_code"] == priority_code), None)
    if not primary:
        primary = next((m for m in matches if m["match_type"] == "exact"), None)
    if not primary:
        primary = matches[0]

    # Trigger manual review if multiple discrete matches map to different codes/titles
    codes = {m["icd_code"] for m in matches if m.get("icd_code")}
    needs_review = len(matches) > 1 and len(codes) > 1
    review_reason = None
    if needs_review:
        review_reason = "Multiple deterministic mappings found for this term. Please select the correct ICD-11 code."
    elif len(matches) > 1:
        review_reason = "Alternate spellings detected for this term. Confirm the ICD-11 code before pushing to ABDM."

    return {
        "primary": primary,
        "matches": matches,
        "needs_review": needs_review,
        "review_reason": review_reason,
    }


def find_term_in_text(text):
    """
    Lightweight fallback parser: scans the seed mappings to see if any AYUSH term
    is already present inside the raw note. Returns the first hit, else None.
    """
    rows = _load_seed_rows()
    lowered = (text or "").lower()
    for row in rows:
        term = row["ayush_term"]
        if term and term.lower() in lowered:
            return term
    return None


def build_fhir(state, patient_ref):
    b = state["best"]
    now = datetime.utcnow().isoformat()+"Z"

    return {
        "resourceType":"Condition",
        "id": str(uuid.uuid4()),
        "code":{
            "coding":[
                {"system":"ICD-11","code": b["code"], "display": b["title"]},
                {"system":"AYUSH","code": state["ayush_term"]}
            ]
        },
        "subject":{"reference":patient_ref},
        "onsetDateTime":now,
        "note":[{"text": state["reason"]}],
        "confidence": state["confidence"]
    }
