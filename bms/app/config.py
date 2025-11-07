"""Simple application configuration for the BMS app."""

import os

class Config:
    # Toggle debug: set FLASK_DEBUG=1 or "true"
    DEBUG = os.getenv("FLASK_DEBUG", "0").lower() in ("1", "true", "yes")

    # Database URL used by SQLAlchemy; change via DATABASE_URL env var
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///bms.db")

    # Recommended to keep False unless you need change tracking
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Secret key for sessions; override in production
    SECRET_KEY = os.getenv("SECRET_KEY", "change-me")

smtp_host = "smtp.gmail.com"      
smtp_port = 587             
username = None             
app_password = "dcoqchnbfjpcddvt"
from_address = "birajdarbibhishan5@gmail.com"
tp_address = "birajdarbibhishan1@gmail.com"
use_tls = True
