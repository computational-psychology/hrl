#!/usr/bin/env python
#coding: CP1250



import serial


DEBUG_MODE = False

error_codes = {"00": 'Command error',\
               "01": 'Setting error',\
               "11": 'Memory value error',\
               "10": 'Measuring range over',\
               "19": 'Display range over',\
               "20": 'EEPROM error',\
               "30": 'Battery exhausted'}

class Minolta:
    def __init__(self,portnum=1,timeout=10):
        self.port = serial.Serial(portnum,4800,bytesize=7,parity=serial.PARITY_EVEN,stopbits=2,timeout=timeout)
        if DEBUG_MODE:
            print 'Using:', self.port.portstr
            print 'isOpen():', self.port.isOpen()
        self.port.flush()
        
    def getLuminance(self):
        self.port.write("MES\r\n")
        res = self.port.readline()
        if DEBUG_MODE: print 'res:', res
        if res[:2] == 'OK':
            if DEBUG_MODE:
                print 'luminance: %s cd/m^2' % res.split()[-1]
            return float(res.split()[-1])
        elif res[:2] == 'ER':
            err = res.strip()[2:]
            return error_codes[err]
        
    def getDisplay(self):
        self.port.write("DSR\r\n")
        res = self.port.readline()
        if DEBUG_MODE:
            print 'DSR:', res
        if res[:2] == 'OK':
            return float(res.split()[-1])
        elif res[:2] == 'ER':
            err = res.strip()[2:]
            return error_codes[err]

    def setMode(self,mode):
        self.port.write("MDS%s\r\n" % (`mode`.zfill(2)))
        res = self.port.readline()
        if DEBUG_MODE:
            print 'MDS:', res
        if res[:2] == 'OK':
            return 0
        elif res[:2] == 'ER':
            err = res.strip()[2:]
            return error_codes[err]

    def clearMem(self):
        self.port.write("CLE\r\n")
        res = self.port.readline()
        if DEBUG_MODE:
            print "CLE:", res
        if res[:2] == 'OK':
            return 0
        elif res[:2] == 'ER':
            err = res.strip()[2:]
            return error_codes[err]

    def close(self):
        self.port.close()


if __name__ == "__main__":

    photometer = Minolta()
    lum = photometer.getLuminance()
    print 'luminance:', lum
    photometer.close()

##    if lum != -7:
##        print 'Current luminance:', lum
##    else:
##        print 'Error'
