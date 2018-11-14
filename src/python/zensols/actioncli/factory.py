import logging
import inspect
from zensols.actioncli import Configurable

logger = logging.getLogger('zensols.actioncli.factory')


class ConfigFactory(object):
    """Creates new instances of classes and configures them given data in a
    configuration ``Config`` instance.

    :param config: an instance of ``Configurable``
    :param pattern: the pattern of the section/name identifier to get kwargs to
        initialize the new instance of the object
    """

    def __init__(self, config: Configurable, pattern='{name}',
                 config_param_name='config', name_param_name='name'):
        self.config = config
        self.pattern = pattern
        self.config_param_name = config_param_name
        self.name_param_name = name_param_name

    @classmethod
    def register(cls, instance_class, name=None):
        if name is None:
            name = instance_class.__name__
        cls.INSTANCE_CLASSES[name] = instance_class

    def _find_class(self, class_name):
        classes = {}
        classes.update(globals())
        classes.update(self.INSTANCE_CLASSES)
        logger.debug(f'looking up class: {class_name}')
        cls = classes[class_name]
        logger.debug(f'found class: {cls}')
        return cls

    def _class_name_params(self, name):
        sec = self.pattern.format(**{'name': name})
        logger.debug(f'section: {sec}')
        params = {}
        params.update(self.config.populate({}, section=sec))
        class_name = params['class_name']
        del params['class_name']
        return class_name, params

    def _has_init_config(self, cls):
        args = inspect.signature(cls.__init__)
        return self.config_param_name in args.parameters

    def _has_init_name(self, cls):
        args = inspect.signature(cls.__init__)
        return self.name_param_name in args.parameters

    def _instance(self, cls, *args, **kwargs):
        logger.debug(f'args: {args}, kwargs: {kwargs}')
        return cls(*args, **kwargs)

    def instance(self, name='default', *args, **kwargs):
        logger.debug(f'creating instance of {name}')
        class_name, params = self._class_name_params(name)
        cls = self._find_class(class_name)
        params.update(kwargs)
        if self._has_init_config(cls):
            logger.debug(f'found config parameter')
            params['config'] = self.config
        if self._has_init_name(cls):
            logger.debug(f'found name parameter')
            params['name'] = name
        if logger.level >= logging.DEBUG:
            for k, v in params.items():
                logger.debug(f'populating {k} -> {v} ({type(v)})')
        return self._instance(cls, *args, **params)
