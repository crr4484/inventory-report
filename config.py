"""
Configuration for the Inventory Report System

All thresholds, supplier buffers, and email settings are centralized here.
"""
import os

# Stock thresholds (in months)
TARGET_STOCK_MONTHS = 3
LOW_STOCK_THRESHOLD_MONTHS = 1
REORDER_TRIGGER_MONTHS_MIN = 1  # Reorder if < 1 month stock
REORDER_TRIGGER_MONTHS_MAX = 2  # OR if < 2 months stock

# Max stock threshold (in days)
MAX_STOCK_THRESHOLD_DAYS = 30

# Analyse all stock flag
ANALYSE_ALL_STOCK = False  # If True, analyse all items even if at target

# Working days per year
WORKING_DAYS_PER_YEAR = 365

# Supplier buffer amounts (in weeks of stock)
SUPPLIER_BUFFER_WEEKS = {
    'SolSteer': 3,
    'Harnex': 4,
    'Real Mounts': 1,
    'MMT': 1,
    'Ubiqconn AU': 4,
    'Ubiqconn USA': 1,
    'Rapid direct': 4,
    'OBDWire': 4,
}

# Default buffer for unlisted suppliers
DEFAULT_BUFFER_WEEKS = 2

# Email settings (support environment variables)
EMAIL_SENDER = os.getenv('EMAIL_SENDER', '')
EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD', '')
EMAIL_RECIPIENTS = os.getenv('EMAIL_RECIPIENTS', '').split(',') if os.getenv('EMAIL_RECIPIENTS') else []

# SMTP settings
SMTP_SERVER = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
SMTP_PORT = int(os.getenv('SMTP_PORT', '587'))

# CSV input path
CSV_INPUT_PATH = os.getenv('CSV_INPUT_PATH', 'data/inventory.csv')
