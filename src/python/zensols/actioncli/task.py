import logging
import re
from pathlib import Path
import itertools as it
import pickle
from time import time
from queue import Queue
import threading

logger = logging.getLogger(__name__)


class TaskQueue(Queue):
    def __init__(self, n_workers=1):
        super(TaskQueue, self).__init__()
        self.n_workers = n_workers
        self.start_time = time()
        self.stop_time = None
        self._start_workers()
        self.results = []
        self.state = 'r'

    def _debug(self, msg, *args):
        tname = threading.currentThread().getName()
        logger.debug(f'{tname}: {msg}', *args)

    def add_task(self, task, *args, **kwargs):
        self._debug('adding task')
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
            t = threading.Thread(target=self._worker)
            t.daemon = True
            t.start()

    def _worker(self):
        self._debug('start while')
        while True:
            item, args, kwargs = self.get()
            self._debug(f'got work: {type(item)}')
            if item is None:
                break
            try:
                result = item(*args, **kwargs)
                self.results.append(result)
            except Exception as e:
                self.task_done()
                raise e
            self._debug('while iter')
            self.task_done()
        self._debug('done while')

    def __str__(self):
        elapsed = self.time_elapsed
        if elapsed is None:
            elapsed = time() - self.start_time
        if self.state == 'r':
            postfix, state = 'ing', 'running'
        else:
            postfix, state = 'ed', 'finished'
        return f'tasks process{postfix} in {elapsed:5f}s: {state}'


class PersistableTask(object):
    FILE_PAT = '{batch:09d}.dat'
    FILE_RE = re.compile(r'^(\d+).dat$')

    def __init__(self, persist_dir, n_workers=40, n_batch=50,
                 create_dir=True, worker=None):
        self.persist_dir = persist_dir
        self.n_workers = n_workers
        self.n_batch = n_batch
        self.create_dir = create_dir
        self.worker = worker

    def _process_batch(self, batch_num, batch):
        if self.worker is not None:
            return self.worker(batch_num, batch)
        return {'batch_num': batch_num,
                'batch': batch}

    def _process_batch_and_dump(self, batch_num, batch):
        fname = self.FILE_PAT.format(**{'batch': batch_num})
        path = Path(self.persist_dir, fname)
        logger.info(f'{batch_num}: processing {len(batch)} ' +
                    f'batch items to {path}...')
        wp = 0
        t0 = time()
        obj = self._process_batch(batch_num, batch)
        with open(path, 'wb') as f:
            pickle.dump(obj, f)
        t = (time() - t0) / 60.
        logger.info(f'{batch_num}: finished processing {wp} words in {t:.5f}m')
        return obj

    def dump(self, items):
        logger.info(f'processing {len(items)} items')
        if not self.persist_dir.exists():
            self.persist_dir.mkdir(
                0o0755, parents=self.create_dir, exist_ok=True)
        batches = []
        for i, item in enumerate(items):
            if (i % self.n_batch) == 0:
                batch = []
                batches.append(batch)
            batch.append(item)
        logger.debug('batches: {batches}')
        logger.info(f'starting queue with {self.n_workers} ' +
                    'fworkers on {len(batches)}')
        queue = TaskQueue(n_workers=self.n_workers)
        self.queue = queue
        logger.info('adding batches to queue...')
        for i, batch in enumerate(batches):
            logger.debug(f'adding batch: {i}: {batch}')
            queue.add_task(self._process_batch_and_dump, i, batch)
        logger.info('waiting for tasks to complete...')
        res = queue.stop()
        t = queue.time_elapsed
        logger.info(f'completed processing {len(items)} items in {t:.3f}s')
        return res

    def _process_batch_and_load(self, path):
        logger.info(f'loading batch from {path}')
        m = self.FILE_RE.match(path.name)
        if m is None:
            raise ValueError(f'unknown or bad file name format: {path}')
        else:
            batch_no = int(m.group(1))
            with open(path, 'rb') as f:
                return (batch_no, pickle.load(f))

    def load(self):
        logger.info(f'loading from {self.persist_dir}')
        queue = TaskQueue(n_workers=self.n_workers)
        self.queue = queue
        for path in filter(lambda x: x.is_file(), self.persist_dir.iterdir()):
            logger.debug(f'adding persisted file: {path}')
            queue.add_task(self._process_batch_and_load, path)
        logger.info('waiting for tasks to complete...')
        batches = queue.stop()
        t = queue.time_elapsed
        logger.info(f'completed processing {len(batches)} items in {t:.3f}s')
        return it.chain(map(lambda x: x[1],
                            sorted(batches, key=lambda x: x[0])))


class PersistableTaskItem(PersistableTask):
    def _process_item(self, items):
        if self.worker is not None:
            return self.worker(items)
        return items

    def _process_batch(self, batch_num, batch):
        batch = tuple(map(self._process_item, batch))
        return {'n': batch_num, 'b': batch}

    def load(self):
        res = super(PersistableTaskItem, self).load()
        return it.chain(*map(lambda x: x['b'],
                             sorted(res, key=lambda x: x['n'])))
