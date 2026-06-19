import os
from dotenv import load_dotenv

# =========================================================================
# Configuration Loader
# This module loads env parameters from .env and configures global settings.
# =========================================================================

# Load env file secrets
load_dotenv()

# The API keys are shared between Groq LPU API and xAI Grok endpoints
# Groq keys usually start with 'gsk_', xAI keys start with 'xai-'
XAI_API_KEY = os.getenv("XAI_API_KEY", "")

# Auto-routing detection flag
is_groq = XAI_API_KEY.startswith("gsk_")

if is_groq:
    # Default to Groq LPU API if gsk_ key is provided
    DEFAULT_API_BASE = "https://api.groq.com/openai/v1"
    DEFAULT_MODEL = "llama-3.3-70b-versatile"
else:
    # Default to xAI API if other/xai- key is provided
    DEFAULT_API_BASE = "https://api.x.ai/v1"
    DEFAULT_MODEL = "grok-2-vision-1212"

XAI_API_BASE = os.getenv("XAI_API_BASE", DEFAULT_API_BASE)
XAI_MODEL = os.getenv("XAI_MODEL", DEFAULT_MODEL)

# Target URL
TARGET_URL = os.getenv("TARGET_URL", "https://www.google.com")

# Safety/Sanity boundaries
MAX_STEPS = int(os.getenv("MAX_STEPS", "10"))

# Headless mode config
headless_env = os.getenv("HEADLESS", "False").lower()
HEADLESS = headless_env in ("true", "1", "yes")

# Directory setup
WORKSPACE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCREENSHOTS_DIR = os.getenv("SCREENSHOTS_DIR", os.path.join(WORKSPACE_DIR, "screenshots"))
LOGS_DIR = os.getenv("LOGS_DIR", os.path.join(WORKSPACE_DIR, "logs"))

# Ensure folders exist
os.makedirs(SCREENSHOTS_DIR, exist_ok=True)
os.makedirs(LOGS_DIR, exist_ok=True)

def print_config():
    """Debug helper to print active config to logs (excluding credentials)"""
    import logging
    logger = logging.getLogger("agent.config")
    logger.info("--- Loaded Settings ---")
    logger.info(f"API Base URL: {XAI_API_BASE}")
    logger.info(f"API Model   : {XAI_MODEL}")
    logger.info(f"Target URL  : {TARGET_URL}")
    logger.info(f"Headless Mode: {HEADLESS}")
    logger.info(f"Max Steps   : {MAX_STEPS}")
    logger.info(f"Screenshots Dir: {SCREENSHOTS_DIR}")
    logger.info(f"Logs Dir    : {LOGS_DIR}")
    logger.info(f"API Key present: {'Yes' if XAI_API_KEY else 'No'}")
    logger.info(f"Using Groq Mode: {is_groq}")
    logger.info("------------------------")
