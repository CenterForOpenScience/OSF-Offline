import shutil
import tempfile
import functools
from multiprocessing.pool import ThreadPool
import time

from faker import Factory
fake = Factory.create()

def chain(f, g):
    @functools.wraps(f)
    def g_wrapper(*args, **kwargs):
        return g(f(*args, **kwargs))
    return g_wrapper

def _unique(factory):
    """
    Turns a factory function into a new factory function that guarentees unique return values.
    Example use:
    unique_name_factory = unique(fake.name)
    unique_name = unique_name_factory()
    """
    used = []
    @functools.wraps(factory)
    def wrapper():
        item = factory()
        over = 0
        while item in used:
            if over > 100:
                raise RuntimeError('Tried 100 times to generate a unqiue value, stopping.')
            item = factory()
            over += 1
        used.append(item)
        return item
    return wrapper

_unique_proper_name = _unique(
    chain(
        fake.domain_word,
        lambda w: w.capitalize()
    )
)

unique_file_name = _unique(fake.file_name)
unique_folder_name = _unique_proper_name
unique_sha256 = _unique(fake.sha256)
unique_guid = _unique(
    functools.partial(
        fake.password,
        length=5,
        special_chars=False
    )
)
unique_id = _unique(
    functools.partial(
        fake.password,
        special_chars=False
    )
)
unique_project_name = _unique_proper_name

def fail_after(timeout=2):
    def test_wrapper(test):
        @functools.wraps(test)
        def _test_wrapper(self, *args, **kwargs):
            pool = ThreadPool(processes=1)
            result = pool.apply_async(test, args=(self, ) + args, kwds=kwargs)
            now = time.time()
            while not result.ready():
                if (time.time() - now > timeout):
                    pool.terminate()
                    self.fail()
                time.sleep(0.1)
            return result.get()
        return _test_wrapper
    return test_wrapper


# h/t http://stackoverflow.com/questions/6587516/how-to-concisely-create-a-temporary-file-that-is-a-copy-of-another-file-in-pytho
def create_temporary_copy(src):
    # create the temporary file in read/write mode (r+)
    tf = tempfile.TemporaryFile(mode='r+b', prefix='__', suffix='.tmp')

    # on windows, we can't open the the file again, either manually
    # or indirectly via shutil.copy2, but we *can* copy
    # the file directly using file-like objects, which is what
    # TemporaryFile returns to us.
    # Use `with open` here to automatically close the source file
    with open(src, 'r+b') as f:
        shutil.copyfileobj(f, tf)

    # rewind the temporary file, otherwise things will go
    # tragically wrong on Windows
    tf.seek(0)
    return tf
