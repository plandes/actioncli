import os
import logging
import re
import configparser
from pathlib import Path
import pkg_resources

logger = logging.getLogger('zensols.actioncli.conf')


class Settings(object):
    def __str__(self):
        return str(self.__dict__)

    def __repr__(self):
        return self.__str__()

    def pprint(self):
        from pprint import pprint
        pprint(self.__dict__)


class Configurable(object):
    FLOAT_REGEXP = re.compile(r'^[-+]?\d*\.\d+$')
    INT_REGEXP = re.compile(r'^[-+]?[0-9]+$')
    BOOL_REGEXP = re.compile(r'^True|False')
    EVAL_REGEXP = re.compile(r'^eval:\s*(.+)$')

    def __init__(self, config_file):
        self.config_file = config_file

    def get_option(self, name, expect=False):
        raise ValueError('get_option is not implemented')

    def get_options(self, name, expect=False):
        raise ValueError('get_options is not implemented')

    @property
    def options(self):
        raise ValueError('get_option is not implemented')

    def populate(self, obj=None, section=None, parse_types=True):
        """Set attributes in ``obj`` with ``setattr`` from the all values in
        ``section``.

        """
        section = self.default_section if section is None else section
        obj = Settings() if obj is None else obj
        is_dict = isinstance(obj, dict)
        for k, v in self.get_options(section).items():
            if parse_types:
                if v == 'None':
                    v = None
                elif self.FLOAT_REGEXP.match(v):
                    v = float(v)
                elif self.INT_REGEXP.match(v):
                    v = int(v)
                elif self.BOOL_REGEXP.match(v):
                    v = v == 'True'
                else:
                    m = self.EVAL_REGEXP.match(v)
                    if m:
                        evalstr = m.group(1)
                        v = eval(evalstr)
            logger.debug('setting {} => {} on {}'.format(k, v, obj))
            if is_dict:
                obj[k] = v
            else:
                setattr(obj, k, v)
        return obj

    def resource_filename(self, resource_name):
        """Return a resource based on a file name.  This uses the ``pkg_resources``
        package first to find the resources.  If it doesn't find it, it returns
        a path on the file system.

        Returns: a path on the file system or resource of the installed module.

        """
        if pkg_resources.resource_exists(__name__, resource_name):
            res = pkg_resources.resource_filename(__name__, resource_name)
        else:
            res = resource_name
        return Path(res)


class Config(Configurable):
    """Application configuration utility.  This reads from a configuration and
    returns sets or subsets of options.

    """

    def __init__(self, config_file=None, default_section='default',
                 robust=False, default_vars=None):
        """Create with a configuration file path.

        Keyword arguments:
        :param str config_file: the configuration file path to read from
        :param str default_section: default section (defaults to `default`)
        :param bool robust: -- if `True`, then don't raise an error when the
                    configuration file is missing
        """
        super(Config, self).__init__(config_file)
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
        return self.parser is not None

    def get_options(self, section='default', opt_keys=None, vars=None):
        """
        Get all options for a section.  If ``opt_keys`` is given return
        only options with those keys.
        """
        vars = vars if vars else self.default_vars
        conf = self.parser
        opts = {}
        if opt_keys is None:
            if conf is None:
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
            logger.debug(f'option: {option}, vars: {vars}')
            opts[option] = conf.get(section, option, vars=vars)
        return opts

    def get_option(self, name, section=None, vars=None, expect=False):
        """Return an option from ``section`` with ``name``.

        :param section: section in the ini file to fetch the value; defaults to
        constructor's ``default_section``

        """
        vars = vars if vars else self.default_vars
        if section is None:
            section = self.default_section
        opts = self.get_options(section, opt_keys=[name], vars=vars)
        if opts:
            return opts[name]
        else:
            if expect:
                raise ValueError('no option \'{}\' found in section {}'.
                                 format(name, section))

    def get_option_list(self, name, section=None, vars=None,
                        expect=False, separator=','):
        """Just like ``get_option`` but parse as a list using ``split``.

        """
        val = self.get_option(name, section, vars, expect)
        return val.split(separator) if val else []

    def get_option_boolean(self, name, section=None, vars=None, expect=False):
        """Just like ``get_option`` but parse as a boolean (any case `true`).

        """
        val = self.get_option(name, section, vars, expect)
        val = val.lower() if val else 'false'
        return val == 'true'

    def get_option_path(self, name, section=None, vars=None, expect=False):
        """Just like ``get_option`` but return a ``pathlib.Path`` object of
        the string.

        """
        val = self.get_option(name, section, vars, expect)
        return Path(val)

    @property
    def options(self):
        "Return all options from the default section."
        return self.get_options()

    @property
    def sections(self):
        "Return all sections."
        secs = self.parser.sections()
        if secs:
            return set(secs)

    def __str__(self):
        return str('file: {}, section: {}'.
                   format(self.config_file, self.sections))

    def __repr__(self):
        return self.__str__()


class ExtendedInterpolationConfig(Config):
    """Configuration class extends using advanced interpolation with
    ``configparser.ExtendedInterpolation``.

    """

    def _create_config_parser(self):
        inter = configparser.ExtendedInterpolation()
        return configparser.ConfigParser(interpolation=inter)


# class ConfigFactory(object):
#     """Creates new instances of classes and configures them given data in a
#     configuration ``Config`` instance.

#     :param config: an instance of ``Configurable``
#     :param pattern: the pattern of the section/name identifier to get kwargs to
#         initialize the new instance of the object
#     """

#     def __init__(self, config: Configurable, pattern='{name}'):
#         self.config = config
#         self.pattern = pattern

#     @classmethod
#     def register(cls, instance_class, name=None):
#         if name is None:
#             name = instance_class.__name__
#         cls.INSTANCE_CLASSES[name] = instance_class

#     def instance(self, name='default', *args, **kwargs):
#         sec = self.pattern.format(**{'name': name})
#         logger.debug(f'section: {sec}')
#         params = {}
#         params.update(self.config.populate({}, section=sec))
#         class_name = params['class_name']
#         del params['class_name']
#         params.update(kwargs)
#         classes = {}
#         classes.update(globals())
#         classes.update(self.INSTANCE_CLASSES)
#         logger.debug(f'looking up class: {class_name}')
#         cls = classes[class_name]
#         logger.debug(f'found class: {cls}')
#         if logger.level >= logging.DEBUG:
#             for k, v in params.items():
#                 logger.debug(f'populating {k} -> {v} ({type(v)})')
#         inst = cls(*args, **params)
#         if hasattr(inst, 'set_config'):
#             attr = getattr(inst, 'set_config')
#             logger.debug(f'setting config on new instance on {attr}')
#             attr(self.config, name)
#         return inst
