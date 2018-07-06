## makefile automates the build and deployment for python projects

PROJ_TYPE=	python

#PY_SRC_TEST_PKGS=log_test.TestLogConf

# make build dependencies
_ :=	$(shell [ ! -d .git ] && git init ; [ ! -d zenbuild ] && \
	  git submodule add https://github.com/plandes/zenbuild && make gitinit )

include ./zenbuild/main.mk

.PHONY:	runexecout
runexecout:
	make PY_SRC_TEST_PKGS=executor_test.TestExecutor.run_sleep_out test
