import configparser, os, logging

logger = logging.getLogger('zensols.config')

class Config(object):
    """
    Application configuration utility.  This reads from a configuration and
    returns sets or subsets of options.
    """
    def __init__(self, config_file=None, default_section='default', robust=False):
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

    def _get_conf(self):
        "Load the configuration file."
        if not hasattr(self, '_conf'):
            cfile = self.config_file
            logger.debug('loading config %s' % cfile)
            if os.path.isfile(cfile):
                conf = configparser.ConfigParser()
                conf.read(os.path.expanduser(cfile))
            else:
                if self.robust:
                    logger.debug('no default config file %s--skipping' % cfile)
                else:
                    raise IOError('no such file: %s' % cfile)
                conf = None
            self._conf = conf
        return self._conf

    def get_options(self, section='default', opt_keys=None):
        """
        Get all options for a section.  If **opt_keys** is given return
        only options with those keys.
        """
        conf = self._get_conf()
        opts = {}
        if opt_keys == None:
            if conf == None:
                opt_keys = {}
            else:
                opt_keys = conf.options(section)
        else:
            opt_keys = set(opt_keys).intersection(set(conf.options(section)))
        for option in opt_keys:
            opts[option] = conf.get(section, option)
        return opts

    def get_option(self, name, section=None):
        """
        Return an option from **section** with **name**.  Parameter
        **section** defaults to constructor's **default_section**.
        """
        if section == None:
            section = self.default_section
        opts = self.get_options(section, opt_keys=[name])
        if opts: return opts[name]

    @property
    def options(self):
        "Return all options from the default section."
        return self.get_options()

    @property
    def sections(self):
        "Return all sections."
        secs = self._get_conf().sections()
        if secs: return set(secs)

    def __str__(self):
        return str(self.options)
