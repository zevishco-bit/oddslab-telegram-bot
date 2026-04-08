import os
from datetime import time
from pytz import timezone

class Config:
    # Telegram
    BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    BOT_USERNAME = os.getenv("TELEGRAM_BOT_USERNAME", "@TheOddsLabBot")
    
    # Channels
    PAID_CHANNEL_ID = int(os.getenv("PAID_CHANNEL_ID", "-3547325521"))
    FREE_CHANNEL_ID = int(os.getenv("FREE_CHANNEL_ID", "-5198853652"))
    
    # Admin
    ADMIN_USER_ID = int(os.getenv("ADMIN_USER_ID", "6707759303"))
    
    # Database
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///oddslab.db")
    
    # Timezone & Time
    TIMEZONE = timezone(os.getenv("TIMEZONE", "Europe/Berlin"))
    PICKS_TIME = time(9, 0)  # 9 AM CET
    
    # Currency
    CURRENCY = os.getenv("CURRENCY", "USD")
    
    # Pricing Plans
    PRICING_PLANS = {
        "monthly": {
            "name": "€19/month",
            "amount": 1900,  # in cents
            "currency": "EUR",
            "duration": "1 month"
        },
        "quarterly": {
            "name": "€49/3 months",
            "amount": 4900,  # in cents
            "currency": "EUR",
            "duration": "3 months"
        }
    }
    
    # Payment
    PAYMENT_PROVIDER_TOKEN = os.getenv("PAYMENT_PROVIDER_TOKEN", "")
    
    # Environment
    ENV = os.getenv("RAILS_ENV", "development")
    DEBUG = ENV == "development"