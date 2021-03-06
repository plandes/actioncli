import logging
import unittest
from pathlib import Path
import shutil
from zensols.actioncli import (
    Config,
    DelegateStash,
    StashFactory,
    DirectoryStash,
    FactoryStash,
)

#logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class RangeStash1(DelegateStash):
    def __init__(self, n):
        super(RangeStash1, self).__init__()
        self.n = n
        self.prefix = ''

    def load(self, name: str):
        return f'{self.prefix}{name}'

    def keys(self):
        return map(str, range(self.n))


StashFactory.register(RangeStash1)


class TestStashFactory(unittest.TestCase):
    def setUp(self):
        self.conf = Config('test-resources/stash-factory.conf')
        self.target_path = Path('target')
        if self.target_path.exists():
            shutil.rmtree(self.target_path)

    def test_create(self):
        fac = StashFactory(self.conf)
        inst = fac.instance('range1')
        self.assertTrue(isinstance(inst, RangeStash1))
        self.assertEqual(set(map(lambda x: (str(x), str(x)), range(5))), set(inst))
        inst.prefix = 'pf'
        self.assertEqual(set(map(lambda x: (str(x), f'pf{x}'), range(5))), set(inst))

    def test_delegate_create(self):
        fac = StashFactory(self.conf)
        inst = fac.instance('range2')
        self.assertFalse(self.target_path.exists())
        self.assertTrue(isinstance(inst, FactoryStash))
        self.assertEqual(set(map(lambda x: (str(x), str(x)), range(5))), set(inst))
        self.assertTrue(self.target_path.is_dir())
        inst.prefix = 'pf'
        self.assertEqual(set(map(lambda x: (str(x), f'{x}'), range(5))), set(inst))
