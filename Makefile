include make.inc

DPXMAKE = src/graphics/datapixx
OPTMAKE = src/optics
HRLMAKE = src/hrl

all:
	mkdir -p $(PYDIR)
	mkdir -p $(LIBDIR)
	$(MAKE) -C $(DPXMAKE)
	$(MAKE) -C $(OPTMAKE)
	$(MAKE) -C $(HRLMAKE)

nodpx:
	mkdir -p $(PYDIR)
	touch $(PYDIR)/datapixx.py
	$(MAKE) -C $(OPTMAKE)
	$(MAKE) -C $(HRLMAKE)

clean:
	$(MAKE) clean -C $(DPXMAKE)
	$(MAKE) clean -C $(OPTMAKE)
	$(MAKE) clean -C $(HRLMAKE)
