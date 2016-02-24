import logging
import configparser

# Must import in order to be included by PyInstaller
import raven
from raven.handlers.logging import SentryHandler

from osfoffline.settings.defaults import *  # noqa

logger = logging.getLogger(__name__)

try:
    from osfoffline.settings.local import *  # noqa
except ImportError:
    logger.debug('No local.py found. Using default settings.')

# Ensure that storage directories are created when application starts
for path in (PROJECT_DB_DIR, PROJECT_LOG_DIR):
    logger.info('Ensuring {} exists'.format(path))
    os.makedirs(path, exist_ok=True)

# Define logging configuration to use individual override params from settings files
LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'console': {'format': FILE_FORMATTER},
        'file_log': {'format': FILE_FORMATTER}
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'level': LOG_LEVEL,
            'formatter': 'console'
        },
        'syslog': {
            'class': 'logging.handlers.SysLogHandler',
            'level': LOG_LEVEL
        },
        'logfile': {
            'class': 'logging.FileHandler',
            'level': LOG_LEVEL,
            'filename': PROJECT_LOG_FILE,
            'formatter': 'file_log'
        },
    },
    'root': {
        'level': LOG_LEVEL,
        'handlers': ['console', 'logfile']
    }
}

# Add Sentry logging separately, so that we can access the client and modify context variables later
# This allows us to send additional data to Sentry (like username, when the user is logged in)

config = configparser.ConfigParser()

# path relative to start.py
user_setting_file = os.path.join(os.getcwd(), '/settings/user-settings.ini')

config.read(user_setting_file)
try:
    allow_logging = config.getboolean('main', 'allow')
except configparser.NoSectionError:
    logger.exception('Cannot open user settings file. Make sure you have copied user-settings-dist.ini to user-settings.ini')
else:
    if allow_logging:
        raven_client = raven.Client(dsn=SENTRY_DSN, VERSION=VERSION, refs=refs)
        handler = SentryHandler(raven_client, level='ERROR')
        raven.conf.setup_logging(handler)
