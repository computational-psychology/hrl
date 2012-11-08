include ../../../make.inc

LIBUSB = libusb
LIBDPX = libdpx

CC = gcc
# get current python includes
PYINCLUDES= `python-config --includes`
FLAGS = -I$(LIBDPX) -I$(LIBUSB) -O3 -lm -Wall
PYFLAGS = -pthread -lGL -lrt
CFLAGS = -fno-strict-aliasing -fPIC

$(PYDIR)/datapixx.so : $(LIBDIR)/datapixx.o
	@echo "Building shared object"
	$(CC) $(FLAGS) $(CFLAGS) $(PYFLAGS) -shared $(LIBDIR)/datapixx.o  $(LIBDIR)/descriptors.o  $(LIBDIR)/error.o  $(LIBDIR)/libdpx.o  $(LIBDIR)/linux.o  $(LIBDIR)/usb.o -o $(PYDIR)/datapixx.so

$(LIBDIR)/datapixx.o : $(LIBDIR)/libdpx.o
	@echo "Building object file"
	$(CC) $(FLAGS) $(CFLAGS) $(PYFLAGS) -g -fwrapv $(PYINCLUDES) -I$(LIBDIR) -c datapixx.c -o $(LIBDIR)/datapixx.o

$(LIBDIR)/libdpx.o : $(LIBDIR)/descriptors.o  $(LIBDIR)/error.o  $(LIBDIR)/linux.o  $(LIBDIR)/usb.o
	@echo "Building DATAPixx API"
	$(CC) $(FLAGS) $(CFLAGS) -I$(LIBDIR) -c $(LIBDPX)/libdpx.c -o $(LIBDIR)/libdpx.o

$(LIBDIR)/descriptors.o :
	$(CC) $(FLAGS) $(CFLAGS) -c $(LIBUSB)/descriptors.c -o $(LIBDIR)/descriptors.o

$(LIBDIR)/error.o :
	$(CC) $(FLAGS) $(CFLAGS) -c $(LIBUSB)/error.c -o $(LIBDIR)/error.o

$(LIBDIR)/linux.o :
	$(CC) $(FLAGS) $(CFLAGS) -c $(LIBUSB)/linux.c -o $(LIBDIR)/linux.o

$(LIBDIR)/usb.o :
	$(CC) $(FLAGS) $(CFLAGS) -c $(LIBUSB)/usb.c -o $(LIBDIR)/usb.o

#install :
#	@echo "Installing datapixx extension module for Python"
#	cp datapixx.so /usr/lib/python2.5/site-packages/

all:
	datapixx.so

clean :
	@echo "removing .o and .so files"
	rm $(PYDIR)/datapixx.so
	rm $(LIBDIR)/datapixx.o
	rm $(LIBDIR)/libdpx.o
	rm $(LIBDIR)/descriptors.o
	rm $(LIBDIR)/error.o
	rm $(LIBDIR)/linux.o
	rm $(LIBDIR)/usb.o

#gcc -Wall -pthread -lGL -lrt -fno-strict-aliasing -g -fwrapv -fPIC -I./libdpx -I/usr/include/python2.5 -c datapixxmodule.c -o datapixx.o
#gcc -Wall -pthread -lGL -lrt -shared datapixx.o  descriptors.o  error.o  libdpx.o  linux.o  usb.o -o datapixx.so

#cp iconvcodec.py /usr/lib/python2.5/site-packages/
#cp datapixx.so /usr/lib/python2.5/site-packages/

