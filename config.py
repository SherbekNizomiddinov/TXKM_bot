import os
from dotenv import load_dotenv

load_dotenv(override=True)

BOT_TOKEN = os.getenv("BOT_TOKEN").strip()
GROUP_ID = int(os.getenv("GROUP_ID"))  # -100... ko‘rinishidap
SECOND_GROUP_ID = int(os.getenv("SECOND_GROUP_ID"))
FALLBACK_INVITE_LINK = os.getenv("FALLBACK_INVITE_LINK", "https://t.me/+WiKHfeUqmCQ4MTgy")