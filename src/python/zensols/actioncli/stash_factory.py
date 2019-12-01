import logging
from zensols.actioncli import (
    ConfigChildrenFactory,
    DelegateStash,
    KeyLimitStash,
    PreemptiveStash,
    FactoryStash,
    DictionaryStash,
    CacheStash,
    DirectoryStash,
    ShelveStash,
)

logger = logging.getLogger(__name__)


class StashFactory(ConfigChildrenFactory):
    USE_CACHE_STASH_KEY = 'use_cache_stash'
    INSTANCE_CLASSES = {}

    def __init__(self, config):
        super(StashFactory, self).__init__(config, '{name}_stash')

    def _instance(self, cls, *args, **kwargs):
        use_cache = False
        if self.USE_CACHE_STASH_KEY in kwargs:
            use_cache = kwargs[self.USE_CACHE_STASH_KEY]
            del kwargs[self.USE_CACHE_STASH_KEY]
        stash = super(StashFactory, self)._instance(cls, *args, **kwargs)
        if use_cache:
            stash = CacheStash(stash)
        return stash


for cls in (DelegateStash,
            KeyLimitStash,
            PreemptiveStash,
            FactoryStash,
            DictionaryStash,
            CacheStash,
            DirectoryStash,
            ShelveStash):
    StashFactory.register(cls)
