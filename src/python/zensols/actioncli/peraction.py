import logging, inspect, optparse, re
from optparse import OptionParser
from zensols.actioncli import SimpleActionCli

logger = logging.getLogger('zensols.actioncli.peraction')

class PrintActionsOptionParser(OptionParser):
    def print_help(self):
        logger.debug('print help: %s' % self.invokes)
        OptionParser.print_help(self)
        for action, invoke in self.invokes.items():
            logger.debug('print action: %s' % action)
            if action in self.action_options:
                opts = map(lambda x: x['opt_obj'], self.action_options[action])
                op = OptionParser(option_list=opts)
                #op.set_usage(optparse.SUPPRESS_USAGE)
                op.set_usage('usage: %%prog %s [options]' % action)
                print()
                print()
                op.print_help()

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
        return PrintActionsOptionParser(usage=usage, version='%prog ' + str(self.version))

    def _config_parser_for_action(self, args, parser):
        logger.debug('config parser for action: %s' % args)
        action = args[0]
        if action in self.action_options:
            for opt_cfg in self.action_options[action]:
                opt_obj = opt_cfg['opt_obj']
                parser.add_option(opt_obj)
                self.opts.add(opt_obj.dest)
                logger.debug('manditory: %s' % opt_cfg['manditory'])
                if opt_cfg['manditory']: self.manditory_opts.add(opt_obj.dest)
        self._log_config()

class OneConfPerActionOptionsCli(PerActionOptionsCli):
    def __init__(self, opt_config, **kwargs):
        self.opt_config = opt_config
        super(OneConfPerActionOptionsCli, self).__init__({}, {}, **kwargs)

    def _config_global(self, oc):
        parser = self.parser
        logger.debug('global opt config: %s' % oc)
        if 'whine' in oc and oc['whine']:
            logger.debug('configuring whine option')
            self._add_whine_option(parser)
        if 'global_options' in oc:
            for opt in oc['global_options']:
                logger.debug('global opt: %s', opt)
                opt_obj = self.make_option(opt[0], opt[1], **opt[3])
                logger.debug('parser opt: %s', opt_obj)
                parser.add_option(opt_obj)
                self.opts.add(opt_obj.dest)
                if opt[2]: self.manditory_opts.add(opt_obj.dest)

    def _config_executor(self, oc):
        name = oc['name']
        invokes = {}
        gaopts = self.action_options
        logger.debug('config opt config: %s' % oc)
        for action in oc['actions']:
            action_name = action['name']
            meth = action['meth'] if 'meth' in action else name
            doc = action['doc'] if 'doc' in action else re.sub(r'[-_]', ' ', meth)
            invokes[action_name] = [name, meth, doc]
            if 'opts' in action:
                aopts = gaopts[action_name] if action_name in gaopts else []
                gaopts[action_name] = aopts
                for opt in action['opts']:
                    logger.debug('action opt: %s' % opt)
                    opt_obj = self.make_option(opt[0], opt[1], **opt[3])
                    logger.debug('action opt obj: %s' % opt_obj)
                    aopts.append({'opt_obj': opt_obj, 'manditory': opt[2]})
        self.executors[name] = oc['executor']
        self.invokes = invokes

    def config_parser(self):
        parser = self.parser
        self._config_global(self.opt_config)
        for oc in self.opt_config['executors']:
            self._config_executor(oc)
        parser.action_options = self.action_options
        parser.invokes = self.invokes
        self._log_config()
