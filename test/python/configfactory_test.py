import unittest
import logging
from pathlib import Path
from zensols.actioncli import (
    Config,
    ConfigFactory,
    ConfigManager,
    DirectoryStash,
)

logger = logging.getLogger('zneosls.configfactory.test')


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
    def __init__(self, param1, config=None, name=None):
        logger.debug(f'params: {param1}, config={config}')
        self.param1 = param1
        self.config = config
        self.name = name


WidgetFactory.register(ConfigInitWidget)


class WidgetManager(ConfigManager):
    INSTANCE_CLASSES = {}

    def __init__(self, config):
        super(WidgetManager, self).__init__(
            config,
            stash=DirectoryStash(create_path=Path('target'),
                                 pattern='{name}_widget_from_mng'),
            pattern='{name}_widget_from_mng',
            default_name='defname')


WidgetManager.register(ConfigInitWidget)


class TestConfigFactory(unittest.TestCase):
    def setUp(self):
        self.config = Config('test-resources/config-factory.conf')
        self.factory = WidgetFactory(self.config)
        self.manager = WidgetManager(self.config)

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
