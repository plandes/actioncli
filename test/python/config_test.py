import unittest
import logging
import sys
from configparser import NoSectionError
from zensols.actioncli import Config

logger = logging.getLogger('zneosls.config.test')


class TestConfig(unittest.TestCase):
    def test_config(self):
        conf = Config('test-resources/config-test.conf')
        self.assertEqual({'param1': '3.14'}, conf.options)

    def test_config_single_opt(self):
        conf = Config('test-resources/config-test.conf')
        self.assertEqual('3.14', conf.get_option('param1'))

    def test_missing_default_raises_error(self):
        def run_conf_create():
            conf = Config('test-resources/config-test-nodef.conf')
            opts = conf.options
        self.assertRaises(NoSectionError, run_conf_create)

    def test_no_default(self):
        conf = Config('test-resources/config-test-nodef.conf', robust=True)
        self.assertEqual({}, conf.options)

    def test_print(self):
        conf = Config('test-resources/config-test.conf')
        s = str(conf)
        self.assertEqual("file: test-resources/config-test.conf, section: {'default'}", s)

    def test_list_parse(self):
        conf = Config('test-resources/config-test-option.conf')
        self.assertEqual(['one', 'two', 'three'], conf.get_option_list('param1'))
        self.assertEqual(True, conf.get_option_boolean('param2'))
        self.assertEqual(True, conf.get_option_boolean('param3'))
        self.assertEqual(True, conf.get_option_boolean('param4'))
        self.assertEqual(False, conf.get_option_boolean('param5'))
        self.assertEqual(False, conf.get_option_boolean('no_such_param'))
        self.assertEqual([], conf.get_option_list('no_such_param'))

    def test_populate(self):
        class Settings:
            pass
        conf = Config('test-resources/populate-test.conf')
        s = Settings()
        conf.populate(s)
        self.assertEqual(s.param1, 3.14)
        self.assertEqual(s.param2, 9)
        self.assertEqual(s.param3, 10.1)
        self.assertEqual(s.param4, -10.1)
        self.assertEqual(s.param5, 'dog')
        self.assertEqual(s.param6, True)
        self.assertEqual(s.param7, False)
        self.assertEqual(s.param8, None)
