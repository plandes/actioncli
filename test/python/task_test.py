import logging
import time
import random
import unittest
from zensols.actioncli import (
    TaskQueue
)

logger = logging.getLogger('zensols.test.task')


class TestPersistWork(unittest.TestCase):
    def test_queue(self):
        def identity(n):
            timeout = random.uniform(1.0/1000000.0, 1.0/100.0)
            time.sleep(timeout)
            return n

        n = 1000
        intlist = range(1, n)
        queue = TaskQueue(n_workers=10)
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
