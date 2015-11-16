"""
General utilities used by the application
"""
import logging
import logging.config
import logging.handlers
import os


def start_app_logging(config=None):
    """
    Start logging for the application
    :param config:
    :return:
    """
    # Avoids circular import
    from osfoffline import settings
    logging.config.dictConfig(config or settings.LOGGING_CONFIG)


def start_user_logging(user_id, level=logging.ERROR):
    """
    Create a log file containing only events for an individual user. Call this after user logs in.

    :param username: The OSF GUID for that user
    :param level: The default severity of messages to log
    :return:
    """
    # Avoids circular import
    from osfoffline import settings

    # FIXME: Connect this once Matt's login changes land
    log_filename = os.path.join(settings.PROJECT_LOG_DIR, '{}.log'.format(user_id))
    handler = logging.FileHandler(log_filename)
    formatter = logging.Formatter(settings.FILE_FORMATTER)
    handler.setLevel(level)

    handler.setFormatter(formatter)

    # Add user logging to the root logger
    logging.getLogger().addHandler(handler)
