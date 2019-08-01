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
    INSTANCE_CLASSES = {}

    def __init__(self, config):
        super(StashFactory, self).__init__(config, '{name}_stash')


for cls in (DelegateStash,
            KeyLimitStash,
            PreemptiveStash,
            FactoryStash,
            DictionaryStash,
            CacheStash,
            DirectoryStash,
            ShelveStash):
    StashFactory.register(cls)
