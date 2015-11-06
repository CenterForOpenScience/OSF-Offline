# -*- coding: utf-8 -*-
import threading
import asyncio
import logging

from watchdog.observers import Observer
import osfoffline.database_manager.models as models
import osfoffline.polling_osf_manager.polling as polling
import osfoffline.filesystem_manager.osf_event_handler as osf_event_handler
from osfoffline.database_manager.db import session


class BackgroundWorker(threading.Thread):
    def __init__(self):
        super().__init__()
        self.user = None
        self.osf_folder = ''
        self.loop = None
        self.paused = True  # start out paused
        self.running = False
        self.poller = None
        self.observer = None

    def run(self):

        logging.debug('Run in background tasks called for first time.')
        self.loop = self.ensure_event_loop()
        self.run_background_tasks()
        self.loop.run_forever()

    def run_background_tasks(self):
        logging.debug('starting run_background_tasks')

        if not self.running:
            self.user = self.get_current_user()
            self.osf_folder = self.user.osf_local_folder_path

            logging.debug('start observing')
            self.start_observing_osf_folder()
            logging.debug('start polling')
            self.start_polling_server()
            self.running = True

    def pause_background_tasks(self):

        if self.running:
            self.stop_polling_server()
            self.stop_observing_osf_folder()
            # self.stop_loop()
            self.running = False

    def start_polling_server(self):
        self.poller = polling.Poll(self.user, self.loop)
        self.poller.start()

    def stop_polling_server(self):
        if self.poller:
            self.poller.stop()

    # todo: can refactor this code out to somewhere

    def get_current_user(self):
        return session.query(models.User).filter(models.User.logged_in).one()

    def stop_loop(self, close=False):
        """ WARNING: Only pass in 'close' if you plan on creating a new loop afterwards
        """
        logging.debug('stop loop')
        if not self.loop:
            logging.debug('loop never initialized')
            return

        if not self.loop.is_running():
            logging.debug('loop already stopped')
            if close:
                if self.loop.is_closed():
                    logging.debug('loop already closed')
                else:
                    logging.debug('closing loop')
                    self.loop.close()
        else:
            logging.debug('calling loop.stop(). will stop when polling/observing events finish.')
            self.loop.stop()
            if close:
                while not self.loop.is_closed():
                    if not self.loop.is_running():
                        logging.debug('closing loop')
                        self.loop.close()

    def stop(self):
        logging.debug('stopping background worker')
        self.stop_polling_server()
        logging.debug('stop polling')
        self.stop_observing_osf_folder()
        logging.debug('stop observing')
        self.stop_loop(close=True)

    def start_observing_osf_folder(self):
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
        # LocalDBSync(self.user.osf_local_folder_path, self.observer, self.user).emit_new_events()

        try:
            self.observer.start()  # start
        except OSError:
            # FIXME: Document these limits and provide better user notification.
            #    See http://pythonhosted.org/watchdog/installation.html for limits.
            logging.warning('limit of watched items reached')

    def stop_observing_osf_folder(self):
        if self.observer:
            self.observer.stop()
            self.observer.join()

    # courtesy of waterbutler
    def ensure_event_loop(self):
        """Ensure the existance of an eventloop
        Useful for contexts where get_event_loop() may
        raise an exception.
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
