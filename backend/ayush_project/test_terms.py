import json
import random
import string
from typing import Dict, Any

import jwt
import requests

BASE = "http://127.0.0.1:8000/api/"

TERMS = [
    (
        "Ajeerna",
        "The patient reports heaviness after meals, sour belching, and abdominal fullness consistent with Ajeerna.",
    ),
    (
        "Bhagandara",
        "Patient presents with chronic perianal discharge and pain suggestive of Bhagandara (fistula in ano).",
    ),
    (
        "Krimi",
        "Child has itching, abdominal colic, and visible worms in stool pointing to Krimi infestation.",
    ),
]


def show(title: str, payload: Dict[str, Any]):
    print(f"\n=== {title} ===")
    print(json.dumps(payload, indent=2))
    print("-----------------------------")


def run_for_term(term: str, note: str):
    suffix = "".join(random.choices(string.ascii_lowercase + string.digits, k=5))
    username = f"{term.lower()}_{suffix}"
    password = "Testpass123!"

    # Register
    reg_resp = requests.post(
        BASE + "register/",
        json={"username": username, "email": f"{username}@example.com", "password": password},
    )
    reg_resp.raise_for_status()

    # Login
    login_resp = requests.post(BASE + "login/", json={"username": username, "password": password})
    login_resp.raise_for_status()
    tokens = login_resp.json()
    access = tokens["access"]
    payload = jwt.decode(access, options={"verify_signature": False})
    user_id = payload["user_id"]
    headers = {"Authorization": f"Bearer {access}"}

    # Create patient
    patient_resp = requests.post(
        BASE + "patients/",
        headers=headers,
        json={
            "user": user_id,
            "ayush_id": f"AY{random.randint(10000, 99999)}",
            "age": random.randint(25, 60),
        },
    )
    patient_resp.raise_for_status()
    patient_id = patient_resp.json()["id"]

    # Run pipeline
    pipeline_resp = requests.post(
        BASE + "run_pipeline/",
        headers=headers,
        json={"patient_id": patient_id, "raw_text": note, "auto_push": False},
    )
    pipeline_resp.raise_for_status()
    return {
        "term": term,
        "user": username,
        "patient_id": patient_id,
        "pipeline_result": pipeline_resp.json()["result"],
    }


if __name__ == "__main__":
    outputs = []
    for term, note in TERMS:
        print(f"\nRunning flow for {term} ...")
        result = run_for_term(term, note)
        outputs.append(result)
        show(f"{term} RESULT", result["pipeline_result"])

    print("\nSUMMARY")
    print(json.dumps(outputs, indent=2))


