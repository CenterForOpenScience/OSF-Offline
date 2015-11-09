"""
General utilities used by the application
"""
import logging
import logging.config
import logging.handlers
import os
import sys

from osfoffline.settings import log_config


def start_app_logging(config=log_config.DEFAULT_LOGGING_CONFIG):
    """
    Start logging for the application
    :param config:
    :return:
    """
    logging.config.dictConfig(config)

    # Activate custom excepthook
    sys.excepthook = log_config.capture_exceptions


def start_user_logging(user_id, level=logging.ERROR):
    """
    Create a log file containing only events for an individual user. Call this after user logs in.

    :param username: The OSF GUID for that user
    :param level: The default severity of messages to log
    :return:
    """
    # FIXME: Connect this once Matt's login changes land
    log_filename = os.path.join(log_config.PROJECT_LOG_DIR, '{}.log'.format(user_id))
    handler = logging.FileHandler(log_filename)
    formatter = logging.Formatter(log_config.FILE_FORMATTER)
    handler.setLevel(level)

    handler.setFormatter(formatter)

    # Add user logging to the root logger
    logging.getLogger().addHandler(handler)
