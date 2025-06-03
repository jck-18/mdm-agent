"""
Central configuration file for MDM Agent
Handles system-independent path resolution and settings
"""

import os
from pathlib import Path

# Base directories
PROJECT_ROOT = Path(__file__).parent.resolve()
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
API_DIR = PROJECT_ROOT / "api"

# Data directories
DATA_DIR = PROJECT_ROOT / "data"
OUTPUT_DIR = PROJECT_ROOT / "output"
IMAGES_DIR = PROJECT_ROOT / "images"
BROCHURES_DIR = PROJECT_ROOT / "brochures"

# Processing directories
COMBINED_OUTPUT_DIR = PROJECT_ROOT / "combined_output"
NORMALIZED_OUTPUT_DIR = PROJECT_ROOT / "normalized_output"
AGGREGATED_OUTPUT_DIR = PROJECT_ROOT / "aggregated_output"

# Config directories
CONFIGS_DIR = PROJECT_ROOT / "configs"

# Ensure all required directories exist
REQUIRED_DIRS = [
    OUTPUT_DIR,
    IMAGES_DIR,
    BROCHURES_DIR,
    COMBINED_OUTPUT_DIR,
    NORMALIZED_OUTPUT_DIR,
    AGGREGATED_OUTPUT_DIR,
]

def setup_directories():
    """Create all required directories if they don't exist"""
    for directory in REQUIRED_DIRS:
        directory.mkdir(parents=True, exist_ok=True)

# Product types and their associated files
PRODUCT_TYPES = {
    "phones": {
        "csv_file": "samsung_galaxy_s24_detailed.csv",
        "config_file": "phones.yaml"
    },
    "watch": {
        "csv_file": "samsung_watch6_classic_detailed.csv",
        "config_file": "watches.yaml"
    },
    "tv": {
        "csv_file": "samsung_frame_tv_detailed.csv",
        "config_file": "tv.yaml"
    }
}

# API Configuration
API_CONFIG = {
    "host": "0.0.0.0",
    "port": 5000,
    "debug": True
}

# Load environment variables
def load_env():
    """Load environment variables from .env file"""
    env_path = PROJECT_ROOT / ".env"
    if env_path.exists():
        from dotenv import load_dotenv
        load_dotenv(env_path)
    
    # Validate required environment variables
    required_vars = ["OPENAI_API_KEY"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        print(f"[!] Warning: Missing required environment variables: {', '.join(missing_vars)}")
        print(f"[!] Please check your .env file at: {env_path}")

# Initialize configuration
setup_directories()
load_env() 