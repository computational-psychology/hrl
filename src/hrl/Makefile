include ../../make.inc

$(PYDIR)/hrl/user.py: hrl/user.py $(PYDIR)/hrl/lut.py $(PYDIR)/hrl/core.py
	cp hrl/user.py $(PYDIR)/hrl

$(PYDIR)/hrl/lut.py: hrl/lut.py $(PYDIR)/hrl/__init__.py
	cp hrl/lut.py $(PYDIR)/hrl

$(PYDIR)/hrl/core.py: hrl/core.py $(PYDIR)/hrl/__init__.py
	cp hrl/core.py $(PYDIR)/hrl

$(PYDIR)/hrl/__init__.py: hrl/__init__.py $(PYDIR)/__init__.py
	mkdir -p $(PYDIR)/hrl
	cp hrl/__init__.py $(PYDIR)/hrl

$(PYDIR)/__init__.py: __init__.py
	cp __init__.py $(PYDIR)

all:
	$(PYDIR)/hrl/user.py

clean :
	rm $(PYDIR)/__init__.py
	rm -r $(PYDIR)/hrl
