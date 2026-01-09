"""Configuration and constants for the train commute optimizer."""

import os
from typing import Dict, Any

# API Configuration
ODPT_API_BASE_URL = "https://api.odpt.org/api/v4"
ODPT_API_CHALLENGE_BASE_URL = "https://api-challenge.odpt.org/api/v4"

# Operator Configuration
# All operators load their API keys from environment variables for security
OPERATORS: Dict[str, Dict[str, Any]] = {
    "JR_EAST": {
        "id": "odpt.Operator:JR-East",
        "name": "JR East",
        "api_base": "challenge",
        "env_key": "ACCESS_TOKEN",  # Uses ACCESS_TOKEN from .env
    },
    "TOKYO_METRO": {
        "id": "odpt.Operator:TokyoMetro",
        "name": "Tokyo Metro",
        "api_base": "production",
        "env_key": "TOKYO_METRO_KEY"  # Uses TOKYO_METRO_KEY from .env
    },
    "KEIKYU": {
        "id": "odpt.Operator:Keikyu",
        "name": "Keikyu",
        "api_base": "challenge",
        "env_key": "ACCESS_TOKEN",  # Uses ACCESS_TOKEN from .env
    }
}

# Database Configuration
DEFAULT_DB_PATH = "train_data.db"

# Network Optimization Parameters
DEFAULT_AVG_TIME_PER_STOP = 2.5  # minutes per station stop
DEFAULT_TRANSFER_TIME = 5.0       # minutes per line transfer
DEFAULT_MAX_COMMUTE_TIME = 120    # maximum commute time to consider (minutes)
DEFAULT_TOP_N_RESULTS = 10        # number of top results to return

# Display Configuration
DISPLAY_WIDTH = 100  # characters width for output formatting

# API Request Configuration
API_TIMEOUT = 60  # seconds
MAX_RETRIES = 3
RETRY_DELAY = 2   # seconds

# Database Schema Version
SCHEMA_VERSION = "2.0"