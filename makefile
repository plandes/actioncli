## makefile automates the build and deployment for python projects

PROJ_TYPE=	python

# make build dependencies
_ :=	$(shell [ ! -d .git ] && git init ; [ ! -d zenbuild ] && \
	  git submodule add https://github.com/plandes/zenbuild && make gitinit )

include ./zenbuild/main.mk

.PHONY:	runexecout
runexecout:
	make PY_SRC_TEST_PKGS=test_executor.TestExecutor.run_sleep_out test

.PHONY:	testclieenv
testclieenv:
	make PY_SRC_TEST_PKGS=test_actioncli.TestActionCli.test_env_conf_cli_env test

.PHONY:	testconfig
testconfig:
	make PY_SRC_TEST_PKGS=test_config.TestConfig test

.PHONY:	testpersist
testpersist:
	make PY_SRC_TEST_PKGS=test_persist.TestStash test

.PHONY:	testtask
testtask:
	make PY_SRC_TEST_PKGS=test_task.TestPersistTask test

.PHONY:	testtpopulate
testtpopulate:
	make PY_SRC_TEST_PKGS=test_populate test

.PHONY:	testfactory
testfactory:
	make PY_SRC_TEST_PKGS=test_configfactory test

.PHONY:	testtime
testtime:
	make PY_SRC_TEST_PKGS=test_time test

.PHONY:	testchunker
testchunker:
	make PY_SRC_TEST_PKGS=test_chunker test

.PHONY:	testhelpfmt
testhelpfmt:
	make PY_SRC_TEST_PKGS=test_help_format.TestHelpFormatter test
