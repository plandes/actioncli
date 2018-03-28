# Action and Mnemonic command line library

This library intends to make command line execution and configuration easy.
The library supports (among other features) an mnemonic centric way to
tie a command line an *action* to a Python 3 handler code segment.
Features include:

* Better command line parsing than [optparse].  This a binding to from a
  command line option using an action mnemonic to invocation of a handler.
* Better application level support for configuration than [configparser].
  Specifically, optional configuration and configuration groups.


## Obtaining

The easiest way to obtain this package is via [pip]:

```bash
pip install zensols.actioncli
```


## Usage

Two ways to use this project follow.  The easiest way is to use the template
method.  Either way, first install the library via [pip] or [easyinstall].


### Template

The best way to get started is to template out this project with the following
commands:

```bash
# clone the boilerplate repo
git clone https://github.com/plandes/template
# download the boilerplate tool
wget https://github.com/plandes/clj-mkproj/releases/download/v0.0.7/mkproj.jar
# create a python template and build it out
java -jar mkproj.jar config -s template/python
java -jar mkproj.jar
```


### Straight Python

If you want to skip templating it out (i.e. don't like Java), create a command
line module:

```python
from zensols.actioncli import OneConfPerActionOptionsCli
from zensols.actioncli import SimpleActionCli
from zensols.tools import HelloWorld

VERSION='0.1'

class ConfAppCommandLine(OneConfPerActionOptionsCli):
    def __init__(self):
        cnf = {'executors':
               [{'name': 'hello',
                 'executor': lambda params: HelloWorld(**params),
                 'actions':[{'name': 'doit',
                             'meth': 'print_message',
                             'opts': [['-m', '--message', True, # require argument
                                       {'dest': 'message', 'metavar': 'STRING',
                                        'help': 'a message to print'}]]}]}],
               # uncomment to add a configparse (ini format) configuration file
               # 'config_option': {'name': 'config',
               #                   'opt': ['-c', '--config', False,
               #                           {'dest': 'config', 'metavar': 'FILE',
               #                            'help': 'configuration file'}]},
               'whine': 1}
        super(ConfAppCommandLine, self).__init__(cnf, version=VERSION)

def main():
    cl = ConfAppCommandLine()
    cl.invoke()
```

See the [command line test cases](test/python/cmdop_test.py) for more examples.


## Changelog

An extensive changelog is available [here](CHANGELOG.md).


## License

Copyright © 2018 Paul Landes

Apache License version 2.0

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

[http://www.apache.org/licenses/LICENSE-2.0](http://www.apache.org/licenses/LICENSE-2.0)

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.


<!-- links -->
[pip]: https://pip.pypa.io/en/stable/
[easyinstall]: https://wiki.python.org/moin/EasyInstall
[configparser]: https://docs.python.org/3/library/configparser.html
[optparse]: https://docs.python.org/3/library/optparse.html
