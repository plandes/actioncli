import re
import os
import sys
import logging
import inspect
from functools import reduce
import optparse
from optparse import OptionParser
from zensols.actioncli import SimpleActionCli, Config

logger = logging.getLogger('zensols.actioncli.peraction')


class PrintActionsOptionParser(OptionParser):
    """Implements a human readable implementation of print_help for action based
    command line handlers (i.e. OneConfPerActionOptionsCli).

    """
    def __init__(self, *args, **kwargs):
        super(PrintActionsOptionParser, self).__init__(*args, **kwargs)

    @property
    def action_options(self):
        return self._action_options

    @property
    def action_names(self):
        return sorted(self.action_options.keys())

    @action_options.setter
    def action_options(self, opts):
        self._action_options = opts
        self.usage = 'usage: %prog <list|{}> [options]'.\
                     format('|'.join(self.action_names))

    def print_help(self, file=sys.stdout):
        logger.debug('print help: %s' % self.invokes)
        logger.debug('action options: %s' % self.action_options)
        OptionParser.print_help(self, file)

        action_name_len = reduce(lambda x, y: max(x, y),
                                 map(lambda x: len(x), self.action_names))
        action_fmt_str = '  {:<' + str(action_name_len) + '}  {}'
        action_help = []
        opt_str_len = 0
        def_str_len = 0
        # format text for each action and respective options
        for action_name in self.action_names:
            if action_name in self.invokes:
                action_doc = self.invokes[action_name][2].capitalize()
                opts = map(lambda x: x['opt_obj'],
                           self.action_options[action_name])
                logger.debug('{} -> {}, {}'.format(
                    action_name, action_doc, opts))
                opt_strs = []
                for opt in opts:
                    short_opt, long_opt, sep, default = '', '', '', ''
                    if opt._short_opts and len(opt._short_opts) > 0:
                        short_opt = opt._short_opts[0]
                    if opt._long_opts and len(opt._long_opts) > 0:
                        long_opt = opt._long_opts[0]
                    otype = ' <{}>'.format(opt.type) if opt.type else ''
                    if len(short_opt) > 0 and len(long_opt) > 0:
                        sep = ', '
                    opt_str = '  {}{}{}{}'.format(
                        short_opt, sep, long_opt, otype)
                    if opt.default and opt.default != ('NO', 'DEFAULT'):
                        default = str(opt.default)
                    opt_strs.append({'str': opt_str,
                                     'default': default,
                                     'help': opt.help})
                    opt_str_len = max(opt_str_len, len(opt_str))
                    def_str_len = max(def_str_len, len(default))
                action_help.append(
                    {'doc': action_fmt_str.format(action_name, action_doc),
                     'opts': opt_strs})

        opt_str_fmt = '{:<' + str(opt_str_len) + '}  {:<' +\
                      str(def_str_len) + '}  {}\n'

        file.write('Actions:\n')
        for i, ah in enumerate(action_help):
            file.write(ah['doc'] + '\n')
            for op in ah['opts']:
                file.write(opt_str_fmt.format(
                    op['str'], op['default'], op['help']))
            if i < len(action_help) - 1:
                file.write('\n')


class PerActionOptionsCli(SimpleActionCli):
    def __init__(self, *args, **kwargs):
        self.action_options = {}
        super(PerActionOptionsCli, self).__init__(*args, **kwargs)

    def _init_executor(self, executor, config, args):
        mems = inspect.getmembers(executor, predicate=inspect.ismethod)
        if 'set_args' in (set(map(lambda x: x[0], mems))):
            executor.set_args(args)

    def _log_config(self):
        logger.debug('executors: %s' % self.executors)
        logger.debug('invokes: %s' % self.invokes)
        logger.debug('action options: %s' % self.action_options)
        logger.debug('opts: %s' % self.opts)
        logger.debug('manditory opts: %s' % self.manditory_opts)

    def make_option(self, *args, **kwargs):
        return optparse.make_option(*args, **kwargs)

    def _create_parser(self, usage):
        return PrintActionsOptionParser(
            usage=usage, version='%prog ' + str(self.version))

    def _config_parser_for_action(self, args, parser):
        logger.debug('config parser for action: %s' % args)
        action = args[0]
        if action in self.action_options:
            for opt_cfg in self.action_options[action]:
                opt_obj = opt_cfg['opt_obj']
                parser.add_option(opt_obj)
                self.opts.add(opt_obj.dest)
                logger.debug('manditory: %s' % opt_cfg['manditory'])
                if opt_cfg['manditory']:
                    self.manditory_opts.add(opt_obj.dest)
        self._log_config()


