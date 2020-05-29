BUILDDIR	=	docs
SPHINXOPTS	=
SPHINXBUILD	=	sphinx-build
SPHINXPROJ	=	KristaBackup
SOURCEDIR	=	docs/source

.PHONY: build

build:
	mkdir -p build 
	docker build -f Dockerfile --no-cache -t kb_builder .
	docker run --rm -v "$(shell pwd)/build:/build" kb_builder

update_docs:
	@$(SPHINXBUILD) -M text "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)
	@$(SPHINXBUILD) -M html "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)
	@$(SPHINXBUILD) -M markdown "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O) "$(SOURCEDIR)/index.rst"
	mv $(BUILDDIR)/markdown/index.md README.md
	rm -rf $(BUILDDIR)/markdown
	rm -rf $(BUILDDIR)/doctrees
	rm -rf $(BUILDDIR)/html/_sources
