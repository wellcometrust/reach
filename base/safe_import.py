"""
Prevents multiple threads from trying to import at the same time and
hitting an import lock. Implemented because airflow's web server
regularly re-imports all DAGs and all tasks therein -- and
unfortunately, our tasks import so many dependencies that reloading them
takes enough time (by some random distribution) that the Airflow times
out imports, resulting in an endless stream of sentry reports from
within gunicorn.

So, we've moved "slow" imports, especially those pulling in ML libraries
such as scipy or even pandas, into the execute() method of our tasks.

This is almost always something you should NEVER do, because imports can
only be trusted not to lock if they're done from the main thread and on
module load.  (And an import lock in Python tends not to (or never?)
resolve itself.) But, not much choice, at least for now.  And, it turns
out that in our execution model, the celery executor spawns subprocesses
to run each task. So, we shouldn't ever have an issue.

Hope isn't a strategy, though. So, here's a context manager to use, so
that we'll know if we were going to hit an import lock.

Sample usage::

    @report_exception
    def execute(self):
        with safe_import:
            from reach.rainbowpony import pony_ai

        # do things with pony_ai here.

"""

from contextlib import contextmanager
from threading import Lock

# Not a re-entrant lock b/c we believe imports of this sort should
# only happen once from the calling thread.
SAFE_IMPORT_LOCK = Lock()

@contextmanager
def safe_import():
    """
    Context manager for ensuring that only one thread is importing
    at a time. If two threads enter this context, the second will fail
    with an exception so that we can't get caught in an import lock.
    """
    acquired = SAFE_IMPORT_LOCK.acquire(blocking=False)
    try:
        if not acquired:
            # NB: we could, instead, just wait here. But the invariant
            # we're expecting is that, thanks to how the celery executor
            # works, only one call to execute() should happen at a time,
            # because only one thread should ever be running.
            raise Exception('Multiple imports attempted at once!')
        yield
    finally:
        if acquired:
            SAFE_IMPORT_LOCK.release()
