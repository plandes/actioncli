import logging
import re
import pickle
from time import time
from pathlib import Path

logger = logging.getLogger('zensols.actioncli.pwork')


class PersistedWork(object):
    """This class automatically caches work that's serialized to the disk.

    In order, it first looks for the data in ``owner``, then in globals (if
    ``cache_global`` is True), then it looks for the data on the file system.
    If it can't find it after all of this it invokes function ``worker`` to
    create the data and then pickles it to the disk.

    This class is a callable itself, which is invoked to get or create the
    work.

    There are two ways to implement the data/work creation: pass a ``worker``
    to the ``__init__`` method or extend this class and override
    ``__do_work__``.

    """
    def __init__(self, path, cache_global=False, owner=None, worker=None,
                 use_disk=True):
        """Create an instance of the class.

        :param path: the path of the cached pickled data
        :param cache_global: cache the data globals; this shares data across
          instances but not classes
        :param worker: a callable used to create the data if not cached
        :param owner: an owning class to get and retrieve as an attribute
        :param use_disk: if True, then persist results on the disk; useful for
          when only in memory caching is desired
        """
        logger.debug('pw inst: path={}, global={}'.format(path, cache_global))
        if isinstance(path, str):
            path = Path(path)
        self.path = path
        self.cache_global = cache_global
        self.owner = owner
        self.worker = worker
        self.use_disk = use_disk

    @property
    def varname(self):
        if not hasattr(self, '_varname'):
            fname = re.sub(r'[ /\\.]', '_', str(self.path.absolute()))
            self._varname = '_pwv_{}'.format(fname)
        return self._varname

    def clear(self):
        """Clear the data, and thus, force it to be created on the next fetch.  This is
        done by removing the attribute from ``owner``, deleting it from globals
        and removing the file from the disk.

        """
        vname = self.varname
        if self.path.exists():
            logger.debug('deleting cached work: {}'.format(self.path))
            self.path.unlink()
        if self.owner is not None and hasattr(self.owner, vname):
            logger.debug('removing instance var: {}'.format(vname))
            delattr(self.owner, vname)
        if vname in globals():
            logger.debug('removing global instance var: {}'.format(vname))
            del globals()[vname]

    def _do_work(self, *argv, **kwargs):
        t0 = time()
        obj = self.__do_work__(*argv, **kwargs)
        logger.info('created work in {:2f}s, saving to {}'.format(
            (time() - t0), self.path))
        return obj

    def _load_or_create(self, *argv, **kwargs):
        """Invoke the file system operations to get the data, or create work.

        If the file does not exist, calling ``__do_work__`` and save it.
        """
        if self.path.exists():
            logger.info('loading work from {}'.format(self.path))
            with open(self.path, 'rb') as f:
                obj = pickle.load(f)
        else:
            with open(self.path, 'wb') as f:
                obj = self._do_work(*argv, **kwargs)
                pickle.dump(obj, f)
        return obj

    def __call__(self, *argv, **kwargs):
        """Return the cached data if it doesn't yet exist.  If it doesn't exist, create
        it and cache it on the file system, optionally ``owner`` and optionally
        the globals.

        """
        vname = self.varname
        obj = None
        logger.debug('call with vname: {}'.format(vname))
        if self.owner is not None and hasattr(self.owner, vname):
            logger.debug('found in instance')
            obj = getattr(self.owner, vname)
        if obj is None and self.cache_global:
            if vname in globals():
                logger.debug('found in globals')
                obj = globals()[vname]
        if obj is None:
            if self.use_disk:
                obj = self._load_or_create(*argv, **kwargs)
            else:
                obj = self._do_work(*argv, **kwargs)
            if self.cache_global:
                vname = self.varname
                if vname not in globals():
                    globals()[vname] = obj
        setattr(self.owner, vname, obj)
        return obj

    def __do_work__(self, *argv, **kwargs):
        """You can extend this class and overriding this method.  This method will
        invoke the worker to do the work.

        """
        return self.worker(*argv, **kwargs)


class persisted(object):
    """Class level annotation to further simplify usage with PersistedWork.


    For example:

    class SomeClass(object):
        @property
        @persisted('counter', 'tmp.dat')
        def someprop(self):
            return tuple(range(5))
    """
    def __init__(self, attr_name, path=None, cache_global=False):
        logger.debug('persisted decorator on attr: {}'.format(attr_name))
        self.attr_name = attr_name
        self.path = path
        self.cache_global = cache_global

    def __call__(self, fn):
        logger.debug('in call')

        def wrapped(*argv, **kwargs):
            logger.debug('in wrapped')
            inst = argv[0]
            if self.path is not None and not hasattr(inst, self.attr_name):
                pwork = PersistedWork(
                    self.path, owner=inst, cache_global=self.cache_global)
                setattr(inst, self.attr_name, pwork)
            else:
                pwork = getattr(inst, self.attr_name)
            pwork.worker = fn
            return pwork(*argv, **kwargs)

        return wrapped
