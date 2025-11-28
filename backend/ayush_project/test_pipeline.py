import json
import random
import string

import jwt
import requests

BASE = "http://127.0.0.1:8000/api/"


def show(title, resp):
    print(f"\n=== {title} ===")
    print("Status:", resp.status_code)
    try:
        print(json.dumps(resp.json(), indent=2))
    except Exception:
        print(resp.text)
    print("-----------------------------")


def main():
    # ---------------- REGISTER ----------------
    rand = "".join(random.choices(string.ascii_lowercase + string.digits, k=6))
    username = f"user_{rand}"

    register_resp = requests.post(
        BASE + "register/",
        json={
            "username": username,
            "email": f"{username}@example.com",
            "password": "testpass123",
        },
    )
    show("REGISTER", register_resp)

    register_resp.raise_for_status()

    # ---------------- LOGIN ----------------
    login_resp = requests.post(
        BASE + "login/", json={"username": username, "password": "testpass123"}
    )
    show("LOGIN", login_resp)
    login_resp.raise_for_status()

    tokens = login_resp.json()
    access = tokens.get("access")

    # ⭐ EXTRACT USER ID FROM JWT (SimpleJWT always includes user_id)
    payload = jwt.decode(access, options={"verify_signature": False})
    user_id = payload["user_id"]
    print("Decoded user_id =", user_id)

    headers = {"Authorization": f"Bearer {access}"}

    # ---------------- CREATE PATIENT ----------------
    patient_resp = requests.post(
        BASE + "patients/",
        headers=headers,
        json={
            "user": user_id,  # doctor user id
            "name": "Test Patient",
            "ayush_id": f"AY{random.randint(10000,99999)}",
            "age": 32,
        },
    )
    show("CREATE PATIENT", patient_resp)
    patient_resp.raise_for_status()

    patient_id = patient_resp.json()["id"]

    # ---------------- RUN PIPELINE ----------------
    pipeline_resp = requests.post(
        BASE + "run_pipeline/",
        headers=headers,
        json={
            "patient_id": patient_id,
            "raw_text": "Clinical note: Patient presents with classical Shvitra patches and depigmented lesions.",
            "auto_push": False,
        },
    )
    show("RUN PIPELINE", pipeline_resp)
    pipeline_resp.raise_for_status()


if __name__ == "__main__":
    main()
