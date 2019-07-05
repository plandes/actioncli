import logging
import math
from multiprocessing import Pool
from zensols.actioncli import Stash

logger = logging.getLogger(__name__)


class StashMapReducer(object):
    def __init__(self, stash: Stash, n_workers: int = 10):
        self.stash = stash
        self.n_workers = n_workers

    @property
    def key_group_size(self):
        n_items = len(self.stash)
        return math.ceil(n_items / self.n_workers)

    def map(self, id: str, val):
        return (id, val)

    def reduce(self, vals):
        return vals

    def _worker(self, id_sets):
        return tuple(map(lambda id: self.map(id, self.stash[id]), id_sets))

    def _map(self):
        id_sets = self.stash.key_groups(self.key_group_size)
        pool = Pool(self.n_workers)
        return pool.map(self._worker, id_sets)

    def __call__(self):
        mapval = self._map()
        return map(self.reduce, mapval)


class FunctionStashMapReducer(StashMapReducer):
    def __init__(self, stash: Stash, func, n_workers: int = 10):
        super(FunctionStashMapReducer, self).__init__(stash, n_workers)
        self.func = func

    def map(self, id: str, val):
        return self.func(id, val)

    @staticmethod
    def map_func(*args, **kwargs):
        mr = FunctionStashMapReducer(*args, **kwargs)
        return mr._map()
