import logging
import time
from pathlib import Path
import itertools as it
import random
import unittest
from zensols.actioncli import (
    TaskQueue, PersistableTask, PersistableTaskItem,
)

logger = logging.getLogger('zensols.test.task')
#logging.basicConfig(level=logging.WARNING)
#logging.getLogger('zensols.actioncli.task').setLevel(logging.INFO)


class TestTaskQueue(unittest.TestCase):
    def test_queue(self):
        def identity(n):
            timeout = random.uniform(1.0/1000000.0, 1.0/100.0)
            time.sleep(timeout)
            return n

        n = 1000
        intlist = range(1, n)
        queue = TaskQueue(n_workers=10)
        self.assertTrue(queue.state == 'r')
        for i in intlist:
            queue.add_task(identity, i)
        self.assertTrue(str(queue).startswith('tasks processing'))
        work = queue.stop()
        # should be out of order if processed as threads given random timeout
        self.assertNotEqual(intlist, work)
        self.assertEqual((n * (n - 1)/2), sum(work))
        self.assertTrue(queue.time_elapsed > 0)
        self.assertTrue(queue.state == 's')
        self.assertTrue(str(queue).startswith('tasks processed'))

    def test_queue_wait(self):
        def identity(n):
            time.sleep(0.5)
            return n

        n = 9
        intlist = range(1, n)
        queue = TaskQueue(n_workers=3)
        for i in intlist:
            queue.add_task(identity, i)
        self.assertTrue(str(queue).startswith('tasks processing'))
        logger.info('stopping queue...')
        work = queue.stop()
        logger.info(f'work: {work}')
        self.assertEqual((n * (n - 1)/2), sum(work))
        self.assertTrue(queue.time_elapsed > 0)
        self.assertTrue(queue.state == 's')
        self.assertTrue(str(queue).startswith('tasks processed'))

    def test_queue_single(self):
        def identity(n):
            time.sleep(0.5)
            return n

        n = 9
        intlist = range(1, n)
        queue = TaskQueue(n_workers=(n*2))
        for i in intlist:
            queue.add_task(identity, i)
        self.assertTrue(str(queue).startswith('tasks processing'))
        logger.info('stopping queue...')
        work = queue.stop()
        logger.info(f'work: {work}')
        self.assertEqual((n * (n - 1)/2), sum(work))
        self.assertTrue(queue.time_elapsed > 0)
        self.assertTrue(queue.state == 's')
        self.assertTrue(str(queue).startswith('tasks processed'))


class TestPersistTask(unittest.TestCase):
    def setUp(self):
        path = Path('target/persist_task')
        path.mkdir(0o0755, parents=True, exist_ok=True)
        for f in path.iterdir():
            f.unlink()
        self.targdir = path

    def test_persist_task(self):
        def worker(job_num, batch):
            return {'job': job_num,
                    'batch': batch}
        n = 50
        intlist = range(1, n)
        pt = PersistableTask(self.targdir, n_batch=3, worker=worker)
        res = pt.dump(intlist)
        lst = tuple(it.chain(*map(lambda x: x['batch'],
                                  sorted(res, key=lambda x: x['job']))))
        self.assertEqual(tuple(intlist), lst)
        lst = pt.load()
        lst = tuple(it.chain(*map(lambda x: x['batch'],
                                  sorted(res, key=lambda x: x['job']))))
        self.assertEqual(tuple(intlist), lst)

    def test_persist_task_item(self):
        def worker(n):
            return n * 2

        n = 50
        intlist = range(1, n)
        pt = PersistableTaskItem(self.targdir, n_batch=3, worker=worker)
        res = pt.dump(intlist)
        logger.debug(f'dump res: {res}')
        lst = pt.load()
        correct = tuple(map(lambda x: x * 2, intlist))
        self.assertEqual(correct, tuple(lst))

    def test_persist_task_no_item(self):
        n = 50
        intlist = range(1, n)
        pt = PersistableTaskItem(self.targdir, n_batch=3)
        res = pt.dump(intlist)
        logger.debug(f'dump res: {res}')
        lst = pt.load()
        self.assertEqual(tuple(intlist), tuple(lst))
