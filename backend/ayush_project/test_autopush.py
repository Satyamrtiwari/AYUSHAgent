import random
import string

import jwt
import requests

BASE = "http://127.0.0.1:8000/api/"


def main():
    username = "autop_" + "".join(random.choices(string.ascii_lowercase + string.digits, k=5))
    password = "Testpass123!"

    # Register/login
    reg = requests.post(
        BASE + "register/", json={"username": username, "email": f"{username}@example.com", "password": password}
    )
    reg.raise_for_status()

    login = requests.post(BASE + "login/", json={"username": username, "password": password})
    login.raise_for_status()
    tokens = login.json()
    access = tokens["access"]
    payload = jwt.decode(access, options={"verify_signature": False})
    headers = {"Authorization": f"Bearer {access}"}

    patient = requests.post(
        BASE + "patients/",
        headers=headers,
        json={"user": payload["user_id"], "ayush_id": f"AY{random.randint(10000,99999)}", "age": 40},
    )
    patient.raise_for_status()
    pid = patient.json()["id"]

    pipeline = requests.post(
        BASE + "run_pipeline/",
        headers=headers,
        json={
            "patient_id": pid,
            "raw_text": "Auto push test for ABDM integration using Ajeerna symptoms.",
            "auto_push": True,
        },
    )
    print("Status:", pipeline.status_code)
    try:
        print(pipeline.json())
    except Exception:
        print(pipeline.text)


if __name__ == "__main__":
    main()


