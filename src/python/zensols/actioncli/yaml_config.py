import logging
import yaml
import pprint
import copy

logger = logging.getLogger('zensols.actioncli.yml')


class YamlConfig(object):
    CLASS_VER = 0

    def __init__(self, config_file=None, delimiter='$', default_vars=None):
        self.config_file = config_file
        self.delimiter = delimiter
        self.default_vars = default_vars if default_vars else {}

    def _parse(self):
        with open(self.config_file) as f:
            content = f.read()
        struct = yaml.load(content)
        context = copy.deepcopy(self.default_vars)

        def flatten(path, n):
            logger.debug('path: {}, n: <{}>'.format(path, n))
            logger.debug('context: <{}>'.format(context))
            if isinstance(n, str) or isinstance(n, list):
                context[path] = n
            else:
                if isinstance(n, dict):
                    for k, v in n.items():
                        k = path + '.' + k if len(path) else k
                        flatten(k, v)
                else:
                    raise ValueError('unknown yaml type {}: {}'.
                                     format(type(n), n))

        flatten('', struct)
        return content, struct, context

    def _make_class(self):
        class_name = 'YamlTemplate{}'.format(self.CLASS_VER)
        self.CLASS_VER += 1
        # why couldn't they have made idpattern and delimiter instance members?
        # note we have to give the option of different delimiters since the
        # default '$$' (use case=OS env vars) is always resolved to '$' given
        # the iterative variable substitution method
        code = """\
from string import Template
class """ + class_name + """(Template):
     idpattern = r'[a-z][_a-z0-9.]*'
     delimiter = '""" + self.delimiter + '\''
        exec(code)
        cls = eval(class_name)
        return cls

    def _compile(self):
        content, struct, context = self._parse()
        prev = None
        cls = self._make_class()
        while prev != content:
            prev = content
            content = cls(content).substitute(context)
        return yaml.load(content)

    @property
    def config(self):
        if not hasattr(self, '_config'):
            self._config = self._compile()
        return self._config

    def pprint(self):
        pprint.PrettyPrinter().pprint(self.config)

    def _option(self, name):
        def find(n, path, name):
            logger.debug(
                'search: n={}, path={}, name={}'.format(n, path, name))
            if path == name:
                logger.debug('found: <{}>'.format(n))
                return n
            elif not isinstance(n, str):
                for k, v in n.items():
                    k = path + '.' + k if len(path) else k
                    v = find(v, k, name)
                    if v is not None:
                        logger.debug('found {} -> {}'.format(name, v))
                        return v
                logger.debug('not found: {}'.format(name))
        return find(self.config, '', name)

    def get_option(self, name, expect=False):
        node = self._option(name)
        if isinstance(node, str) or isinstance(node, list):
            return node
        elif self.default_vars is not None and name in self.default_vars:
            return self.default_vars[name]
        elif expect:
            raise ValueError('no such option: {}'.format(name))

    def get_options(self, name):
        node = self._option(name)
        if not isinstance(node, str) or isinstance(node, list):
            return node
        elif name in self.default_vars:
            return self.default_vars[name]
