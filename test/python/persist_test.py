import logging
from pathlib import Path
import pickle
from io import BytesIO
import unittest
from zensols.actioncli import (
    PersistedWork, persisted, PersistableContainer
)

#logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class SomeClass(PersistableContainer):
    def __init__(self, n):
        self.n = n
        self._sp = PersistedWork(Path('target/tmp.dat'), owner=self)

    @property
    @persisted('_sp')
    def someprop(self):
        logger.info('returning: {}'.format(self.n))
        return self.n * 2


class AnotherClass(object):
    def __init__(self, n):
        self.n = n

    @property
    @persisted('counter', Path('target/tmp2.dat'))
    def someprop(self):
        return self.n * 2


class YetAnotherClass(object):
    @persisted('counter', Path('target/tmp3.dat'))
    def get_prop(self, n):
        return n * 2


class HybridClass(object):
    def __init__(self, n):
        self.n = n
        self._counter = PersistedWork(
            Path('target/tmp4.dat'), owner=self)

    def clear(self):
        self._counter.clear()

    @property
    @persisted('_counter')
    def someprop(self):
        return self.n * 2


class HybridClassPickle(PersistableContainer):
    def __init__(self, n):
        self.n = n
        self._counter = PersistedWork(
            Path('target/tmp4.dat'), owner=self)

    def clear(self):
        self._counter.clear()

    @property
    @persisted('_counter')
    def someprop(self):
        return self.n * 2


class PropertyOnlyClass(PersistableContainer):
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


class GlobalTestPickle(PersistableContainer):
    def __init__(self, n):
        self.n = n

    @property
    @persisted('_someprop', cache_global=True)
    def someprop(self):
        self.n += 10
        return self.n


class TransientPickle(PersistableContainer):
    def __init__(self, n):
        self.n = n

    @property
    @persisted('_someprop', transient=True)
    def someprop(self):
        self.n += 10
        return self.n


class TransientPickleOverride(TransientPickle):
    def __setstate__(self, state):
        super(TransientPickleOverride, self).__setstate__(state)
        self.n = 40


