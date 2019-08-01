import logging
import re
import itertools as it
import parse
from copy import copy
import pickle
from time import time
from pathlib import Path
import shelve as sh
from abc import abstractmethod, ABC

logger = logging.getLogger(__name__)


# class level persistance
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

    def clear_global(self):
        """Clear only any cached global data.

        """
        vname = self.varname
        logger.debug(f'global clearning {vname}')
        if vname in globals():
            logger.debug('removing global instance var: {}'.format(vname))
            del globals()[vname]

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
        self.clear_global()

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


# resource/sql
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


# collections
class Stash(ABC):
    """Pure virtual clsss that represents CRUDing data.  The data is usually CRUDed
    to the file system but need not be.  Instance can be used as iterables or
    dicsts.  If the former, each item is returned as a key/value tuple.

    """
    @abstractmethod
    def load(self, name: str):
        "Load a data value from the pickled data with key ``name``."
        pass

    @abstractmethod
    def exists(self, name: str):
        "Return ``True`` if data with key ``name`` exists."
        pass

    @abstractmethod
    def dump(self, name: str, inst):
        "Persist data value ``inst`` with key ``name``."
        pass

    @abstractmethod
    def delete(self, name=None):
        """Delete the resource for data pointed to by ``name`` or the entire resource
        if ``name`` is not given.

        """
        pass

    def clear(self):
        """Delete all data from the from the stash.

        *Important*: Exercise caution with this method, of course.

        """
        for k in self.keys():
            self.delete(k)

    @abstractmethod
    def keys(self):
        """Return an iterable of keys in the collection."""
        pass

    def key_groups(self, n):
        "Return an iterable of groups of keys, each of size at least ``n``."
        klst = tuple(self.keys())
        for i in range(0, len(klst), n):
            yield klst[i:i+n]

    def items(self):
        """Return an iterable of all stash items"""
        return map(lambda x: self.__getitem__(x), self.keys())

    def __getitem__(self, key):
        exists = self.exists(key)
        item = self.load(key)
        if not exists:
            self.dump(key, item)
        return item

    def __setitem__(self, key, value):
        self.dump(key, value)

    def __delitem__(self, key):
        self.delete(key)

    def __contains__(self, key):
        return self.exists(key)

    def __iter__(self):
        return map(lambda x: (x, self.__getitem__(x),), self.keys())

    def __len__(self):
        return len(tuple(self.keys()))


class CloseableStash(Stash):
    """Any stash that has a resource that needs to be closed.

    """
    @abstractmethod
    def close(self):
        "Close all resources created by the stash."
        pass


class DelegateStash(CloseableStash):
    """Delegate pattern.  It can also be used as a no-op if no delegate is given.

    A minimum functioning implementation needs the ``load`` and ``keys``
    methods overriden.  Inheriting and implementing a ``Stash`` such as this is
    usually used as the ``factory`` in a ``FactoryStash``.

    """
    def __init__(self, delegate=None):
        if delegate is not None and not isinstance(delegate, Stash):
            raise ValueError(f'not a stash: {delegate}')
        self.delegate = delegate

    def load(self, name: str):
        if self.delegate is not None:
            return self.delegate.load(name)

    def exists(self, name: str):
        if self.delegate is not None:
            return self.delegate.exists(name)
        else:
            return False

    def dump(self, name: str, inst):
        if self.delegate is not None:
            return self.delegate.dump(name, inst)

    def delete(self, name=None):
        if self.delegate is not None:
            return self.delegate.delete(name)

    def keys(self):
        if self.delegate is not None:
            return self.delegate.keys()
        return ()

    def close(self):
        if self.delegate is not None:
            return self.delegate.close()


class KeyLimitStash(DelegateStash):
    """A stash that limits the number of generated keys useful for debugging.

    For most stashes, this also limits the iteration output since that is based
    on key mapping.

    """
    def __init__(self, delegate: Stash, n_limit=10):
        super(KeyLimitStash, self).__init__(delegate)
        self.n_limit = n_limit

    def keys(self):
        ks = super(KeyLimitStash, self).keys()
        return it.islice(ks, self.n_limit)



class PreemptiveStash(DelegateStash):
    """Provide support for preemptively creating data in a stash.

    """
    @property
    def has_data(self):
        """Return whether or not the stash has any data available or not."""
        if not hasattr(self, '_has_data'):
            try:
                next(iter(self.delegate.keys()))
                self._has_data = True
            except StopIteration:
                self._has_data = False
        return self._has_data

    def _reset_has_data(self):
        """Reset the state of whether the stash has data or not."""
        if hasattr(self, '_has_data'):
            delattr(self, '_has_data')

    def _set_has_data(self, has_data=True):
        """Set the state of whether the stash has data or not."""
        self._has_data = has_data


