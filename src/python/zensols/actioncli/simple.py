import logging, sys, os

from optparse import OptionParser
from zensols.actioncli import Config

logger = logging.getLogger('zensols.actioncli')

class ActionCliError(Exception):
    def __init__(self,*args,**kwargs):
        Exception.__init__(self,*args,**kwargs)

class SimpleActionCli(object):
    """A simple action based command line interface.
    """
    def __init__(self, executors, invokes, config=None, version='0.1',
                 opts=None, manditory_opts=None, environ_opts=None,
                 default_action=None):
        """Construct.

        :param dict executors:
            keys are executor names and values are
            function that create the executor handler instance
        :param dict invokes:
            keys are names of in executors and values are
            arrays with the form: [<option name>, <method name>, <usage doc>]
        :param config: an instance of `zensols.config.Config`
        :param str version: the version of this command line module
        :param set opts: options to be parsed
        :param set manditory_opts: options that must be supplied in the command
        :param set environ_opts:
            options to add from environment variables; each are upcased to
            be match and retrieved from the environment but are lowercased in
            the results param set
        :param str default_action: the action to use if non is specified (if any)
        """
        opts = opts if opts else set([])
        manditory_opts = manditory_opts if manditory_opts else set([])
        environ_opts = environ_opts if environ_opts else set([])
        self.executors = executors
        self.invokes = invokes
        self.opts = opts
        self.manditory_opts = manditory_opts
        self.environ_opts = environ_opts
        self.version = version
        self.add_logging = False
        self.config = config
        self.default_action = default_action

    def _config_logging(self, level):
        root = logging.getLogger()
        map(root.removeHandler, root.handlers[:])
        if level == 0:
            levelno = logging.WARNING
        elif level == 1:
            levelno = logging.INFO
        elif level == 2:
            levelno = logging.DEBUG
        if level <= 1:
            fmt = '%(message)s'
        else:
            fmt = '%(levelname)s:%(asctime)-15s %(name)s: %(message)s'
        logging.basicConfig(format=fmt, level=levelno)
        root.setLevel(levelno)
        logger.setLevel(levelno)

    def print_actions(self, short):
        if short:
            for (name, action) in self.invokes.items():
                print(name)
        else:
            pad = max(map(lambda x: len(x), self.invokes.keys())) + 2
            fmt = '%%-%ds %%s' % pad
            for (name, action) in self.invokes.items():
                print(fmt % (name, action[2]))

    def _add_whine_option(self, parser, default=0):
        parser.add_option('-w', '--whine', dest='whine', metavar='NUMBER',
                          type='int', default=default, help='add verbosity to logging')
        self.add_logging = True

    def _parser_error(self, msg):
        self.parser.error(msg)

    def _default_environ_opts(self):
        opts = {}
        for opt in self.environ_opts:
            opt_env = opt.upper()
            if opt_env in os.environ:
                opts[opt] = os.environ[opt_env]
        logger.debug('default environment options: %s' % opts)
        return opts

    def _init_executor(self, executor, config, args):
        pass

    def get_config(self, params):
        return self.config

    def _config_parser_for_action(self, args, parser):
        pass

    def _create_parser(self, usage):
        return OptionParser(usage=usage, version='%prog ' + str(self.version))

    def invoke(self, args=sys.argv[1:]):
        usage = 'usage: %prog <list|...> [options]'
        parser = self._create_parser(usage)
        parser.add_option('-s', '--short', dest='short',
                          help='short output for list', action='store_true')
        self.parser = parser
        self.config_parser()
        if len(args) > 0 and args[0] in self.invokes:
            logger.info('configuring parser on action: %s' % args[0])
            self._config_parser_for_action(args, parser)
        (options, args) = parser.parse_args(args)
        logger.debug('options: <%s>, args: <%s>' % (options, args))
        if len(args) > 0:
            action = args[0]
        else:
            if self.default_action == None:
                self._parser_error('missing action mnemonic')
            else:
                logger.debug('using default action: %s' % self.default_action)
                action = self.default_action
        if self.add_logging: self._config_logging(options.whine)
        if action == 'list': self.print_actions(options.short)
        else:
            if not action in self.invokes:
                self._parser_error("no such action: '%s'" % action)
            (exec_name, meth, _) = self.invokes[action]
            logging.debug('exec_name: %s, meth: %s' % (exec_name, meth))
            params = vars(options)
            config = self.get_config(params)
            def_params = config.options if config else {}
            def_params.update(self._default_environ_opts())
            for k,v in params.items():
                if v == None and k in def_params:
                    params[k] = def_params[k]
            logger.debug('before filter: %s' % params)
            params = {k: params[k] for k in params.keys() & self.opts}
            for opt in self.manditory_opts:
                if not opt in params or params[opt] == None:
                    self._parser_error('missing option: %s' % opt)
            params['config'] = config
            try:
                exec_obj = self.executors[exec_name](params)
                self._init_executor(exec_obj, config, args[1:])
                logging.debug('invoking: %s.%s' % (exec_obj, meth))
                getattr(exec_obj, meth)()
            except ActionCliError as err:
                self._parser_error(format(err))
