import unittest
import logging
from zensols.actioncli import YamlConfig

logger = logging.getLogger('zensols.actioncli.yaml')


class TestYaml(unittest.TestCase):
    def test_yaml(self):
        conf = YamlConfig('test-resources/config-test.yml')
        single_op = conf.get_option('project.template-directory.default')
        self.assertEqual('make-proj', single_op)
        self.assertEqual('Zensol Python Project', conf.get_option(
            'project.context.project.aval', expect=True))
