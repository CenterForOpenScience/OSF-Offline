from decorator import decorator
import asyncio

@decorator
def async(func, *args, **kwargs):
    future = func(*args, **kwargs)
    asyncio.get_event_loop().run_until_complete(future)

