import logging
from pathlib import Path
import unittest
from zensols.actioncli import (
    PersistedWork, persisted
)

logger = logging.getLogger('zensols.test.persist')


class SomeClass(object):
    def __init__(self, n):
        self.n = n
        self.counter = PersistedWork(
            'target/tmp.dat', owner=self, worker=self.do_work)

    @property
    def someprop(self):
        logger.info('returning: {}'.format(self.n))
        return self.counter(self.n)

    def do_work(self, num):
        return num * 2


class AnotherClass(object):
    def __init__(self, n):
        self.n = n

    @property
    @persisted('counter', 'target/tmp2.dat')
    def someprop(self):
        return self.n * 2


class YetAnotherClass(object):
    @persisted('counter', 'target/tmp3.dat')
    def get_prop(self, n):
        return n * 2


class HybridClass(object):
    def __init__(self, n):
        self.n = n
        self._counter = PersistedWork('target/tmp4.dat', owner=self)

    def clear(self):
        self._counter.clear()

    @property
    @persisted('_counter')
    def someprop(self):
        return self.n * 2


class TestPersistWork(unittest.TestCase):
    def setUp(self):
        targdir = Path('target')
        for f in 'tmp tmp2 tmp3 tmp4'.split():
            p = Path(targdir, f + '.dat')
            if p.exists():
                p.unlink()
        targdir.mkdir(0o0755, exist_ok=True)

    def test_class_meth(self):
        sc = SomeClass(10)
        self.assertEqual(20, sc.someprop)
        sc = SomeClass(5)
        self.assertEqual(20, sc.someprop)
        sc = SomeClass(8)
        sc.counter.clear()
        self.assertEqual(16, sc.someprop)

    def test_property_meth(self):
        sc = AnotherClass(10)
        self.assertEqual(20, sc.someprop)
        sc = AnotherClass(5)
        self.assertEqual(20, sc.someprop)
        sc = AnotherClass(8)
        # has to create the attribute first by callling
        sc.someprop
        sc.counter.clear()
        self.assertEqual(16, sc.someprop)

    def test_getter_meth(self):
        sc = YetAnotherClass()
        self.assertEqual(20, sc.get_prop(10))
        sc = YetAnotherClass()
        self.assertEqual(20, sc.get_prop(5))
        sc = YetAnotherClass()
        # has to create the attribute first by callling
        sc.get_prop()
        sc.counter.clear()
        self.assertEqual(16, sc.get_prop(8))

    def test_hybrid_meth(self):
        sc = HybridClass(10)
        self.assertEqual(20, sc.someprop)
        sc = HybridClass(5)
        self.assertEqual(20, sc.someprop)
        sc = HybridClass(8)
        # has to create the attribute first by callling
        sc.someprop
        sc.clear()
        self.assertEqual(16, sc.someprop)
