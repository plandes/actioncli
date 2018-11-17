import logging
import inspect
import pickle
from pathlib import Path
from zensols.actioncli import (
    Configurable,
    DirectoryStash,
)

logger = logging.getLogger(__name__)


class ConfigFactory(object):
    """Creates new instances of classes and configures them given data in a
    configuration ``Config`` instance.

    :param config: an instance of ``Configurable``
    :param pattern: the pattern of the section/name identifier to get kwargs to
        initialize the new instance of the object
    """

    def __init__(self, config: Configurable, pattern='{name}',
                 config_param_name='config', name_param_name='name',
                 default_name='default'):
        self.config = config
        self.pattern = pattern
        self.config_param_name = config_param_name
        self.name_param_name = name_param_name
        self.default_name = default_name

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

    def instance(self, name=None, *args, **kwargs):
        logger.info(f'new instance of {name}')
        name = self.default_name if name is None else name
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
        inst = self._instance(cls, *args, **params)
        logger.debug(f'created instance: {inst}')
        return inst


class ConfigManager(ConfigFactory):
    def __init__(self, config: Configurable, stash, *args, **kwargs):
        super(ConfigManager, self).__init__(config, *args, **kwargs)
        self.stash = stash

    def load(self, name=None, *args, **kwargs):
        inst = self.stash.load(name)
        if inst is None:
            inst = self.instance(*args, **kwargs)
        logger.debug(f'loaded (conf mng) instance: {inst}')
        return inst

    def dump(self, inst):
        self.stash.dump(inst)

    def delete(self, name):
        self.stash.delete(name)


class SingleClassConfigManager(ConfigManager):
    def __init__(self, config, cls, *args, **kwargs):
        super(SingleClassConfigManager, self).__init__(config, *args, **kwargs)
        self.cls = cls

    def _find_class(self, class_name):
        return self.cls

    def _class_name_params(self, name):
        sec = self.pattern.format(**{'name': name})
        logger.debug(f'section: {sec}')
        params = {}
        params.update(self.config.populate({}, section=sec))
        return None, params


class CachingConfigFactory(object):
    def __init__(self, delegate):
        self.delegate = delegate
        self.insts = {}

    def instance(self, name=None, *args, **kwargs):
        logger.debug(f'cache config instance for {name}')
        if name in self.insts:
            logger.debug(f'reusing cached instance of {name}')
            return self.insts[name]
        else:
            logger.debug(f'creating new instance of {name}')
            inst = self.delegate.instance(name, *args, **kwargs)
            self.insts[name] = inst
            return inst

    def load(self, name=None, *args, **kwargs):
        if name in self.insts:
            logger.debug(f'reusing (load) cached instance of {name}')
            return self.insts[name]
        else:
            logger.debug(f'load new instance of {name}')
            inst = self.delegate.load(name, *args, **kwargs)
            self.insts[name] = inst
            return inst

    def dump(self, inst):
        self.delegate.dump(inst)

    def delete(self, name):
        self.delegate.delete(name)
        self.evict(name)

    def evict(self, name):
        if name in self.insts:
            del self.insts[name]

    def evict_all(self):
        self.insts.clear()
