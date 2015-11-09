import logging
import logging.config
import os
import colorlog

from appdirs import user_log_dir

from .app_settings import DEV_MODE, PROJECT_NAME, PROJECT_AUTHOR

### Where to store project-level logs
PROJECT_LOG_DIR = user_log_dir(appname=PROJECT_NAME, appauthor=PROJECT_AUTHOR)
PROJECT_LOG_FILE = os.path.join(PROJECT_LOG_DIR, 'osfoffline.log')


### Logging configuration
CONSOLE_FORMATTER = {
    '()': 'colorlog.ColoredFormatter',
    'format': '%(cyan)s[%(asctime)s]%(log_color)s[%(threadName)s][%(filename)s][%(levelname)s][%(name)s]: %(reset)s%(message)s'
}

FILE_FORMATTER = '[%(asctime)s][%(threadName)s][%(filename)s][%(levelname)s][%(name)s]: %(message)s'

if DEV_MODE is True:
    log_level = 'DEBUG'
else:
    log_level = 'INFO'


DEFAULT_LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'console': CONSOLE_FORMATTER,
        'file_log': {'format': FILE_FORMATTER}
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'level': log_level,
            'formatter': 'console'
        },
        'syslog': {
            'class': 'logging.handlers.SysLogHandler',
            'level': log_level
        },
        'logfile': {
            'class': 'logging.FileHandler',
            'level': log_level,
            'filename': PROJECT_LOG_FILE,
            'formatter': 'file_log'
        },
    },
    'loggers': {
        '': {
            'handlers': ['console'],
            'level': log_level,
            'propagate': False
        }
    },
    'root': {
        'level': log_level,
        'handlers': ['console', 'logfile']
    }
}


def capture_exceptions(exc_type, exc_value, tb):
    """Ensure that uncaught exceptions are logged"""
    logging.exception('Uncaught exception: ', exc_info=(exc_type, exc_value, tb))

