# Minimal makefile for Sphinx documentation
#

# You can set these variables from the command line, and also
# from the environment for the first two.
SPHINXOPTS    ?=
SPHINXBUILD   ?= sphinx-build
SOURCEDIR     = .
BUILDDIR      = _build

# Put it first so that "make" without argument is like "make help".
help:
	@$(SPHINXBUILD) -M help "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)
	@echo
	@echo "Custom targets:"
	@echo "  zh          to build Chinese documentation"
	@echo "  en          to build English documentation"
	@echo "  all         to build documentation for all supported languages"

# Multi-language build
all: zh en

# Chinese build
zh:
	@$(SPHINXBUILD) -M latexpdf "$(SOURCEDIR)" "$(BUILDDIR)" && \
	 $(SPHINXBUILD) -M html "$(SOURCEDIR)" "$(BUILDDIR)"

# English build
en:
	@$(SPHINXBUILD) -b latex "$(SOURCEDIR)" "$(BUILDDIR)/latex/en" -D language=en && \
	 make -C "$(BUILDDIR)/latex/en" all-pdf && \
	 $(SPHINXBUILD) -b html "$(SOURCEDIR)" "$(BUILDDIR)/html/en" -D language=en

.PHONY: help all zh en Makefile

# Catch-all target: route all unknown targets to Sphinx using the new
# "make mode" option.  $(O) is meant as a shortcut for $(SPHINXOPTS).
%: Makefile
	@$(SPHINXBUILD) -M $@ "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)
