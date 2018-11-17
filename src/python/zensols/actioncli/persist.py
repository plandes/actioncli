import logging
import re
from copy import copy
import pickle
from time import time
from pathlib import Path

logger = logging.getLogger(__name__)


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
    def __init__(self, path, owner, cache_global=False, transient=False):
        """Create an instance of the class.

        :param path: if type of ``pathlib.Path`` then use disk storage to cache
            of the pickeled data, otherwise a string used to store in the owner
        :type path: pathlib.Path or str
        :param owner: an owning class to get and retrieve as an attribute
        :param cache_global: cache the data globals; this shares data across
            instances but not classes

        """
        logger.debug('pw inst: path={}, global={}'.format(path, cache_global))
        self.owner = owner
        self.cache_global = cache_global
        self.transient = transient
        self.worker = None
        if isinstance(path, Path):
            self.path = path
            self.use_disk = True
            fname = re.sub(r'[ /\\.]', '_', str(self.path.absolute()))
        else:
            self.path = Path(path)
            self.use_disk = False
            fname = str(path)
        cstr = owner.__module__ + '.' + owner.__class__.__name__
        self.varname = f'_{cstr}_{fname}_pwvinst'

    def _info(self, msg, *args):
        logger.debug(self.varname + ': ' + msg, *args)

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
        self._info('created work in {:2f}s, saving to {}'.format(
            (time() - t0), self.path))
        return obj

    def _load_or_create(self, *argv, **kwargs):
        """Invoke the file system operations to get the data, or create work.

        If the file does not exist, calling ``__do_work__`` and save it.
        """
        if self.path.exists():
            self._info('loading work from {}'.format(self.path))
            with open(self.path, 'rb') as f:
                obj = pickle.load(f)
        else:
            self._info('saving work to {}'.format(self.path))
            with open(self.path, 'wb') as f:
                obj = self._do_work(*argv, **kwargs)
                pickle.dump(obj, f)
        return obj

    def set(self, obj):
        logger.debug(f'saving in memory value {type(obj)}')
        vname = self.varname
        setattr(self.owner, vname, obj)
        if self.cache_global:
            if vname not in globals():
                globals()[vname] = obj

    def __getstate__(self):
        """We must null out the owner and worker as they are not pickelable.

        :seealso: PersistableContainer

        """
        d = copy(self.__dict__)
        # if self.worker is not None:
        #     d['worker_name'] = self.worker.__name__
        # del d['owner']
        # del d['worker']
        d['owner'] = None
        d['worker'] = None
        return d

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
                self._info('invoking worker')
                obj = self._do_work(*argv, **kwargs)
        self.set(obj)
        return obj

    def __do_work__(self, *argv, **kwargs):
        """You can extend this class and overriding this method.  This method will
        invoke the worker to do the work.

        """
        return self.worker(*argv, **kwargs)


class PersistableContainer(object):
    """Classes can extend this that want to persist ``PersistableWork`` instances,
    which otherwise are not persistable.

    """
    def __getstate__(self):
        state = copy(self.__dict__)
        removes = []
        for k, v in state.items():
            logger.debug(f'container get state: {k} => {v}')
            if isinstance(v, PersistedWork):
                if v.transient:
                    removes.append(v.varname)
        for k in removes:
            #del state[k]
            state[k] = None
        return state

    def __setstate__(self, state):
        """Set the owner to containing instance and the worker function to the owner's
        function by name.

        """
        self.__dict__.update(state)
        for k, v in state.items():
            logger.debug(f'container set state: {k} => {v}')
            if isinstance(v, PersistedWork):
                #logger.debug(f'worker: {v.worker_name} => {v}')
                #setattr(self, v.worker_name, property(v.worker_name).getter)
                #delattr(v, 'worker_name')
                setattr(v, 'owner', self)


class persisted(object):
    """Class level annotation to further simplify usage with PersistedWork.


    For example:

    class SomeClass(object):
        @property
        @persisted('counter', 'tmp.dat')
        def someprop(self):
            return tuple(range(5))
    """
    def __init__(self, attr_name, path=None, cache_global=False,
                 transient=False):
        logger.debug('persisted decorator on attr: {}, global={}'.format(
            attr_name, cache_global))
        self.attr_name = attr_name
        self.path = path
        self.cache_global = cache_global
        self.transient = transient

    def __call__(self, fn):
        logger.debug(f'call: {fn}:{self.attr_name}:{self.path}:' +
                     f'{self.cache_global}')

        def wrapped(*argv, **kwargs):
            inst = argv[0]
            logger.debug(f'wrap: {fn}:{self.attr_name}:{self.path}:' +
                         f'{self.cache_global}')
            if hasattr(inst, self.attr_name):
                pwork = getattr(inst, self.attr_name)
            else:
                if self.path is None:
                    path = self.attr_name
                else:
                    path = Path(self.path)
                pwork = PersistedWork(
                    path, owner=inst, cache_global=self.cache_global,
                    transient=self.transient)
                setattr(inst, self.attr_name, pwork)
            pwork.worker = fn
            return pwork(*argv, **kwargs)

        return wrapped


class resource(object):
    """This annotation uses a template pattern to (de)allocate resources.  For
    example, you can declare class methods to create database connections and
    then close them.  This example looks like this:

    class CrudManager(object):
        def _create_connection(self):
            return sqlite3.connect(':memory:')

        def _dispose_connection(self, conn):
            conn.close()

        @resource('_create_connection', '_dispose_connection')
        def commit_work(self, conn, obj):
            conn.execute(...)

    """
    def __init__(self, create_method_name, destroy_method_name):
        """Create the instance based annotation.

        :param create_method_name: the name of the method that allocates
        :param destroy_method_name: the name of the method that deallocates
        """
        logger.debug(f'connection decorator {create_method_name} ' +
                     f'destructor method name: {destroy_method_name}')
        self.create_method_name = create_method_name
        self.destroy_method_name = destroy_method_name

    def __call__(self, fn):
        logger.debug(f'connection call with fn: {fn}')

        def wrapped(*argv, **kwargs):
            logger.debug(f'in wrapped {self.create_method_name}')
            inst = argv[0]
            resource = getattr(inst, self.create_method_name)()
            try:
                result = fn(inst, resource, *argv[1:], **kwargs)
            finally:
                getattr(inst, self.destroy_method_name)(resource)
            return result

        return wrapped


class Stash(object):
    def load(self, name=None, *args, **kwargs):
        pass

    def dump(self, name, inst):
        pass

    def delete(self, name):
        pass


class DirectoryStash(Stash):
    def __init__(self, create_path: Path, pattern='{name}.dat'):
        self.create_path = create_path
        self.pattern = pattern

    def _get_instance_path(self, name):
        fname = self.pattern.format(**{'name': name})
        if not self.create_path.exists():
            self.create_path.mkdir(parents=True)
        return Path(self.create_path, fname)

    def load(self, name=None):
        name = self.default_name if name is None else name
        path = self._get_instance_path(name)
        inst = None
        if path.exists():
            logger.info(f'loading instance from {path}')
            with open(path, 'rb') as f:
                inst = pickle.load(f)
        logger.debug(f'loaded instance: {inst}')
        return inst

    def dump(self, name, inst):
        logger.info(f'saving instance: {inst}')
        path = self._get_instance_path(name)
        with open(path, 'wb') as f:
            pickle.dump(inst, f)

    def delete(self, name):
        logger.info(f'deleting instance: {name}')
        path = self._get_instance_path(name)
        if path.exists():
            path.unlink()
