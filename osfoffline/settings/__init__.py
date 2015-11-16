import os
import logging

from appdirs import user_data_dir
from appdirs import user_log_dir

from osfoffline.settings.defaults import *  # noqa
from osfoffline.utils.path import ensure_folders

logger = logging.getLogger(__name__)


try:
    from osfoffline.settings.local import *  # noqa
except ImportError:
    logger.warning('No local.py found. Using default settings.')


# Generated setttings

# Variables used to control where application config data is stored
PROJECT_DB_DIR = user_data_dir(appname=PROJECT_NAME, appauthor=PROJECT_AUTHOR)
PROJECT_DB_FILE = os.path.join(PROJECT_DB_DIR, 'osf.db')

PROJECT_LOG_DIR = user_log_dir(appname=PROJECT_NAME, appauthor=PROJECT_AUTHOR)
PROJECT_LOG_FILE = os.path.join(PROJECT_LOG_DIR, 'osfoffline.log')


# Ensure that storage directories are created when application starts
for path in (PROJECT_DB_DIR, PROJECT_LOG_DIR):
    logger.info('Ensuring {} exists'.format(path))
    ensure_folders(path)


# Best for last, the logging configuration

LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'console': CONSOLE_FORMATTER,
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
    'loggers': {
        '': {
            'handlers': ['console'],
            'level': LOG_LEVEL,
            'propagate': False
        }
    },
    'root': {
        'level': LOG_LEVEL,
        'handlers': ['console', 'logfile']
    }
}
