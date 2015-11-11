from osfoffline.utils.path import ensure_folders

from osfoffline.settings.app_settings import ALERT_TIME, API_BASE, PROJECT_DB_FILE, FILE_BASE, PROJECT_DB_DIR, DEV_MODE, POLL_DELAY
from osfoffline.settings.log_config import PROJECT_LOG_FILE, PROJECT_LOG_DIR

# Ensure that storage directories are created when application starts
ensure_folders(PROJECT_DB_DIR)
ensure_folders(PROJECT_LOG_DIR)

# Exposed settings
__all__ = (
    'ALERT_TIME',
    'API_BASE',
    'DEV_MODE',
    'FILE_BASE',
    'POLL_DELAY',
    'PROJECT_DB_DIR',
    'PROJECT_DB_FILE',
    'PROJECT_LOG_DIR',
    'PROJECT_LOG_FILE',
)
