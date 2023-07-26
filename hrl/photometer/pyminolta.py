#!/usr/bin/env python
# coding: CP1250
import serial

DEBUG_MODE = False


error_codes = {
    b"00": "Command error",
    b"01": "Setting error",
    b"11": "Memory value error",
    b"10": "Measuring range over",
    b"19": "Display range over",
    b"20": "EEPROM error",
    b"30": "Battery exhausted",
}


class MinoltaException(BaseException):
    def __init__(self, value):
        self.parameter = value

    def __str__(self):
        return repr(self.parameter)


class Minolta:
    def __init__(self, portnum=1, timeout=10):
        self.port = serial.Serial(
            portnum, 4800, bytesize=7, parity=serial.PARITY_EVEN, stopbits=2, timeout=timeout
        )
        if DEBUG_MODE:
            print("Using:", self.port.portstr)
            print("isOpen():", self.port.isOpen())
        self.port.flush()

    def getLuminance(self):
        self.port.write(b"MES\r\n")
        res = self.port.readline()
        if DEBUG_MODE:
            print("res:", res)
        if res[0:2] == b"OK":
            if DEBUG_MODE:
                print("luminance: %s cd/m^2" % res.split()[-1])
            return float(res.split()[-1])
        elif res[:2] == b"ER":
            err = res.strip()[2:]
            raise MinoltaException(error_codes[err])
        else:
            # Data is corrupt or absent
            raise MinoltaException("Data Link Error")

    def getDisplay(self):
        self.port.write(b"DSR\r\n")
        res = self.port.readline()
        if DEBUG_MODE:
            print("DSR:", res)
        if res[:2] == b"OK":
            return float(res.split()[-1])
        elif res[:2] == b"ER":
            err = res.strip()[2:]
            return error_codes[err]

    def setMode(self, mode):
        self.port.write(b"MDS%s\r\n" % (mode.zfill(2)))
        res = self.port.readline()
        if DEBUG_MODE:
            print(b"MDS:", res)
        if res[:2] == b"OK":
            return 0
        elif res[:2] == b"ER":
            err = res.strip()[2:]
            return error_codes[err]

    def clearMem(self):
        self.port.write(b"CLE\r\n")
        res = self.port.readline()
        if DEBUG_MODE:
            print("CLE:", res)
        if res[:2] == b"OK":
            return 0
        elif res[:2] == b"ER":
            err = res.strip()[2:]
            return error_codes[err]

    def close(self):
        self.port.close()


if __name__ == "__main__":
    photometer = Minolta("/dev/ttyUSB0")
    try:
        photometer.getDisplay()
        lum = photometer.getLuminance()
        print("luminance:", lum)
    except MinoltaException as instance:
        print("caught error:", instance.parameter)

    photometer.close()

##    if lum != -7:
##        print 'Current luminance:', lum
##    else:
##        print 'Error'
