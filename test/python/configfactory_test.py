import unittest
import logging
import shutil
from pathlib import Path
from zensols.actioncli import (
    Config,
    ConfigFactory,
    ConfigManager,
    DirectoryStash,
    MultiThreadedPoolStash,
)

logger = logging.getLogger('zneosls.configfactory.test')
#logging.basicConfig(level=logging.DEBUG, format="%(threadName)s:%(message)s")


class WidgetFactory(ConfigFactory):
    INSTANCE_CLASSES = {}

    def __init__(self, config):
        super(WidgetFactory, self).__init__(config, '{name}_widget')


class SimpleWidget(object):
    def __init__(self, param1, param2=None):
        logger.debug(f'params: {param1}, {param2}')
        self.param1 = param1
        self.param2 = param2


WidgetFactory.register(SimpleWidget)


class ConfigInitWidget(object):
    def __init__(self, param1, param2=None, config=None, name=None):
        logger.debug(f'params: {param1}, {param2}, config={config}')
        self.param1 = param1
        self.param2 = param2
        self.config = config
        self.name = name


WidgetFactory.register(ConfigInitWidget)


class WidgetManager(ConfigManager):
    INSTANCE_CLASSES = {}
    PATH = Path('target/wmanager')

    def __init__(self, config):
        super(WidgetManager, self).__init__(
            config,
            stash=DirectoryStash(
                create_path=self.PATH, pattern='{name}_widget_from_mng.dat'),
            pattern='{name}_widget_from_mng',
            default_name='defname')


WidgetManager.register(ConfigInitWidget)


class DataPoint(object):
    INSTANCES = 0

    def __init__(self, id):
        self.id = id
        self.value = id * 2
        self.__class__.INSTANCES += 1

    def __repr__(self):
        return f'({self.id}, {self.value})'


class WidgetStash(MultiThreadedPoolStash):
    PATH = Path('target/wmmanager')

    def __init__(self, workers, data):
        stash = DirectoryStash(
            create_path=self.PATH, pattern='{name}_wmulti.dat')
        super(WidgetStash, self).__init__(stash, workers, data)


class TestConfigFactory(unittest.TestCase):
    def setUp(self):
        self.config = Config('test-resources/config-factory.conf')
        self.factory = WidgetFactory(self.config)
        self.manager = WidgetManager(self.config)
        targ = Path('target')
        if targ.is_dir():
            shutil.rmtree(targ)
        targ.mkdir()

    def test_simple(self):
        w = self.factory.instance('cool')
        self.assertEqual(3.14, w.param1)
        self.assertEqual(None, w.param2)

    def test_pass_param(self):
        w = self.factory.instance('cool', param2=234)
        self.assertEqual(3.14, w.param1)
        self.assertEqual(234, w.param2)

    def test_pass_param_arg(self):
        w = self.factory.instance('cool_pass', 'p1')
        self.assertEqual('p1', w.param1)
        self.assertEqual('p2', w.param2)

    def test_config_init(self):
        w = self.factory.instance('confi')
        self.assertEqual(3.14, w.param1)
        self.assertEqual(None, w.param2)
        self.assertTrue(isinstance(w.config, Config))
        self.assertEqual('globdef', w.config.get_option('def_param1'))
        self.assertEqual('confi', w.name)

    def test_config_init_pass(self):
        w = self.factory.instance('confi', param2=123.5)
        self.assertEqual(3.14, w.param1)
        self.assertEqual(123.5, w.param2)
        self.assertTrue(isinstance(w.config, Config))
        self.assertEqual('globdef', w.config.get_option('def_param1'))

    def test_config_init_pass_arg(self):
        w = self.factory.instance('confi_pass', 'ip1')
        self.assertEqual('ip1', w.param1)
        self.assertEqual('ip2', w.param2)

    def test_config_mng(self):
        w = self.manager.instance('confi_pass')
        self.assertEqual('ip3', w.param1)
        self.assertFalse(self.manager.exists('one'))
        self.assertEqual(set(), set(self.manager.keys()))
        self.manager.dump('one', 123)
        self.assertEqual(123, self.manager.load('one'))
        self.assertEqual(set(('one',)), set(self.manager.keys()))

    def test_multi_tread(self):
        data = map(DataPoint, range(0, 10))
        wstash = WidgetStash(5, data)
        self.assertEqual(False, wstash.has_data)
        self.assertEqual(False, wstash.has_data)
        self.assertEqual(10, len(tuple(wstash.keys())))
        self.assertEqual(True, wstash.has_data)
        self.assertEqual(10, DataPoint.INSTANCES)
        self.assertEqual(10, len(tuple(wstash.keys())))
        self.assertEqual(10, DataPoint.INSTANCES)
        for i in range(0, 10):
            self.assertEqual(i * 2, wstash.load(i).value)

        data = map(DataPoint, range(0, 20))
        wstash = WidgetStash(5, data)
        self.assertEqual(True, wstash.has_data)
        self.assertEqual(10, len(tuple(wstash.keys())))
        self.assertEqual(20, len(tuple(data)))
        for i in range(0, 10):
            self.assertEqual(i * 2, wstash.load(i).value)

        wstash = WidgetStash(5, None)
        alldat = wstash.load_all()
        self.assertEqual(10, len(alldat))
        ids = set()
        for i, dat in enumerate(alldat):
            ids.add(i)
            self.assertEqual(dat.id * 2, dat.value)
        self.assertEqual(set(range(0, 10)), ids)
