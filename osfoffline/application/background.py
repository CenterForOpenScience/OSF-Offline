# -*- coding: utf-8 -*-
import asyncio
import logging
import threading

from watchdog.observers import Observer


from osfoffline.database_manager import models
from osfoffline.database_manager.db import session
from osfoffline.filesystem_manager import osf_event_handler
from osfoffline.filesystem_manager.sync_local_filesystem_and_db import LocalDBSync
from osfoffline.polling_osf_manager import polling


logger = logging.getLogger(__name__)


class BackgroundWorker(threading.Thread):

    def __init__(self):
        super().__init__()

        # Start out with null variables for NoneType errors rather than Attribute Errors
        self.user = None
        self.osf_folder = None

        self.loop = None
        self.poller = None
        self.observer = None

    # courtesy of waterbutler
    def ensure_event_loop(self):
        """Ensure the existance of an eventloop
        Useful for contexts where get_event_loop() may raise an exception.
        Such as multithreaded applications

        :returns: The new event loop
        :rtype: BaseEventLoop
        """
        try:
            return asyncio.get_event_loop()
        except (AssertionError, RuntimeError):
            asyncio.set_event_loop(asyncio.new_event_loop())

        # Note: No clever tricks are used here to dry up code
        # This avoids an infinite loop if settings the event loop ever fails
        return asyncio.get_event_loop()

    def run(self):
        logger.debug('Background worker starting')
        self.loop = self.ensure_event_loop()
        # self.loop.set_debug(True)

        self.user = self.get_current_user()
        self.osf_folder = self.user.osf_local_folder_path

        logger.debug('Starting observer thread')
        self.start_folder_observer()

        logging.debug('Starting OSF polling')
        self.start_osf_poller()

        logging.debug('Starting background event loop')
        try:
            self.loop.run_forever()
        except Exception as e:
            logger.exception(e)
        finally:
            self.stop()
        logging.debug('Background event loop exited')

    def get_current_user(self):
        return session.query(models.User).one()

    def start_osf_poller(self):
        self.poller = polling.Poll(self.user, self.loop)
        self.poller.start()

    def start_folder_observer(self):
        # if something inside the folder changes, log it to config dir
        # create event handler
        self.event_handler = osf_event_handler.OSFEventHandler(
            self.osf_folder,
            loop=self.loop
        )

        # todo: if config actually has legitimate data. use it.

        # start
        self.observer = Observer()  # create observer. watched for events on files.
        # attach event handler to observed events. make observer recursive
        self.observer.schedule(self.event_handler, self.osf_folder, recursive=True)
        LocalDBSync(self.user.osf_local_folder_path, self.observer, self.user).emit_new_events()

        try:
            self.observer.start()  # start
        except OSError as e:
            # FIXME: Document these limits and provide better user notification.
            #    See http://pythonhosted.org/watchdog/installation.html for limits.
            raise RuntimeError('Limit of watched items reached') from e

    def stop(self):
        # Note: This method is **NOT called from this current thread**
        # All method/function/routines/etc MUST be thread safe from here out
        if not self.poller or not self.observer:
            raise RuntimeError('OSF poller or folder observer is not defined, Background work was not correctly initialized')

        logger.debug('Stopping background worker')

        logger.debug('Stopping OSF polling')
        self.loop.call_soon_threadsafe(self.poller.stop)

        logger.debug('Stopping observer thread')
        # observer is actually a seperate child thread and must be join()ed
        self.observer.stop()
        self.observer.join()

        logger.debug('Stopping the event loop')
        # Note: this is what actually stops the current thread
        # Calls self.join, be careful with what is on the event loop
        self.stop_loop(close=True)

    def stop_loop(self, close=False):
        """ WARNING: Only pass in 'close' if you plan on creating a new loop afterwards
        """
        if not self.loop:
            logger.warning('loop never initialized')
            return

        if self.loop.is_running():
            self.loop.call_soon_threadsafe(self.loop.stop)
            logging.debug('Stopped event loop')
            self.join()

        if close:
            self.loop.close()
            logging.debug('Closed event loop')


# HOW DOES LOGIN/LOGOUT WORK?
#
# previously logged in:
# when you first open osf offline, you go to main.py which sets up views, connections, and controller.
# controller sets up db, logs, and determines which user is logged in.
# when all is good, controller starts background worker.
# background worker polls api and observer osf folder
#
# not logged in:
# when you first open osf offline, you go to main.py which sets up views, connections, and controller.
# controller sets up db, logs, and opens create user screen. user logs in. then get user from db.
# when all is good, controller starts background worker.
# background worker polls api and observer osf folder
