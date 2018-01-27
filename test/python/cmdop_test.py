import logging

import inspect, optparse

#logging.basicConfig(level=logging.DEBUG)
logging.basicConfig(level=logging.INFO)

import unittest, sys, os
from zensols.actioncli import SimpleActionCli, Config

logger = logging.getLogger('zensols.test')

class AppTester(object):
    def __init__(self, config, some_opt_name, a_file_name, a_num_option=None):
        self.some_opt_name = some_opt_name
        self.a_file_name = a_file_name
        self.a_num_option = a_num_option

    def startaction(self):
        current_test.assertEqual(test_opt_gval, self.some_opt_name)
        current_test.assertEqual(test_file_gval, self.a_file_name)
        current_test.assertEqual(test_args_gval, self.args)

    def stopaction(self):
        current_test.assertEqual(test_opt_gval, self.some_opt_name + '_stop')
        current_test.assertEqual(test_file_gval, self.a_file_name + '_stop')
        current_test.assertEqual(test_args_gval, self.args)
        current_test.assertEqual(test_num_gval, self.a_num_option)

    def set_args(self, args):
        self.args = args

class PrintActionsOptionParser(optparse.OptionParser):
    def __init__(self, action_options, invokes, *args, **kwargs):
        self.action_options = action_options
        self.invokes = invokes
        optparse.OptionParser.__init__(self, *args, **kwargs)

    def print_help(self):
        logger.debug('print help: %s' % self.invokes)
        optparse.OptionParser.print_help(self)
        for action, invoke in self.invokes.items():
            logger.debug('print action: %s' % action)
            if action in self.action_options:
                opts = self.action_options[action]
                op = optparse.OptionParser(option_list=opts)
                #op.set_usage(optparse.SUPPRESS_USAGE)
                op.set_usage('usage: %%prog %s [options]' % action)
                print()
                print()
                #print('Action: %s [options]' % action)
                op.print_help()

class PerActionOptionsCli(SimpleActionCli):
    def __init__(self, *args, **kwargs):
        self.action_options = {}
        SimpleActionCli.__init__(self, *args, **kwargs)

    def _init_executor(self, executor, config, args):
        mems = inspect.getmembers(executor, predicate=inspect.ismethod)
        if 'set_args' in (set(map(lambda x: x[0], mems))):
            executor.set_args(args)

    def _log_config(self):
        logger.debug('executors: %s' % self.executors)
        logger.debug('invokes: %s' % self.invokes)
        logger.debug('action options: %s' % self.action_options)
        logger.debug('opts: %s' % self.opts)

    def make_option(self, *args, **kwargs):
        return optparse.make_option(*args, **kwargs)

    def _create_parser(self, usage):
        return PrintActionsOptionParser(self.action_options, self.invokes, usage=usage,
                                        version='%prog ' + str(self.version))

    def _config_parser_for_action(self, args, parser):
        logger.debug('config parser for action: %s' % args)
        action = args[0]
        if action in self.action_options:
            for opt_cfg in self.action_options[action]:
                parser.add_option(opt_cfg)
        self._log_config()

class SwitchActionOptionsCli(PerActionOptionsCli):
    def __init__(self, opt_config, **kwargs):
        self.opt_config = opt_config
        PerActionOptionsCli.__init__(self, {}, {}, **kwargs)

    def _config_executor(self, oc):
        parser = self.parser
        name = oc['name']
        invokes = {}
        gaopts = self.action_options
        logger.debug('config opt config: %s' % oc)
        if 'whine' in oc and oc['whine']:
            logger.debug('configuring whine option')
            self._add_whine_option(parser)
        if 'global_options' in oc:
            for opt in oc['global_options']:
                logger.debug('global opt: %s', opt)
                opt_obj = self.make_option(opt[0], opt[1], **opt[2])
                logger.debug('parser opt: %s', opt_obj)
                parser.add_option(opt_obj)
                self.opts.add(opt_obj.dest)
        for action in oc['actions']:
            action_name = action['name']
            invokes[action_name] = [name, action['meth'], action['doc']]
            if 'opts' in action:
                aopts = gaopts[action_name] if action_name in gaopts else []
                gaopts[action_name] = aopts
                for opt in action['opts']:
                    opt_obj = self.make_option(opt[0], opt[1], **opt[2])
                    aopts.append(opt_obj)
                    self.opts.add(opt_obj.dest)
        self.executors[name] = oc['executor']
        self.invokes = invokes

    def config_parser(self):
        parser = self.parser
        for oc in self.opt_config:
            self._config_executor(oc)
        parser.action_options = self.action_options
        parser.invokes = self.invokes
        self._log_config()

class AppCommandLine(PerActionOptionsCli):
    def __init__(self, conf_file=None, use_environ=False, config_mand=False):
        opts = {'some_opt_name', 'config', 'a_file_name', 'a_num_option'}
        manditory_opts = {'some_opt_name'}
        if config_mand: manditory_opts.update({'config'})
        if use_environ: environ_opts = opts
        else: environ_opts = {}
        executors = {'app_test_key': lambda params: AppTester(**params)}
        invokes = {'start': ['app_test_key', 'startaction', 'test doc'],
                   'stop': ['app_test_key', 'stopaction', 'test doc']}
        if conf_file: conf = Config(conf_file, robust=True)
        else: conf = None
        PerActionOptionsCli.__init__(self, executors, invokes, config=conf,
                                     opts=opts, manditory_opts=manditory_opts,
                                     environ_opts=environ_opts)

    def config_parser(self):
        parser = self.parser
        self._add_whine_option(parser)
        parser.add_option('-o', '--optname', dest='some_opt_name')
        self.action_options['start'] = [self.make_option('-f', '--file', dest='a_file_name')]
        self.action_options['stop'] = [self.make_option('-x', '--xfile', dest='a_file_name'),
                                       self.make_option('-n', '--num', dest='a_num_option', type='int')]

class TestCommandOpTest(unittest.TestCase):
    def setUp(self):
        global current_test
        current_test = self

    def test_per_action_options(self):
        global test_opt_gval, test_file_gval, test_args_gval, test_num_gval
        test_opt_gval = 'test1'
        test_file_gval = 'afile'
        test_args_gval = ['another_arg']
        AppCommandLine().invoke('start -o test1 -f afile another_arg'.split(' '))
        test_opt_gval = 'test1_stop'
        test_file_gval = 'afile_stop'
        test_num_gval = 123454321
        AppCommandLine().invoke('stop -n 123454321 -o test1 -x afile another_arg'.split(' '))

    def test__per_action_class_meth(self):
        global test_opt_gval, test_file_gval, test_args_gval, test_num_gval
        test_opt_gval = 'test1'
        test_file_gval = 'afile'
        test_args_gval = ['another_arg']
        cnf = [{'name': 'app_testor',
                'executor': lambda params: AppTester(**params),
                'actions': [{'name': 'start',
                             'meth': 'startaction',
                             'doc': 'start doc',
                             'opts': [['-f', '--file', {'dest': 'a_file_name'}]]},
                            {'name': 'stop',
                             'meth': 'stopaction',
                             'doc': 'stop doc',
                             'opts': [['-x', '--xfile', {'dest': 'a_file_name'}],
                                      ['-n', '--num', {'dest': 'a_num_option', 'type': 'int'}]]}],
                'global_options': [['-o', '--optname', {'dest': 'some_opt_name'}]],
                'whine': True}]
        SwitchActionOptionsCli(cnf).invoke('start -o test1 -f afile another_arg'.split(' '))
