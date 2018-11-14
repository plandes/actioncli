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


class PropertyOnlyClass(object):
    def __init__(self, n):
        self.n = n

    @property
    @persisted('_someprop')
    def someprop(self):
        self.n += 10
        return self.n


class GlobalTest(object):
    def __init__(self, n):
        self.n = n

    @property
    @persisted('_someprop', cache_global=True)
    def someprop(self):
        self.n += 10
        return self.n


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
        self.assertEqual(10, sc.someprop)
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
        self.assertEqual(10, sc.someprop)
        sc = HybridClass(8)
        # has to create the attribute first by callling
        sc.someprop
        sc.clear()
        self.assertEqual(16, sc.someprop)

    def test_property_cache_only(self):
        po = PropertyOnlyClass(100)
        self.assertEqual(110, po.someprop)
        po.n = 10
        self.assertEqual(10, po.n)
        self.assertEqual(110, po.someprop)
        po._someprop.clear()
        self.assertEqual(20, po.someprop)
        po = PropertyOnlyClass(3)
        self.assertEqual(13, po.someprop)

    def test_global(self):
        gt = GlobalTest(100)
        self.assertEqual(110, gt.someprop)
        gt = GlobalTest(10)
        gt.n = 1
        self.assertEqual(110, gt.someprop)
        self.assertEqual(110, gt.someprop)

    def test_set(self):
        po = PropertyOnlyClass(5)
        self.assertEqual(15, po.someprop)
        self.assertEqual(PersistedWork, type(po._someprop))
        po._someprop.set(20)
        self.assertEqual(20, po.someprop)
