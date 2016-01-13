from collections import OrderedDict
import itertools
import logging
import os
from pathlib import Path
import threading

from watchdog.events import PatternMatchingEventHandler

from osfoffline import settings
from osfoffline.exceptions import NodeNotFound


logger = logging.getLogger(__name__)


class ConsolidatedEventHandler(PatternMatchingEventHandler):

    def __init__(self):
        super().__init__(ignore_patterns=settings.IGNORED_PATTERNS)
        self._event_cache = TreeDict()
        self._create_cache = []
        self.timer = threading.Timer(5, self.flush)
        self.timer.start()
        self.lock = threading.RLock()

    def dispatch(self, event):
        with self.lock:
            logger.debug('Watchdog event fired: {}'.format(event))

            src_parts = event.src_path.split(os.path.sep)
            if not hasattr(event, 'dest_path'):
                dest_parts = itertools.repeat(None)
            else:
                dest_parts = event.dest_path.split(os.path.sep)

            parts = list(zip(src_parts, dest_parts))

            # Windows represents folder deletes incorrectly as file deletes, and as
            # result we can't trust event.is_directory to check whether or not delete
            # events need to be consolidated
            consolidate = event.is_directory
            if event.event_type == 'deleted':
                consolidate = (parts in self._event_cache)

            if event.event_type == 'modified':
                if event.is_directory:
                    return
                move_events = [
                    evt
                    for evt in self._event_cache.children()
                    if evt.event_type == 'moved' and evt.dest_path == event.src_path
                ]
                if move_events:
                    return
            if event.event_type == 'created':
                self._create_cache.append(event)
            else:
                if not consolidate and parts in self._event_cache:
                    ev = self._event_cache[parts]
                    if not isinstance(ev, OrderedDict) and ev.event_type == 'deleted':
                        # For leaf entries, turn deletes followed by creates into updates,
                        #   eg saving in vim or replacing a file in finder.
                        # Would be more correct to create an actual modified event, but only `event_type` is checked
                        event.event_type = 'modified'
                self._event_cache[parts] = event

            logger.debug('Create cache: {}'.format(self._create_cache))
            logger.debug('Event cache: {}'.format(self._event_cache))

            self.timer.cancel()
            self.timer = threading.Timer(settings.EVENT_DEBOUNCE, self.flush)
            self.timer.start()

    def _sorted_create_cache(self):
        return sorted(
            self._create_cache,
            key=lambda ev: len(Path(ev.src_path).parents)
        )

    def flush(self):
        with self.lock:
            # Create events after all other types, and parent folder creation events happen before child files
            for event in itertools.chain(
                    self._event_cache.children(),
                    self._sorted_create_cache(),
            ):
                logger.debug('Watchdog event dispatched: {}'.format(event))
                try:
                    super().dispatch(event)
                except (NodeNotFound, ) as e:
                    logger.warning(e)
                except Exception:
                    logger.exception('Failure while dispatching watchdog event: {}'.format(event))

            # TODO: Create cache has no deduplication mechanism
            self._create_cache = []
            self._event_cache = TreeDict()


def flatten(dict_obj, acc):
    for value in dict_obj.values():
        if isinstance(value, dict):
            flatten(value, acc)
        else:
            acc.append(value)
    return acc


class TreeDict:

    def __init__(self):
        self._inner = OrderedDict()

    def __setitem__(self, keys, value):
        inner = self._inner
        for key in keys[:-1]:
            inner = inner.setdefault(key, OrderedDict())
        inner[keys[-1]] = value

    def __getitem__(self, keys):
        if not isinstance(keys, (tuple, list)):
            keys = (keys,)
        inner = self._inner
        for key in keys:
            inner = inner[key]
        return inner

    def children(self, *, keys=None):
        try:
            sub_dict = self[keys] if keys is not None else self._inner
        except KeyError:
            return []
        return flatten(sub_dict, [])

    def __contains__(self, keys):
        try:
            self[keys]
        except KeyError:
            return False
        return True

    def __delitem__(self, keys):
        self[keys] = OrderedDict()

    def __repr__(self):
        return str(self._inner)
