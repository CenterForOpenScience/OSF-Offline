import os
from appdirs import user_config_dir, user_data_dir


## Development mode: use a local OSF dev version and more granular logging
DEV_MODE = False  # TODO (abought): auto-set flag when using `inv start_for_tests`

### General settings
PROJECT_NAME = 'osf-offline'
PROJECT_AUTHOR = 'cos'

### Variables used to control where application config data is stored
PROJECT_DB_DIR = user_data_dir(appname=PROJECT_NAME, appauthor=PROJECT_AUTHOR)
PROJECT_DB_FILE = os.path.join(PROJECT_DB_DIR, 'osf.db')


### Base URL for API server; used to fetch data
# API_BASE = 'http://localhost:5000'
if DEV_MODE is True:
    API_BASE = 'http://localhost:8000'
    FILE_BASE = 'http://localhost:7777'  ## FIXME: Dev mode currently does not work with local waterbutler (abought)
else:
    API_BASE = 'https://staging-api.osf.io'
    FILE_BASE = 'https://staging-files.osf.io'

### Interval (in seconds) to poll the OSF for server-side file changes
if DEV_MODE is True:
    POLL_DELAY = 5  # seconds
else:
    POLL_DELAY = 5 * 60  # seconds

### Time to keep alert messages on screen (in milliseconds); may not be configurable on all platforms
ALERT_TIME = 1000  # ms
