#!/usr/bin/env python

import unittest, logging, sys
from zensols.actioncli import Config

logger = logging.getLogger('zneosls.config.test')

class TestHelloWorld(unittest.TestCase):
    def test_config(self):
        conf = Config('test-resources/config-test.conf')
        self.assertEqual({'param1':'3.14'}, conf.options)

def main(args=sys.argv[1:]):
    logging.basicConfig(level=logging.DEBUG)
    unittest.main()

if __name__ == '__main__':
    main()
