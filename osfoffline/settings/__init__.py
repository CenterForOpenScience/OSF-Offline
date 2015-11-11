from osfoffline.utils.path import ensure_folders

from .app_settings import ALERT_TIME, API_BASE, PROJECT_DB_FILE, FILE_BASE, PROJECT_DB_DIR, DEV_MODE, POLL_DELAY
from .log_config import PROJECT_LOG_FILE, PROJECT_LOG_DIR

# Ensure that storage directories are created when application starts
ensure_folders(PROJECT_DB_DIR)
ensure_folders(PROJECT_LOG_DIR)
