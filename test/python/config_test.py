#!/usr/bin/env python

import unittest, logging, sys
from configparser import NoSectionError
from zensols.actioncli import Config

logger = logging.getLogger('zneosls.config.test')

class TestHelloWorld(unittest.TestCase):
    def test_config(self):
        conf = Config('test-resources/config-test.conf')
        self.assertEqual({'param1':'3.14'}, conf.options)

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

def main(args=sys.argv[1:]):
    logging.basicConfig(level=logging.DEBUG)
    unittest.main()

if __name__ == '__main__':
    main()
