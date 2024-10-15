# config.py
import os
from dotenv import load_dotenv

load_dotenv()

RAKUTEN_APP_ID = os.getenv('RAKUTEN_APP_ID')
RAKUTEN_AFFILIATE_ID = os.getenv('RAKUTEN_AFFILIATE_ID')
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
SMTP_SERVER = os.getenv('SMTP_SERVER')
SMTP_PORT = os.getenv('SMTP_PORT')
SMTP_USERNAME = os.getenv('SMTP_USERNAME')
SMTP_PASSWORD = os.getenv('SMTP_PASSWORD')