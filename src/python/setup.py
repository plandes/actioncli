from pathlib import Path
from zensols.pybuild import SetupUtil

su = SetupUtil(
    setup_path=Path(__file__).parent.absolute(),
    package_names=['zensols'],
    name='zensols.actioncli',
    project='actioncli',
    user='plandes',
    description='This library intends to make command line execution and configuration easy.',
    keywords=['tooling', 'command line'],
    has_entry_points=False,
)

su.setup()
