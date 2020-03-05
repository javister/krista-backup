ifneq ($(shell which python3.7),)
	PYTHON	:=	python3.7
else
	PYTHON	:=	python3
endif

BUILDDIR	=	docs
SPHINXOPTS	=
SPHINXBUILD	=	sphinx-build
SPHINXPROJ	=	KristaBackup
SOURCEDIR	=	docs/source

python_version_full := $(wordlist 2,4,$(subst ., ,$(shell python --version 2>&1)))
python_version_major := $(word 1,${python_version_full})

# Put it first so that "make" without argument is like "make help".
sphinx_help:
	@$(SPHINXBUILD) -M help "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

build_docs:
	@$(SPHINXBUILD) -M text "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)
	@$(SPHINXBUILD) -M html "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)
	@$(SPHINXBUILD) -M markdown "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O) "$(SOURCEDIR)/index.rst"
	mv $(BUILDDIR)/markdown/index.md ../README.md
	rm -rf $(BUILDDIR)/markdown
	rm -rf $(BUILDDIR)/doctrees
	rm -rf $(BUILDDIR)/html/_sources

build_wrapped:
	$(PYTHON) build.py

.PHONY: help Makefile

# Catch-all target: route all unknown targets to Sphinx using the new
# "make mode" option.  $(O) is meant as a shortcut for $(SPHINXOPTS).
#%: Makefile
#	@$(SPHINXBUILD) -M $@ "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)
