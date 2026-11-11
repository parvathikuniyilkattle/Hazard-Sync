import pandas as pd
from pathlib import Path

SUBSCRIBER_FILE = Path(__file__).resolve().parent / "subscribers.csv"


def register_email(email):
    email = email.strip().lower()

    if not email or "@" not in email or "." not in email.split("@")[-1]:
        return False, "Please enter a valid email address."

    if SUBSCRIBER_FILE.exists():
        df = pd.read_csv(SUBSCRIBER_FILE)
    else:
        df = pd.DataFrame(columns=["email"])

    if email in df["email"].astype(str).str.lower().values:
        return False, "This email is already registered."

    df.loc[len(df)] = [email]
    df.to_csv(SUBSCRIBER_FILE, index=False)

    return True, "Email registered successfully!"