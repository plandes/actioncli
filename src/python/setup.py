from setuptools import setup
from os import path

nname, dname = None, path.abspath(path.join(path.dirname(__file__)))
while nname != dname:
    nname, dname = dname, path.abspath(path.join(dname, path.pardir))
    if path.exists(path.join(dname, 'README.md')):
        break
with open(path.join(dname, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name = "zensols.actioncli",
    packages = ['zensols.actioncli'],
    version = '0.6',
    description = 'This library intends to make command line execution and configuration easy.',
    author = 'Paul Landes',
    author_email = 'landes@mailc.net',
    url = 'https://github.com/plandes/actioncli',
    download_url = 'https://github.com/plandes/actioncli/releases/download/v0.0.6/zensols.actioncli-0.6-py3-none-any.whl',
    long_description = long_description,
    long_description_content_type = 'text/markdown',
    keywords = ['tooling'],
    classifiers = [],
)
