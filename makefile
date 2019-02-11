## makefile automates the build and deployment for python projects

PROJ_TYPE=	python

# make build dependencies
_ :=	$(shell [ ! -d .git ] && git init ; [ ! -d zenbuild ] && \
	  git submodule add https://github.com/plandes/zenbuild && make gitinit )

include ./zenbuild/main.mk

.PHONY:	runexecout
runexecout:
	make PY_SRC_TEST_PKGS=executor_test.TestExecutor.run_sleep_out test

.PHONY:	testclieenv
testclieenv:
	make PY_SRC_TEST_PKGS=actioncli_test.TestActionCli.test_env_conf_cli_env test

.PHONY:	testconfig
testconfig:
	make PY_SRC_TEST_PKGS=config_test.TestConfig test

.PHONY:	testpersist
testpersist:
	make PY_SRC_TEST_PKGS=persist_test.TestStash test
#	make PY_SRC_TEST_PKGS=persist_test test

.PHONY:	testtask
testtask:
	make PY_SRC_TEST_PKGS=task_test.TestPersistTask test

.PHONY:	testtpopulate
testtpopulate:
	make PY_SRC_TEST_PKGS=populate_test test

.PHONY:	testfactory
testfactory:
#	make PY_SRC_TEST_PKGS=configfactory_test test
	make PY_SRC_TEST_PKGS=configfactory_test.TestConfigFactory.test_multi_thread test
