import os
from os import path
from setuptools import setup

README_FILE = 'README.md'
REQUIREMENTS_FILE = 'requirements.txt'


def get_packages(dnames):
    dirs = []
    for dname in dnames:
        for root, subdirs, files in os.walk(dname):
            root = path.relpath(root, dname)
            if root != '.':
                dirs.append(path.join(dname, root.replace(os.sep, '.')))
    return dirs


def get_curpath():
    return path.abspath(path.join(path.dirname(__file__)))


def get_root_dir():
    nname, dname = None, get_curpath()
    while nname != dname:
        nname, dname = dname, path.abspath(path.join(dname, path.pardir))
        if path.exists(path.join(dname, README_FILE)):
            break
    return dname


def get_long_description():
    dname = get_root_dir()
    with open(path.join(dname, README_FILE), encoding='utf-8') as f:
        return f.read()


def get_requires():
    req_file = path.join(path.dirname(__file__), REQUIREMENTS_FILE)
    with open(req_file, encoding='utf-8') as f:
        return [x.strip() for x in f.readlines()]

setup(
    name = "zensols.actioncli",
    packages=get_packages(['zensols']),
    version = '1.0.6',
    description = 'This library intends to make command line execution and configuration easy.',
    author = 'Paul Landes',
    author_email = 'landes@mailc.net',
    url = 'https://github.com/plandes/actioncli',
    download_url = 'https://github.com/plandes/actioncli/releases/download/v1.0.6/zensols.actioncli-1.0.6-py3-none-any.whl',
    long_description=get_long_description(),
    long_description_content_type = 'text/markdown',
    keywords = ['tooling'],
    classifiers = [],
    install_requires = [
        'configparser==3.5.0',
        'PyYAML>=3.12',
    ],
)
