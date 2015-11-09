__author__ = 'himanshu'
import asyncio

"""
# todo: FIGURE OUT HOW TO MAKE POLLINGEVENTQUEUE WORK WITH LOOP PROPERLY....
https://github.com/python/asyncio/blob/f4111812967fded634637936225205f29035a449/tests/test_queues.py
"""


class PollingEventQueue(object):
    def __init__(self, loop):
        self._queue = asyncio.Queue(loop=loop)

    @asyncio.coroutine
    def run(self):
        while not self._queue.empty():
            event = self._queue.get_nowait()
            yield from event.run()

    def put(self, event):
        self._queue.put_nowait(event)
