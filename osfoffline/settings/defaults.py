# Just to insure requirement
import colorlog  # noqa

# Development mode: use a local OSF dev version and more granular logging
DEV_MODE = False  # TODO (abought): auto-set flag when using `inv start_for_tests`

# General settings
PROJECT_NAME = 'osf-offline'
PROJECT_AUTHOR = 'cos'
APPLICATION_SCOPES = 'osf.full_write'

# Base URL for API server; used to fetch data
API_BASE = 'https://staging-api.osf.io'
FILE_BASE = 'https://staging-files.osf.io'

# Interval (in seconds) to poll the OSF for server-side file changes
# YEARS * DAYS * HOURS * MIN * SECONDS
POLL_DELAY = 20 * 365 * 24 * 60 * 60  # 20 years in seconds

# Time to keep alert messages on screen (in milliseconds); may not be configurable on all platforms
ALERT_TIME = 1000  # ms

LOG_LEVEL = 'INFO'

# Logging configuration
CONSOLE_FORMATTER = {
    '()': 'colorlog.ColoredFormatter',
    'format': '%(cyan)s[%(asctime)s]%(log_color)s[%(threadName)s][%(filename)s][%(levelname)s][%(name)s]: %(reset)s%(message)s'
}

FILE_FORMATTER = '[%(asctime)s][%(threadName)s][%(filename)s][%(levelname)s][%(name)s]: %(message)s'
