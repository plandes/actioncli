import configparser, os, logging

logger = logging.getLogger('zensols.config')

class Config(object):
    """
    Application configuration utility.  This reads from a configuration and
    returns sets or subsets of options.
    """
    def __init__(self, config_file=None, default_section='default',
                 robust=False, default_vars=None):
        """Create with a configuration file path.

        Keyword arguments:
        :param str config_file: the configuration file path to read from
        :param str default_section: default section (defaults to `default`)
        :param bool robust: -- if `True`, then don't raise an error when the configuration
                    file is missing
        """
        self.config_file = config_file
        self.default_section = default_section
        self.robust = robust
        self.default_vars = default_vars

    def _create_config_parser(self):
        "Factory method to create the ConfigParser."
        return configparser.ConfigParser()

    @property
    def parser(self):
        "Load the configuration file."
        if not hasattr(self, '_conf'):
            cfile = self.config_file
            logger.debug('loading config %s' % cfile)
            if os.path.isfile(cfile):
                conf = self._create_config_parser()
                conf.read(os.path.expanduser(cfile))
            else:
                if self.robust:
                    logger.debug('no default config file %s--skipping' % cfile)
                else:
                    raise IOError('no such file: %s' % cfile)
                conf = None
            self._conf = conf
        return self._conf

    @property
    def file_exists(self):
        return (self.parser != None)

    def get_options(self, section='default', opt_keys=None, vars=None):
        """
        Get all options for a section.  If **opt_keys** is given return
        only options with those keys.
        """
        vars = vars if vars else self.default_vars
        conf = self.parser
        opts = {}
        if opt_keys == None:
            if conf == None:
                opt_keys = {}
            else:
                if not self.robust or conf.has_section(section):
                    opt_keys = conf.options(section)
                else:
                    opt_keys = {}
        else:
            logger.debug('conf: %s' % conf)
            copts = conf.options(section) if conf else {}
            opt_keys = set(opt_keys).intersection(set(copts))
        for option in opt_keys:
            opts[option] = conf.get(section, option, vars=vars)
        return opts

    def get_option(self, name, section=None, vars=None, expect=False):
        """
        Return an option from **section** with **name**.  Parameter
        **section** defaults to constructor's **default_section**.
        """
        vars = vars if vars else self.default_vars
        if section == None:
            section = self.default_section
        opts = self.get_options(section, opt_keys=[name], vars=vars)
        if opts:
            return opts[name]
        else:
            if expect:
                raise ValueError('''no option '%s' found in section %s''' % (name, section))

    @property
    def options(self):
        "Return all options from the default section."
        return self.get_options()

    @property
    def sections(self):
        "Return all sections."
        secs = self.parser.sections()
        if secs: return set(secs)

    def __str__(self):
        return str('file: %s, section: %s' % (self.config_file, self.sections))
