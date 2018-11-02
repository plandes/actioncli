import logging
from time import time
from queue import Queue
from threading import Thread

logger = logging.getLogger('zensols.actioncli.task')


class TaskQueue(Queue):
    def __init__(self, n_workers=1):
        super(TaskQueue, self).__init__()
        self.n_workers = n_workers
        self.start_time = time()
        self.stop_time = None
        self._start_workers()
        self.results = []
        self.state = 'r'

    def add_task(self, task, *args, **kwargs):
        args = args or ()
        kwargs = kwargs or {}
        self.put((task, args, kwargs))

    def stop(self):
        self.join()
        self.stop_time = time()
        self.state = 's'
        for i in range(self.n_workers):
            self.put((None, None, None))
        return self.results

    @property
    def time_elapsed(self):
        if self.stop_time is not None:
            return self.stop_time - self.start_time

    def _start_workers(self):
        for i in range(self.n_workers):
            t = Thread(target=self._worker)
            t.daemon = True
            t.start()

    def _worker(self):
        logger.debug('start while')
        while True:
            item, args, kwargs = self.get()
            if item is None:
                break
            try:
                result = item(*args, **kwargs)
                self.results.append(result)
            except Exception as e:
                self.task_done()
                raise e
            logger.debug('while iter')
            self.task_done()
        logger.debug('done while')

    def __str__(self):
        elapsed = self.time_elapsed
        if elapsed is None:
            elapsed = time() - self.start_time
        if self.state == 'r':
            postfix, state = 'ing', 'running'
        else:
            postfix, state = 'ed', 'finished'
        return f'tasks process{postfix} in {elapsed:5f}s: {state}'
