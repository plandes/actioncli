## makefile automates the build and deployment for python projects

PROJ_TYPE=	python

# make build dependencies
_ :=	$(shell [ ! -d .git ] && git init ; [ ! -d zenbuild ] && \
	  git submodule add https://github.com/plandes/zenbuild && make gitinit )

include ./zenbuild/main.mk

#PY_SRC_TEST_PKGS=cmdop_test.TestCommandOpTest