class OneConfPerActionOptionsCli(PerActionOptionsCli):
    """Convenience action handler that allows a definition on a per action
    basis.  See the test cases for examples of how to use this as the detail is
    all in the configuration pased to the init method.

    """
    def __init__(self, opt_config, **kwargs):
        self.opt_config = opt_config
        super(OneConfPerActionOptionsCli, self).__init__({}, {}, **kwargs)

    def _config_global(self, oc):
        parser = self.parser
        logger.debug('global opt config: %s' % oc)
        if 'whine' in oc and oc['whine']:
            logger.debug('configuring whine option')
            self._add_whine_option(parser, default=oc['whine'])
        if 'short' in oc and oc['short']:
            logger.debug('configuring short option')
            self._add_short_option(parser)
        if 'config_option' in oc:
            conf = oc['config_option']
            self.config_opt_conf = conf
            opt = conf['opt']
            logger.debug('config opt: %s', opt)
            opt_obj = self.make_option(opt[0], opt[1], **opt[3])
            parser.add_option(opt_obj)
            if opt[2]:
                self.manditory_opts.add(opt_obj.dest)
        if 'global_options' in oc:
            for opt in oc['global_options']:
                logger.debug('global opt: %s', opt)
                opt_obj = self.make_option(opt[0], opt[1], **opt[3])
                logger.debug('parser opt: %s', opt_obj)
                parser.add_option(opt_obj)
                self.opts.add(opt_obj.dest)
                if opt[2]:
                    self.manditory_opts.add(opt_obj.dest)

    def _config_executor(self, oc):
        exec_name = oc['name']
        gaopts = self.action_options
        logger.debug('config opt config: %s' % oc)
        for action in oc['actions']:
            action_name = action['name']
            meth = action['meth'] if 'meth' in action else re.sub(r'[- ]', '_', action_name)
            doc = action['doc'] if 'doc' in action else re.sub(r'[-_]', ' ', meth)
            inv = [exec_name, meth, doc]
            logger.debug('inferred action: %s: %s' % (action, inv))
            self.invokes[action_name] = inv
            if 'opts' in action:
                aopts = gaopts[action_name] if action_name in gaopts else []
                gaopts[action_name] = aopts
                for opt in action['opts']:
                    logger.debug('action opt: %s' % opt)
                    opt_obj = self.make_option(opt[0], opt[1], **opt[3])
                    logger.debug('action opt obj: %s' % opt_obj)
                    aopts.append({'opt_obj': opt_obj, 'manditory': opt[2]})
        self.executors[exec_name] = oc['executor']

    def config_parser(self):
        super(OneConfPerActionOptionsCli, self).config_parser()
        parser = self.parser
        self._config_global(self.opt_config)
        for oc in self.opt_config['executors']:
            self._config_executor(oc)
        parser.action_options = self.action_options
        parser.invokes = self.invokes
        self._log_config()

    def _create_config(self, conf_file, default_vars):
        return Config(config_file=conf_file, default_vars=default_vars)

    def _get_default_config(self, params):
        return super(OneConfPerActionOptionsCli, self).get_config(params)

    def get_config(self, params):
        if not hasattr(self, 'config_opt_conf'):
            return self._get_default_config(params)
        else:
            conf = self.config_opt_conf
            conf_name = conf['name']
            logger.debug('config configuration: %s, name: %s, params: %s' %
                         (conf, conf_name, params))
            conf_file = params[conf_name]
            if not conf_file:
                return self._get_default_config(params)
            if not os.path.isfile(conf_file):
                if 'expect' in conf and not conf['expect']:
                    return self._get_default_config(params)
                raise IOError('no such configuration file: %s' % conf_file)
            good_keys = filter(lambda x: params[x] is not None, params.keys())
            defaults = {k: str(params[k]) for k in good_keys}
            logger.debug('defaults: %s' % defaults)
            conf = self._create_config(conf_file, defaults)
            logger.debug('created config: %s' % conf)
            return conf


class OneConfPerActionOptionsCliEnv(OneConfPerActionOptionsCli):
    """A command line option parser that first parses an ini file and passes that
    configuration on to the rest of the CLI action processing in the super
    class.

    """
    def __init__(self, opt_config, conf_var, *args, **kwargs):
        super(PerActionOptionsCli, self).__init__(opt_config, *args, **kwargs)
        conf_env_var = conf_var.upper()
        if conf_env_var in os.environ:
            default_config_file = os.environ[conf_env_var]
        else:
            default_config_file = os.path.expanduser('~/.{}'.format(conf_var))
        self.default_config_file = default_config_file

    def _create_config(self, conf_file, default_vars):
        defs = {}
        defs.update(default_vars)
        defs.update(os.environ)
        defs.update(self.default_config_file)
        return Config(config_file=conf_file, default_vars=defs)
