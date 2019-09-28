# Change Log
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/)
and this project adheres to [Semantic Versioning](http://semver.org/).


## [Unreleased]


## [1.0.18] - 2019-09-28
## Added
- More Pythonic `dict` semantics for `Stash` classes.  Now they have the same
  API as a Python `dict`.
- Time out functionality: decorator and context managers to time out blocks and
  functions/methods.
- Minor configuration features.

## Changed
- Logging switches affect *only* the applications module for defined CLI
  packages as apposed to the entire Python logging system.  This cuts down a
  lot on the verbosity of the logging.  If no package is defined, the old
  default behavior is used.
- More `dict` semantics for stashes.


## [1.0.17] - 2019-07-31
## Added
- Robust configuration handling: derived configuration from resource files.
- Settable base configuration for `zensols.actioncli.Config`.
- `CacheStash` allows any backing stash.
- Now the CLI parser keeps parsed options and arguments to downstream pipeline
  processing.


## [1.0.16] - 2019-07-25
### Added
- Moved `test.py` from [zensols.dltools] to this repository to.

### Changed
- Fixed abstract class usage.  Now the interpreter will complain if you don't
  fully implement an abstract class.


## [1.0.15] - 2019-07-06
### Added
- Feature to allow CLI clients to create executors.
- Key limit stash for debugging.
- Stash based multi-process library.
### Removed
- Superfluous multi-threaded stash.


## [1.0.14] - 2019-06-23
### Added
- CLI created executors.


## [1.0.13 - 2019-05-27]
## Changed
- Documentation.
- Better error message on missing config file.
- Rid YAML deprecation warnings and upgrade.


## [1.0.12 - 2019-03-24]
### Added 
- Class importer.
- Better persist semantics.


## [1.0.11] - 2019-02-03
### Added
- Multithreading Stash.


## [1.0.10] - 2019-11-26
### Added
- Cache framework.


## [1.0.9] - 2018-09-20
### Changed
- Better options handling.


## [1.0.8] - 2018-09-14
### Changes
- CLI bug fix.
- Move to zensols.pybuild for build/release.


## [1.0.7] - 2018-09-14
### Changes
- Environment configuration with resource files bug fixes and extensions.
- More documentation and test cases to show how to use the environment based
  CLI driver classes.


## [1.0.6] - 2018-09-01
### Changes
- Package not found for out of order init order.


## [1.0.5] - 2018-08-31
### Changes
- Bug fix in YAML parser.
- Get version from pkg_resources instead of from a hard coded string.


## [1.0.3] - 2018-08-18
### Changes
- Requirements in setup.


## [1.0.2] - 2018-08-18
### Changes
- Yaml bug fix: priority of default variables to mimic ConfigParser.


## [1.0.1] - 2018-08-18
### Changes
- Yaml configuration bug fixes.
- Backward compat with ini version of config parser.


## [1.0.0] - 2018-08-18
### Added
- Command line help is now much more readable

### Changed
- Fix yaml bug on list processing


## [0.0.5] - 2018-07-21
### Added
- Opt in short list option like whine.


## [0.0.4] - 2018-07-05
### Added
- General utility logging functionality.
- OS System execution with logging.


## [0.0.3] - 2018-06-27
### Added
- Configuration type (list, boolean) parameter parsing.
- Contribution file.
- Travis

### Changed
- Move to MIT license.


## [0.0.2] - 2018-05-21
### Changed
- Overridable short option listing configuration.


## [0.0.1] - 2018-03-27
### Added
- Initial version


[Unreleased]: https://github.com/plandes/actioncli/compare/v1.0.18...HEAD
[1.0.18]: https://github.com/plandes/actioncli/compare/v1.0.17...v1.0.18
[1.0.17]: https://github.com/plandes/actioncli/compare/v1.0.16...v1.0.17
[1.0.16]: https://github.com/plandes/actioncli/compare/v1.0.15...v1.0.16
[1.0.15]: https://github.com/plandes/actioncli/compare/v1.0.14...v1.0.15
[1.0.14]: https://github.com/plandes/actioncli/compare/v1.0.13...v1.0.14
[1.0.13]: https://github.com/plandes/actioncli/compare/v1.0.12...v1.0.13
[1.0.12]: https://github.com/plandes/actioncli/compare/v1.0.11...v1.0.12
[1.0.11]: https://github.com/plandes/actioncli/compare/v1.0.10...v1.0.11
[1.0.10]: https://github.com/plandes/actioncli/compare/v1.0.9...v1.0.10
[1.0.9]: https://github.com/plandes/actioncli/compare/v1.0.8...v1.0.9
[1.0.8]: https://github.com/plandes/actioncli/compare/v1.0.7...v1.0.8
[1.0.7]: https://github.com/plandes/actioncli/compare/v1.0.6...v1.0.7
[1.0.6]: https://github.com/plandes/actioncli/compare/v1.0.5...v1.0.6
[1.0.5]: https://github.com/plandes/actioncli/compare/v1.0.4...v1.0.5
[1.0.4]: https://github.com/plandes/actioncli/compare/v1.0.3...v1.0.4
[1.0.3]: https://github.com/plandes/actioncli/compare/v1.0.2...v1.0.3
[1.0.2]: https://github.com/plandes/actioncli/compare/v1.0.1...v1.0.2
[1.0.1]: https://github.com/plandes/actioncli/compare/v1.0.0...v1.0.1
[1.0.0]: https://github.com/plandes/actioncli/compare/v0.0.6...v1.0.0
[0.0.5]: https://github.com/plandes/actioncli/compare/v0.0.4...v0.0.5
[0.0.4]: https://github.com/plandes/actioncli/compare/v0.0.3...v0.0.4
[0.0.3]: https://github.com/plandes/actioncli/compare/v0.0.2...v0.0.3
[0.0.2]: https://github.com/plandes/actioncli/compare/v0.0.1...v0.0.2

[zensols.dltools]: https://github.com/plandes/dltools
