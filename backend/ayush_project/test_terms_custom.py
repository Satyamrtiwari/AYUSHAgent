import json
import random
import string

import jwt
import requests

BASE = "http://127.0.0.1:8000/api/"

TERMS = [
    (
        "Kasa",
        "Persistent dry cough with wheezing and scanty sputum consistent with Kasa.",
    ),
    (
        "Ardhavabhedaka",
        "Severe unilateral throbbing headache with photophobia indicating Ardhavabhedaka.",
    ),
    (
        "Ashmari",
        "Flank pain radiating to groin with dysuria pointing to Ashmari (urinary stones).",
    ),
]


def run_flow(term, note):
    suffix = "".join(random.choices(string.ascii_lowercase + string.digits, k=5))
    username = f"{term.lower()}_{suffix}"
    password = "Testpass123!"

    register_resp = requests.post(
        BASE + "register/",
        json={"username": username, "email": f"{username}@example.com", "password": password},
    )
    register_resp.raise_for_status()

    login_resp = requests.post(BASE + "login/", json={"username": username, "password": password})
    login_resp.raise_for_status()
    tokens = login_resp.json()
    access = tokens["access"]
    payload = jwt.decode(access, options={"verify_signature": False})
    headers = {"Authorization": f"Bearer {access}"}

    patient_resp = requests.post(
        BASE + "patients/",
        headers=headers,
        json={"user": payload["user_id"], "ayush_id": f"AY{random.randint(10000,99999)}", "age": random.randint(25, 60)},
    )
    patient_resp.raise_for_status()
    patient_id = patient_resp.json()["id"]

    pipeline_resp = requests.post(
        BASE + "run_pipeline/",
        headers=headers,
        json={"patient_id": patient_id, "raw_text": note, "auto_push": False},
    )
    pipeline_resp.raise_for_status()
    return pipeline_resp.json()["result"]


if __name__ == "__main__":
    outputs = []
    for term, note in TERMS:
        print(f"\nRunning agent pipeline for {term} ...")
        result = run_flow(term, note)
        outputs.append({"term": term, "result": result})
        print(json.dumps(result, indent=2))

    print("\nSUMMARY")
    print(json.dumps(outputs, indent=2))


