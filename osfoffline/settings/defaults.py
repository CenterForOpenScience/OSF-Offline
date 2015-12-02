# General settings
PROJECT_NAME = 'osf-offline'
PROJECT_AUTHOR = 'cos'
APPLICATION_SCOPES = 'osf.full_write'

# Base URL for API server; used to fetch data
API_BASE = 'https://test-api.osf.io'
FILE_BASE = 'https://test-files.osf.io'

# Interval (in seconds) to poll the OSF for server-side file changes
REMOTE_CHECK_INTERVAL = 60 * 5  # Every 5 minutes

# Time to keep alert messages on screen (in milliseconds); may not be configurable on all platforms
ALERT_TIME = 10000  # ms

LOG_LEVEL = 'INFO'

# Logging configuration
FILE_FORMATTER = '[%(asctime)s][%(threadName)s][%(filename)s][%(levelname)s][%(name)s]: %(message)s'

IGNORED_NAMES = ['.DS_Store', 'lost+found', 'Desktop.ini']
IGNORED_PATTERNS = ['*.DS_Store', '*lost+found', '*Desktop.ini']

OSF_STORAGE_FOLDER = 'OSF Storage'

LOCAL_DELETE_THRESHOLD = 10

# wab~,vmc,vhd,vo1,vo2,vsv,vud,vmdk,vmsn,vmsd,hdd,vdi,vmwarevm,nvram,vmx,vmem,iso,dmg,sparseimage,wim,ost,o,qtch,log
# wab~,vmc,vhd,vdi,vo1,vo2,vsv,vud,iso,dmg,sparseimage,sys,cab,exe,msi,dll,dl_,wim,ost,o,qtch,log,ithmb,vmdk,vmem,vmsd,vmsn,vmss,vmx,vmxf,menudata,appicon,appinfo,pva,pvs,pvi,pvm,fdd,hds,drk,mem,nvram,hdd
