# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
from queue import Queue

from PyQt5.QtWidgets import QSystemTrayIcon

from osfoffline.settings import ALERT_TIME


show_alerts = True

DOWNLOAD = 0
UPLOAD = 1
MODIFYING = 2
DELETING = 3
MOVING = 4


alert_icon = None
tray_alert_signal = None

last_alert_time = None
alert_queue = Queue()


def setup_alerts(system_tray_icon, tray_signal):
    global alert_icon
    global show_alerts
    global tray_alert_signal

    alert_icon = system_tray_icon
    if not alert_icon.supportsMessages():
        show_alerts = False
    tray_alert_signal = tray_signal


def alert_running():
    global last_alert_time
    cur_time = datetime.now()

    if not last_alert_time:
        return False
    return cur_time - last_alert_time < timedelta(milliseconds=ALERT_TIME)


def run_alert(alert_title, alert_message):
    alert_icon.showMessage(
        alert_title,
        alert_message,
        QSystemTrayIcon.NoIcon,
        msecs=ALERT_TIME  # NOTE: some systems don't allow any control over this...
    )

    global last_alert_time
    last_alert_time = datetime.now()


def clear_queue():
    # clear the queue in a thread safe manner.
    with alert_queue.mutex:
        alert_queue.queue.clear()


def warn(message):
    global show_alerts

    if (alert_icon is None) or (not show_alerts):
        return
    else:
        if alert_icon.supportsMessages():
            run_alert("Problems Syncing", message)


def create_alert_tuple(file_name, action):
    title = {
        DOWNLOAD: "Downloading",
        UPLOAD: "Uploading",
        MODIFYING: "Modifying",
        DELETING: "Deleting",
        MOVING: 'Moving'
    }
    text = "{} {}".format(title[action], file_name)
    alert_tuple = (text, "- OSF Offline")
    return alert_tuple


def up_to_date():
    global tray_alert_signal
    tray_alert_signal.emit("Up to Date")


def info(file_name, action):
    global show_alerts
    global last_alert_time
    global tray_alert_signal

    # get text for alert ready
    alert_tuple = create_alert_tuple(file_name, action)

    # emit signal to update tray action alert
    tray_alert_signal.emit(str(alert_tuple[0]))

    # run balloon alert
    if (alert_icon is None) or (not show_alerts):
        return

    if alert_icon.supportsMessages():

        # if a alert is running, we queue the new alert
        # otherwise:
        #           if the alert queue is empty, we run the alert
        #           otherwise:
        #                   if the previous alert is recent, we merge the alert queue into 1 alert.
        #                           The idea is that if multiple alerts happen around the same time, they can be
        #                           merged into one alert.
        #                   if the previous alert is old, run the new alert.
        #                           The idea here is that the old alert is stale. We delete it. We run the new one.

        if alert_running():
            alert_queue.put_nowait(alert_tuple)
        else:
            if alert_queue.empty():
                run_alert(alert_tuple[0], alert_tuple[1])
            else:
                if datetime.now() - last_alert_time < timedelta(milliseconds=(ALERT_TIME * 3)):  # last alert was recent
                    run_alert('Updating {} files'.format(alert_queue.qsize() + 1),
                              "Check <a href='www.osf.io'>www.osf.io</a> for details.")
                    clear_queue()
                else:
                    run_alert(alert_tuple[0], alert_tuple[1])
                    clear_queue()
    else:
        show_alerts = False