class TestPersistWork(unittest.TestCase):
    def setUp(self):
        targdir = Path('target')
        for f in 'tmp tmp2 tmp3 tmp4'.split():
            p = Path(targdir, f + '.dat')
            if p.exists():
                p.unlink()
        targdir.mkdir(0o0755, exist_ok=True)

    def _freeze_thaw(self, o):
        bio = BytesIO()
        pickle.dump(o, bio)
        data = bio.getvalue()
        bio2 = BytesIO(data)
        return pickle.load(bio2)

    def test_class_meth(self):
        sc = SomeClass(10)
        path = Path('target/tmp.dat')
        self.assertFalse(path.exists())
        self.assertEqual(20, sc.someprop)
        self.assertTrue(path.exists())
        sc = SomeClass(5)
        self.assertEqual(20, sc.someprop)
        sc = SomeClass(8)
        sc._sp.clear()
        self.assertEqual(16, sc.someprop)

    def test_property_meth(self):
        sc = AnotherClass(10)
        path = Path('target/tmp2.dat')
        self.assertFalse(path.exists())
        self.assertEqual(20, sc.someprop)
        self.assertTrue(isinstance(sc.counter, PersistedWork))
        self.assertTrue(path.exists())
        sc = AnotherClass(5)
        self.assertEqual(20, sc.someprop)
        sc = AnotherClass(8)
        # has to create the attribute first by callling
        sc.someprop
        sc.counter.clear()
        self.assertEqual(16, sc.someprop)

    def test_getter_meth(self):
        sc = YetAnotherClass()
        path = Path('target/tmp3.dat')
        self.assertFalse(path.exists())
        self.assertEqual(20, sc.get_prop(10))
        self.assertTrue(isinstance(sc.counter, PersistedWork))
        self.assertTrue(path.exists())
        sc = YetAnotherClass()
        self.assertEqual(20, sc.get_prop(5))
        sc = YetAnotherClass()
        # has to create the attribute first by callling
        sc.get_prop()
        sc.counter.clear()
        self.assertEqual(16, sc.get_prop(8))

    def test_hybrid_meth(self):
        sc = HybridClass(10)
        path = Path('target/tmp4.dat')
        self.assertFalse(path.exists())
        self.assertEqual(20, sc.someprop)
        self.assertTrue(path.exists())
        sc = HybridClass(5)
        self.assertEqual(20, sc.someprop)
        sc = HybridClass(8)
        # has to create the attribute first by callling
        sc.someprop
        sc.clear()
        self.assertEqual(16, sc.someprop)

    def test_property_cache_only(self):
        po = PropertyOnlyClass(100)
        self.assertEqual(110, po.someprop)
        self.assertTrue(isinstance(po._someprop, PersistedWork))
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

    def test_pickle(self):
        sc = SomeClass(5)
        path = Path('target/tmp.dat')
        self.assertFalse(path.exists())
        self.assertEqual(10, sc.someprop)
        self.assertTrue(path.exists())
        self.assertEqual(10, sc.someprop)
        sc2 = self._freeze_thaw(sc)
        self.assertEqual(SomeClass, type(sc2))
        self.assertEqual(10, sc2.someprop)

    def test_pickle_proponly(self):
        sc = PropertyOnlyClass(2)
        self.assertEqual(12, sc.someprop)
        self.assertEqual(12, sc.someprop)
        sc2 = self._freeze_thaw(sc)
        self.assertEqual(PropertyOnlyClass, type(sc2))
        self.assertEqual(12, sc2.someprop)

    def test_pickle_global(self):
        sc = GlobalTestPickle(2)
        # fails because of global name collision
        self.assertEqual(12, sc.someprop)
        self.assertEqual(12, sc.someprop)
        sc2 = self._freeze_thaw(sc)
        self.assertEqual(GlobalTestPickle, type(sc2))
        self.assertEqual(12, sc2.someprop)

    def test_pickle_hybrid(self):
        sc = HybridClassPickle(2)
        # fails because of global name collision
        self.assertEqual(4, sc.someprop)
        self.assertEqual(4, sc.someprop)
        sc2 = self._freeze_thaw(sc)
        self.assertEqual(HybridClassPickle, type(sc2))
        self.assertEqual(4, sc2.someprop)

    def test_pickle_transient(self):
        sc = TransientPickle(10)
        sc.n = 2
        # fails because of global name collision
        self.assertEqual(12, sc.someprop)
        self.assertEqual(12, sc.someprop)
        sc2 = self._freeze_thaw(sc)
        self.assertEqual(TransientPickle, type(sc2))
        logger.debug('setting sc2.n')
        # should recalculate from updated value instead of hanging on to old
        sc2.n = 3
        self.assertEqual(13, sc2.someprop)

    def test_pickle_transient_override(self):
        sc = TransientPickleOverride(2)
        # fails because of global name collision
        self.assertEqual(12, sc.someprop)
        self.assertEqual(12, sc.someprop)
        sc2 = self._freeze_thaw(sc)
        self.assertEqual(TransientPickleOverride, type(sc2))
        self.assertEqual(50, sc2.someprop)

    def test_pickle_transient_two_pass(self):
        sc = TransientPickle(10)
        sc.n = 2
        # fails because of global name collision
        self.assertEqual(12, sc.someprop)
        self.assertEqual(12, sc.someprop)
        sc2 = self._freeze_thaw(sc)
        self.assertEqual(TransientPickle, type(sc2))
        logger.debug('setting sc2.n')
        # should recalculate from updated value instead of hanging on to old
        sc2.n = 3
        self.assertEqual(13, sc2.someprop)
        sc3 = self._freeze_thaw(sc)
        sc3.n = 4
        self.assertEqual(12, sc.someprop)
        self.assertEqual(13, sc2.someprop)
        self.assertEqual(14, sc3.someprop)
        self.assertEqual(TransientPickle, type(sc3))