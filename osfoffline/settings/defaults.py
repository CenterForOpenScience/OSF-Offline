import os

from appdirs import user_data_dir
from appdirs import user_log_dir


# General settings
PROJECT_NAME = 'osf-offline'
PROJECT_AUTHOR = 'cos'
APPLICATION_SCOPES = 'osf.full_write'

DEBUG = False

DRY = False

# Base URL for API server; used to fetch data
OSF_URL = 'https://test.osf.io'
API_BASE = 'https://test-api.osf.io'
API_VERSION = 'v2'
FILE_BASE = 'https://test-files.osf.io'

# Interval (in seconds) to poll the OSF for server-side file changes
REMOTE_CHECK_INTERVAL = 60 * 5  # Every 5 minutes

# Time to keep alert messages on screen (in seconds); may not be configurable on all platforms
ALERT_DURATION = 5.0  # sec

LOG_LEVEL = 'INFO'

SENTRY_DSN = None

# Logging configuration
FILE_FORMATTER = '[%(levelname)s][%(asctime)s][%(threadName)s][%(name)s]: %(message)s'

IGNORED_NAMES = ['.DS_Store', 'lost+found', 'Desktop.ini']
IGNORED_PATTERNS = ['*.DS_Store', '*lost+found', '*Desktop.ini']

OSF_STORAGE_FOLDER = 'OSF Storage'
COMPONENTS_FOLDER = 'Components'

# wab~,vmc,vhd,vo1,vo2,vsv,vud,vmdk,vmsn,vmsd,hdd,vdi,vmwarevm,nvram,vmx,vmem,iso,dmg,sparseimage,wim,ost,o,qtch,log
# wab~,vmc,vhd,vdi,vo1,vo2,vsv,vud,iso,dmg,sparseimage,sys,cab,exe,msi,dll,dl_,wim,ost,o,qtch,log,ithmb,vmdk,vmem,vmsd,vmsn,vmss,vmx,vmxf,menudata,appicon,appinfo,pva,pvs,pvi,pvm,fdd,hds,drk,mem,nvram,hdd

# Variables used to control where application config data is stored
PROJECT_DB_DIR = user_data_dir(appname=PROJECT_NAME, appauthor=PROJECT_AUTHOR)
PROJECT_DB_FILE = os.path.join(PROJECT_DB_DIR, 'osf.db')

PROJECT_LOG_DIR = user_log_dir(appname=PROJECT_NAME, appauthor=PROJECT_AUTHOR)
PROJECT_LOG_FILE = os.path.join(PROJECT_LOG_DIR, 'osfoffline.log')

EVENT_DEBOUNCE = 2

#check connection polling timer
CONNECTION_TIMER = 60