class FactoryStash(PreemptiveStash):
    """A stash that defers to creation of new items to another ``factory`` stash.

    """
    def __init__(self, delegate, factory):
        """Initialize.

        :param delegate: the stash used for persistence
        :type delegate: Stash
        :param factory: the stash used to create using ``load`` and ``keys``
        :type factory: Stash
        """
        super(FactoryStash, self).__init__(delegate)
        self.factory = factory

    def load(self, name: str):
        if self.exists(name):
            item = super(FactoryStash, self).load(name)
        else:
            self._reset_has_data()
            item = self.factory.load(name)
        return item

    def keys(self):
        if self.has_data:
            ks = super(FactoryStash, self).keys()
        else:
            ks = self.factory.keys()
        return ks


class DictionaryStash(DelegateStash):
    """Use a dictionary as a backing store to the stash.  If one is not provided in
    the initializer a new ``dict`` is created.

    """
    def __init__(self, data: dict=None):
        if data is None:
            self.data = {}
        else:
            self.data = data

    def load(self, name: str):
        return self.data[name]

    def exists(self, name: str):
        return name in self.data

    def dump(self, name: str, inst):
        self.data[name] = inst

    def delete(self, name=None):
        del self.data[name]

    def keys(self):
        return self.data.keys()

    def __getitem__(self, key):
        return self.data[key]


class CacheStash(DelegateStash):
    """Provide a dictionary based caching based stash.

    """
    def __init__(self, delegate, cache_stash=None):
        super(CacheStash, self).__init__(delegate)
        if cache_stash is None:
            self.cache_stash = DictionaryStash()
        else:
            self.cache_stash = cache_stash

    def load(self, name: str):
        if self.cache_stash.exists(name):
            return self.cache_stash.load(name)
        else:
            obj = self.delegate.load(name)
            self.cache_stash.dump(name, obj)
            return obj

    def exists(self, name: str):
        return self.cache_stash.exists(name) or self.delegate.exists(name)

    def delete(self, name=None):
        if self.cache_stash.exists(name):
            self.cache_stash.delete(name)
        return self.delegate.delete(name)


class DirectoryStash(Stash):
    """Creates a pickeled data file with a file name in a directory with a given
    pattern across all instances.

    """
    def __init__(self, create_path: Path, pattern='{name}.dat'):
        """Create a stash.

        :param create_path: the directory of where to store the files
        :param pattern: the file name portion with ``name`` populating to the
            key of the data value

        """
        self.pattern = pattern
        self.create_path = create_path

    def _create_path_dir(self):
        self.create_path.mkdir(parents=True, exist_ok=True)

    def _get_instance_path(self, name):
        "Return a path to the pickled data with key ``name``."
        fname = self.pattern.format(**{'name': name})
        logger.debug(f'path {self.create_path}: {self.create_path.exists()}')
        self._create_path_dir()
        return Path(self.create_path, fname)

    def load(self, name):
        path = self._get_instance_path(name)
        inst = None
        if path.exists():
            logger.info(f'loading instance from {path}')
            with open(path, 'rb') as f:
                inst = pickle.load(f)
        logger.debug(f'loaded instance: {inst}')
        return inst

    def exists(self, name):
        path = self._get_instance_path(name)
        return path.exists()

    def keys(self):
        def path_to_key(path):
            p = parse.parse(self.pattern, path.name).named
            if 'name' in p:
                return p['name']

        if not self.create_path.is_dir():
            keys = ()
        else:
            keys = filter(lambda x: x is not None,
                          map(path_to_key, self.create_path.iterdir()))
        return keys

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

    def close(self):
        pass


class ShelveStash(CloseableStash):
    """Stash that uses Python's shelve library to store key/value pairs in dbm
    (like) databases.

    """
    def __init__(self, create_path: Path, writeback=False):
        """Initialize.

        :param create_path: a file to be created to store and/or load for the
            data storage
        :param writeback: the writeback parameter given to ``shelve``

        """
        self.create_path = create_path
        self.writeback = writeback
        self.is_open = False

    @property
    @persisted('_shelve')
    def shelve(self):
        """Return an opened shelve object.

        """
        logger.info('creating shelve data')
        fname = str(self.create_path.absolute())
        inst = sh.open(fname, writeback=self.writeback)
        self.is_open = True
        return inst

    def load(self, name):
        if self.exists(name):
            return self.shelve[name]

    def dump(self, name, inst):
        self.shelve[name] = inst

    def exists(self, name):
        return name in self.shelve

    def keys(self):
        return self.shelve.keys()

    def delete(self, name=None):
        "Delete the shelve data file."
        logger.info('clearing shelve data')
        self.close()
        for path in Path(self.create_path.parent, self.create_path.name), \
            Path(self.create_path.parent, self.create_path.name + '.db'):
            logger.debug(f'clearing {path} if exists: {path.exists()}')
            if path.exists():
                path.unlink()
                break

    def close(self):
        "Close the shelve object, which is needed for data consistency."
        if self.is_open:
            logger.info('closing shelve data')
            try:
                self.shelve.close()
                self._shelve.clear()
            except Exception:
                self.is_open = False



# utility functions
class shelve(object):
    """Object used with a ``with`` scope that creates the closes a shelve object.

    """
    def __init__(self, *args, **kwargs):
        self.shelve = ShelveStash(*args, **kwargs)

    def __enter__(self):
        return self.shelve

    def __exit__(self, type, value, traceback):
        self.shelve.close()
