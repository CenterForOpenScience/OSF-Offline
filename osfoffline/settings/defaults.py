# Just to insure requirement
import colorlog  # noqa

# Development mode: use a local OSF dev version and more granular logging
DEV_MODE = False  # TODO (abought): auto-set flag when using `inv start_for_tests`

LOGOUT_CODE = -10607

# General settings
PROJECT_NAME = 'osf-offline'
PROJECT_AUTHOR = 'cos'
APPLICATION_SCOPES = 'osf.full_write'

# Base URL for API server; used to fetch data
OSF_URL = 'https://staging.osf.io'
API_BASE = 'https://staging-api.osf.io'
FILE_BASE = 'https://staging-files.osf.io'

# Interval (in seconds) to poll the OSF for server-side file changes
POLL_DELAY = 5 * 60  # seconds (set to 1 min now for QA purpose, #todo change it back)

# Time to keep alert messages on screen (in milliseconds); may not be configurable on all platforms
ALERT_TIME = 1000  # ms

LOG_LEVEL = 'INFO'

# Logging configuration
CONSOLE_FORMATTER = {
    '()': 'colorlog.ColoredFormatter',
    'format': '%(cyan)s[%(asctime)s]%(log_color)s[%(threadName)s][%(filename)s][%(levelname)s][%(name)s]: %(reset)s%(message)s'
}

FILE_FORMATTER = '[%(asctime)s][%(threadName)s][%(filename)s][%(levelname)s][%(name)s]: %(message)s'
