/*
 *	DATAPixx cross-platform low-level C programming library
 *	Created by Peter April.
 *	Copyright (C) 2008-2012 Peter April, VPixx Technologies
 *	
 *	This library is free software; you can redistribute it and/or
 *	modify it under the terms of the GNU Library General Public
 *	License as published by the Free Software Foundation; either
 *	version 2 of the License, or (at your option) any later version.
 *	
 *	This library is distributed in the hope that it will be useful,
 *	but WITHOUT ANY WARRANTY; without even the implied warranty of
 *	MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
 *	Library General Public License for more details.
 *	
 *	You should have received a copy of the GNU Library General Public
 *	License along with this library; if not, write to the
 *	Free Software Foundation, Inc., 51 Franklin St, Fifth Floor,
 *	Boston, MA  02110-1301, USA.
 *
 */

// Maximum number of USB bulk I/O retries
#define MAX_RETRIES	4

// Set to 1 to enable console debugging output from EZ to host.
// Must match setting in EZ firmware.
#define	ENABLE_CONSOLE	0



#include <stdio.h>
#include <string.h>
#include <math.h>
#include <ctype.h>

#include "libdpx.h"		// user API.  Make sure to include libdpx src folder in user include path
#include "usb.h"		// Must be from libusb, not OS, so  make sure libusb is in user include path

/************************************************************************************/
/*																					*/
/*	Here we start to define low-level interfaces not presented in lib_datapixx.h	*/
/*																					*/
/************************************************************************************/


int		dpxInitialized = 0;								// Has to be global so that libusb can be initialized without necessarily opening a DATAPixx; eg; for usb_scan command
int		dpxError = 0;									// A global function error code
int		dpxDebugLevel = 0;								// 0/1/2 controls level of debug output
int		dpxActivePSyncTimeout = -1;						// When not -1, gives the current psync register readback timeout.
UInt16	dpxSavedRegisters[DPX_REG_SPACE/2] = { 0 };		// Local copy of DATAPixx register for save/restore
UInt16	dpxRegisterCache[DPX_REG_SPACE/2] = { 0 };		// Must be 16-bit, because I use memcpy from USB tram
int		dpxRegisterModified[DPX_REG_SPACE/2] = { 0 };

// Keep track of the total number of USB bulk I/O retries/fails for each endpoint and direction
int		dpxEp1WrRetries = 0;
int		dpxEp1RdRetries = 0;
int		dpxEp2WrRetries = 0;
int		dpxEp6RdRetries = 0;
int		dpxEp1WrFails = 0;
int		dpxEp1RdFails = 0;
int		dpxEp2WrFails = 0;
int		dpxEp6RdFails = 0;

// USB interface stuff
struct usb_device	*dpxDev = NULL;
usb_dev_handle		*dpxHdl = NULL;
int					dpxRawUsb = 0;						// Non-0 if a detected DP has no EZ-USB firmware
int					dpxGoodFpga = 0;					// Non-0 if system has a well-configured FPGA
int					dpxIsViewpixx = 0;					// Non-0 if a detected peripheral is actually a VIEWPixx
int					dpxIsPropixx = 0;					// Non-0 if a detected peripheral is actually a PROPixx

int nEP1Writes = 0;
int nEP1Reads = 0;

// Largest EP1 trams are 265 bytes for SPI page R/W:
//	   4 bytes for tram header
//	+  4 bytes for SPI cmd/addr1/addr2/addr3
//	+256 bytes for SPI page data
//  +  1 byte delay in SPI fast readback command
// That's a payload of 261 bytes
unsigned char ep1in_Tram[265];
unsigned char ep1out_Tram[265];

// We will limit other endpoint trams to 64k bytes long.
// This means that the maximum payload size is 65536 - 4-byte header = 65532 bytes.
unsigned char ep2out_Tram[65536];
unsigned char ep6in_Tram[65536];

// FPGA configuration data buffers
unsigned char configBuffer[CONFIG_BUFFER_SIZE];
unsigned char configBuffer2[CONFIG_BUFFER_SIZE];

// We'll cache CODEC I2C registers for (optional) faster readback.
// Try to initialize cache to the actual reset values.
unsigned char cachedCodecRegs[128] = {
	0x00, 0x00, 0x22, 0x20, 0x04, 0x00, 0x00, 0x6A, 0x00, 0x4E, 0x00, 0xE1, 0x00, 0x00, 0x00, 0x50,
	0x50, 0xFF, 0xFF, 0x04, 0x78, 0x78, 0x04, 0x78, 0x78, 0x44, 0x00, 0xFE, 0x00, 0x00, 0xFE, 0x00,
	0x00, 0x00, 0x00, 0x00, 0xCC, 0xE0, 0x1C, 0x00, 0x80, 0x00, 0x8C, 0x00, 0x00, 0x00, 0x00, 0xA8,
	0x00, 0x00, 0x00, 0x0B, 0x00, 0x00, 0x80, 0x00, 0x00, 0x80, 0x0B, 0x00, 0x00, 0x00, 0x00, 0x00,
	0xA8, 0x0B, 0x00, 0x00, 0x00, 0x00, 0x00, 0x80, 0x0B, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
	0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0xC6, 0x0C,
	0x00, 0x00, 0x00, 0x00, 0x00, 0x01, 0x02, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
	0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00
};

int gSpifEnable = 1;                    // Enable fast FPGA SPI access


void EZUploadRam(unsigned char *buf, int start, int len)
{
	int i;
	int tlen;
	int quanta=16;
	int a;

	CheckUsb();
	for(i=start;i<start+len;i+=quanta) {
		tlen = len+start-i;
		if (tlen > quanta)
			tlen = quanta;
		a = usb_control_msg(dpxHdl, 0x40, 0xa0, i, 0, (char*)(buf+(i-start)), tlen, 1000);
		if (a < 0)
			return;
	}
}


// Can't write the SFR's, but CAN write the CPU RESET bit.
// Uses EP0, so might not maintain order wrt EZWriteByte, which uses EP1.
void EZUploadByte(int addr, unsigned char val)
{
	EZUploadRam(&val, addr, 1);
}


int EZWriteByte(unsigned short addr, unsigned char val)
{
	unsigned char buffer[7];
	buffer[0] = '^';
	buffer[1] = EP1OUT_WRITEBYTE;
	buffer[2] = 3;
	buffer[3] = 0;
	buffer[4] = LSB(addr);
	buffer[5] = MSB(addr);
	buffer[6] = val;
	if (EZWriteEP1Tram(buffer, 0, 0)) {
		DPxDebugPrint0("ERROR: EZWriteByte() call to EZWriteEP1Tram() failed\n");
		return -1;
	}
	return 0;
}


// Read a single byte from EZ memory.
// Return the byte value (0-255), or -1 if an error.
int EZReadByte(unsigned short addr)
{
	unsigned char buffer[6];
	buffer[0] = '^';
	buffer[1] = EP1OUT_READBYTE;
	buffer[2] = 2;
	buffer[3] = 0;
	buffer[4] = LSB(addr);
	buffer[5] = MSB(addr);
	if (EZWriteEP1Tram(buffer, EP1IN_READBYTE, 1)) {
		DPxDebugPrint0("ERROR: EZReadByte() call to EZWriteEP1Tram() failed\n");
		return -1;
	}
	return ep1in_Tram[4];
}


// Write a byte to an EZ-USB Special Function Register.
// Return -1 if there was an error.
int EZWriteSFR(unsigned char addr, unsigned char val)
{
	unsigned char buffer[6];
	buffer[0] = '^';
	buffer[1] = EP1OUT_WRITEBYTE;
	buffer[2] = 2;
	buffer[3] = 0;
	buffer[4] = addr;
	buffer[5] = val;
	if (EZWriteEP1Tram(buffer, 0, 0)) {
		DPxDebugPrint0("ERROR: EZWriteSFR() call to EZWriteEP1Tram() failed\n");
		return -1;
	}
	return 0;
}


// Read a byte from an EZ-USB Special Function Register.
// Return the byte value (0-255), or -1 if an error.
int EZReadSFR(unsigned char addr)
{
	unsigned char buffer[5];
	buffer[0] = '^';
	buffer[1] = EP1OUT_READBYTE;
	buffer[2] = 1;
	buffer[3] = 0;
	buffer[4] = addr;
	if (EZWriteEP1Tram(buffer, EP1IN_READBYTE, 1)) {
		DPxDebugPrint0("ERROR: EZReadSFR() call to EZWriteEP1Tram() failed\n");
		return -1;
	}
	return ep1in_Tram[4];
}


// Write a tram to EP1OUT, and read EP1IN at least once to see if there's any console data.
// Optionally wait for a response tram whose code is passed in rxTramCode.
// Returns 0 for success, or -1 error if:
//	-EP1OUT write failed.
//	-EP1IN read failed.
//	-expectedRxTram was non-0 (indicating an expected Rx message), but the Rx tram had the wrong code.
int EZWriteEP1Tram(unsigned char* txTram, unsigned char expectedRxTram, int expectedRxLen)
{
	int packetSize;
	int nTxBytes = 4 + txTram[2] + (txTram[3] << 8);									// Number of bytes to transmit
	int iRetry;
#if ENABLE_CONSOLE
	int readEP1 = (txTram[1] != EP1OUT_RESET);
#else
	int readEP1 = expectedRxTram;
#endif

	CheckUsb();
	while (nTxBytes) {
		packetSize = nTxBytes >= 64 ? 64 : nTxBytes;									// EZ EP1 only supports 64 byte packets
		for (iRetry = 0; ; iRetry++) {
            nEP1Writes++;
			if (usb_bulk_write(dpxHdl, 1, (char*)txTram, packetSize, 1000) == packetSize)
				break;
			else if (iRetry < MAX_RETRIES) {
				DPxDebugPrint1("ERROR: EZWriteEP1Tram() bulk write retried: %s\n", usb_strerror());
				dpxEp1WrRetries++;
			}
			else {
				DPxDebugPrint1("ERROR: EZWriteEP1Tram() bulk write failed: %s\n", usb_strerror());
				dpxEp1WrFails++;
				return -1;
			}
		}
		txTram += packetSize;
		nTxBytes -= packetSize;
	}

	// Do at least one EP1IN read to catch EZ console output, unless the tram we just sent is resetting the EZ.
	if (readEP1 && EZReadEP1Tram(expectedRxTram, expectedRxLen) < 0) {
		DPxDebugPrint0("ERROR: EZWriteEP1Tram() call to EZReadEP1Tram() failed\n");
		return -1;
	}
	return 0;
}


// EZReadEP1Tram() reads a tram from the EZUSB EP1IN endpoint.
// There are 2 modes of operation, depending on the value of the "expectedTram" argument:
// 1) If expectedTram = 0, then EZReadEP1Tram() operates in a look-ahead mode.
// EZReadEP1Tram() is called often in this mode (even when no trams are expected) and the function should return as quicky as possible.
// Individual USB reads should typically be pretty snappy because EZ FW keeps stuffing empty EP1IN pipe with flush trams.
// This mode does a maximum of 1 read from EZ, printing any returned console trams.
// If a data tram is received, it is cached and its tram code is returned.
// The cached tram will be returned again the next time EZReadEP1Tram() is called.
// Otherwise EZReadEP1Tram() returns 0 if no data trams are available, or a negative error code.
// 2) If expectedTram != 0, then EZReadEP1Tram() will wait until a data tram is received, or a timeout occurs.
// If a data tram is received, and its tram code equals expectedTram, EZReadEP1Tram() returns 0.
// All other cases return an error code.
int EZReadEP1Tram(unsigned char expectedTram, int expectedLen)
{
	static char packet[64];				// Largest possible EP1 USB packet
	static int	packetLength	= 0;
	static int	packetRdIndex	= 0;
	static int	tramWrIndex		= 0;
	static int	tramLen			= 0;	// The length of the payload
	static int	cached			= 0;
	int iRetry;

	// Do we already have a tram cached from a previous call to EZReadEP1Tram(0) ?
	if (cached) {
		if (expectedTram == 0)
			return ep1in_Tram[1];								// Next caller will get same tram
		cached = 0;
		if (ep1in_Tram[1] != expectedTram) {
			DPxDebugPrint2("ERROR: EZReadEP1Tram() received tram code [%d] instead of [%d]\n", (int)ep1in_Tram[1], (int)expectedTram);
			return -1;
		}
		if (tramLen != expectedLen) {
			DPxDebugPrint2("ERROR: EZReadEP1Tram() received tram length [%d] instead of [%d]\n", tramLen, expectedLen);
			return -1;
		}
		return 0;
	}

	// Each iteration either reads a new 64 byte USB packet, or starts a new tram
	CheckUsb();
	while (1) {
		// If we're out of data, or we had an error, read another packet.
		// If the EZ FW is still alive, it should always return pretty quickly with at least a flush packet;
		// otherwise, FW is toast, or breakdown in USB communications.
		if (packetLength <= 0) {
			for (iRetry = 0; ; iRetry++) {
                nEP1Reads++;
				packetLength = usb_bulk_read(dpxHdl, 0x81, packet, 64, 1000);
				if (packetLength > 0)
					break;
				else if (iRetry < MAX_RETRIES) {
					DPxDebugPrint1("ERROR: EZReadEP1Tram() bulk read failed with [%d], retrying...\n", packetLength);
					dpxEp1RdRetries++;
				}
				else {
					DPxDebugPrint1("ERROR: EZReadEP1Tram() bulk read failed with [%d]\n", packetLength);
					dpxEp1RdFails++;
					return packetLength;
				}
			}

			packetRdIndex = 0;			// We start reading the new packet from index 0
		}

		// Each iteration copies 1 byte from the USB packet to the tram.
		while (packetLength) {
			ep1in_Tram[tramWrIndex++] = packet[packetRdIndex++];	// Copy the byte from the USB packet to the tram
			packetLength--;

			// If there's a framing error, flush byte and keep scanning for hat
			if (tramWrIndex == 1 && ep1in_Tram[0] != '^') {
				DPxDebugPrint1("ERROR: EZReadEP1Tram() framing error [%d]\n", (int)ep1in_Tram[0]);
				while (packetLength && packet[packetRdIndex] != '^') {	// Try to only print 1 error message per framing error
					packetLength--;
					packetRdIndex++;
				}
				tramWrIndex = 0;
				return -1;
			}

			if (tramWrIndex == 4)
				tramLen = ep1in_Tram[2] + (ep1in_Tram[3] << 8);

			// The tram ends as soon as we've received the payload
			if (tramWrIndex >= 4 && tramWrIndex == tramLen + 4) {
				tramWrIndex = 0;										// Next tram will start writing at start of buffer
				if (ep1in_Tram[1] == EP1IN_CONSOLE)						// Filter out and print console trams
					EZPrintConsoleTram(ep1in_Tram);
				else if (ep1in_Tram[1] == EP1OUT_FLUSH)					// Ignore flush trams
					(void)0;
				else if (expectedTram) {								// We're looking for a specific tram
					if (ep1in_Tram[1] != expectedTram) {
						DPxDebugPrint2("ERROR: EZReadEP1Tram() received tram code [%d] instead of [%d]\n", (int)ep1in_Tram[1], (int)expectedTram);
						return -1;
					}
					if (tramLen != expectedLen) {
						DPxDebugPrint2("ERROR: EZReadEP1Tram() received tram length [%d] instead of [%d]\n", tramLen, expectedLen);
						return -1;
					}
					return 0;
				}
				else {
					cached = 1;
					return ep1in_Tram[1];								// Next caller will get same tram
				}
			}
		}	// while (packetLength)

		// If we get here, we've used up the current packet, but have no data tram assembled yet.
		// Under some circumstances, usb_bulk_read can stick for the entire timeout time.
		// (I'm not sure where I saw this.  Might have been due to a bug of mine).
		// In any case, if we're not actually looking for a command to process (expectedTram == 0),
		// then get back to caller ASAP.
		if (expectedTram == 0)
			return 0;
	}
	return 0;	// Make compiler happy
}


// Write a tram to EP2OUT, and optionally wait for a response tram whose code is passed in rxTramCode.
// Returns 0 for success, or -1 error if:
//	-EP2OUT write failed.
//	-EP6IN read failed.
//	-expectedRxTram was non-0 (indicating an expected Rx message), but the Rx tram had the wrong code.
int EZWriteEP2Tram(unsigned char* txTram, unsigned char expectedRxTram, int expectedRxLen)
{
	int packetSize;
	int nTxBytes = 4 + txTram[2] + (txTram[3] << 8);									// Number of bytes to transmit
	int iRetry;

	// There seems to be a bug when requesting a memory read.
	// If the resulting returned message's length is a multiple of 512 bytes,
	// there's a mismatch in someone's handshaking.
	// I've also seen references to this on the web.
	// The EZ should follow the full packet with a 0-length packet indicating that the msg is over.
	// It does do this (at least it's programmed to do to), but OS X still mixes it up.
	// I will get over this by simply detecting requests which would result in a x512 result,
	// and bumping up the request length by 2 bytes.
	if (txTram[1] == EP2OUT_READRAM && txTram[8] == 0xfc && (txTram[9] & 1)) {
		txTram[8] += 2;
		expectedRxLen += 2;
	}

	CheckUsb();
	while (nTxBytes) {
	
		// Allowing total size gives write bandwidth approaching 30 MBps.
		// FYI, limiting maximum size to 512B reduces write bandwidth to about 4 MBps.
		// Limiting maximum size to 100B reduces write bandwidth to about 0.2 MBps.
		packetSize = nTxBytes;

		for (iRetry = 0; ; iRetry++) {
			if (usb_bulk_write(dpxHdl, 2, (char*)txTram, packetSize, 1000) == packetSize)
				break;
			else if (iRetry < MAX_RETRIES) {
				DPxDebugPrint1("ERROR: EZWriteEP2Tram() bulk write retried: %s\n", usb_strerror());
				dpxEp2WrRetries++;
			}
			else {
				DPxDebugPrint1("ERROR: EZWriteEP2Tram() bulk write failed: %s\n", usb_strerror());
				dpxEp2WrFails++;
				return -1;
			}
		}
		txTram += packetSize;
		nTxBytes -= packetSize;
	}

	// Read from EP6IN if requested
	if (expectedRxTram && EZReadEP6Tram(expectedRxTram, expectedRxLen) < 0) {
		DPxDebugPrint0("ERROR: EZWriteEP2Tram() call to EZReadEP6Tram() failed\n");
		return -1;
	}
	return 0;
}

#if 1
// EZReadEP6Tram() reads a tram from the EZUSB EP6IN endpoint.
// If a data tram is received, and its tram code equals expectedTram, EZReadEP6Tram() returns 0.
// All other cases return an error code.
int EZReadEP6Tram(unsigned char expectedTram, int expectedLen)
{
	int	reqLength, tramLen, packetLength;
	int iRetry;
	int timeout;
	
	// Default USB read timeout will be 1 second.
	// Watch out though.  If this read is behind a pixel sync, the timeout could be much larger.
	// We'll estimate the maximum psync timeout consertively, assuming a 60 Hz refresh rate.
	timeout = 5000;
	if (dpxActivePSyncTimeout != -1)
		timeout = dpxActivePSyncTimeout / 60.0 * 1000;

	reqLength = expectedLen + 4;
	CheckUsb();
	for (iRetry = 0; ; iRetry++) {
		packetLength = usb_bulk_read(dpxHdl, 0x86, (char*)ep6in_Tram, reqLength, timeout);
		if (packetLength == reqLength)
			break;
		else if (iRetry < MAX_RETRIES) {
			DPxDebugPrint2("ERROR: EZReadEP6Tram() bulk read returned [%d] instead of [%d] bytes, retrying...\n", packetLength, reqLength);
			dpxEp6RdRetries++;
		}
		else {
			DPxDebugPrint2("ERROR: EZReadEP6Tram() bulk read returned [%d] instead of [%d] bytes, failed\n", packetLength, reqLength);
			dpxEp6RdFails++;
			return -1;
		}
	}

	if (ep6in_Tram[0] != '^') {
		DPxDebugPrint1("ERROR: EZReadEP6Tram() framing error [%d]\n", (int)ep6in_Tram[0]);
		return -1;
	}
	if (ep6in_Tram[1] != expectedTram) {
		DPxDebugPrint2("ERROR: EZReadEP6Tram() received tram code [%d] instead of [%d]\n", (int)ep6in_Tram[1], (int)expectedTram);
		return -1;
	}
	tramLen = ep6in_Tram[2] + (ep6in_Tram[3] << 8);
	if (tramLen != expectedLen) {
		DPxDebugPrint2("ERROR: EZReadEP6Tram() received tram length [%d] instead of [%d]\n", tramLen, expectedLen);
		return -1;
	}

	return 0;
}

#else

// EZReadEP6Tram() reads a tram from the EZUSB EP6IN endpoint.
// If a data tram is received, and its tram code equals expectedTram, EZReadEP6Tram() returns 0.
// All other cases return an error code.
// Keep this strategy of buffering returned trams, just in case the DP is returning multiple trams for some reason.
// I could go back to using this routine if I wanted to.  It has a more of an async interface to trams.
int EZReadEP6Tram(unsigned char expectedTram, int expectedLen)
{
	static char packet[65536];				// Largest possible EP6 USB packet
	static int	packetLength	= 0;
	static int	packetRdIndex	= 0;
	static int	tramWrIndex		= 0;
	static int	tramLen			= 0;		// The length of the payload

	// Each iteration either reads a new 512 byte USB packet, or starts a new tram
	CheckUsb();
	while (1) {

		// If we're out of data, or we had an error, read another packet.
		if (packetLength <= 0) {
			packetLength = usb_bulk_read(dpxHdl, 0x86, packet, expectedLen+4, 1000);
			if (packetLength <= 0) {
				DPxDebugPrint1("ERROR: EZReadEP6Tram() bulk read returned [%d]\n", packetLength);
				return packetLength;
			}
			packetRdIndex = 0;			// We start reading the new packet from index 0
		}

		// Each iteration copies 1 byte from the USB packet to the tram.
		while (packetLength) {
			ep6in_Tram[tramWrIndex++] = packet[packetRdIndex++];	// Copy the byte from the USB packet to the tram
			packetLength--;

			// If there's a framing error, flush byte and keep scanning for hat
			if (tramWrIndex == 1 && ep6in_Tram[0] != '^') {
				DPxDebugPrint1("ERROR: EZReadEP6Tram() framing error [%d]\n", (int)ep6in_Tram[0]);
				while (packetLength && packet[packetRdIndex] != '^') {	// Try to only print 1 error message per framing error
					packetLength--;
					packetRdIndex++;
				}
				tramWrIndex = 0;
				return -1;
			}

			if (tramWrIndex == 4)
				tramLen = ep6in_Tram[2] + (ep6in_Tram[3] << 8);

			// The tram ends as soon as we've received the payload
			if (tramWrIndex >= 4 && tramWrIndex == tramLen + 4) {
				tramWrIndex = 0;										// Next tram will start writing at start of buffer
				if (ep6in_Tram[1] == EP1IN_CONSOLE)						// Filter out and print console trams
					EZPrintConsoleTram(ep6in_Tram);
				else if (ep6in_Tram[1] == EP1OUT_FLUSH)					// Ignore flush trams
					(void)0;
				else if (expectedTram) {								// We're looking for a specific tram
					if (ep6in_Tram[1] != expectedTram) {
						DPxDebugPrint1("ERROR: EZReadEP6Tram() received tram code [%d] instead of [%d]\n", (int)ep6in_Tram[1], (int)expectedTram);
						return -1;
					}
					if (tramLen != expectedLen) {
						DPxDebugPrint1("ERROR: EZReadEP6Tram() received tram length [%d] instead of [%d]\n", tramLen, expectedLen);
						return -1;
					}
					return 0;
				}
			}
		}	// while (packetLength)

		// If we get here, we've used up the current packet, but have no data tram assembled yet.
		// Under some circumstances, usb_bulk_read can stick for the entire timeout time.
		// (I'm not sure where I saw this.  Might have been due to a bug of mine).
		// In any case, if we're not actually looking for a command to process (expectedTram == 0),
		// then get back to caller ASAP.
		if (expectedTram == 0)
			return 0;
	}
	return 0;	// Make compiler happy
}
#endif


void EZPrintConsoleTram(unsigned char* tram)
{
	static int newLine = 1;

	int i, theChar;
	int nChars = tram[2] + (tram[3] << 8);
	for (i = 0; i < nChars; i++) {
		if (newLine) {
			printf(" EZ_CONSOLE> ");
			newLine = 0;
		}
		theChar = tram[i+4];
		switch (theChar) {
			case EP1IN_ERR_HAT:
				printf("Tram: Framing error\n");
				newLine = 1;
				break;
			case EP1IN_ERR_NOP:
				printf("Tram: Null command code\n");
				newLine = 1;
				break;
			case EP1IN_ERR_LEN:
				printf("Tram: Illegal payload length\n");
				newLine = 1;
				break;
			case EP1IN_ERR_CMD:
				printf("Tram: Unrecognized command code\n");
				newLine = 1;
				break;
			default:
				putchar(theChar);
				newLine = (theChar == 10);
		}
	}
	fflush(stdout);
}


// Returns non-zero if we can access the SPI flash through the VIEWPixx/PROPixx high-speed FPGA interface,
// or returns 0 if we must use the slower software-based EZ-USB interface.
// Currently, the FPGA interface only works for an open, configured VIEWPixx/PROPixx.
// DATAPixx only supports the EZ-USB access to SPI.
// A rev1 PCB VIEWPixx doesn't support _any_ access to SPI if FPGA is unconfigured!  Need to use byte-blaster to configure FPGAs for those first PCBs.
int DPxSpiHasVpxFpgaCtrl()
{
    return DPxIsOpen() && (DPxIsViewpixx() || DPxIsPropixx()) && DPxIsReady() && gSpifEnable;
}


#define FAIL_IF_SPI_START_NEG(x) do { if (x < 0) { fprintf(stderr, "ERROR: DPxSpiStart() error = %d\n", x); goto fail; }} while (0)

// Prepare SPI interface for I/O.
// return 0 for success.
int DPxSpiStart()
{
	int rc, i, qsBitMask;

    // VIEWPixx uses Stratix 3, which never seems to tristate its damned SPI interface!
    // We had to put a Quickswitch on the PCB between the SPI and FPGA, in order for the EZ-USB to have access to SPI.
    // If we want to use the FPGA interface to the SPI, make sure that this QS is enabled, and EZ SPI access is tristate.
    // Nope.  Programming the SPI using ASMI is very unreliable.
    // We'll use the FPGA's home-grown SPI interface.
    if (DPxSpiHasVpxFpgaCtrl()) {

        // Tell FPGA to not use ASMI
        DPxSetReg16(DPXREG_CTRL, DPxGetReg16(DPXREG_CTRL) | 0x8000);
        DPxUpdateRegCache();

        // Drive output onto FPGA_SPI_CTRL signal, but tristate rest of EZ access to SPI device
        rc = EZWriteSFR(EZ_SFR_OEC, (unsigned char)0x20); FAIL_IF_SPI_START_NEG(rc);

        // Open QuickSwitch to block FPGA ASMI from accessing SPI
        rc = EZReadSFR(EZ_SFR_IOC); FAIL_IF_SPI_START_NEG(rc);
        rc = EZWriteSFR(EZ_SFR_IOC, (unsigned char)rc | 0x20); FAIL_IF_SPI_START_NEG(rc);

        return 0;
    }

    // We will be using the EZ-USB to access the SPI device.
    // For VIEWPixx, we'll drive FPGA_SPI_CTRL high to stop Stratix 3 from hogging the SPI bus.
    // For DATAPixx, once I had this great idea of forcing FPGA_PGMn low before accessing the SPI over USB.
    // This would deconfigure the FPGA, but that's the only way we can be absolutely sure it's not driving SPI bus.
    // Otherwise, a buggy FPGA load could inhibit us from reprogramming the SPI with a correct load.
    // That's the plan anyways.  In practice, doing this was causing one production DP to give "ERROR: does not recognize SPI device" from below.
    // Seems that bringing down PGMn was clobbering EZ-USB access to SPI.  No idea why, but I'll leave the FPGA configured for now.
    // This isn't too bad.  The FPGA only accesses the SPI for a could of ms at startup to read calibration data.
    // By forcing reconfig off, the FPGA won't reconfig during the SPI reprogramming, so the user won't loose their display.
    // Only on the next powerup will the real reconfiguration occur.  Might be a good thing.
    // Leave it up to a higher-level API to decide if/when FPGA PGMn should be strobed.
    // Kinda makes sense.  The configuration logic might be wanting to control the SPI bus about this time,
    // although the datasheet seems to suggest it is floating the SPI bus.
    // Probably best to not try to drive the SPI bus when I drop PGMn if I can help it.
    // Best to strobe PGMn _after_ I've programmed the SPI.
    qsBitMask = (DPxIsViewpixx() || DPxIsPropixx()) ? 0x20 : 0;

    // Make sure SPI_CSn is high, and SPI_SCK is low, and FPGA_SPI_CTRL is high on VIEWPixx
    rc = EZReadSFR(EZ_SFR_IOC); FAIL_IF_SPI_START_NEG(rc);
    rc = EZWriteSFR(EZ_SFR_IOC, ((unsigned char)rc | 0x04 | qsBitMask) & ~0x08); FAIL_IF_SPI_START_NEG(rc);

    // Drive output onto SPI_CSn, SPI_SCK, SPI_DI, and FPGA_SPI_CTRL on VIEWPixx
    rc = EZReadSFR(EZ_SFR_OEC); FAIL_IF_SPI_START_NEG(rc);
    rc = EZWriteSFR(EZ_SFR_OEC, (unsigned char)rc | 0x0D | qsBitMask); FAIL_IF_SPI_START_NEG(rc);

    // Execute SPI RDID command to ensure we recognize device.
    // Also a sanity check that device is powered up, SPI interface works, etc.
    if (EZWriteEP1Tram((unsigned char*)"^S\x04\x00\x9F\x00\x00\x00", EP1IN_SPI, 4))
        { fprintf(stderr,"ERROR: DPxSpiStart() call to EZWriteEP1Tram() failed\n"); goto fail; }
    if (memcmp(ep1in_Tram+5, "\x20\x20\x16", 3) &&								// STMicroelectronics M25P32
        memcmp(ep1in_Tram+5, "\x20\x20\x17", 3)) {								// STMicroelectronics M25P64
        fprintf(stderr, "ERROR: DPxSpiStart() does not recognize SPI device:");
        for (i = 5; i < 8; i++)
            fprintf(stderr, " %02X", ep1in_Tram[i]);										// So we know just what SPI returned
        putchar('\n');
        goto fail;
    }

    // Unlock the SPI flash.  We never lock it, but maybe some other software...
    if (EZWriteEP1Tram((unsigned char*)"^S\x01\x00\x06", EP1IN_SPI, 1))                     // WREN command needed before writing status reg
        { fprintf(stderr,"ERROR: DPxSpiStart() call to EZWriteEP1Tram() failed\n"); goto fail; }
    if (EZWriteEP1Tram((unsigned char*)"^S\x02\x00\x01\x00", EP1IN_SPI, 2))                 // WRSR clear status reg to disable write protection
        { fprintf(stderr,"ERROR: DPxSpiStart() call to EZWriteEP1Tram() failed\n"); goto fail; }
    do {                                                                                    // Have to wait until WRSR has completed
        if (EZWriteEP1Tram((unsigned char*)"^S\x02\x00\x05\x00", EP1IN_SPI, 2))             // RDSR Read Status Register
            { fprintf(stderr,"ERROR: DPxSpiStart() call to EZWriteEP1Tram() failed\n"); goto fail; }
    } while (ep1in_Tram[5] & 1);		// Stay here while the Write In Progress bit is set.

    return 0;

fail:
	DPxSetError(DPX_ERR_SPI_START);
    return DPX_ERR_SPI_START;
}


int DPxSpiStop()
{
	int rc;

	// Stop EZ from driving SPI_CSn, SPI_SCK, SPI_DI nets.
	// The FPGA might be driving this interface soon!
    rc = EZReadSFR(EZ_SFR_OEC);
    if (rc < 0)
        { fprintf(stderr, "ERROR: DPxSpiStop() error 1\n"); goto fail; }
    if (EZWriteSFR(EZ_SFR_OEC, (unsigned char)rc & ~0x0D) < 0)
        { fprintf(stderr, "ERROR: DPxSpiStop() error 2\n"); goto fail; }

    // On VIEWPixx FPGA, we'll return to ASMI access.  ASMI reads seem to be reliable.
    if (DPxSpiHasVpxFpgaCtrl()) {
        DPxSetReg16(DPXREG_CTRL, DPxGetReg16(DPXREG_CTRL) & ~0x8000);
        DPxUpdateRegCache();
        rc = EZReadSFR(EZ_SFR_IOC);
        if (rc < 0)
            { fprintf(stderr, "ERROR: DPxSpiStop() error 3\n"); goto fail; }
        rc = EZWriteSFR(EZ_SFR_IOC, (unsigned char)rc & ~0x20);
    }

    return 0;

fail:
	DPxSetError(DPX_ERR_SPI_STOP);
    return DPX_ERR_SPI_STOP;
}


// Read a SPI block of any size.
// Assumes that spiAddr starts on a 256-byte boundary.
int DPxSpiRead(int spiAddr, int nReadBytes, unsigned char* readBuffer, PercentCompletionCallback percentCompletionCallback)
{
    DPxSpiStart();
    DPxSpiReadNoStartStop(spiAddr,  nReadBytes, readBuffer, percentCompletionCallback);
    DPxSpiStop();
    return 0;
}


#define FAIL_IF_SPI_READ_ERR do { if (DPxGetError()) { fprintf(stderr, "ERROR: DPxSpiRead() error = %d\n", DPxGetError()); goto fail; }} while (0)

// We have a NoStartStop version so that users of other SPI commands can do a read w/o indirectly calling DPxSpiStop().
int DPxSpiReadNoStartStop(int spiAddr, int nReadBytes, unsigned char* readBuffer, PercentCompletionCallback percentCompletionCallback)
{
    int nBytesRead, nBytesRemaining, nSpiBytes, nTramPayloadBytes, oldPercentDone, newPercentDone;

    nBytesRead = 0;
    oldPercentDone = 0;
    if (percentCompletionCallback)
        percentCompletionCallback(0);

    while (nBytesRead < nReadBytes) {
        nBytesRemaining = nReadBytes - nBytesRead;
        nSpiBytes = nBytesRemaining < 256 ? nBytesRemaining : 256;
        if (DPxSpiHasVpxFpgaCtrl()) {
            ep2out_Tram[0] = '^';
            ep2out_Tram[1] = 'S';
            ep2out_Tram[2] = 4;
            ep2out_Tram[3] = 0;
            ep2out_Tram[4] = 0x0B;		// Fast Read command
            ep2out_Tram[5] = (unsigned char)(spiAddr >> 16);
            ep2out_Tram[6] = (unsigned char)(spiAddr >>  8);
            ep2out_Tram[7] = (unsigned char)spiAddr;
            EZWriteEP2Tram(ep2out_Tram, EP6IN_SPI, 256); FAIL_IF_SPI_READ_ERR;
            memcpy(readBuffer, ep6in_Tram+4, nSpiBytes);
        }
        else {
            nTramPayloadBytes = nSpiBytes + 5;  // 1 SPI command byte + 3 SPI address bytes + 1 dummy readback byte
            ep1out_Tram[0] = '^';
            ep1out_Tram[1] = 'S';
            ep1out_Tram[2] = LSB(nTramPayloadBytes);
            ep1out_Tram[3] = MSB(nTramPayloadBytes);
            ep1out_Tram[4] = 0x0B;		// Fast Read command
            ep1out_Tram[5] = (unsigned char)(spiAddr >> 16);
            ep1out_Tram[6] = (unsigned char)(spiAddr >>  8);
            ep1out_Tram[7] = (unsigned char)spiAddr;
            EZWriteEP1Tram(ep1out_Tram, EP1IN_SPI, nTramPayloadBytes); FAIL_IF_SPI_READ_ERR;
            memcpy(readBuffer, ep1in_Tram+9, nSpiBytes);
        }
        spiAddr += nSpiBytes;
        readBuffer += nSpiBytes;
        nBytesRead += nSpiBytes;
        newPercentDone = nBytesRead * 100 / nReadBytes;
        if (percentCompletionCallback && newPercentDone != oldPercentDone)
            percentCompletionCallback(newPercentDone);
        oldPercentDone = newPercentDone;
    }

    return 0;

fail:
	DPxSetError(DPX_ERR_SPI_READ);
    return DPX_ERR_SPI_READ;
}


#define FAIL_IF_SPI_WRITE_ERR do { if (DPxGetError()) { fprintf(stderr, "ERROR: DPxSpiWrite() error = %d\n", DPxGetError()); goto fail; }} while (0)

// Write a SPI block of any size.
// Assumes that spiAddr starts on a 256-byte boundary.
// If nWriteBytes is not a multiple of 256 bytes, the last page is padded with 0.
int DPxSpiWrite(int spiAddr, int nWriteBytes, unsigned char* writeBuffer, PercentCompletionCallback percentCompletionCallback)
{
    int nBytesWritten, nBytesRemaining, nSpiBytes, oldPercentDone, newPercentDone;
    unsigned char dummyBuff;

    DPxSpiStart(); FAIL_IF_SPI_WRITE_ERR;

    nBytesWritten = 0;
    oldPercentDone = 0;
    if (percentCompletionCallback)
        percentCompletionCallback(0);

    while (nBytesWritten < nWriteBytes) {
        nBytesRemaining = nWriteBytes - nBytesWritten;
        nSpiBytes = nBytesRemaining < 256 ? nBytesRemaining : 256;
        if (DPxSpiHasVpxFpgaCtrl()) {
            ep2out_Tram[0] = '^';
            ep2out_Tram[1] = 'S';
            ep2out_Tram[2] = 4;
            ep2out_Tram[3] = 1;     // We will always program SPI in chunks of 256 bytes
            ep2out_Tram[4] = 0x02;  // SPI Page Program command
            ep2out_Tram[5] = (unsigned char)(spiAddr >> 16);
            ep2out_Tram[6] = (unsigned char)(spiAddr >>  8);
            ep2out_Tram[7] = (unsigned char)spiAddr;
            memcpy(ep2out_Tram+8, writeBuffer, nSpiBytes);
            memset(ep2out_Tram+8+nSpiBytes, 0, 256-nSpiBytes);  // Pad last page with 0's
            EZWriteEP2Tram(ep2out_Tram, 0, 0); FAIL_IF_SPI_WRITE_ERR;
        }
        else {
			EZWriteEP1Tram((unsigned char*)"^S\x01\x00\x06", EP1IN_SPI, 1); FAIL_IF_SPI_WRITE_ERR;		// WREN command needed before programming each page
            ep1out_Tram[0] = '^';
            ep1out_Tram[1] = 'S';
            ep1out_Tram[2] = 4;
            ep1out_Tram[3] = 1;     // We will always program SPI in chunks of 256 bytes
            ep1out_Tram[4] = 0x02;  // SPI Page Program command
            ep1out_Tram[5] = (unsigned char)(spiAddr >> 16);
            ep1out_Tram[6] = (unsigned char)(spiAddr >>  8);
            ep1out_Tram[7] = (unsigned char)spiAddr;
            memcpy(ep1out_Tram+8, writeBuffer, nSpiBytes);
            memset(ep1out_Tram+8+nSpiBytes, 0, 256-nSpiBytes);  // Pad last page with 0's
            EZWriteEP1Tram(ep1out_Tram, EP1IN_SPI, 260); FAIL_IF_SPI_WRITE_ERR;

            // Wait until the page write completes.
            // The FPGA SPI interface is robust, and automatically unlocks sectors, waits if SPI is busy, etc;
            // but our EZ-USB software SPI interface is not so robust, so we'll hang here until we know SPI is available for next operation.
            do {
                EZWriteEP1Tram((unsigned char*)"^S\x02\x00\x05\x00", EP1IN_SPI, 2); FAIL_IF_SPI_WRITE_ERR;	// RDSR Read Status Register
            } while (ep1in_Tram[5] & 1);		// Stay here while the Write In Progress bit is set.
        }
        spiAddr += nSpiBytes;
        writeBuffer += nSpiBytes;
        nBytesWritten += nSpiBytes;
        newPercentDone = nBytesWritten * 100 / nWriteBytes;
        if (percentCompletionCallback && newPercentDone != oldPercentDone)
            percentCompletionCallback(newPercentDone);
        oldPercentDone = newPercentDone;
    }

    // We'll wait around until last write has actually completed;
    // otherwise, someone like DPxSpiStop() can steal SPI bus while SP2 is still polling the SPI status register.
    if (DPxSpiHasVpxFpgaCtrl())
        DPxSpiReadNoStartStop(0, 1, &dummyBuff, NULL);

    DPxSpiStop();
    return 0;

fail:
    DPxSpiStop();
	DPxSetError(DPX_ERR_SPI_WRITE);
    return DPX_ERR_SPI_WRITE;
}


#define FAIL_IF_SPI_ERASE_ERR do { if (DPxGetError()) { fprintf(stderr, "ERROR: DPxSpiErase() error = %d\n", DPxGetError()); goto fail; }} while (0)

// Erase (sets to 1) a SPI block of any size.
// Assumes that spiAddr starts on a 64kB boundary.
// The SPI is erased in 64kB chunks; if nEraseBytes is not a 64k multiple, it is rounded up to the next 64k multiple.
int DPxSpiErase(int spiAddr, int nEraseBytes, PercentCompletionCallback percentCompletionCallback)
{
    int nBytesErased, nBytesRemaining, nSpiBytes, oldPercentDone, newPercentDone;
    unsigned char dummyBuff;

    DPxSpiStart(); FAIL_IF_SPI_ERASE_ERR;

    nBytesErased = 0;
    oldPercentDone = 0;
    if (percentCompletionCallback)
        percentCompletionCallback(0);

    while (nBytesErased < nEraseBytes) {
        nBytesRemaining = nEraseBytes - nBytesErased;
        nSpiBytes = nBytesRemaining < 65536 ? nBytesRemaining : 65536;
        if (DPxSpiHasVpxFpgaCtrl()) {
            ep2out_Tram[0] = '^';
            ep2out_Tram[1] = 'S';
            ep2out_Tram[2] = 4;
            ep2out_Tram[3] = 0;
            ep2out_Tram[4] = 0xD8;										// Sector Erase command
            ep2out_Tram[5] = (unsigned char)(spiAddr >> 16);
            ep2out_Tram[6] = (unsigned char)(spiAddr >>  8);
            ep2out_Tram[7] = (unsigned char)spiAddr;
            EZWriteEP2Tram(ep2out_Tram, 0, 0); FAIL_IF_SPI_ERASE_ERR;

            // We'll wait around until erase is actually completed;
            // otherwise the FPGA SPI controller will just instantly buffer all the erase commands,
            // and the next SPI read/write command will block until the erases complete and the USB transaction will timeout.
            // Also, the % complete status would instantly jump to 100%.
            DPxSpiReadNoStartStop(0, 1, &dummyBuff, NULL); FAIL_IF_SPI_ERASE_ERR;
        }
        else {
            EZWriteEP1Tram((unsigned char*)"^S\x01\x00\x06", EP1IN_SPI, 1); FAIL_IF_SPI_ERASE_ERR;      // WREN command needed before erasing a sector
            ep1out_Tram[0] = '^';
            ep1out_Tram[1] = 'S';
            ep1out_Tram[2] = 4;
            ep1out_Tram[3] = 0;
            ep1out_Tram[4] = 0xD8;										// Sector Erase command
            ep1out_Tram[5] = (unsigned char)(spiAddr >> 16);
            ep1out_Tram[6] = (unsigned char)(spiAddr >>  8);
            ep1out_Tram[7] = (unsigned char)spiAddr;
            EZWriteEP1Tram(ep1out_Tram, EP1IN_SPI, 4); FAIL_IF_SPI_ERASE_ERR;

            // We'll wait around until erase is complete, so next operation can start without checking SPI status
            do {                                                                                            // Have to wait until WRSR has completed
                EZWriteEP1Tram((unsigned char*)"^S\x02\x00\x05\x00", EP1IN_SPI, 2); FAIL_IF_SPI_ERASE_ERR;	// RDSR Read Status Register
            } while (ep1in_Tram[5] & 1);		// Stay here while the Write In Progress bit is set.
        }
        spiAddr += nSpiBytes;
        nBytesErased += nSpiBytes;
        newPercentDone = nBytesErased * 100 / nEraseBytes;
        if (percentCompletionCallback && newPercentDone != oldPercentDone)
            percentCompletionCallback(newPercentDone);
        oldPercentDone = newPercentDone;
    }

    // We'll wait around until last erase has actually completed;
    // otherwise, someone like DPxSpiStop() can steal SPI bus while SP2 is still polling the SPI status register.
    if (DPxSpiHasVpxFpgaCtrl())
        DPxSpiRead(0, 1, &dummyBuff, NULL);

    DPxSpiStop();
    return 0;

fail:
    DPxSpiStop();
	DPxSetError(DPX_ERR_SPI_ERASE);
    return DPX_ERR_SPI_ERASE;
}



unsigned char spiModifyBuff[65536];

// Modify a region of SPI within a single 64kB page
void DPxSpiModify(int spiAddr, int nWriteBytes, unsigned char* writeBuffer)
{
    int page = spiAddr & 0xFFFF0000;
    int offset = spiAddr & 0x0000FFFF;
    DPxSpiRead(page, 65536, spiModifyBuff, NULL);
    memcpy(spiModifyBuff+offset, writeBuffer, nWriteBytes);   
    DPxSpiErase(page, 65536, NULL);
    DPxSpiWrite(page, 65536, spiModifyBuff, NULL);
}


// Non-0 if DPxOpen found a DP
int DPxIsOpen()
{
	return dpxHdl != 0;
}


// Non-0 if a detected DP has no EZ-USB firmware
int DPxHasRawUsb()
{
	return dpxRawUsb;
}


// DPxReset causes the following sequence:
//	1) DATAPixx hardware reset for 200 microseconds
//	2) DATAPixx disconnects from USB
//	3) 1.5 second delay
//	4) DATAPixx reconnects to USB
// We need gDoingHardwareReset backdoor to tell DPxClose() to not try to do any USB access
int gDoingHardwareReset = 0;

void DPxReset()
{
	if (EZWriteEP1Tram((unsigned char*)"^B\x00\x00", 0, 0))
		{ fprintf(stderr,"ERROR: Sending reset tram\n"); }

    gDoingHardwareReset = 1;
	DPxClose();
    gDoingHardwareReset = 0;
}


StringCallback gStatusCallback;
static char statusMsg[256];

void FPGAErasePercentCompletionCallback(int percentCompletion);
void FPGAWritePercentCompletionCallback(int percentCompletion);
void FPGAVerifyPercentCompletionCallback(int percentCompletion);

void FPGAErasePercentCompletionCallback(int percentCompletion)
{
    sprintf(statusMsg, "\rFlash Erase  %3d%% completed", percentCompletion);
    if (gStatusCallback)
        gStatusCallback(statusMsg);
    else {
        printf("%s", statusMsg);
        fflush(stdout);
    }
}

void FPGAWritePercentCompletionCallback(int percentCompletion)
{
    sprintf(statusMsg, "\rFlash Write  %3d%% completed", percentCompletion);
    if (gStatusCallback)
        gStatusCallback(statusMsg);
    else {
        printf("%s", statusMsg);
        fflush(stdout);
    }
}


void FPGAVerifyPercentCompletionCallback(int percentCompletion)
{
    sprintf(statusMsg, "\rFlash Verify %3d%% completed", percentCompletion);
    if (gStatusCallback)
        gStatusCallback(statusMsg);
    else {
        printf("%s", statusMsg);
        fflush(stdout);
    }
}


int DPxProgramFPGA(unsigned char* configBuff, int configFileSize, int doProgram, int doVerify, int reconfigFpga, StringCallback statusCallback)
{
	int		spiAddr;
	int		sfr_ioe, sfr_oee, i, nErrors;
    unsigned char dummyBuff;

	spiAddr = (DPxIsViewpixx() || DPxIsPropixx()) ? SPI_ADDR_VPX_FPGA : SPI_ADDR_DPX_FPGA;

    // Need to flip bits in configuration file if programming VIEWPixx/PROPixx
    if (DPxIsViewpixx() || DPxIsPropixx()) {
        for (i = 0; i < configFileSize; i++)
            configBuff[i] = (configBuff[i] & 0x01 ? 0x80 : 0)
                          + (configBuff[i] & 0x02 ? 0x40 : 0)
                          + (configBuff[i] & 0x04 ? 0x20 : 0)
                          + (configBuff[i] & 0x08 ? 0x10 : 0)
                          + (configBuff[i] & 0x10 ? 0x08 : 0)
                          + (configBuff[i] & 0x20 ? 0x04 : 0)
                          + (configBuff[i] & 0x40 ? 0x02 : 0)
                          + (configBuff[i] & 0x80 ? 0x01 : 0);
    }

	if (doProgram) {

		// Erase the SPI flash.  DATAPixx takes about 12 seconds, VIEWPixx/PROPixx takes about 26 seconds.
		if (!statusCallback)
			printf("\nReflashing %s\n*** Do not turn off system until flash programming complete! ***\n\n", DPxIsViewpixx() ? "VIEWPixx" : DPxIsPropixx() ? "PROPixx" : "DATAPixx");
        gStatusCallback = statusCallback;
        if (DPxSpiErase(spiAddr, configFileSize, FPGAErasePercentCompletionCallback))
            goto abort;
		if (!statusCallback)
			putchar('\n');

		// Write the SPI flash.  DATAPixx takes about 24 seconds, VIEWPixx takes about 10 seconds when using fast FPGA SPI interface.
        if (DPxSpiWrite(spiAddr, configFileSize, configBuff, FPGAWritePercentCompletionCallback))
            goto abort;
		if (!statusCallback)
			putchar('\n');
    }

	// Do readback to confirm that we successfully programmed the SPI.  DATAPixx takes about 19 seconds, VIEWPixx takes about 3 seconds when using fast FPGA SPI interface.
    // I was getting some verify errors on VIEWPixx, but I seem to have corrected the problem in VHDL.
    if (doVerify) {
        if (DPxSpiRead(spiAddr, configFileSize, configBuffer2, FPGAVerifyPercentCompletionCallback))
            goto abort;
		if (!statusCallback)
			putchar('\n');
        if (memcmp(configBuff, configBuffer2, configFileSize)) {
            fprintf(stderr, "ERROR: flash verify failed\n");
            nErrors = 0;
            for (i = 0; i < configFileSize; i++)
                if (configBuff[i] != configBuffer2[i] && ++nErrors <= 10)
                    fprintf(stderr, "byte %d is %d instead of %d\n", i, configBuffer2[i], configBuff[i]);
            printf("%d total verify errors\n", nErrors);
        }
    }

    // If we're _not_ doing a verify, we'll still do 1 small SPI readback, just to ensure that the SPI programming has completed.
    else if (DPxSpiRead(0, 1, &dummyBuff, NULL))
        goto abort;

	// Strobe VIEWPixx nConfig, or DATAPixx PGMn _after_ I've finished programming the SPI device.
	// If the user is using our video output as their primary display, they don't loose the display during SPI programming.
	// Also, if the SPI programming is stopped, or fails, they haven't lost their FPGA unless they powerdown.
	// They still have a chance to retry the FPGA programming.
	if (reconfigFpga) {
		sfr_ioe = EZReadSFR(EZ_SFR_IOE);
		if (sfr_ioe < 0)
			{ fprintf(stderr, "ERROR: PGMn start IOE EZReadSFR() failed\n"); }
		if (EZWriteSFR(EZ_SFR_IOE, (unsigned char)sfr_ioe & ~0x20) < 0)
			{ fprintf(stderr, "ERROR: PGMn start IOE EZWriteSFR() failed\n"); }

		// Drive low output onto FPGA_PGMn net.
		// This should also force the FPGA to tristate its SPI interface.
		sfr_oee = EZReadSFR(EZ_SFR_OEE);
		if (sfr_oee < 0)
			{ fprintf(stderr, "ERROR: PGMn start OEE EZReadSFR() failed\n"); }
		if (EZWriteSFR(EZ_SFR_OEE, (unsigned char)sfr_oee | 0x20) < 0)
			{ fprintf(stderr, "ERROR: PGMn start OEE EZWriteSFR() failed\n"); }

		// ***Here's a good one.  I'm doing a powered reconfig here, so HRESET is currently inactive.
		// Unfortunately, on DATAPixx HRESET is driving the FPGA's SPIFASTN pin, so FPGA will use the slower SPI read command.
		// My SPI only has an Fmax of 20 MHz for the slow commands, as opposed to 50 MHz for the fast commands.
		// The FPGA tries to reconfigure at high speed using the slow commands, and crashes miserably (at least with the 64 Mbit parts).
		// The solution is to immediately bring down HRESET!
		// When the EZ goes into reset, it releases FPGA_PGMn, and the FPGA starts to configure.
		// The FPGA sees low on SPIFASTN, so configures at high speed.
        // For VIEWPixx, the hardware reset will reset EZ, causing it to stop driving SPI QuickSwitch OEn high, which will give FPGA configuration logic access to SPI.
		DPxReset();
	}

	return 0;

abort:
	return -1;
}


// Examples of a few EDID structures for other displays
unsigned char planarEdid[128] = {
	0x00, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0x00, 0x52, 0xD4, 0x56, 0x00, 0x7E, 0x01, 0x00, 0x00,
	0x19, 0x0D, 0x01, 0x03, 0x81, 0x27, 0x1D, 0x78, 0xEA, 0xEC, 0x50, 0xA5, 0x58, 0x4A, 0x9A, 0x26,
	0x21, 0x50, 0x54, 0xA0, 0x00, 0x00, 0x81, 0x80, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01,
	0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x30, 0x2A, 0x00, 0x98, 0x51, 0x00, 0x2A, 0x40, 0x30, 0x70,
	0x13, 0x00, 0x78, 0x2D, 0x11, 0x00, 0x00, 0x1E, 0x00, 0x00, 0x00, 0xFD, 0x00, 0x38, 0x46, 0x1E,
	0x40, 0x0B, 0x00, 0x0A, 0x20, 0x20, 0x20, 0x20, 0x20, 0x20, 0x00, 0x00, 0x00, 0xFC, 0x00, 0x50,
	0x4C, 0x31, 0x39, 0x31, 0x4D, 0x20, 0x0A, 0x20, 0x20, 0x20, 0x20, 0x20, 0x00, 0x00, 0x00, 0xFC,
	0x00, 0x20, 0x0A, 0x20, 0x20, 0x20, 0x20, 0x20, 0x20, 0x20, 0x20, 0x20, 0x20, 0x20, 0x00, 0x51
};

unsigned char hansEdid[128] = {
	0x00, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0x00, 0x22, 0x64, 0x91, 0x89, 0x9A, 0x0D, 0x00, 0x00,
	0x18, 0x10, 0x01, 0x03, 0x80, 0x29, 0x1A, 0x78, 0x2A, 0x9B, 0xB6, 0xA4, 0x53, 0x4B, 0x9D, 0x24,
	0x14, 0x4F, 0x54, 0xBF, 0xEF, 0x00, 0x31, 0x46, 0x61, 0x46, 0x71, 0x4F, 0x81, 0x40, 0x81, 0x80,
	0x95, 0x00, 0x95, 0x0F, 0x01, 0x01, 0x9A, 0x29, 0xA0, 0xD0, 0x51, 0x84, 0x22, 0x30, 0x50, 0x98,
	0x36, 0x00, 0x98, 0xFF, 0x10, 0x00, 0x00, 0x1C, 0x00, 0x00, 0x00, 0xFD, 0x00, 0x31, 0x4B, 0x1E,
	0x50, 0x0E, 0x00, 0x0A, 0x20, 0x20, 0x20, 0x20, 0x20, 0x20, 0x00, 0x00, 0x00, 0xFC, 0x00, 0x48,
	0x57, 0x31, 0x39, 0x31, 0x44, 0x0A, 0x20, 0x20, 0x20, 0x20, 0x20, 0x20, 0x00, 0x00, 0x00, 0xFF,
	0x00, 0x36, 0x32, 0x34, 0x47, 0x48, 0x33, 0x30, 0x43, 0x41, 0x33, 0x34, 0x38, 0x32, 0x00, 0x7A
};

// Apple's 30" cinema display EDID.  Note that byte 0x14 is 0x80 and not 0x81, saying they don't support DLP?
unsigned char cinema30Edid[128] = {
	0x00, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0x00, 0x06, 0x10, 0x20, 0x92, 0xE3, 0x00, 0x00, 0x02,
	0x2D, 0x0E, 0x01, 0x03, 0x80, 0x40, 0x28, 0x78, 0x28, 0x60, 0xE5, 0xA3, 0x57, 0x4B, 0x9C, 0x25,
	0x11, 0x50, 0x54, 0x00, 0x00, 0x00, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01,
	0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0xBC, 0x1B, 0x00, 0xA0, 0x50, 0x20, 0x17, 0x30, 0x30, 0x20,
	0x36, 0x00, 0x81, 0x91, 0x21, 0x00, 0x00, 0x1A, 0xB0, 0x68, 0x00, 0xA0, 0xA0, 0x40, 0x2E, 0x60,
	0x30, 0x20, 0x36, 0x00, 0x81, 0x91, 0x21, 0x00, 0x00, 0x1A, 0x00, 0x00, 0x00, 0xFC, 0x00, 0x43,
	0x69, 0x6E, 0x65, 0x6D, 0x61, 0x20, 0x48, 0x44, 0x20, 0x0A, 0x00, 0x00, 0x00, 0x00, 0x00, 0xFC,
	0x00, 0x44, 0x69, 0x73, 0x70, 0x6C, 0x61, 0x79, 0x0A, 0x00, 0x00, 0x00, 0x00, 0x00, 0x01, 0x8C
};

unsigned char accusync120Edid[128] = {
	0x00, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0x00, 0x38, 0xA3, 0xD1, 0x61, 0x01, 0x01, 0x01, 0x01,
	0x08, 0x10, 0x01, 0x03, 0x0C, 0x28, 0x1E, 0xBA, 0xEA, 0x61, 0xE9, 0xA4, 0x52, 0x49, 0x98, 0x24,
	0x0F, 0x48, 0x4C, 0xFF, 0xFF, 0x80, 0x31, 0x59, 0x45, 0x59, 0x61, 0x59, 0x71, 0x4F, 0x81, 0x59,
	0x81, 0x99, 0xA9, 0x4F, 0xD1, 0x40, 0x86, 0x3D, 0x00, 0xC0, 0x51, 0x00, 0x30, 0x40, 0x40, 0xA0,
	0x13, 0x00, 0x86, 0x25, 0x11, 0x00, 0x00, 0x1E, 0x00, 0x00, 0x00, 0xFD, 0x00, 0x37, 0xA0, 0x1F,
	0x60, 0x19, 0x00, 0x0A, 0x20, 0x20, 0x20, 0x20, 0x20, 0x20, 0x00, 0x00, 0x00, 0xFC, 0x00, 0x41,
	0x63, 0x63, 0x75, 0x53, 0x79, 0x6E, 0x63, 0x20, 0x31, 0x32, 0x30, 0x0A, 0x00, 0x00, 0x00, 0xFF,
	0x00, 0x36, 0x32, 0x34, 0x30, 0x30, 0x33, 0x34, 0x34, 0x4B, 0x41, 0x0A, 0x20, 0x20, 0x00, 0x59
};


// The initial EDID for factory DATAPixx
unsigned char datapixxEdid[128] = {
	0x00, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0x00,	// Header
	0x22, 0x64,										// Manuf ID.  0x22, 0x64 is value for Hanns.G.
	0x01, 0x01,										// Product ID.  Don't use Apple Manuf/Product ID, or drivers hard code certain behaviours.
	0x01, 0x01, 0x01, 0x01,							// Little endian serial number, I don't use.  NEC sets to 0x01.
	   1,   19, 									// Week of manuf, Year of manuf (minus 1990). = 1st wk of 2009.
	0x01, 0x03,										// EDID version 1.3
	0x81,											// Bit 7 means digital video (or GPU doesn't gen DVI!), bit 0 means we support DLP, which seems to mean DVI.  NEC AS120 clears these, but we'll set them
	0x28, 0x1E,										// Max h/v image size in cm.  40x30 cm = 20" diagonal.
	 120,											//  / 100 + 1 gives gamma = 2.2, NEC sets to 0xBA = 186 = gamma of 2.86!
	0x0A,											// RGB color, bit 1 (preferred timing mode set) means that descriptor block 1 contains "Native" geometry (eg: an LCD).
	0x61, 0xE9, 0xA4, 0x52, 0x49, 0x98, 0x24, 0x0F, 0x48, 0x4C,  // Phosphor colours of NEC
	0xFF, 0xEF,	0x80,								// Accept all standard timings except 1 interlaced

	// The next block must contain exactly 8 pairs of bytes, each describing a mode, Cinema Display had only 1's.
	// Seems that even when I put the 120 Hz modes, it doesn't encourage OS X to offer 120 Hz modes.
	// Might make a difference in other OS's though, so I'll offer a simple 640x480 at 120 Hz.
	// BUT, offering at least 1 dual-link mode does enable other dual-link modes, so this is a must.
	0x31, 0x59,										//  640  x  480  x  85 Hz
//	0x31, 0x7C,										//  640  x  480  x 120 Hz, 120 Hz never shows up anyways, and I want the 1440 x 900
	0x45, 0x59,										//  800  x  600  x  85 Hz
//	0x45, 0x7C,										//  800  x  600  x 120 Hz
	0x61, 0x59,										// 1024  x  768  x  85 Hz
//	0x61, 0x7C,										// 1024  x  768  x 120 Hz
//	0x71, 0x4F,										// 1152  x  864  x  75 Hz, never shows up on OS X, so sacrifice this one
	0x81, 0x59,										// 1280  x  960  x  85 Hz
	0x81, 0x99,										// 1280  x 1024  x  85 Hz, HFREQ = 91.15 kHz, ZFREQ = 157.5 MHz
	0x95, 0x00,										// 1440  x  900  x  60 Hz, need this to get 16:10 ratio.  Unfortunately, this isn't sufficient.  Also need a detailed timing block.
//	0xA9, 0x40,										// 1600  x 1200  x  60 Hz, HFREQ = 75.00 kHz, ZFREQ = 162.0 MHz (enabled automatically when 75 Hz included)
	0xA9, 0x4F,										// 1600  x 1200  x  75 Hz, HFREQ = 93.75 kHz, ZFREQ = 202.5 MHz (dual link)
	0xD1, 0x40,										// 1920  x 1440  x  60 Hz, HFREQ = 90.00 kHz, ZFREQ = 234.0 MHz (dual link)

	// Next are 4 18-byte descriptor blocks which can appear in any order.
	// Since we set the "preferred timing mode set" bit above, descriptor 1 has to contain the "native" geometry (eg: for LCD).
	// We'll borrow the NEC AccuSync 120 timings for 1280 x 1024 x 85 Hz.
	0x86, 0x3D,										// 157.5 MHz
	0x00, 0xC0, 0x51,								// HRES = 1280, HBL   = 448
	0x00, 0x30, 0x40,								// VRES = 1024, VBL   =  48
	0x40, 0xA0,										// HFP  =   64, HSYNC = 160
	0x13, 0x00,										// VFP  =    1, VSYNC =   3
	0x86, 0x25, 0x11,								// H/V image size = 390 x 293 mm (19.2" diag)
	0x00, 0x00,										// No border
	0x1E,											// No stereo, syncs separated, V/HSYNC positive

	// Descriptor block is Apple CD details for 2560x1600, VFREQ=59.86Hz, HFREQ=98.53kHz, ZFREQ=268MHz.
	// I think I'll leave this one out.  Sophisticated users can use SwitchResX put in whatever they want,
	// but most monitors will choke on the high HFREQ, leaving the display useless.
	// Also, this mode enables a bunch of other modes of lower resolution,
	// but these modes are actually remapped to 2560x1600 in the graphics board;
	// which would reke havoc to my pixel processing.
//	0xB0, 0x68, 0x00, 0xA0, 0xA0, 0x40, 0x2E, 0x60, 0x30, 0x20, 0x36, 0x00, 0x81, 0x91, 0x21, 0x00, 0x00, 0x1A,

	// We'll do another detailed video mode for Hanns-G 1440 x 900 x 60Hz.
	// This is the only way to get a 1440x900 showing up in my displays control panel.
	// Might be good to have at least one 16:10 aspect ratio.
	0x9A, 0x29,										// 106.5 MHz
	0xA0, 0xD0, 0x51,								// HRES = 1440, HBL   = 464
	0x84, 0x22, 0x30,								// VRES = 900,  VBL   = 34
	0x50, 0x98,										// HFP  = 80,   HSYNC = 152
	0x36, 0x00,										// VFP  = 3,    VSYNC = 6
	0x98, 0xFF, 0x10,								// H/V image size = 408 x 255 mm
	0x00, 0x00,										// No border
	0x1C,											// No stereo, syncs separated, VSYNC positive, HSYNC negative

	// Since we want to include 2 video timing descriptor blocks, we have no space for a serial number block
//	0x00, 0x00, 0x00, 0xFF, 0x00, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x0A, 0x20, 0x20,	// Serial Number

	// Descriptor block 3 has monitor range limits.
	// EDID v1.3 spec says a range limits descriptor is a requirement.
	0x00, 0x00, 0x00, 0xFD, 0x00,
//	0x37, 0xA0,										// VFREQ range 55 - 160 Hz for AccuSync 120.
//	0x1E, 0x60,										// HFREQ range 30 - 96 kHz for AccuSync 120.
	0x37, 0xC8,										// VFREQ range 55 - 200 Hz is maximum for any CRT I've seen.
	0x1E, 0xA0,										// HFREQ range 30 - 160 kHz.  Highest I've seen in a CRT is 121 kHz.
	0x21,											// 330 MHz pixel clock.  NEC AS120 used 0x19=>250MHz, but should be OK for 200 MHz clock of DP.
	0x00, 0x0A, 0x20, 0x20, 0x20, 0x20, 0x20, 0x20,	// Just means use previous values

	// Descriptor block 4 is the monitor name, CD uses 0 padding.
	// First character must be 'D' for DATAPixx to recognize that an EDID has been written to SPI flash.
	0x00, 0x00, 0x00, 0xFC, 0x00,
	'D', 'A', 'T', 'A', 'P', 'i', 'x', 'x', 0x0A, 0x00, 0x00, 0x00, 0x00,

	0x00,											// Indicates no extension blocks in EDID 1.3.  CD had 0x1 here, seemed to cause fixed 2560x1600 w scaling.  That was BAD.
	0x00											// Checksum.  Will be overwritten.
};


// The initial EDID for factory VIEWPixx
unsigned char viewpixxEdid[256] = {
	0x00, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0x00,	// Header
	0x22, 0x64,										// Manuf ID.  0x22, 0x64 is value for Hanns.G.
	0x02, 0x01,										// Product ID.  Don't use Apple Manuf/Product ID, or drivers hard code certain behaviours.
	0x01, 0x01, 0x01, 0x01,							// Little endian serial number, I don't use.  NEC sets to 0x01.
	   1,   21, 									// Week of manuf, Year of manuf (minus 1990). = 1st wk of 2011.
	0x01, 0x03,										// EDID version 1.3
	0x81,											// Bit 7 means digital video (or GPU doesn't gen DVI!), bit 0 means we support DLP, which seems to mean DVI.  NEC AS120 clears these, but we'll set them
	0x30, 0x1E,										// Max h/v image size of VIEWPixx in cm.  48x30 cm = 16:10 ratio and 22" diagonal.
	 120,											//  / 100 + 1 gives gamma = 2.2, NEC sets to 0xBA = 186 = gamma of 2.86!
	0x0A,											// RGB color, bit 1 (preferred timing mode set) means that descriptor block 1 contains "Native" geometry (eg: an LCD).
//	0x61, 0xE9, 0xA4, 0x52, 0x49, 0x98, 0x24, 0x0F, 0x48, 0x4C,  // Phosphor colours of NEC
    0x4B, 0x85, 0xAF, 0x4E, 0x2A, 0xA9, 0x1F, 0x1A, 0x50, 0x54, // LCD R=(.685,.305) G=(.166,.663) B=(.123,.102) D65=(.313,.329)
	0x00, 0x01,	0x00,								// Only acceptable standard timing is 1280x1024x75 = 139.18 MHz

	// The next block must contain exactly 8 pairs of bytes, each describing a mode.
    // Cinema Display had only 1's, but we'll try to make use of this field.
	// Seems that even when I put the 120 Hz modes, it doesn't encourage OS X to offer 120 Hz modes.  Might make a difference in other OS's though.
	// BUT, offering at least 1 dual-link mode does enable other dual-link modes, so this is a must.
    // We will limit ourselves to modes with a DVI_CLK in the range 82.5-165MHz so that a single PLL configuration will lock.  Estimate dot clock with GTF timings.
    // I've removed 3 of the older timings with 3 new 1920x1200 timings with various refresh rates.
	0x45, 0x7C,										//  800  x  600  x 120 Hz,  83.49 MHz
	0x59, 0x3C,										//  960  x  600  x 120 Hz, 100.31 MHz, 16:10 with exactly half VIEWPixx H/V resolution
	0x61, 0x59,										// 1024  x  768  x  85 Hz,  94.39 MHz
//	0x61, 0x7C,										// 1024  x  768  x 120 Hz, 138.46 MHz
//	0x81, 0x99,										// 1280  x 1024  x  85 Hz, 159.54 MHz
//	0xA9, 0x40,										// 1600  x 1200  x  60 Hz, 161.11 MHz
	0xD1, 0x00,										// 1920  x 1200  x  60 Hz, 154.00 MHz CVT-RB
	0xD1, 0x0F,										// 1920  x 1200  x  75 Hz
	0xD1, 0x19,										// 1920  x 1200  x  85 Hz
	0xD1, 0x28,										// 1920  x 1200  x 100 Hz
	0xD1, 0x3C,										// 1920  x 1200  x 120 Hz, 317.00 MHz, dual link, CVT-RB

	// Next are 4 18-byte descriptor blocks which can appear in any order.
	// Since we set the "preferred timing mode set" bit above, descriptor 1 has to contain the "native" geometry.

    // We'll do a 1920 x 1200 x 100.00 Hz; HFREQ = 148.00 kHz.
    // Put 100Hz first.  It's probably the most popular.
    // The lower refresh rate gives LCD pixels longer to stabilize, reducing ghosting with scanning backlight.
    // Don't want to go much lower than 100 Hz though, because we start to see the vertical artifact.
    // Use close to the 308 MHz dot clock, since the DisplayPort->DVI dongles seem to like it.
    // All of our EDIDs will use about 148kHz HFREQ to ensure that VP decides it is lockable.
    // ***NOTE*** VTOTAL used here in test patterns should match VHDL test pattern VTOTAL.
    // Otherwise, scanning backlight luminance calibration won't apply to EDID-based video!
#if 0
	0x55, 0x78,										// 308.05 MHz
	0x80, 0xA0, 0x70,								// HRES = 1920, HBL   = 160
	0xB0, 0x19, 0x41,								// VRES = 1200, VBL   = 281, See ***NOTE***
	0x30, 0x20,										// HFP  =   48, HSYNC =  32
	0x36, 0x00,										// VFP  =    3, VSYNC =   6
	0xE4, 0x2E, 0x11,								// H/V image size = 484 x 302 mm (16:10 w 22.5" diag)
	0x00, 0x00,										// No border
	0x1E,											// No stereo, syncs separated, V/HSYNC positive
#endif

    // We'll use the same horizontal/dot timing as for VP3D, and just trade off 120 VBP for 120 more VACTIVE
    // EDID HTOTAL=2080, VTOTAL=1492, dot clock=310.34MHz, HFREQ=149202, VFREQ=100.001Hz.
    // HWTP HTOTAL=2144, VTOTAL=1493, dot clock=320.00MHz, HFREQ=149254, VFREQ=99.969Hz.
	0x3A, 0x79,										// 310.34 MHz dot clock
	0x80, 0xA0, 0x70,								// HRES = 1920, HBL   = 160
	0xB0, 0x24, 0x41,								// VRES = 1200, VBL   = 292, See ***NOTE1***
	0x10, 0x20,										// HFP  =   16, HSYNC =  32
	0x36, 0x00,										// VFP  =    3, VSYNC =   6
	0xE4, 0x2E, 0x11,								// H/V image size = 484 x 302 mm (16:10 w 22.5" diag)
	0x00, 0x00,										// No border
	0x1E,											// No stereo, syncs separated, V/HSYNC positive

#if 0
	// LCD native timing is 1920 x 1200 x 120.00 Hz; HFREQ = 148.08 kHz.
    // We replaced this VBL of 34 with above VBL of 35 for better stabilization with ViewSonic V3D245.
	0x51, 0x78,										// 308.01 MHz
	0x80, 0xA0, 0x70,								// HRES = 1920, HBL   = 160
	0x38, 0x22, 0x40,								// VRES = 1200, VBL   =  34
	0x30, 0x20,										// HFP  =   48, HSYNC =  32
	0x36, 0x00,										// VFP  =    3, VSYNC =   6
	0xE4, 0x2E, 0x11,								// H/V image size = 484 x 302 mm (16:10 w 22.5" diag)
	0x00, 0x00,										// No border
	0x1E,											// No stereo, syncs separated, V/HSYNC positive
    
	// LCD native timing is 1920 x 1080 x 120.00 Hz; HFREQ = 148.08 kHz, to test different dongles
	0x51, 0x78,										// 308.01 MHz
	0x80, 0xA0, 0x70,								// HRES = 1920, HBL   = 160
	0x38, 0x9A, 0x40,								// VRES = 1080, VBL   =  154
	0x30, 0x20,										// HFP  =   48, HSYNC =  32
	0x36, 0x00,										// VFP  =    3, VSYNC =   6
	0xE4, 0x2E, 0x11,								// H/V image size = 484 x 302 mm (16:10 w 22.5" diag)
	0x00, 0x00,										// No border
	0x1E,											// No stereo, syncs separated, V/HSYNC positive

	// Intentional invalid timings to test VLOCKABLE function
	0x50, 0x78,										// 308.00 MHz
	0x80, 0x40, 0x70,								// HRES = 1920, HBL   = 64, gives HFREQ = 155.24kHz, VFREQ = 125.8Hz
	0xB0, 0x22, 0x40,								// VRES = 1200, VBL   =  34
	0x10, 0x20,										// HFP  =   16, HSYNC =  32
	0x36, 0x00,										// VFP  =    3, VSYNC =   6
	0xE4, 0x2E, 0x11,								// H/V image size = 484 x 302 mm (16:10 w 22.5" diag)
	0x00, 0x00,										// No border
	0x1E,											// No stereo, syncs separated, V/HSYNC positive
    
	// 1920 x 1200 x 120 Hz.
    // Use timings from NEC datasheet, reduces VBP to get lower dot rate, and fixes sparkling with black DisplayPort->DVI dongle
	0xD9, 0x77,										// 306.81 MHz dot clock gives 120 Hz.
	0x80, 0xC8, 0x70,								// HRES = 1920, HBL   = 200
	0xB0, 0x06, 0x40,								// VRES = 1200, VBL   =  6
	0x30, 0x20,										// HFP  =   48, HSYNC =  32
	0x22, 0x00,										// VFP  =    2, VSYNC =   2
	0xE4, 0x2E, 0x11,								// H/V image size = 484 x 302 mm (16:10 w 22.5" diag)
	0x00, 0x00,										// No border
	0x1E,											// No stereo, syncs separated, V/HSYNC positive
    
    // We'll do a 1920 x 1200 x 85 Hz.
    // The lower refresh rate gives LCD pixels longer to stabilize, reducing ghosting with scanning backlight.
    // Don't want to go much lower than 85 Hz though, because we start to see flicker with scanning backlight.
    // Use the same 308 MHz dot clock, since the DisplayPort->DVI dongles seem to like it.
    // Actually, 85Hz is a bit low.  We start to see the vertical artifact.
	0x50, 0x78,										// 308 MHz dot clock
	0x80, 0xA0, 0x70,								// HRES = 1920, HBL   = 160
	0xB0, 0x1E, 0x42,								// VRES = 1200, VBL   = 542 (gives 85.00Hz)
	0x30, 0x20,										// HFP  =   48, HSYNC =  32
	0x36, 0x00,										// VFP  =    3, VSYNC =   6
	0xE4, 0x2E, 0x11,								// H/V image size = 484 x 302 mm (16:10 w 22.5" diag)
	0x00, 0x00,										// No border
	0x1E,											// No stereo, syncs separated, V/HSYNC positive
    
    // CVT-RB, except vertical back porch is reduced from 62 to 61 to get closer to 120 Hz.
	0xD4, 0x7B,										// 317 MHz dot clock gives 120 Hz.
	0x80, 0xA0, 0x70,								// HRES = 1920, HBL   = 160
	0xB0, 0x46, 0x40,								// VRES = 1200, VBL   =  70
	0x30, 0x20,										// HFP  =   48, HSYNC =  32
	0x36, 0x00,										// VFP  =    3, VSYNC =   6
	0xE4, 0x2E, 0x11,								// H/V image size = 484 x 302 mm (16:10 w 22.5" diag)
	0x00, 0x00,										// No border
	0x1E,											// No stereo, syncs separated, V/HSYNC positive
    
    // Minimal vertical timing, but both the Apple and Accel DisplayPort->DVI dongles fail to lock, and image flashes; so, 308MHz it is!
	0x96, 0x75,										// 301.02 MHz dot clock gives 120 Hz.
	0x80, 0xA0, 0x70,								// HRES = 1920, HBL   = 160
	0xB0, 0x06, 0x40,								// VRES = 1200, VBL   =  6
	0x30, 0x20,										// HFP  =   48, HSYNC =  32
	0x22, 0x00,										// VFP  =    2, VSYNC =   2
	0xE4, 0x2E, 0x11,								// H/V image size = 484 x 302 mm (16:10 w 22.5" diag)
	0x00, 0x00,										// No border
	0x1E,											// No stereo, syncs separated, V/HSYNC positive
    
    // 120Hz modified
	// LCD native timing is 1920 x 1200 x 120.00 Hz; HFREQ = 148.15 kHz.
    // ***NOTE*** VTOTAL used here in test patterns should match VHDL test pattern VTOTAL.
    // Otherwise, scanning backlight luminance calibration won't apply to EDID-based video!
	0x5F, 0x78,										// 308.15 MHz
	0x80, 0xA0, 0x70,								// HRES = 1920, HBL   = 160
	0xB0, 0x23, 0x40,								// VRES = 1200, VBL   =  35, See ***NOTE***
	0x30, 0x20,										// HFP  =   48, HSYNC =  32
	0x36, 0x00,										// VFP  =    3, VSYNC =   6
	0xE4, 0x2E, 0x11,								// H/V image size = 484 x 302 mm (16:10 w 22.5" diag)
	0x00, 0x00,										// No border
	0x1E,											// No stereo, syncs separated, V/HSYNC positive
#endif

    // We'll use the same horizontal/dot timing as for VP3D, and just trade off 120 VBP for 120 more VACTIVE
    // EDID HTOTAL=2080, VTOTAL=1243, dot clock=310.25MHz, HFREQ=149159, VFREQ=119.999Hz.
    // HWTP HTOTAL=2144, VTOTAL=1244, dot clock=320.00MHz, HFREQ=149254, VFREQ=119.979Hz.
	0x31, 0x79,										// 310.25 MHz dot clock
	0x80, 0xA0, 0x70,								// HRES = 1920, HBL   = 160
	0xB0, 0x2B, 0x40,								// VRES = 1200, VBL   = 43, See ***NOTE1***
	0x10, 0x20,										// HFP  =   16, HSYNC =  32
	0x36, 0x00,										// VFP  =    3, VSYNC =   6
	0xE4, 0x2E, 0x11,								// H/V image size = 484 x 302 mm (16:10 w 22.5" diag)
	0x00, 0x00,										// No border
	0x1E,											// No stereo, syncs separated, V/HSYNC positive    

	// Since we now have 2 video timing descriptor blocks, no more space for a serial number block
//	0x00, 0x00, 0x00, 0xFF, 0x00, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x0A, 0x20, 0x20,	// Serial Number

	// Descriptor block 3 has monitor range limits.
	// EDID v1.3 spec says a range limits descriptor is a requirement.
	0x00, 0x00, 0x00, 0xFD, 0x00,
	0x3C, 0x78,										// VFREQ range 60 - 120 Hz.
	0x1E, 0xA0,										// HFREQ range 30 - 160 kHz. VIEWPixx needs 152.4 kHz.
	0x21,											// 330 MHz pixel clock.  NEC AS120 used 0x19=>250MHz, but should be OK for 200 MHz clock of DP.
	0x00, 0x0A, 0x20, 0x20, 0x20, 0x20, 0x20, 0x20,	// Just means use previous values

	// Descriptor block 4 is the monitor name, CD uses 0 padding.
	// First character must be 'D' for DATAPixx to recognize that an EDID has been written to SPI flash, or 'V' for VIEWPixx.
	0x00, 0x00, 0x00, 0xFC, 0x00,
	'V', 'I', 'E', 'W', 'P', 'i', 'x', 'x', 0x0A, 0x00, 0x00, 0x00, 0x00,

	0x00,											// Indicates no extension blocks in EDID 1.3.  CD had 0x1 here, seemed to cause fixed 2560x1600 w scaling.  That was BAD.
	0x00,											// Checksum.  Will be overwritten.



    // Second EDID for VIEWPixx3D
	0x00, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0x00,	// Header
	0x22, 0x64,										// Manuf ID.  0x22, 0x64 is value for Hanns.G.
	0x02, 0x02,										// Product ID.  Use 2/2 instead of 2/1 so I can recognize VIEWPixx3D
	0x01, 0x01, 0x01, 0x01,							// Little endian serial number, I don't use.  NEC sets to 0x01.
    1,   21,                                        // Week of manuf, Year of manuf (minus 1990). = 1st wk of 2011.
	0x01, 0x03,										// EDID version 1.3
	0x81,											// Bit 7 means digital video (or GPU doesn't gen DVI!), bit 0 means we support DLP, which seems to mean DVI.  NEC AS120 clears these, but we'll set them
	0x34, 0x1D,										// Max h/v image size of VIEWPixx3D is 52x29 cm.
    120,											//  / 100 + 1 gives gamma = 2.2, NEC sets to 0xBA = 186 = gamma of 2.86!
	0x0A,											// RGB color, bit 1 (preferred timing mode set) means that descriptor block 1 contains "Native" geometry (eg: an LCD).
    //	0x61, 0xE9, 0xA4, 0x52, 0x49, 0x98, 0x24, 0x0F, 0x48, 0x4C,  // Phosphor colours of NEC
    0x4B, 0x85, 0xAF, 0x4E, 0x2A, 0xA9, 0x1F, 0x1A, 0x50, 0x54, // LCD R=(.685,.305) G=(.166,.663) B=(.123,.102) D65=(.313,.329)
	0x00, 0x01,	0x00,								// Only acceptable standard timing is 1280x1024x75 = 139.18 MHz
    
	// The next block must contain exactly 8 pairs of bytes, each describing a mode.
	0x45, 0x7C,										//  800  x  600  x 120 Hz
	0x59, 0xFC,										//  960  x  540  x 120 Hz
	0x61, 0x59,										// 1024  x  768  x  85 Hz
	0xA9, 0xC0,										// 1600  x  900  x  60 Hz
	0xA9, 0xFC,										// 1600  x  900  x 120 Hz
	0xD1, 0xC0,										// 1920  x 1080  x  60 Hz
	0xD1, 0xE8,										// 1920  x 1080  x 100 Hz
	0xD1, 0xFC,										// 1920  x 1080  x 120 Hz
    
	// Next are 4 18-byte descriptor blocks which can appear in any order.
	// Since we set the "preferred timing mode set" bit above, descriptor 1 has to contain the "native" geometry.
	// LCD native timing is 1920 x 1080 x 120.00 Hz for VIEWPixx3D.  HFREQ = 155040Hz.  It's high to maximize VBLANK for stereo goggles.
    // DisplayPort dongle works best around 308MHz dot clock, but we'll go for 310MHz so VTOTAL is correct.
    // and active shutter goggles work best with largest possible VBL time, which we'll put into the vertical back porch.
    // ***NOTE1*** VTOTAL used here in test patterns should match VHDL test pattern VTOTAL.
    // Otherwise, scanning backlight luminance calibration won't apply to EDID-based video!
    // There could be a small difference, in which case the calibration would be off by the % difference;
    // eg: off by 1 scanline would be less than a 0.1% luminance calibration error.
    // Hmmm.  ViewSonic doesn't sync when we use an HFREQ of 155040 Hz.
#if 0
	0x20, 0x79,										// 310.08 MHz dot clock
	0x80, 0x50, 0x70,								// HRES = 1920, HBL   = 80
	0x38, 0xD4, 0x40,								// VRES = 1080, VBL   = 212, See ***NOTE1***
	0x10, 0x20,										// HFP  =   16, HSYNC =  32
	0x36, 0x00,										// VFP  =    3, VSYNC =   6
	0x09, 0x25, 0x21,								// H/V image size = 521 x 293 mm (16:9 w 23.6" diag)
	0x00, 0x00,										// No border
	0x1E,											// No stereo, syncs separated, V/HSYNC positive
    
    // With above EDID, ViewSonic alternates between HTOTAL=2048/2080, implying HFREQ=156250/153846.
    // HWTP run at constant HTOTAL=2064, HFREQ=155039, ViewSonic can't sync to this either.
    // Need to go below 155kHz.  Next step down is HWTP HTOTAL of 2080 for test patterns, giving an HFREQ of 153846.
    // Maybe ViewSonic doesn't like HTOTAL going below 2080?
    // So if we want HFREQ=153846, with ZFREQ=310MHz, HTOTAL=2015.  Nearest x32 is 2016.
    // EDID HTOTAL=2016, VTOTAL=1280, dot clock=309.66MHz, HFREQ=153601, VFREQ=120.001Hz.
    // HWTP HTOTAL=2080, VTOTAL=1282, dot clock=320.00MHz, HFREQ=153846, VFREQ=120.005Hz.
    // Since the HWTP HFREQ is slightly higher than the EDID HFREQ, EDID video sent to ViewSonic will have HTOTAL=2080/2096.
	0xF6, 0x78,										// 309.66 MHz dot clock
	0x80, 0x60, 0x70,								// HRES = 1920, HBL   = 96
	0x38, 0xC8, 0x40,								// VRES = 1080, VBL   = 200, See ***NOTE1***
	0x10, 0x20,										// HFP  =   16, HSYNC =  32
	0x36, 0x00,										// VFP  =    3, VSYNC =   6
	0x09, 0x25, 0x21,								// H/V image size = 521 x 293 mm (16:9 w 23.6" diag)
	0x00, 0x00,										// No border
	0x1E,											// No stereo, syncs separated, V/HSYNC positive
#endif

    // NOPE! ViewSonic V3D245 couldn't lock.
    // Have to reduce HFREQ to just under 150kHz.
    // EDID HTOTAL=2080, VTOTAL=1243, dot clock=310.25MHz, HFREQ=149159, VFREQ=119.999Hz.
    // HWTP HTOTAL=2144, VTOTAL=1244, dot clock=320.00MHz, HFREQ=149254, VFREQ=119.979Hz.
	0x31, 0x79,										// 310.25 MHz dot clock
	0x80, 0xA0, 0x70,								// HRES = 1920, HBL   = 160
	0x38, 0xA3, 0x40,								// VRES = 1080, VBL   = 163, See ***NOTE1***
	0x10, 0x20,										// HFP  =   16, HSYNC =  32
	0x36, 0x00,										// VFP  =    3, VSYNC =   6
	0x09, 0x25, 0x21,								// H/V image size = 521 x 293 mm (16:9 w 23.6" diag)
	0x00, 0x00,										// No border
	0x1E,											// No stereo, syncs separated, V/HSYNC positive
    
    // We'll do a 1920 x 1080 x 100.00 Hz; HFREQ = 155 kHz.
    // Don't want to go much lower than 100 Hz because we start to see the vertical artifact.
    // These timings won't sync with V3D245.  See notes for 120Hz mode.
#if 0
	0x18, 0x79,										// 310 MHz dot clock
	0x80, 0x50, 0x70,								// HRES = 1920, HBL   = 80
	0x38, 0xD6, 0x41,								// VRES = 1080, VBL   = 470, See ***NOTE1***
	0x10, 0x20,										// HFP  =   16, HSYNC =  32
	0x36, 0x00,										// VFP  =    3, VSYNC =   6
	0x09, 0x25, 0x21,								// H/V image size = 521 x 293 mm (16:9 w 23.6" diag)
	0x00, 0x00,										// No border
	0x1E,											// No stereo, syncs separated, V/HSYNC positive
#endif

    // EDID HTOTAL=2080, VTOTAL=1492, dot clock=310.34MHz, HFREQ=149202, VFREQ=100.001Hz.
    // HWTP HTOTAL=2144, VTOTAL=1493, dot clock=320.00MHz, HFREQ=149254, VFREQ=99.969Hz.
	0x3A, 0x79,										// 310.34 MHz dot clock
	0x80, 0xA0, 0x70,								// HRES = 1920, HBL   = 160
	0x38, 0x9C, 0x41,								// VRES = 1080, VBL   = 412, See ***NOTE1***
	0x10, 0x20,										// HFP  =   16, HSYNC =  32
	0x36, 0x00,										// VFP  =    3, VSYNC =   6
	0x09, 0x25, 0x21,								// H/V image size = 521 x 293 mm (16:9 w 23.6" diag)
	0x00, 0x00,										// No border
	0x1E,											// No stereo, syncs separated, V/HSYNC positive

	// Descriptor block 3 has monitor range limits.
	// EDID v1.3 spec says a range limits descriptor is a requirement.
	0x00, 0x00, 0x00, 0xFD, 0x00,
	0x3C, 0x78,										// VFREQ range 60 - 120 Hz.
	0x1E, 0xA0,										// HFREQ range 30 - 160 kHz.
	0x21,											// 330 MHz pixel clock.  NEC AS120 used 0x19=>250MHz, but should be OK for 200 MHz clock of DP.
	0x00, 0x0A, 0x20, 0x20, 0x20, 0x20, 0x20, 0x20,	// Just means use previous values

	// Descriptor block 4 is the monitor name, CD uses 0 padding.
	// First character must be 'D' for DATAPixx to recognize that an EDID has been written to SPI flash, or 'V' for VIEWPixx.
    // (Actually VIEWPixx no longer supports EDID in SPI.)
	0x00, 0x00, 0x00, 0xFC, 0x00,
	'V', 'I', 'E', 'W', 'P', 'i', 'x', 'x', '3', 'D', 0x0A, 0x00, 0x00,
    
	0x00,											// Indicates no extension blocks in EDID 1.3.  CD had 0x1 here, seemed to cause fixed 2560x1600 w scaling.  That was BAD.
	0x00											// Checksum.  Will be overwritten.
};


// The initial EDID for factory PROPixx
unsigned char propixxEdid[128] = {
	0x00, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0x00,	// Header
	0x22, 0x64,										// Manuf ID.  0x22, 0x64 is value for Hanns.G.
	0x02, 0x02,										// Product ID.  Use 2/2 instead of 2/1 so I can recognize VIEWPixx3D
	0x01, 0x01, 0x01, 0x01,							// Little endian serial number, I don't use.  NEC sets to 0x01.
    1,   21,                                        // Week of manuf, Year of manuf (minus 1990). = 1st wk of 2011.
	0x01, 0x03,										// EDID version 1.3
	0x81,											// Bit 7 means digital video (or GPU doesn't gen DVI!), bit 0 means we support DLP, which seems to mean DVI.  NEC AS120 clears these, but we'll set them
	0x34, 0x1D,										// Max h/v image size of VIEWPixx3D is 52x29 cm.  Don't really know what to put for projector...
    120,											//  / 100 + 1 gives gamma = 2.2, NEC sets to 0xBA = 186 = gamma of 2.86!
	0x0A,											// RGB color, bit 1 (preferred timing mode set) means that descriptor block 1 contains "Native" geometry (eg: an LCD).
    //	0x61, 0xE9, 0xA4, 0x52, 0x49, 0x98, 0x24, 0x0F, 0x48, 0x4C,  // Phosphor colours of NEC
    0x4B, 0x85, 0xAF, 0x4E, 0x2A, 0xA9, 0x1F, 0x1A, 0x50, 0x54, // LCD R=(.685,.305) G=(.166,.663) B=(.123,.102) D65=(.313,.329)
	0x00, 0x01,	0x00,								// Only acceptable standard timing is 1280x1024x75 = 139.18 MHz
    
	// The next block must contain exactly 8 pairs of bytes, each describing a mode.
	0x45, 0x7C,										//  800  x  600  x 120 Hz
	0x59, 0xFC,										//  960  x  540  x 120 Hz
	0x61, 0x59,										// 1024  x  768  x  85 Hz
	0xA9, 0xC0,										// 1600  x  900  x  60 Hz
	0xA9, 0xFC,										// 1600  x  900  x 120 Hz
	0xD1, 0xC0,										// 1920  x 1080  x  60 Hz
	0xD1, 0xE8,										// 1920  x 1080  x 100 Hz
	0xD1, 0xFC,										// 1920  x 1080  x 120 Hz
    
	// Next are 4 18-byte descriptor blocks which can appear in any order.
	// Since we set the "preferred timing mode set" bit above, descriptor 1 has to contain the "native" geometry.
	// LCD native timing is 1920 x 1080 x 120.00 Hz for VIEWPixx3D.  HFREQ = 148.15kHz.
    // DisplayPort dongle works best around 308MHz dot clock,
    // and active shutter goggles work best with largest possible VBL time, which we'll put into the vertical back porch.
	0x5F, 0x78,										// 308.15 MHz
	0x80, 0xA0, 0x70,								// HRES = 1920, HBL   = 160
	0x38, 0x9B, 0x40,								// VRES = 1080, VBL   = 155
	0x30, 0x20,										// HFP  =   48, HSYNC =  32
	0x36, 0x00,										// VFP  =    3, VSYNC =   6
	0x09, 0x25, 0x21,								// H/V image size = 521 x 293 mm (16:9 w 23.6" diag)
	0x00, 0x00,										// No border
	0x1E,											// No stereo, syncs separated, V/HSYNC positive
    
    // We'll do a 1920 x 1080 x 100.00 Hz; HFREQ = 148.00 kHz.
    // Don't want to go much lower than 100 Hz because we start to see the vertical artifact.
    // Use close to the 308 MHz dot clock, since the DisplayPort->DVI dongles seem to like it.
    // All of our EDIDs will use about 148kHz HFREQ to ensure that VP decides it is lockable.
	0x40, 0x78,										// 307.84 MHz
	0x80, 0xA0, 0x70,								// HRES = 1920, HBL   = 160
	0x38, 0x90, 0x41,								// VRES = 1080, VBL   = 400
	0x30, 0x20,										// HFP  =   48, HSYNC =  32
	0x36, 0x00,										// VFP  =    3, VSYNC =   6
	0x09, 0x25, 0x21,								// H/V image size = 521 x 293 mm (16:9 w 23.6" diag)
	0x00, 0x00,										// No border
	0x1E,											// No stereo, syncs separated, V/HSYNC positive
    
	// Descriptor block 3 has monitor range limits.
	// EDID v1.3 spec says a range limits descriptor is a requirement.
	0x00, 0x00, 0x00, 0xFD, 0x00,
	0x3C, 0x78,										// VFREQ range 60 - 120 Hz.
	0x1E, 0xA0,										// HFREQ range 30 - 160 kHz. VIEWPixx needs 152.4 kHz.
	0x21,											// 330 MHz pixel clock.  NEC AS120 used 0x19=>250MHz, but should be OK for 200 MHz clock of DP.
	0x00, 0x0A, 0x20, 0x20, 0x20, 0x20, 0x20, 0x20,	// Just means use previous values
    
	// Descriptor block 4 is the monitor name, CD uses 0 padding.
	// First character must be 'D' for DATAPixx to recognize that an EDID has been written to SPI flash, or 'V' for VIEWPixx.
	0x00, 0x00, 0x00, 0xFC, 0x00,
	'P', 'R', 'O', 'P', 'i', 'x', 'x', 0x0A, 0x00, 0x00, 0x00, 0x00, 0x00,
    
	0x00,											// Indicates no extension blocks in EDID 1.3.  CD had 0x1 here, seemed to cause fixed 2560x1600 w scaling.  That was BAD.
	0x00											// Checksum.  Will be overwritten.
};


unsigned char *srcEdid;
unsigned char edid[256];
unsigned char* edidDescriptorBase;

struct {
	int hActive;
	int hFrontPorch;
	int hSync;
	int hTotal;
	int vActive;
	int vFrontPorch;
	int vSync;
	int vTotal;
	float hFreq;	// floats, not doubles, so sscanf %f input specifier works
	float vFreq;
	float zFreq;
} gtfParams;


// mode = 0   means update user EDID structure within DATAPixx flash with user-specified custom video timings.
// mode = 'd' means write a Lattice FPGA .mem initialization file to regen FPGA EDID RAM for next DATAPixx VHDL compile.
// mode = 'v' means write an Altera FPGA .mif initialization file to regen FPGA EDID RAM for next VIEWPixx VHDL compile.
// mode = 'p' means write an Altera FPGA .mif initialization file to regen FPGA EDID RAM for next PROPixx VHDL compile.
void DPxEdidWrite(int mode)
{
	FILE* fp = NULL;
	int i;
	int payloadLength;
	unsigned char checksum = 0;
	int spiAddr;
	int iConfig;
	char str[256];

	double minVsyncPlusVBackPorch;
	double hPeriodEstimate;
	int vSyncPlusVBackPorch;
	double idealHBlankDutyCycle;
	int hBlank;
	int edidPixelClock;
	int edidHBlank, edidVBlank;
    int srcEdidSize;
    int eraseUserEdid;

	// Sanity clause
	if (mode != 0 && mode != 'd' && mode != 'v' && mode != 'p') {
		printf("ERROR: Unrecognized mode %d\n", mode);
		return;
	}

    // mode 0 is used to program a user EDID inside SPI flash.
    // We'll say that we only support this on the DATAPixx.
    // VIEWPixx, VIEWPixx/3D, PROPixx will only support the VHDL hard-coded EDID.
    if (mode == 0 && (DPxIsViewpixx() || DPxIsPropixx())) {
		printf("ERROR: User EDID programming is only supported on the DATAPixx\n");
		return;        
    }
    
	// Make working copy of the factory EDID.
	if (mode == 'v' || (mode == 0 && DPxIsViewpixx())) {
		srcEdid = viewpixxEdid;
        srcEdidSize = 256;
    }
	else if (mode == 'p' || (mode == 0 && DPxIsPropixx())) {
		srcEdid = propixxEdid;
        srcEdidSize = 128;
    }
	else {
		srcEdid = datapixxEdid;
        srcEdidSize = 128;
    }

	for (i = 0; i < srcEdidSize; i++)
		edid[i] = srcEdid[i];

	// For DATAPixx, get user-specified custom video timings, and program user EDID in SPI.
    // As a special case, if user enters hActive of 0, we'll erase the user EDID block to restore factory EDID.
    eraseUserEdid = 0;
	if (!(DPxIsViewpixx() || DPxIsPropixx()) && mode == 0) {
		for (iConfig = 0; iConfig < 2; iConfig++) {
			printf("Enter configuration %d horizontal resolution: [1280]: ", iConfig+1);
			fgets(str, 256, stdin);
			if (sscanf(str, "%d", &gtfParams.hActive) != 1)
				gtfParams.hActive = 1280;
            if (gtfParams.hActive == 0) {
                eraseUserEdid = 1;
                break;
            }
			printf("Enter configuration %d vertical resolution: [1024]: ", iConfig+1);
			fgets(str, 256, stdin);
			if (sscanf(str, "%d", &gtfParams.vActive) != 1)
				gtfParams.vActive = 1024;
			printf("Enter configuration %d refresh rate: [75]: ", iConfig+1);
			fgets(str, 256, stdin);
			if (sscanf(str, "%f", &gtfParams.vFreq) != 1)
				gtfParams.vFreq = 75.0;

			// Vertical Timing
			gtfParams.vFrontPorch	= 1;
			gtfParams.vSync			= 3;
			minVsyncPlusVBackPorch	= 550.0e-6;		// Standard minimum acceptable duration of vertical sync pulse plus back porch, in seconds
			hPeriodEstimate			= ((1.0 / gtfParams.vFreq) - minVsyncPlusVBackPorch) / (gtfParams.vActive + gtfParams.vFrontPorch);
			vSyncPlusVBackPorch		= (int)floor(minVsyncPlusVBackPorch / hPeriodEstimate + 0.5);
			gtfParams.vTotal		= gtfParams.vActive + gtfParams.vFrontPorch + vSyncPlusVBackPorch;
			if (gtfParams.vTotal & 1)				// Force even VTOTAL,
				gtfParams.vTotal++;					// so refresh rate doubling will not be interpreted as an interlaced signal

			// Horizontal Timing
			// hBlank duration targets an "ideal" duty cycle.
			// "Standard" GTF actually forces hActive to be a multiple of character width (defaults to 8),
			// so we confirm this in our sanity checking code.
			// GTF also requires hSync to be a multiple of the character width, and hBlank to be a multiple of twice the character width.
			// Standard GTF character width is 8, so we'll follow that same timing.
			gtfParams.hFreq			= gtfParams.vFreq * gtfParams.vTotal;
			idealHBlankDutyCycle	= 0.3 - (3000 / gtfParams.hFreq);
			hBlank					= (int)floor(gtfParams.hActive * idealHBlankDutyCycle / (1 - idealHBlankDutyCycle) / 16.0 + 0.5) * 16;
			gtfParams.hTotal		= gtfParams.hActive + hBlank;
			gtfParams.zFreq			= gtfParams.hFreq * gtfParams.hTotal;
			gtfParams.hSync			= (int)(floor(gtfParams.hTotal * 0.08 / 8 + 0.5) * 8);	// Nominal HSYNC pulse length is 8% of horizontal period
			gtfParams.hFrontPorch	= hBlank / 2 - gtfParams.hSync;

			// Sanity clause
			if (gtfParams.hActive & 7) {
				printf("ERROR: Horizontal resolution of %d is not a multiple of 8\n", gtfParams.hActive);
				return;
			}
			if (gtfParams.vFreq < 50 || gtfParams.vFreq > 500) {
				printf("ERROR: Refresh rate of %.1fHz is outside the valid range of 50-500Hz\n", gtfParams.vFreq);
				return;
			}
			if (gtfParams.zFreq < 20e6 || gtfParams.zFreq > 330e6) {
				printf("ERROR: Dot frequency of %.1fMHz is outside the valid range of 20-330MHz\n", gtfParams.zFreq / 1.0e6);
				return;
			}

			// Overwrite factory EDID timing fields
			edidPixelClock	= (int)floor(gtfParams.zFreq / 10000.0 + 0.5);
			edidHBlank		= gtfParams.hTotal - gtfParams.hActive;
			edidVBlank		= gtfParams.vTotal - gtfParams.vActive;
			edidDescriptorBase		= edid + (iConfig ? 72 : 54);
			edidDescriptorBase[0]	= (unsigned char)(edidPixelClock & 0x00FF);
			edidDescriptorBase[1]	= (unsigned char)((edidPixelClock & 0xFF00) >> 8);
			edidDescriptorBase[2]	= (unsigned char)(gtfParams.hActive & 0x00FF);
			edidDescriptorBase[3]	= (unsigned char)(edidHBlank & 0x00FF);
			edidDescriptorBase[4]	= (unsigned char)(((gtfParams.hActive & 0x0F00) >> 4) + ((edidHBlank & 0x0F00) >> 8));
			edidDescriptorBase[5]	= (unsigned char)(gtfParams.vActive & 0x00FF);
			edidDescriptorBase[6]	= (unsigned char)(edidVBlank & 0x00FF);
			edidDescriptorBase[7]	= (unsigned char)(((gtfParams.vActive & 0x0F00) >> 4) + ((edidVBlank & 0x0F00) >> 8));
			edidDescriptorBase[8]	= (unsigned char)(gtfParams.hFrontPorch & 0x00FF);
			edidDescriptorBase[9]	= (unsigned char)(gtfParams.hSync & 0x00FF);
			edidDescriptorBase[10]	= (unsigned char)(((gtfParams.vFrontPorch & 0x000F) << 4) + (gtfParams.vSync & 0x000F));
			edidDescriptorBase[11]	= (unsigned char)(((gtfParams.hFrontPorch & 0x0300) >> 2) +
													  ((gtfParams.hSync & 0x0300) >> 4) +
													  ((gtfParams.vFrontPorch & 0x0030) >> 2) +
													  ((gtfParams.vSync & 0x0030) >> 4));
			edidDescriptorBase[17]	= (unsigned char)0x1E;											// No stereo, syncs separated, V/HSYNC positive
		}
	}

	// Calculate checksum
    checksum = 0;
	for (i = 0; i < 127; i++)
		checksum += edid[i];
	edid[127] = (-checksum) & 0x00ff;	// Overwrite with correct checksum

    // Either make a copy of first edid, or compute checksum of second edid
    if (srcEdidSize == 128) {
        for (i = 0; i < 128; i++)
            edid[i+128] = edid[i];
    }
    else {
        checksum = 0;
        for (i = 128; i < 255; i++)
            checksum += edid[i];
        edid[255] = (-checksum) & 0x00ff;
    }

	// mode = 'd' means write a Lattice FPGA .mem initialization file to regen FPGA EDID RAM for next DATAPixx VHDL compile.
	// Write 2 copies of EDID to initialize both the factory and custom EDID SRAM.
	if (mode == 'd') {
		fp = fopen("EDID.mem", "wb");
		if (!fp) {
			fprintf(stderr, "ERROR: Couldn't open edid.mem\n");
			return;
		}
		fprintf(fp, "#Format=Hex\n#Depth=256\n#Width=8\n#Data\n");
		for (i = 0; i < 256; i++)
			fprintf(fp, "%02x\n", edid[i]);
		fclose(fp);
		return;
	}

	// mode = 'v' means write an Altera FPGA .mif initialization file to regen FPGA EDID RAM for next VIEWPixx VHDL compile.
	// Write 2 EDIDs for VIEWPixx and VIEWPixx3D.
	// mode = 'p' is similar, but for PROPixx.
	if (mode == 'v' || mode == 'p') {
		fp = fopen("EDID.mif", "wb");
		if (!fp) {
			fprintf(stderr, "ERROR: Couldn't open edid.mif\n");
			return;
		}
		fprintf(fp, "WIDTH=8;\nDEPTH=256;\nADDRESS_RADIX=HEX;\nDATA_RADIX=HEX;\nCONTENT BEGIN\n");
		for (i = 0; i < 256; i++)
			fprintf(fp, "%02x : %02x;\n", i, edid[i]);
		fprintf(fp, "END;\n");
		fclose(fp);
        
        // Know what?  While I'm at it, I'll make the CLUT_RAM.mif as well
		fp = fopen("CLUT_RAM.mif", "wb");
		if (!fp) {
			fprintf(stderr, "ERROR: Couldn't open CLUT_RAM.mif\n");
			return;
		}
		fprintf(fp, "WIDTH=48;\nDEPTH=512;\nADDRESS_RADIX=HEX;\nDATA_RADIX=HEX;\nCONTENT BEGIN\n");
		for (i = 0; i < 512; i++)
			fprintf(fp, "%03x : %02x%02x%02x%02x%02x%02x;\n", i, i%256, i%256, i%256, i%256, i%256, i%256);
		fprintf(fp, "END;\n");
		fclose(fp);
        
		return;
	}

	// From here on in, we're definitely in mode 0.
	// Pass 128 bytes of EDID data to DATAPixx volatile SRAM.
	// We'll actually pass 2 copies, since we don't know which of the 128-byte banks the FPGA is using.
	// (If the user has programmed a custom EDID, FPGA is using bank 1, otherwise bank 0).
	// The next time the OS reads the EDID, it will see the new structure.
	// Note that this is temporary.  Will be replaced by EDID from FPGA or SPI flash data on next powerup.
    // If we've been asked to clear the EDID, we'll replace with FF's.  SPI will look like it's been erased.
    // Note that the DP will now have an invalid EDID in its FPGA, and will have to be power cycled.
    if (eraseUserEdid)
        memset(edid, 0xFF, sizeof(edid));
	payloadLength = 512;
	ep2out_Tram[0] = '^';
	ep2out_Tram[1] = EP2OUT_WRITEEDID;
	ep2out_Tram[2] = LSB(payloadLength);
	ep2out_Tram[3] = MSB(payloadLength);    
	for (i = 0; i < payloadLength/2; i++) {
		ep2out_Tram[i*2+4] = edid[i];
		ep2out_Tram[i*2+5] = i;
	}
	if (EZWriteEP2Tram(ep2out_Tram, 0, 0)) {
		DPxDebugPrint0("ERROR: DPxEdidWrite() call to EZWriteEP2Tram() failed\n");
		DPxSetError(DPX_ERR_VID_EDID_WRITE_USB_ERROR);
	}

	// Write EDID to non-volatile SPI flash so that it reloads on next DATAPixx powerup.
	printf("Writing EDID to SPI\n");
    spiAddr = DPxIsViewpixx() ? SPI_ADDR_VPX_EDID : SPI_ADDR_DPX_EDID;
    DPxSpiErase(spiAddr, 128, NULL);
    DPxSpiWrite(spiAddr, 128, edid, NULL);

    // Reload SPI so EDID is available next time system queries
    DPxEnableCalibReload();
    printf("EDID has been updated.  You may have to reboot for changes to take effect.\n");
}


#define HIGH_CAL_DAC_VALUE	0x6000	// Gives +7.5V on +-10V DACs
#define LOW_CAL_DAC_VALUE	0xA000	// Gives -7.5V on +-10V DACs

void DPxCalibRead()
{
	int spiAddr;
	unsigned char dataBuff[88], *dataPtr;
	int iChan;
	unsigned short param;
	double m, b;

    spiAddr = (DPxIsViewpixx() || DPxIsPropixx()) ? SPI_ADDR_VPX_ANALOG : SPI_ADDR_DPX_ANALOG;
    if (DPxSpiRead(spiAddr, 88, dataBuff, NULL)) {
        fprintf(stderr, "ERROR: Could not read SPI\n");
        return;
    }

    dataPtr = dataBuff;
	for (iChan = 0; iChan < 22; iChan++) {
		param = *dataPtr++ << 8;
		param += *dataPtr++;
		m = (param + 32768.0) / 65536.0;
		param = *dataPtr++ << 8;
		param += *dataPtr++;
		b = (signed short)param;
		if (iChan < 4)
			printf("DAC[%d]", iChan);
		else if (iChan < 20)
			printf("ADC[%d]", iChan - 4);
		else
			printf("REF[%d]", iChan - 20);
		printf(" m = %.5f, b = %.1f\n", m, b);
		if (iChan == 3)
			printf("\n");
    }
}


void DPxCalibWrite()
{
	double adcFDatum;
	double dacHighV[4];
	double dacLowV[4];
	double sx[18], sx2[18];
	double adcHighMeanDatum[18];
	double adcLowMeanDatum[18];
	double adcMean, adcSD;
	double rangeMin, rangeMax;
	double highCalDatum, lowCalDatum;
	double adcHighV, adcLowV;
	double m, b;
	char str[256];
	int i, iChan;
	int lsbRange;
	signed short adcDatum, adcMin[18], adcMax[18];
	int nSamples;
	signed short dacHighRawDatum, dacLowRawDatum;
	unsigned short dacVhdlm[4];
	signed short dacVhdlb[4];
	unsigned short adcVhdlm[18];
	signed short adcVhdlb[18];
	int spiAddr;
	unsigned char dataBuff[88], *dataPtr;

	// Set the DACs and ADCs to bypass calibration
	DPxEnableDacCalibRaw();
	DPxEnableAdcCalibRaw();

	// Write the DAC values for the first calibration voltage
	printf("Enter first calibration DAC datum (hit enter for 0x%0X): ", HIGH_CAL_DAC_VALUE);
	fgets(str, 256, stdin);
	dacHighRawDatum = DPxStringToInt(str);
	if (dacHighRawDatum == 0)
		dacHighRawDatum = HIGH_CAL_DAC_VALUE;
	printf("Using DAC datum 0x%0X\n", (int)dacHighRawDatum & 0x0000FFFF);
	DPxSetDacValue(dacHighRawDatum, 0);
	DPxSetDacValue(dacHighRawDatum, 1);
	DPxSetDacValue(dacHighRawDatum, 2);
	DPxSetDacValue(dacHighRawDatum, 3);
	DPxEnableAdcFreeRun();
	DPxUpdateRegCache();
	if (DPxGetError())
		{ fprintf(stderr, "ERROR: Could not set initial DAC values\n"); return; }

	// Get the precision measured voltages from user
	printf("Enter measured voltages for DAC0 - DAC3: ");
	fgets(str, 256, stdin);
	if (sscanf(str, "%lf%lf%lf%lf", dacHighV, dacHighV+1, dacHighV+2, dacHighV+3) != 4) {
		printf("Couldn't read voltages\n");
		return;
	}

	// Read the ADCs 1000 times, and calculate the mean voltages
	for (i = 0; i < 18; i++) {
		sx[i] = 0;
		sx2[i] = 0;
		adcMin[i] = 0x7fff;	// Largest signed short
		adcMax[i] = 0x8000;	// Smallest signed short
	}

	nSamples = 1000;
	
	for (i = 0; i < nSamples; i++) {
		DPxUpdateRegCache();
		for (iChan = 0; iChan < 18; iChan++) {
			adcDatum = DPxGetAdcValue(iChan);
			adcFDatum = adcDatum;	// Convert from signed short to double.
			sx[iChan] += adcFDatum;
			sx2[iChan] += adcFDatum * adcFDatum;
			if (adcMin[iChan] > adcDatum)
				adcMin[iChan] = adcDatum;
			if (adcMax[iChan] < adcDatum)
				adcMax[iChan] = adcDatum;
		}
	}

	for (iChan = 0; iChan < 18; iChan++) {
		adcMean = sx[iChan] / nSamples;
		adcSD = sqrt(nSamples*sx2[iChan] - sx[iChan]*sx[iChan]) / nSamples;
		lsbRange = adcMax[iChan] - adcMin[iChan];
		printf("ch%02d: mean = %7.4fV, sd = %7.4fV, +-LSB = %d\n", iChan, adcMean / 32768.0 * 10.0, adcSD / 32768.0 * 10.0, lsbRange/2);
		adcHighMeanDatum[iChan] = adcMean;
	}

	// Write the DAC values for the second calibration voltage
	printf("Enter second calibration DAC datum (hit enter for 0x%0X): ", LOW_CAL_DAC_VALUE);
	fgets(str, 256, stdin);
	dacLowRawDatum = DPxStringToInt(str);
	if (dacLowRawDatum == 0)
		dacLowRawDatum = LOW_CAL_DAC_VALUE;
	printf("Using DAC datum 0x%0X\n", (int)dacLowRawDatum & 0x0000FFFF);
	DPxSetDacValue(dacLowRawDatum, 0);
	DPxSetDacValue(dacLowRawDatum, 1);
	DPxSetDacValue(dacLowRawDatum, 2);
	DPxSetDacValue(dacLowRawDatum, 3);
	DPxUpdateRegCache();
	if (DPxGetError())
		fprintf(stderr,"ERROR: call to EZWriteEP2Tram() failed\n");

	// Get the precision measured voltages from user
	printf("Enter measured voltages for DAC0 - DAC3: ");
	fgets(str, 256, stdin);
	if (sscanf(str, "%lf%lf%lf%lf", dacLowV, dacLowV+1, dacLowV+2, dacLowV+3) != 4) {
		printf("Couldn't read voltages\n");
		return;
	}

	// Read the ADCs 1000 times, and calculate the mean voltages
	for (i = 0; i < 18; i++) {
		sx[i] = 0;
		sx2[i] = 0;
		adcMin[i] = 0x7fff;	// Largest signed short
		adcMax[i] = 0x8000;	// Smallest signed short
	}

	for (i = 0; i < nSamples; i++) {
		DPxUpdateRegCache();
		for (iChan = 0; iChan < 18; iChan++) {
			adcDatum = DPxGetAdcValue(iChan);
			adcFDatum = adcDatum;	// Convert from signed short to double.
			sx[iChan] += adcFDatum;
			sx2[iChan] += adcFDatum * adcFDatum;
			if (adcMin[iChan] > adcDatum)
				adcMin[iChan] = adcDatum;
			if (adcMax[iChan] < adcDatum)
				adcMax[iChan] = adcDatum;
		}
	}

	for (iChan = 0; iChan < 18; iChan++) {
		adcMean = sx[iChan] / nSamples;
		adcSD = sqrt(nSamples*sx2[iChan] - sx[iChan]*sx[iChan]) / nSamples;
		lsbRange = adcMax[iChan] - adcMin[iChan];
		printf("ch%02d: mean = %7.4fV, sd = %7.4fV, +-LSB = %d\n", iChan, adcMean / 32768.0 * 10.0, adcSD / 32768.0 * 10.0, lsbRange/2);
		adcLowMeanDatum[iChan] = adcMean;
	}

	// Calculate mx+b terms to map DAC calib datum to raw datum.
	printf("\n");
	for (iChan = 0; iChan < 4; iChan++) {
        DPxGetDacRange(iChan, &rangeMin, &rangeMax);
		highCalDatum = dacHighV[iChan] / rangeMax * 32768.0;
		lowCalDatum = dacLowV[iChan] / rangeMax * 32768.0;
		m = ((double)dacHighRawDatum - (double)dacLowRawDatum) / (highCalDatum - lowCalDatum);
		b = dacLowRawDatum - m * lowCalDatum;
		printf("DAC[%d] m = %.5f, b = %.1f\n", iChan, m, b);
		if (m < 0.75 || m > 1.25 || b < -8192 || b > 8192) {	// Sanity check
			fprintf(stderr,"ERROR: DAC calibration factors out of range\n");
			return;
		}
		dacVhdlm[iChan] = floor(m * 65536 - 32768 + 0.5);		// scale to 16-bit unsigned cal factor, and offset to give range of 0.5-1.5x
		dacVhdlb[iChan] = floor(b + 0.5);						// Round to integer offset which will be used in VHDL calibration

		// See if extreme values will clamp in VHDL; ie: is a DAC physically capable of outputting its full +-10V (or 5V) range?
		// Need to do in double for enough sig digits.
		if (((dacVhdlm[iChan] + 32768.0) *  0x7FFF + dacVhdlb[iChan] > ( 0x7FFF * 65536.0)) ||
			((dacVhdlm[iChan] + 32768.0) * -0x8000 + dacVhdlb[iChan] < (-0x8000 * 65536.0)))
			printf("                            WARNING: DAC cannot drive full +-%dV range\n", (int)rangeMax);
	}

	// Calculate mx+b terms to map ADC raw datum to calib datum.
	printf("\n");
	for (iChan = 0; iChan < 18; iChan++) {
		if (iChan == 17) {
			adcHighV = dacHighV[3];
			adcLowV = dacLowV[3];
		}
		else if (iChan == 16) {
			adcHighV = dacHighV[2];
			adcLowV = dacLowV[2];
		}
		else if (iChan & 1) {
			adcHighV = dacHighV[1];
			adcLowV = dacLowV[1];
		}
		else {
			adcHighV = dacHighV[0];
			adcLowV = dacLowV[0];
		}

		highCalDatum = adcHighV / 10.0 * 32768.0;
		lowCalDatum = adcLowV / 10.0 * 32768.0;
		m = (highCalDatum - lowCalDatum) / (adcHighMeanDatum[iChan] - adcLowMeanDatum[iChan]);
		b = lowCalDatum - m * adcLowMeanDatum[iChan];
		printf("ADC[%d] m = %.5f, b = %.1f\n", iChan, m, b);
		if (m < 0.75 || m > 1.25 || b < -8192 || b > 8192) {	// Sanity check
			fprintf(stderr,"ERROR: ADC calibration factors out of range\n");
			return;
		}
		adcVhdlm[iChan] = floor(m * 65536 - 32768 + 0.5);		// scale to 16-bit unsigned cal factor, and offset to give range of 0.5-1.5x
		adcVhdlb[iChan] = floor(b + 0.5);						// Round to integer offset which will be used in VHDL calibration

		// See if extreme values will clamp in VHDL; ie: is the full +-10V range within the ADC's output codes?
		// Need to do in double for enough sig digits.
		if (((adcVhdlm[iChan] + 32768.0) *  0x7FFF + adcVhdlb[iChan] < ( 0x7FFF * 65536.0)) ||
			((adcVhdlm[iChan] + 32768.0) * -0x8000 + adcVhdlb[iChan] > (-0x8000 * 65536.0)))
			printf("                            WARNING: ADC cannot decode full +-10V range.  VHDL will clamp.\n");
	}

    // Put the data into a buffer
    dataPtr = dataBuff;
    for (iChan = 0; iChan < 4; iChan++) {
        *dataPtr++ = MSB(dacVhdlm[iChan]);
        *dataPtr++ = LSB(dacVhdlm[iChan]);
        *dataPtr++ = MSB(dacVhdlb[iChan]);
        *dataPtr++ = LSB(dacVhdlb[iChan]);
    }
    for (iChan = 0; iChan < 18; iChan++) {
        *dataPtr++ = MSB(adcVhdlm[iChan]);
        *dataPtr++ = LSB(adcVhdlm[iChan]);
        *dataPtr++ = MSB(adcVhdlb[iChan]);
        *dataPtr++ = LSB(adcVhdlb[iChan]);
    }

	// Write the calibration info to the SPI.
	// I'll assume that the FPGA is not accessing the SPI device.
	// It should be OK.  FPGA only accesses SPI for less than a millisecond, right after reset.
	// This way, I don't get screen flash, EZ Slave interface problems, etc.
	printf("Writing calibration to SPI\n");
    spiAddr = (DPxIsViewpixx() || DPxIsPropixx()) ? SPI_ADDR_VPX_ANALOG : SPI_ADDR_DPX_ANALOG;
    DPxSpiErase(spiAddr, 88, NULL);
    DPxSpiWrite(spiAddr, 88, dataBuff, NULL);

	// Put DAC/ADC back into calibration mode,
	// and tell CALIB_CTRL to reload its calibration table from SPI.
	DPxDisableDacCalibRaw();
	DPxDisableAdcCalibRaw();
	DPxEnableCalibReload();
	DPxUpdateRegCache();
}


// Reload DAC and ADC hardware calibration tables
void DPxEnableCalibReload()
{
	DPxSetReg16(DPXREG_CTRL, DPxGetReg16(DPXREG_CTRL) | DPXREG_CTRL_CALIB_RELOAD);
}


int DPxStringToInt(char* string)
{
	int i;
	int retVal;
	
	// Convert to lower case.  Helps with hex "0x", hex digits, and maybe exponential?
	for (i = 0; string[i]; i++)
		string[i] = tolower(string[i]);

	// We accept hex, and decimal strings
	if (!strchr(string, 'x'))
		return atoi(string);
	sscanf(string, "%x", &retVal);
	return retVal;
}


// Scan USB device tree in search of a DATAPixx
void DPxUsbScan(int doPrint)
{
	struct usb_bus*		bus = NULL;
	struct usb_device*	dev = NULL;
	char*				tag = NULL;
	int					rc;

	// One-time initialization of libusb, important for linux.
	if (!dpxInitialized) {
		usb_init();
		dpxInitialized = 1;
	}

	// (Re)scan the USB device tree
	if (doPrint)
		printf(" Scan of USB devices:\n");

	// We'll always rescan from scratch, in order to catch recent connects/disconnects.
	// If we detect a DATAPixx during this scan, we'll use the newfound DATAPixx;
	// so we'll start this scan by closing any existing DATAPixx which we might already be using.
	DPxClose();
	dpxDev = NULL;
	dpxRawUsb = 0;
    dpxIsViewpixx = 0;
    dpxIsPropixx = 0;

	// Repopulate libusb's USB hierarchy
	usb_find_busses();
	usb_find_devices();

	// and look for our baby
	for (bus = usb_busses; bus; bus = bus->next) {
		for (dev = bus->devices; dev; dev = dev->next) {
			if (dev->descriptor.idVendor == 0x04b4 && dev->descriptor.idProduct == 0x8613) {		// Unconfigured EZ-USB
				dpxDev = dev;
				dpxRawUsb = 1;
                dpxIsViewpixx = 0;
                dpxIsPropixx = 0;
				tag = "(Unprogrammed EZ-USB)";
			}
			else if (dev->descriptor.idVendor == DPX_VID && dev->descriptor.idProduct == DPX_PID) {
				dpxDev = dev;
				dpxRawUsb = 0;
                dpxIsViewpixx = 0;
                dpxIsPropixx = 0;
				tag = "(DATAPixx)";
			}
			else if (dev->descriptor.idVendor == DPX_VID && dev->descriptor.idProduct == VPX_PID) {
				dpxDev = dev;
				dpxRawUsb = 0;
                dpxIsViewpixx = 1;
                dpxIsPropixx = 0;
				tag = "(VIEWPixx)";
			}
			else if (dev->descriptor.idVendor == DPX_VID && dev->descriptor.idProduct == PPX_PID) {
				dpxDev = dev;
				dpxRawUsb = 0;
                dpxIsViewpixx = 0;
                dpxIsPropixx = 1;
				tag = "(PROPixx)";
			}
			else
				tag = "";
			if (doPrint)
				printf("  Vendor ID = 0x%04x, Product ID = 0x%04x %s\n", dev->descriptor.idVendor, dev->descriptor.idProduct, tag);
		}
	}

	// No DATAPixx found in the system?
	if (!dpxDev) {
		dpxHdl = NULL;	// In case there used to be one, but it's gone now.  User could have pulled it.
		DPxSetError(DPX_ERR_USB_NO_DATAPIXX);
		goto Done;
	}

	// We'll set a global error if the interface is raw.
	// User can look for this special case if they can handle a raw device.
	if (dpxRawUsb)
		DPxSetError(DPX_ERR_USB_RAW_EZUSB);

	// If we already have a DATAPixx open from a previous call, just return it.
	// NOTE: Must put this _after_ the DPX_ERR_USB_RAW_EZUSB above.
	// NOTE: Our current strategy is to close the DP on entry, so this condition will never be true.
	if (dpxHdl)
		goto Done;

	// If we found a new DP, setup an interface handle
	dpxHdl = usb_open(dpxDev);
	if (!dpxHdl) {
		DPxDebugPrint0("ERROR: Could not open DATAPixx!\n");
		DPxSetError(DPX_ERR_USB_OPEN);
		goto Done;
	}

	rc = usb_set_configuration(dpxHdl, 1);
	if (rc < 0) {
		DPxDebugPrint1("ERROR: Could not set DATAPixx configuration [%d]!\n", rc);
		usb_close(dpxHdl);
		dpxHdl = NULL;
		DPxSetError(DPX_ERR_USB_SET_CONFIG);
		goto Done;
	}
	rc = usb_claim_interface(dpxHdl, 0);
	if (rc < 0) {
		DPxDebugPrint1("ERROR: Could not claim DATAPixx interface [%d]!\n", rc);
		usb_close(dpxHdl);
		dpxHdl = NULL;
		DPxSetError(DPX_ERR_USB_CLAIM_INTERFACE);
		goto Done;
	}
	rc = usb_set_altinterface(dpxHdl, 0);
	if (rc < 0) {
		DPxDebugPrint1("ERROR: Could not set DATAPixx alternate interface [%d]!\n", rc);
		usb_close(dpxHdl);
		dpxHdl = NULL;
		DPxSetError(DPX_ERR_USB_ALT_INTERFACE);
		goto Done;
	}

Done:
	if (doPrint)
		fflush(stdout);
}


/********************************************************************************/
/*																				*/
/*	Here we start to define the interface which is presented in libdpx.h	*/
/*																				*/
/********************************************************************************/


void DPxSetDebug(int level)
{
	// Don't look for ARG errors here, since DPxSetDebug() is used in macros that test for other ARG errors.
	// For the same reason, don't call DPxSetError() and change dpxError.
	dpxDebugLevel = level;

	// Don't print info here.  I'm changing the debug level many times as I test DPX_ARG_ERROR for API functions
//	if (dpDebugLevel || level)
//		DPxDebugPrint1("DPxSetDebug: Setting debugging level to %d\n", level);

	// Set libusb level to one less than ours, so that dp_api messages kick in before libusb messages.
	usb_set_debug(level > 0 ? level - 1 : 0);
}


int DPxGetDebug()
{
	// DPxGetDebug() is used in error macros, so don't call DPxSetError() and change dpxError.
	return dpxDebugLevel;
}


void DPxSetError(int error)
{
	dpxError = error;
}


void DPxClearError()
{
	dpxError = DPX_SUCCESS;
}


// DPxGetError() does not clear dpError.
// User might want to implement an exception-type mechanism, in which error propagates.
int DPxGetError()
{
	return dpxError;
}


// Get number of USB retries/fails for each endpoint and direction
int DPxGetEp1WrRetries()
{
	return dpxEp1WrRetries;
}
int DPxGetEp1RdRetries()
{
	return dpxEp1RdRetries;
}
int DPxGetEp2WrRetries()
{
	return dpxEp2WrRetries;
}
int DPxGetEp6RdRetries()
{
	return dpxEp6RdRetries;
}
int DPxGetEp1WrFails()
{
	return dpxEp1WrFails;
}
int DPxGetEp1RdFails()
{
	return dpxEp1RdFails;
}
int DPxGetEp2WrFails()
{
	return dpxEp2WrFails;
}
int DPxGetEp6RdFails()
{
	return dpxEp6RdFails;
}


// Concatenate two unsigned 32-bit numbers and return as a 64-bit floating point number.
// Note that there may be some loss of precision, as an IEEE 64-bit float only has a 53 bit mantissa.
double DPxMakeFloat64FromTwoUInt32(UInt32 highUInt32, UInt32 lowUInt32)
{
	return (4294967296.0 * highUInt32 + lowUInt32);		// Use 2^32 constant.  Accuracy of pow(2,32) might be platform-dependant.
}


// Call before any other DPx*() functions
void DPxOpen()
{
	int err;
#if !TARGET_WINDOWS
    int rc;
#endif

	// Any error during open should leave the register cache cleared
	memset(dpxRegisterCache, 0, sizeof(dpxRegisterCache));

    // Throw out any posted writes which haven't been executed yet!
    // We don't want the upcoming DPxUpdateRegCache() to write back a 0 to a register.
	memset(dpxRegisterModified, 0, sizeof(dpxRegisterModified));

	// One-time initialization of libusb, important for linux.
	if (!dpxInitialized) {
		usb_init();
		dpxInitialized = 1;
	}

	// Look for a DP.  Could be there isn't one connected, or it could be a raw device.
	dpxGoodFpga = 0;	// Default
	DPxUsbScan(0);
	err = DPxGetError();
	if (err != DPX_SUCCESS) {
		if (err != DPX_ERR_USB_RAW_EZUSB)
			DPxDebugPrint1("Fail: [DPxUsbScan] failed with error %d\n", err);
		return;
	}

	// Reset host controller toggle bit on Windows machines.
	// Seems this is not needed under OS X, but Windows doesn't seem to reset the toggle bit.
	// Each time dpxutil starts, one of the above routines (claim interface?) probably clears the toggle on the EZ,
	// but the toggle on the host side never gets cleared, except by the code below.
	// Without this, dpxutil has a 50% chance (for each EP) of loading with the correct toggle value.
	// Note that EP0 doesn't have a toggle (I think).
	// Sometimes dpxutil works when I don't include this code, but sometimes it doesn't.
	// Lately, testing with JF, multiple rr work, but then after entering a rrr command, then rr, FAIL.
	// So keep this code here.
	usb_clear_halt(dpxHdl, 0x01);
	usb_clear_halt(dpxHdl, 0x81);
	usb_clear_halt(dpxHdl, 0x02);
	usb_clear_halt(dpxHdl, 0x86);

    // We'll keep track of the number of EP1 read and writes, and make sure that it's an even number when we DPxClose().
    nEP1Writes = 0;
    nEP1Reads = 0;

    
	// We found a DATAPixx, and its EZ-USB has a valid firmware.
	// If this firmware was downloaded from host, it's still possible that the FPGA has not been configured.
	// We'll just ask the EZ-USB if the FPGA has pulled down INT1 to indicate its healthy presence.
	// *** Windows chokes on this.  JF's machine returns errors.  Maybe Mario had this error as well.
	// Use conditional compile to remove this under Windows.
	// Note that my Windows Matlab mex build defines _MSC_VER, but the Octave build doesn't,
	// so I'll also define my own person WIN_BUILD when making mex files.
#if !TARGET_WINDOWS
	rc = EZReadSFR(EZ_SFR_IOA);
	if (rc < 0) {
		fprintf(stderr, "ERROR: DPxOpen() EZReadSFR() failed with error 0x%X\n", rc);
		DPxSetError(DPX_ERR_USB_OPEN_FPGA);
		return;
	}

	// FPGA pulls down INT1 when it is running OK.  Otherwise, pullup means raw FPGA
	if (rc & 2) {
		DPxSetError(DPX_ERR_USB_RAW_FPGA);
		return;
	}
#endif

	// Now that we know the FPGA is there, we'll try a register read.
	// We also absolutely have to initialize our cache with the real register values.
	// Remember that the registers could have been written by some other app.
	// We don't want our caller doing even one register write until our cache is valid.
	DPxUpdateRegCache();
	if (DPxGetError() != DPX_SUCCESS) {
		DPxSetError(DPX_ERR_USB_RAW_FPGA);
		return;
	}

	// And finally, make sure we recognize the ID register.
	if (DPxGetID() != DPXREG_DPID_DP && DPxGetID() != DPXREG_DPID_VP && DPxGetID() != DPXREG_DPID_PP)
		DPxSetError(DPX_ERR_USB_UNKNOWN_DPID);
	dpxGoodFpga = 1;
}


// Call when finished with DATAPixx.
// Should be OK to call DPxOpen() / DPxClose() multiple times within application.
void DPxClose()
{
    // Under Windows, EP1 sometimes has a USB data toggle bit problem.
    // If the USB port is closed after an odd number of 64B EP1 packets, then the next EP1 transaction fails with a toggle bit error.
    // The only way I've found to fix this is to always I/O an even number of 64B USB packets before calling usb_close().
    // We'll just always I/O an even number of 64B packets, by appending a single 64B packet if necessary.
    // Special function register for port E is innocuous enough.  Writing an output enable of 0 is the default hard reset value.  Leaves JTAG tristate.
    // Of course, if we are closing because we just told the EZ-USB to initiate a hardware reset, then don't try to do any USB accesses.
    if (DPxIsOpen() && !gDoingHardwareReset) {
        if (nEP1Reads & 1)
            EZReadSFR(EZ_SFR_OEE);      // This has to come first, since it does both a write and a read
        if (nEP1Writes & 1)
            EZWriteSFR(EZ_SFR_OEE, 0);
    }
    nEP1Reads = 0;
    nEP1Writes = 0;

	// Note that usb_close() takes care of calling usb_release_interface(),
	// so there's no more cleanup required here.
	if (dpxHdl)
		usb_close(dpxHdl);
	dpxHdl = NULL;
	dpxGoodFpga = 0;
	dpxRawUsb = 0;
}


// Non-0 if DPxOpen() found a DATAPixx with firmware, and a well-configured FPGA
int DPxIsReady()
{
	return dpxGoodFpga;
}


// Read a block of DATAPixx RAM into a local buffer
void DPxReadRam(unsigned address, unsigned length, void* buffer)
{
	unsigned short blockLength;
	char* buffPtr = (char*)buffer;
	// Validate args
	if (address & 1) {
		DPxDebugPrint1("ERROR: DPxReadRam() argument address 0x%x is not an even number\n", address);
		DPxSetError(DPX_ERR_RAM_READ_ADDR_ODD);
		return;
	}
	if (length & 1) {
		DPxDebugPrint1("ERROR: DPxReadRam() argument length 0x%x is not an even number\n", length);
		DPxSetError(DPX_ERR_RAM_READ_LEN_ODD);
		return;
	}
	if (address + length > DPxGetRamSize()) {
		DPxDebugPrint2("ERROR: DPxReadRam() argument address 0x%x plus length 0x%x exceeds DATAPixx memory size\n", address, length);
		DPxSetError(DPX_ERR_RAM_READ_TOO_HIGH);
		return;
	}
	if (!buffer) {
		DPxDebugPrint0("ERROR: DPxReadRam() argument buffer address is null\n");
		DPxSetError(DPX_ERR_RAM_READ_BUFFER_NULL);
		return;
	}

	// Break into largest supported tram chunks
	while (length) {
		if (length > DPX_RWRAM_BLOCK_SIZE)
			blockLength = DPX_RWRAM_BLOCK_SIZE;
		else
			blockLength = (unsigned short)length;
		ep2out_Tram[0] = '^';
		ep2out_Tram[1] = EP2OUT_READRAM;
		ep2out_Tram[2] = 6;
		ep2out_Tram[3] = 0;
		ep2out_Tram[4] = (address >>  0) & 0xFF;
		ep2out_Tram[5] = (address >>  8) & 0xFF;
		ep2out_Tram[6] = (address >> 16) & 0xFF;
		ep2out_Tram[7] = (address >> 24) & 0xFF;
		ep2out_Tram[8] = LSB(blockLength);
		ep2out_Tram[9] = MSB(blockLength);
		if (EZWriteEP2Tram(ep2out_Tram, EP6IN_READRAM, blockLength)) {
			DPxDebugPrint0("ERROR: DPxReadRam() call to EZWriteEP2Tram() failed\n");
			DPxSetError(DPX_ERR_RAM_READ_USB_ERROR);
			return;
		}

		if ((void*)buffPtr != (void*)(ep6in_Tram+4))	// Users are allowed to read directly from ep6in_Tram to save memcpy
			memcpy(buffPtr, ep6in_Tram+4, blockLength);
		address += blockLength;
		buffPtr += blockLength;
		length  -= blockLength;
	}
}


// Write a local buffer to DATAPixx RAM
void DPxWriteRam(unsigned address, unsigned length, void* buffer)
{
	unsigned short blockLength, payloadLength;
	char* buffPtr = (char*)buffer;

	// Validate args
	if (address & 1) {
		DPxDebugPrint1("ERROR: DPxWriteRam() argument address 0x%x is not an even number\n", address);
		DPxSetError(DPX_ERR_RAM_WRITE_ADDR_ODD);
		return;
	}
	if (length & 1) {
		DPxDebugPrint1("ERROR: DPxWriteRam() argument length 0x%x is not an even number\n", length);
		DPxSetError(DPX_ERR_RAM_WRITE_LEN_ODD);
		return;
	}
	if (address + length > DPxGetRamSize()) {
		DPxDebugPrint2("ERROR: DPxWriteRam() argument address 0x%x plus length 0x%x exceeds DATAPixx memory size\n", address, length);
		DPxSetError(DPX_ERR_RAM_WRITE_TOO_HIGH);
		return;
	}
	if (!buffer) {
		DPxDebugPrint0("ERROR: DPxWriteRam() argument buffer address is null\n");
		DPxSetError(DPX_ERR_RAM_WRITE_BUFFER_NULL);
		return;
	}

	// Break into largest supported tram chunks
	while (length) {
		if (length > DPX_RWRAM_BLOCK_SIZE)
			blockLength = DPX_RWRAM_BLOCK_SIZE;
		else
			blockLength = (unsigned short)length;
		payloadLength = blockLength + 4;
		ep2out_Tram[0] = '^';
		ep2out_Tram[1] = EP2OUT_WRITERAM;
		ep2out_Tram[2] = LSB(payloadLength);
		ep2out_Tram[3] = MSB(payloadLength);
		ep2out_Tram[4] = (address >>  0) & 0xFF;
		ep2out_Tram[5] = (address >>  8) & 0xFF;
		ep2out_Tram[6] = (address >> 16) & 0xFF;
		ep2out_Tram[7] = (address >> 24) & 0xFF;
		if ((void*)(ep2out_Tram+8) != (void*)buffPtr)		// Users are allowed to write directly into ep2out_Tram to save memcpy
			memcpy(ep2out_Tram+8, buffPtr, blockLength);
		if (EZWriteEP2Tram(ep2out_Tram, 0, 0)) {
			DPxDebugPrint0("ERROR: DPxWriteRam() call to EZWriteEP2Tram() failed\n");
			DPxSetError(DPX_ERR_RAM_WRITE_USB_ERROR);
			return;
		}

		address += blockLength;
		buffPtr += blockLength;
		length  -= blockLength;
	}
}


// Address of API internal read RAM buffer.
// Caller can access this buffer directly to avoid an extra memcpy when reading Datapixx RAM.
size_t DPxGetReadRamBuffAddr()
{
	return (size_t)ep6in_Tram + 4;
}


// Number of bytes in internal read RAM buffer.
// Users of the buffer returned by DPxGetReadRamBuffAddr() must limit their transaction size to this value.
int DPxGetReadRamBuffSize()
{
	return DPX_RWRAM_BLOCK_SIZE;
}


// Address of API internal write RAM buffer.
// Caller can access this buffer directly to avoid an extra memcpy when writing Datapixx RAM.
size_t DPxGetWriteRamBuffAddr()
{
	return (size_t)ep2out_Tram + 8;
}


// Number of bytes in internal write RAM buffer.
// Users of the buffer returned by DPxGetWriteRamBuffAddr() must limit their transaction size to this value.
int DPxGetWriteRamBuffSize()
{
	return DPX_RWRAM_BLOCK_SIZE;
}


// Set a 16-bit register's value in dpxRegisterCache[]
void DPxSetReg16(int regAddr, int regValue)
{
	if (regAddr & 1) {
		DPxDebugPrint1("ERROR: DPxSetReg16() argument register address 0x%x is not an even number\n", regAddr);
		DPxSetError(DPX_ERR_SETREG16_ADDR_ODD);
		return;
	}
	if (regAddr < 0 || regAddr >= DPX_REG_SPACE) {
		DPxDebugPrint2("ERROR: DPxSetReg16() argument register address 0x%x is not in range 0 to 0x%X\n", regAddr, DPX_REG_SPACE-2);
		DPxSetError(DPX_ERR_SETREG16_ADDR_RANGE);
		return;
	}
	if (regValue < -32768 || regValue > 65535) {
		DPxDebugPrint1("ERROR: DPxSetReg16() argument register value 0x%x is out of range\n", regValue);
		DPxSetError(DPX_ERR_SETREG16_DATA_RANGE);
		return;
	}

	dpxRegisterCache[regAddr/2] = regValue;
	dpxRegisterModified[regAddr/2] = 1;
}


// Read a 16-bit register's value from dpxRegisterCache[].
// Note that this returns an _unsigned_ 16-bit value.
int DPxGetReg16(int regAddr)
{
	if (regAddr & 1) {
		DPxDebugPrint1("ERROR: DPxGetReg16() argument register address 0x%x is not an even number\n", regAddr);
		DPxSetError(DPX_ERR_GETREG16_ADDR_ODD);
		return 0;
	}
	if (regAddr < 0 || regAddr >= DPX_REG_SPACE) {
		DPxDebugPrint2("ERROR: DPxGetReg16() argument register address 0x%x is not in range 0 to 0x%X\n", regAddr, DPX_REG_SPACE-2);
		DPxSetError(DPX_ERR_GETREG16_ADDR_RANGE);
		return 0;
	}
	return dpxRegisterCache[regAddr/2];
}


// Set a 32-bit register's value in dpxRegisterCache[]
// Assumes 32-bit registers have 32-bit address alignment.
void DPxSetReg32(int regAddr, unsigned regValue)
{
	if (regAddr & 3) {
		DPxDebugPrint1("ERROR: DPxSetReg32() argument register address 0x%x is not 32-bit aligned\n", regAddr);
		DPxSetError(DPX_ERR_SETREG32_ADDR_ALIGN);
		return;
	}
	if (regAddr < 0 || regAddr >= DPX_REG_SPACE) {
		DPxDebugPrint2("ERROR: DPxSetReg32() argument register address 0x%x is not in range 0 to 0x%X\n", regAddr, DPX_REG_SPACE-4);
		DPxSetError(DPX_ERR_SETREG32_ADDR_RANGE);
		return;
	}
	dpxRegisterCache[regAddr/2  ] = LSW(regValue);
	dpxRegisterCache[regAddr/2+1] = MSW(regValue);
	dpxRegisterModified[regAddr/2  ] = 1;
	dpxRegisterModified[regAddr/2+1] = 1;
}


// Read a 32-bit register's value from dpxRegisterCache[]
unsigned DPxGetReg32(int regAddr)
{
	if (regAddr & 3) {
		DPxDebugPrint1("ERROR: DPxGetReg32() argument register address 0x%x is not 32-bit aligned\n", regAddr);
		DPxSetError(DPX_ERR_GETREG32_ADDR_ALIGN);
		return 0;
	}
	if (regAddr < 0 || regAddr >= DPX_REG_SPACE) {
		DPxDebugPrint2("ERROR: DPxGetReg32() argument register address 0x%x is not in range 0 to 0x%X\n", regAddr, DPX_REG_SPACE-4);
		DPxSetError(DPX_ERR_GETREG32_ADDR_RANGE);
		return 0;
	}
	return (dpxRegisterCache[regAddr/2+1] << 16) + dpxRegisterCache[regAddr/2];
}


int DPxGetRegSize(int regAddr)
{
	if (regAddr >= DPXREG_NANOTIME_15_0	&& regAddr <= DPXREG_NANOMARKER_63_48+1)			return 8;

	if (regAddr >= DPXREG_DAC_BUFF_BASEADDR_L	&& regAddr <= DPXREG_DAC_SCHED_CTRL_H+1)	return 4;
	if (regAddr >= DPXREG_ADC_CHANREF_L			&& regAddr <= DPXREG_ADC_CHANREF_H+1)		return 4;
	if (regAddr >= DPXREG_ADC_BUFF_BASEADDR_L	&& regAddr <= DPXREG_ADC_SCHED_CTRL_H+1)	return 4;
	if (regAddr >= DPXREG_DOUT_DATA_L			&& regAddr <= DPXREG_DOUT_DATA_H+1)			return 4;
	if (regAddr >= DPXREG_DOUT_BUFF_BASEADDR_L	&& regAddr <= DPXREG_DOUT_SCHED_CTRL_H+1)	return 4;
	if (regAddr >= DPXREG_DIN_DATA_L			&& regAddr <= DPXREG_DIN_DATAOUT_H+1)		return 4;
	if (regAddr >= DPXREG_DIN_BUFF_BASEADDR_L	&& regAddr <= DPXREG_DIN_SCHED_CTRL_H+1)	return 4;
	if (regAddr >= DPXREG_AUD_BUFF_BASEADDR_L	&& regAddr <= DPXREG_AUX_SCHED_CTRL_H+1)	return 4;
	if (regAddr >= DPXREG_MIC_BUFF_BASEADDR_L	&& regAddr <= DPXREG_MIC_SCHED_CTRL_H+1)	return 4;
	if (regAddr >= DPXREG_VID_VPERIOD_L			&& regAddr <= DPXREG_VID_VPERIOD_H+1)		return 4;

	return 2;
}


// Data structures for accumulating a composite USB message over multiple API calls.
// Other DP users (eg: CODEC I2C) could be sending ep2out traffic between the buildUsbMsg calls,
// so we need our own static copy of the message buffer, and message pointer.
UInt16	dpxBuildUsbMsgBuff[4096];			// size is overkill if we're just using this for register updates
UInt16*	dpxBuildUsbMsgPtr = dpxBuildUsbMsgBuff;
int		dpxBuildUsbMsgHasReadback = 0;


// Start accumulating a composite USB message
void DPxBuildUsbMsgBegin()
{
	dpxBuildUsbMsgPtr = dpxBuildUsbMsgBuff;
	dpxBuildUsbMsgHasReadback = 0;
}


// Append composite USB message to write modified registers from local cache to DATAPixx.
// Combines contiguous modified registers into single trams.
void DPxBuildUsbMsgWriteRegs()
{
	int iReg;
	int lastModifiedRegIndex = -2;	// -1 could make reg(0) think it's a follower.
	UInt16* payloadPtr = 0;

	// Check each register to see if it has been modified in the local cache
	for (iReg = 0; iReg < DPX_REG_SPACE/2; iReg++) {

		// Construct trams for writing modified registers to DP
		if (dpxRegisterModified[iReg]) {
			dpxRegisterModified[iReg] = 0;								// Indicates that DP is getting new modified value
			if (lastModifiedRegIndex != iReg-1) {						// If reg is not contiguous with previous modified register, start a new write tram 
				*dpxBuildUsbMsgPtr++ = (EP2OUT_WRITEREGS << 8) + '^';	// Tram header for a register write
				*dpxBuildUsbMsgPtr++ = 2;								// Tram payload initialized for register index only
				*dpxBuildUsbMsgPtr++ = iReg;							// Index of first register to write with tram
				payloadPtr = dpxBuildUsbMsgPtr - 2;						// So we can increment as we add contig registers
			}

			// Add the modified register write to the current tram
			*dpxBuildUsbMsgPtr++ = dpxRegisterCache[iReg];
			(*payloadPtr) += 2;
			lastModifiedRegIndex = iReg;
		}
	}

    // Some register bits are one-shots, and must be manually reset to 0 once they are written
	dpxRegisterCache[DPXREG_SCHED_STARTSTOP/2] = 0;                     // Starting/stopping schedules
    dpxRegisterCache[DPXREG_CTRL/2] &= ~DPXREG_CTRL_CALIB_RELOAD;       // SPI calibration table reload
	dpxRegisterCache[DPXREG_VID_VESA/2] &= ~DPXREG_VID_VESA_LEFT_WEN;   // Writing VESA Left/Right bit
}


// Append composite USB message to read Datapixx register set.
void DPxBuildUsbMsgReadRegs()
{
	*dpxBuildUsbMsgPtr++ = (EP2OUT_READREGS << 8) + '^';			// Tram header for a register read
	*dpxBuildUsbMsgPtr++ = 0;										// No payload for a register read command
	dpxBuildUsbMsgHasReadback = 1;
}


// Append composite USB message to freeze Datapixx USB message treatment
// until next leading edge of video vertical sync pulse.
// ***What to do if the DATAPixx is not receiving any video?  This could freeze an application on next register readback!
// If there's no video, we'll set an error code, and will not implement the video sync.
// On VIEWPixx/PROPixx there is no such requirement, since a software or hardware test pattern will always be running.
// Not quite true anymore.  Display could be sleeping.  In that case it will freeze.
void DPxBuildUsbMsgVideoSync()
{
    if (DPxIsVidDviActive() || DPxIsViewpixx() || DPxIsPropixx()) {
        *dpxBuildUsbMsgPtr++ = (EP2OUT_VSYNC << 8) + '^';				// Tram header for vertical sync
        *dpxBuildUsbMsgPtr++ = 0;										// No payload
    }
    else
        DPxSetError(DPX_ERR_VID_VSYNC_WITHOUT_VIDEO);
}


// Append composite USB message to freeze Datapixx USB message treatment
// until a prespecified RGB pixel sequence is seen at the video input.
// The timeout argument specifies the maximum number of video frames which the Datapixx will wait.
// After this time, USB message treatment will continue, and DPxIsPsyncTimeout() will return true.
// pixelData contains a list of 8-bit RGB component values; ie: R0, G0, B0, R1, G1, B1...
void DPxBuildUsbMsgPixelSync(int nPixels, unsigned char* pixelData, int timeout)
{
	if (nPixels < 1 || nPixels > 8) {
		DPxDebugPrint0("ERROR: DPxBuildUsbMsgPixelSync() nPixels argument must be in the range 1-8\n");
		DPxSetError(DPX_ERR_VID_PSYNC_NPIXELS_ARG_ERROR);
		return;
	}
	if (timeout < 0 || timeout > 65535) {
		DPxDebugPrint0("ERROR: DPxBuildUsbMsgPixelSync() timeout must be in the range 0-65535\n");
		DPxSetError(DPX_ERR_VID_PSYNC_TIMEOUT_ARG_ERROR);
		return;
	}

	*dpxBuildUsbMsgPtr++ = (EP2OUT_WRITEPSYNC << 8) + '^';	// Tram header for pixel sync sequence
	*dpxBuildUsbMsgPtr++ = nPixels * 6;						// payload contains 16-bit RGB pixel components
	while (nPixels--) {
		*dpxBuildUsbMsgPtr++ = *pixelData++ << 8;			// Red
		*dpxBuildUsbMsgPtr++ = *pixelData++ << 8;			// Green
		*dpxBuildUsbMsgPtr++ = *pixelData++ << 8;			// Blue
	}

	*dpxBuildUsbMsgPtr++ = (EP2OUT_PSYNC << 8) + '^';		// Tram header for pixel sync
	*dpxBuildUsbMsgPtr++ = 2;								// 2-byte payload
	*dpxBuildUsbMsgPtr++ = timeout;
}


// Transmit the message we just built,
// and possibly wait for an incoming register read USB message.
void DPxBuildUsbMsgEnd()
{
	int packetSize, iRetry;

	// It's possible that user called DPxBuildUsbMsgWriteRegs() but no registers were modified.
	packetSize = (char*)dpxBuildUsbMsgPtr - (char*)dpxBuildUsbMsgBuff;
	if (!packetSize)
		return;

	// Write the packet with the trams to DATAPixx
	CheckUsb();
	for (iRetry = 0; ; iRetry++) {
		if (usb_bulk_write(dpxHdl, 2, (char*)dpxBuildUsbMsgBuff, packetSize, 1000) == packetSize)
			break;
		else if (iRetry < MAX_RETRIES) {
			DPxDebugPrint1("ERROR: DPxBuildUsbMsgEnd() call to usb_bulk_write() retried: %s\n", usb_strerror());
			dpxEp2WrRetries++;
		}
		else {
			DPxDebugPrint1("ERROR: DPxBuildUsbMsgEnd() call to usb_bulk_write() failed: %s\n", usb_strerror());
			DPxSetError(DPX_ERR_USB_REG_BULK_WRITE);
			dpxEp2WrFails++;
			return;
		}
	}

	// If reading, go get the new register values, and copy into local cache
	if (dpxBuildUsbMsgHasReadback) {
		if (EZReadEP6Tram(EP6IN_READREGS, DPX_REG_SPACE) < 0) {
			DPxDebugPrint0("ERROR: DPxBuildUsbMsgEnd() call to EZReadEP6Tram() failed\n");
			DPxSetError(DPX_ERR_USB_REG_BULK_READ);
			return;
		}
		memcpy(dpxRegisterCache, ep6in_Tram+4, DPX_REG_SPACE);
	}
}


// Write local register cache to Datapixx over USB
void DPxWriteRegCache()
{
	DPxBuildUsbMsgBegin();
	DPxBuildUsbMsgWriteRegs();
	DPxBuildUsbMsgEnd();
}


// Write local register cache to Datapixx over USB, then read back DATAPixx registers over USB into local cache
void DPxUpdateRegCache()
{
	DPxBuildUsbMsgBegin();
	DPxBuildUsbMsgWriteRegs();
	DPxBuildUsbMsgReadRegs();
	DPxBuildUsbMsgEnd();
}


// Write local register cache to Datapixx over USB.
// This routine sends the USB message and returns quickly,
// but Datapixx only writes the registers on leading edge of next vertical sync pulse.
void DPxWriteRegCacheAfterVideoSync()
{
	DPxBuildUsbMsgBegin();
	DPxBuildUsbMsgVideoSync();
	DPxBuildUsbMsgWriteRegs();
	DPxBuildUsbMsgEnd();
}


// Write local register cache to Datapixx over USB,
// then read back DATAPixx registers over USB into local cache.
// Datapixx blocks until leading edge of next vertical sync pulse before writing/reading registers.
void DPxUpdateRegCacheAfterVideoSync()
{
	DPxBuildUsbMsgBegin();
	DPxBuildUsbMsgVideoSync();
	DPxBuildUsbMsgWriteRegs();
	DPxBuildUsbMsgReadRegs();
	DPxBuildUsbMsgEnd();
}


// Write local register cache to Datapixx over USB.
// This routine sends the USB message and returns quickly,
// but Datapixx only writes the registers when the previously defined pixel sync sequence has been displayed.
void DPxWriteRegCacheAfterPixelSync(int nPixels, unsigned char* pixelData, int timeout)
{
	DPxBuildUsbMsgBegin();
	DPxBuildUsbMsgPixelSync(nPixels, pixelData, timeout);
	DPxBuildUsbMsgWriteRegs();
	DPxBuildUsbMsgEnd();
}


// Write local register cache to Datapixx over USB,
// then read back DATAPixx registers over USB into local cache.
// Datapixx blocks until the specified pixel sync sequence has been displayed before writing/reading registers.
void DPxUpdateRegCacheAfterPixelSync(int nPixels, unsigned char* pixelData, int timeout)
{
	DPxBuildUsbMsgBegin();
	DPxBuildUsbMsgPixelSync(nPixels, pixelData, timeout);
	DPxBuildUsbMsgWriteRegs();
	DPxBuildUsbMsgReadRegs();
	dpxActivePSyncTimeout = timeout;	// Let low-level know that the timeout could be large
	DPxBuildUsbMsgEnd();
	dpxActivePSyncTimeout = -1;			// Let low-level return timeout to normal value
}


// Get all DATAPixx registers, and save them in a local copy
void DPxSaveRegs()
{
	DPxUpdateRegCache();
	memcpy(dpxSavedRegisters, dpxRegisterCache, sizeof(dpxSavedRegisters));
}


// Write the local copy back to the DATAPixx
void DPxRestoreRegs()
{
	memcpy(dpxRegisterCache, dpxSavedRegisters, sizeof(dpxRegisterCache));
	memset(dpxRegisterModified, 1, sizeof(dpxRegisterModified));
	DPxUpdateRegCache();
}


// Set an 8-bit I2C register in audio CODEC IC
void DPxSetCodecReg(int regAddr, int regValue)
{
	regAddr &= 0x7F;
	DPxSetI2cReg(regAddr, regValue);

	// Sometimes we want to readback cached CODEC I2C register values
	cachedCodecRegs[regAddr] = (unsigned char)regValue;
}


// Read an 8-bit I2C register from audio CODEC IC
int DPxGetCodecReg(int regAddr)
{
	return DPxGetI2cReg(regAddr & 0x7F);
}


// Read an 8-bit I2C register from CODEC cache, instead of from audio CODEC IC hardware.
// This is much faster, but could be wrong if another app has written the register.
int DPxGetCachedCodecReg(int regAddr)
{
	return cachedCodecRegs[regAddr & 0x7F];
}


// Set an 8-bit I2C register in Silicon Image DVI IC
void DPxSetDviReg(int regAddr, int regValue)
{
	DPxSetI2cReg(regAddr | 0x80, regValue);
}


// Read an 8-bit I2C register from Silicon Image DVI IC
int DPxGetDviReg(int regAddr)
{
	return DPxGetI2cReg(regAddr | 0x80);
}


// Set an 8-bit register in audio CODEC IC, or DVI receiver
void DPxSetI2cReg(int regAddr, int regValue)
{
	UInt16* tramPtr = (UInt16*)ep2out_Tram;
	int packetSize;
	int iRetry;

	*tramPtr++ = (EP2OUT_WRITEI2C << 8) + '^';	// Tram header for an I2C register write
	*tramPtr++ = 2;								// Tram payload has 1 byte for register number, and 1 byte for datum
	*tramPtr++ = ((unsigned char)regAddr << 8) + (unsigned char)regValue;
	packetSize = (char*)tramPtr - (char*)ep2out_Tram;
	CheckUsb();
	for (iRetry = 0; ; iRetry++) {
		if (usb_bulk_write(dpxHdl, 2, (char*)ep2out_Tram, packetSize, 1000) == packetSize)
			break;
		else if (iRetry < MAX_RETRIES) {
			DPxDebugPrint1("ERROR: DPxSetI2cReg() call to usb_bulk_write() retried: %s\n", usb_strerror());
			dpxEp2WrRetries++;
		}
		else {
			DPxDebugPrint1("ERROR: DPxSetI2cReg() call to usb_bulk_write() failed: %s\n", usb_strerror());
			dpxEp2WrFails++;
			DPxSetError(DPX_ERR_USB_REG_BULK_WRITE);
			return;
		}
	}
}


// Read an 8-bit register from audio CODEC IC
int DPxGetI2cReg(int regAddr)
{
	UInt16* tramPtr = (UInt16*)ep2out_Tram;
	int packetSize;
	int iRetry;

	*tramPtr++ = (EP2OUT_READI2C << 8) + '^';			// Tram header for an I2C register read
	*tramPtr++ = 2;										// 2-byte payload for an I2C register read command
	*tramPtr++ = regAddr << 8;
	packetSize = (char*)tramPtr - (char*)ep2out_Tram;
	CheckUsb();
	for (iRetry = 0; ; iRetry++) {
		if (usb_bulk_write(dpxHdl, 2, (char*)ep2out_Tram, packetSize, 1000) == packetSize)
			break;
		else if (iRetry < MAX_RETRIES) {
			DPxDebugPrint1("ERROR: DPxGetI2cReg() call to usb_bulk_write() retried: %s\n", usb_strerror());
			dpxEp2WrRetries++;
		}
		else {
			DPxDebugPrint1("ERROR: DPxGetI2cReg() call to usb_bulk_write() failed: %s\n", usb_strerror());
			dpxEp2WrFails++;
			DPxSetError(DPX_ERR_USB_REG_BULK_WRITE);
			return -1;
		}
	}
	if (EZReadEP6Tram(EP6IN_READI2C, 2) < 0) {
		DPxDebugPrint0("ERROR: DPxGetI2cReg() call to EZReadEP6Tram() failed\n");
		DPxSetError(DPX_ERR_USB_REG_BULK_READ);
		return -1;
	}
	return (unsigned)ep6in_Tram[4];
}


// Get the DATAPixx identifier code
int DPxGetID()
{
	return DPxGetReg16(DPXREG_DPID);
}


// Returns non-0 if DATAPixx is embedded in a VIEWPixx OR a VIEWPixx3D
int DPxIsViewpixx()
{
    return dpxIsViewpixx;   // This is based on USB product ID instead of FPGA register set, so it's valid even if FPGA has not been programmed.
}


// Returns non-0 if DATAPixx is embedded in a VIEWPixx3D
int DPxIsViewpixx3D()
{
    switch (DPxGetPartNumber())
    {
        case 2004:               // VIEWPixx3D
        case 2005: return 1;     // VIEWPixx3D Lite
    }
    
    return 0;
}


// Returns non-0 if DATAPixx is embedded in a PROPixx
int DPxIsPropixx()
{
    return dpxIsPropixx;   // This is based on USB product ID instead of FPGA register set, so it's valid even if FPGA has not been programmed.
}


// Get the number of bytes of RAM in the DATAPixx system
int DPxGetRamSize()
{
	int ramMB;

	switch (DPxGetReg16(DPXREG_OPTIONS) & DPXREG_OPTIONS_RAM_MASK) {
		case DPXREG_OPTIONS_RAM_32M : ramMB = 32;  break;
		case DPXREG_OPTIONS_RAM_64M : ramMB = 64;  break;
		case DPXREG_OPTIONS_RAM_128M: ramMB = 128; break;
		case DPXREG_OPTIONS_RAM_256M: ramMB = 256; break;
		default: ramMB = 0;
	}
	if (ramMB == 0) {
		DPxDebugPrint0("ERROR: DPxGetRamSize() doesn't recognize RAM size\n");
		DPxSetError(DPX_ERR_RAM_UNKNOWN_SIZE);
	}
	return ramMB * (1 << 20);
}


// Get the DATAPixx part number
int DPxGetPartNumber()
{
    if (DPxIsViewpixx()) {
        switch (DPxGetReg16(DPXREG_OPTIONS) & DPXREG_OPTIONS_PART_MASK) {
            case DPXREG_OPTIONS_PART_LITE : return 2000;
            case DPXREG_OPTIONS_PART_FULL : return 2001;
            case DPXREG_OPTIONS_PART_3DLITE : return 2004;
            case DPXREG_OPTIONS_PART_3DFULL : return 2005;
        }
    }
    else if (DPxIsPropixx()) {
        switch (DPxGetReg16(DPXREG_OPTIONS) & DPXREG_OPTIONS_PART_MASK) {
            case DPXREG_OPTIONS_PART_LITE : return 3000;
            case DPXREG_OPTIONS_PART_FULL : return 3001;
        }
    }
    else {  // Assume a DATAPixx
        if (DPxGetFirmwareRev() < 14)
            return 1001;	// DATAPixx options reg only has part number starting with VHDL rev 14.

        switch (DPxGetReg16(DPXREG_OPTIONS) & DPXREG_OPTIONS_PART_MASK) {
            case DPXREG_OPTIONS_PART_LITE : return 1000;
            case DPXREG_OPTIONS_PART_FULL : return 1001;
        }
    }
	DPxDebugPrint0("ERROR: DPxGetPartNumber() doesn't recognize part number\n");
	DPxSetError(DPX_ERR_UNKNOWN_PART_NUMBER);

	return 0;
}


// Get the DATAPixx firmware revision
int DPxGetFirmwareRev()
{
	return DPxGetReg16(DPXREG_FIRMWARE_REV);
}


// Get voltage being supplied from +5V supply
double DPxGetSupplyVoltage()
{
	return MSB(DPxGetReg16(DPXREG_POWER)) / 256.0 * 6.65;
}


// Get current being supplied from +5V supply.
double DPxGetSupplyCurrent()
{
    return LSB(DPxGetReg16(DPXREG_POWER)) / 256.0 * ((DPxIsViewpixx() || DPxIsPropixx()) ? 21.168 : 10.584);    // DATAPixx uses a 10 mOhm current sense resistor; VIEWPixx/PROPixx use 5 mOhms
}


// Get voltage being supplied from +12V supply.  Only implemented on VIEWPixx.
double DPxGetSupply2Voltage()
{
	return MSB(DPxGetReg16(DPXREG_POWER2)) / 256.0 * 26.52;
}


// Get current being supplied from +12V supply.  Only implemented on VIEWPixx.
double DPxGetSupply2Current()
{
    return LSB(DPxGetReg16(DPXREG_POWER2)) / 256.0 * 21.168;
}


// Returns non-0 if VESA and Analog I/O +5V pins are trying to draw more than 500 mA
int DPxIs5VFault()
{
	return DPxGetReg16(DPXREG_STATUS) & DPXREG_STATUS_5V_FAULT;
}


// Returns non-0 if last pixel sync wait timed out
int DPxIsPsyncTimeout()
{
	return DPxGetReg16(DPXREG_STATUS) & DPXREG_STATUS_PSYNC_TIMEOUT;
}


// Returns non-0 if DDR SDRAM controller has not yet brought memory system online
int DPxIsRamOffline()
{
	return DPxGetReg16(DPXREG_STATUS) & DPXREG_STATUS_RAM_OFFLINE;
}


// Get temperature inside of DATAPixx chassis, in degrees Celcius
double DPxGetTempCelcius()
{
	return (double)(signed char)(LSB(DPxGetReg16(DPXREG_TEMP)));
}


// Get temperature2 inside of VIEWPixx chassis, in degrees Celcius
double DPxGetTemp2Celcius()
{
	return (double)(signed char)(MSB(DPxGetReg16(DPXREG_TEMP)));
}


// Get temperature of VIEWPixx FPGA die, in degrees Celcius
double DPxGetTemp3Celcius()
{
	return (double)(signed char)(MSB(DPxGetReg16(DPXREG_STATUS)));
}


// Get temperature inside of DATAPixx chassis, in degrees Farenheit
double DPxGetTempFarenheit()
{
	return DPxGetTempCelcius() * 9 / 5 + 32;
}


// Get double precision seconds since powerup
double DPxGetTime()
{
	return DPxMakeFloat64FromTwoUInt32(DPxGetReg32(DPXREG_NANOTIME_47_32), DPxGetReg32(DPXREG_NANOTIME_15_0)) * 1.0e-9;
}


// Latch the current NanoTime value into the marker register
void DPxSetMarker()
{
	DPxSetReg16(DPXREG_NANOMARKER_15_0, 0);	// Write any value to the register to latch nanotime
}


// Get double precision seconds when DPxSetNanoMark() was last called
double DPxGetMarker()
{
	return DPxMakeFloat64FromTwoUInt32(DPxGetReg32(DPXREG_NANOMARKER_47_32), DPxGetReg32(DPXREG_NANOMARKER_15_0)) * 1.0e-9;
}


// Get low/high UInt32 nanoseconds since powerup
void DPxGetNanoTime(unsigned *nanoHigh32, unsigned *nanoLow32)
{
	if (!nanoHigh32 || !nanoLow32) {
		DPxDebugPrint0("ERROR: DPxGetNanoTime() argument is null\n");
		DPxSetError(DPX_ERR_NANO_TIME_NULL_PTR);
		return;
	}

	*nanoHigh32 = DPxGetReg32(DPXREG_NANOTIME_47_32);
	*nanoLow32  = DPxGetReg32(DPXREG_NANOTIME_15_0);
}


// Get high/low UInt32 nanosecond marker
void DPxGetNanoMarker(unsigned *nanoHigh32, unsigned *nanoLow32)
{
	if (!nanoHigh32 || !nanoLow32) {
		DPxDebugPrint0("ERROR: DPxGetNanoMarker() argument is null\n");
		DPxSetError(DPX_ERR_NANO_MARK_NULL_PTR);
		return;
	}

	*nanoHigh32 = DPxGetReg32(DPXREG_NANOMARKER_47_32);
	*nanoLow32  = DPxGetReg32(DPXREG_NANOMARKER_15_0);
}



/********************************************************************************/
/*																				*/
/*	DAC Subsystem																*/
/*																				*/
/********************************************************************************/


// Returns number of DAC channels in system
int DPxGetDacNumChans()
{
	return DPX_DAC_NCHANS;
}


// Set the 16-bit 2's complement signed value for one DAC channel (0-3)
void DPxSetDacValue(int value, int channel)
{
	if (value < -32768 || value > 65535) {	// We'll permit full combined range of SInt16 and UInt16.
		DPxDebugPrint1("ERROR: DPxSetDacValue() argument value %d is out of 16-bit range\n", value);
		DPxSetError(DPX_ERR_DAC_SET_BAD_VALUE);
		return;
	}
	if (channel < 0 || channel > DPX_DAC_NCHANS-1) {
		DPxDebugPrint2("ERROR: DPxSetDacValue() argument channel %d is not in range 0 to %d\n", channel, DPX_DAC_NCHANS-1);
		DPxSetError(DPX_ERR_DAC_SET_BAD_CHANNEL);
		return;
	}
	DPxSetReg16(DPXREG_DAC_DATA0+channel*2, value);
}


// Get the 16-bit 2's complement signed value for one DAC channel (0-3);
int DPxGetDacValue(int channel)
{
	if (channel < 0 || channel > DPX_DAC_NCHANS-1) {
		DPxDebugPrint2("ERROR: DPxGetDacValue() argument channel %d is not in range 0 to %d\n", channel, DPX_DAC_NCHANS-1);
		DPxSetError(DPX_ERR_DAC_GET_BAD_CHANNEL);
		return 0;
	}
	return (SInt16)DPxGetReg16(DPXREG_DAC_DATA0+channel*2);
}


// Get the voltage min/max range for a DAC channel (0-3).
// Note that the true max value will really be 1 LSB less than the reported max value.
void DPxGetDacRange(int channel, double *minV, double *maxV)
{
	if (!minV) {
		DPxDebugPrint0("ERROR: DPxGetDacRange() minV argument is null\n");
		DPxSetError(DPX_ERR_DAC_RANGE_NULL_PTR);
		return;
	}
	if (!maxV) {
		DPxDebugPrint0("ERROR: DPxGetDacRange() maxV argument is null\n");
		DPxSetError(DPX_ERR_DAC_RANGE_NULL_PTR);
		return;
	}
	
	switch(channel) {
		case 0:
		case 1: *minV = -10; *maxV = 10; break;
		case 2:
		case 3:
            if (DPxIsViewpixx() || DPxIsPropixx())
                { *minV = -10; *maxV = 10; }
            else
                { *minV = -5; *maxV = 5; }  // DATAPixx
            break;
		default:
			*minV = -1; *maxV = 1;		// Use +-1 to protect user against divide by 0
			DPxDebugPrint2("ERROR: DPxGetDacRange() argument channel %d is not in range 0 to %d\n", channel, DPX_DAC_NCHANS-1);
			DPxSetError(DPX_ERR_DAC_RANGE_BAD_CHANNEL);
			return;
	}
}


// Set the voltage for one DAC channel +-10V for ch0/1, +-5V for ch2/3
void DPxSetDacVoltage(double voltage, int channel)
{
	double minV, maxV, fValue;
	int iValue;

	if (channel < 0 || channel > DPX_DAC_NCHANS-1) {
		DPxDebugPrint2("ERROR: DPxSetDacVoltage() argument channel %d is not in range 0 to %d\n", channel, DPX_DAC_NCHANS-1);
		DPxSetError(DPX_ERR_DAC_SET_BAD_CHANNEL);
		return;
	}
	ReturnIfError(DPxGetDacRange(channel, &minV, &maxV));
	if (voltage < minV || voltage > maxV) {
		DPxDebugPrint3("ERROR: DPxSetDacVoltage() argument voltage %g is not in range %g to %g\n", voltage, minV, maxV);
		DPxSetError(DPX_ERR_DAC_SET_BAD_VALUE);
		return;
	}

	fValue = (voltage - minV) / (maxV - minV) - 0.5;	// -0.5 to +0.5
	iValue = (int)floor(fValue * 65536 + 0.5);			// -32768 to +32768 with rounding (not truncation)
	if (iValue == 32768)
		iValue = 32767;									// Since maxV is 1 LSB over top
	DPxSetDacValue(iValue, channel);
}


// Get the voltage for one DAC channel +-10V for ch0/1, +-5V for ch2/3
double DPxGetDacVoltage(int channel)
{
	int iValue;
	double minV, maxV;

	Return0IfError(iValue = DPxGetDacValue(channel));
	Return0IfError(DPxGetDacRange(channel, &minV, &maxV));
	return ((double)iValue + 32768) / 65536 * (maxV - minV) + minV;
}


// Enable RAM buffering of a DAC channel
void DPxEnableDacBuffChan(int channel)
{
	if (channel < 0 || channel > DPX_DAC_NCHANS-1) {
		DPxDebugPrint2("ERROR: DPxEnableDacBuffChan() argument channel %d is not in range 0 to %d\n", channel, DPX_DAC_NCHANS-1);
		DPxSetError(DPX_ERR_DAC_BUFF_BAD_CHANNEL);
		return;
	}
	DPxSetReg16(DPXREG_DAC_CHANSEL, DPxGetReg16(DPXREG_DAC_CHANSEL) | (1 << channel));	
}


// Disable RAM buffering of a DAC channel
void DPxDisableDacBuffChan(int channel)
{
	if (channel < 0 || channel > DPX_DAC_NCHANS-1) {
		DPxDebugPrint2("ERROR: DPxDisableDacBuffChan() argument channel %d is not in range 0 to %d\n", channel, DPX_DAC_NCHANS-1);
		DPxSetError(DPX_ERR_DAC_BUFF_BAD_CHANNEL);
		return;
	}
	DPxSetReg16(DPXREG_DAC_CHANSEL, DPxGetReg16(DPXREG_DAC_CHANSEL) & ~(1 << channel));	
}


// Disable RAM buffering of all DAC channels
void DPxDisableDacBuffAllChans()
{
	DPxSetReg16(DPXREG_DAC_CHANSEL, 0);	
}


// Returns non-0 if RAM buffering is enabled for a channel
int DPxIsDacBuffChan(int channel)
{
	if (channel < 0 || channel > DPX_DAC_NCHANS-1) {
		DPxDebugPrint2("ERROR: DPxIsDacBuffChan() argument channel %d is not in range 0 to %d\n", channel, DPX_DAC_NCHANS-1);
		DPxSetError(DPX_ERR_DAC_BUFF_BAD_CHANNEL);
		return 0;
	}
	return DPxGetReg16(DPXREG_DAC_CHANSEL) & (1 << channel);
}


// Enable DAC "raw" mode, causing DAC data to bypass hardware calibration
void DPxEnableDacCalibRaw()
{
	DPxSetReg16(DPXREG_DAC_CTRL, DPxGetReg16(DPXREG_DAC_CTRL) | DPXREG_DAC_CTRL_CALIB_RAW);
}


// Disable DAC "raw" mode, causing normal DAC hardware calibration
void DPxDisableDacCalibRaw()
{
	DPxSetReg16(DPXREG_DAC_CTRL, DPxGetReg16(DPXREG_DAC_CTRL) & ~DPXREG_DAC_CTRL_CALIB_RAW);
}


// Returns non-0 if DAC data is bypassing hardware calibration
int DPxIsDacCalibRaw()
{
	return DPxGetReg16(DPXREG_DAC_CTRL) & DPXREG_DAC_CTRL_CALIB_RAW;
}


// Set DAC RAM buffer base address.  Must be an even value.
void DPxSetDacBuffBaseAddr(unsigned buffBaseAddr)
{
	if (buffBaseAddr & 1) {
		DPxDebugPrint1("ERROR: DPxSetDacBuffBaseAddr(0x%x) illegal odd address\n", buffBaseAddr);
		DPxSetError(DPX_ERR_DAC_BUFF_ODD_BASEADDR);
		return;
	}
	if (buffBaseAddr >= DPxGetRamSize()) {
		DPxDebugPrint1("ERROR: DPxSetDacBuffBaseAddr(0x%x) exceeds DATAPixx RAM\n", buffBaseAddr);
		DPxSetError(DPX_ERR_DAC_BUFF_BASEADDR_TOO_HIGH);
		return;
	}
	DPxSetReg32(DPXREG_DAC_BUFF_BASEADDR_L, buffBaseAddr);
}


// Get DAC RAM buffer base address
unsigned DPxGetDacBuffBaseAddr()
{
	return DPxGetReg32(DPXREG_DAC_BUFF_BASEADDR_L);
}


// Set RAM address from which next DAC datum will be read.  Must be an even value.
void DPxSetDacBuffReadAddr(unsigned buffReadAddr)
{
	if (buffReadAddr & 1) {
		DPxDebugPrint1("ERROR: DPxSetDacBuffReadAddr(0x%x) illegal odd address\n", buffReadAddr);
		DPxSetError(DPX_ERR_DAC_BUFF_ODD_READADDR);
		return;
	}
	if (buffReadAddr >= DPxGetRamSize()) {
		DPxDebugPrint1("ERROR: DPxSetDacBuffReadAddr(0x%x) exceeds DATAPixx RAM\n", buffReadAddr);
		DPxSetError(DPX_ERR_DAC_BUFF_READADDR_TOO_HIGH);
		return;
	}
	DPxSetReg32(DPXREG_DAC_BUFF_READADDR_L, buffReadAddr);
}


// Get RAM address from which next DAC datum will be read
unsigned DPxGetDacBuffReadAddr()
{
	return DPxGetReg32(DPXREG_DAC_BUFF_READADDR_L);
}


// Set DAC RAM buffer size in bytes.  Must be an even value.
// The hardware will automatically wrap the BuffReadAddr, when it gets to BuffBaseAddr+BuffSize, back to BuffBaseAddr.
// This simplifies spooled playback, or the continuous playback of periodic waveforms.
void DPxSetDacBuffSize(unsigned buffSize)
{
	if (buffSize & 1) {
		DPxDebugPrint1("ERROR: DPxSetDacBuffSize(0x%x) illegal odd size\n", buffSize);
		DPxSetError(DPX_ERR_DAC_BUFF_ODD_SIZE);
		return;
	}
	if (buffSize > DPxGetRamSize()) {
		DPxDebugPrint1("ERROR: DPxSetDacBuffSize(0x%x) exceeds DATAPixx RAM\n", buffSize);
		DPxSetError(DPX_ERR_DAC_BUFF_TOO_BIG);
		return;
	}
	DPxSetReg32(DPXREG_DAC_BUFF_SIZE_L, buffSize);
}


// Get DAC RAM buffer size in bytes
unsigned DPxGetDacBuffSize()
{
	return DPxGetReg32(DPXREG_DAC_BUFF_SIZE_L);
}


// Shortcut which assigns Size/BaseAddr/ReadAddr
void DPxSetDacBuff(unsigned buffAddr, unsigned buffSize)
{
	DPxSetDacBuffBaseAddr(buffAddr);
	DPxSetDacBuffReadAddr(buffAddr);
	DPxSetDacBuffSize(buffSize);
}


// Set nanosecond delay between schedule start and first DAC update
void DPxSetDacSchedOnset(unsigned onset)
{
	DPxSetReg32(DPXREG_DAC_SCHED_ONSET_L, onset);
}


// Get nanosecond delay between schedule start and first DAC update
unsigned DPxGetDacSchedOnset()
{
	return DPxGetReg32(DPXREG_DAC_SCHED_ONSET_L);
}


// Set DAC schedule update rate and units.
// Documentation limits to 1 MHz (but in practice I've tested up to 2 MHz).
// rateUnits is one of the following predefined constants:
//		DPXREG_SCHED_CTRL_RATE_HZ		: rateValue is samples per second, maximum 1 MHz
//		DPXREG_SCHED_CTRL_RATE_XVID		: rateValue is samples per video frame, maximum 1 MHz
//		DPXREG_SCHED_CTRL_RATE_NANO		: rateValue is sample period in nanoseconds, minimum 1000 ns
void DPxSetDacSchedRate(unsigned rateValue, int rateUnits)
{
	switch (rateUnits) {
		case DPXREG_SCHED_CTRL_RATE_HZ:
			if (rateValue > 1000000) {
				DPxDebugPrint1("ERROR: DPxSetDacSchedRate() frequency too high %u\n", rateValue);
				DPxSetError(DPX_ERR_DAC_SCHED_TOO_FAST);
				return;
			}
			break;
		case DPXREG_SCHED_CTRL_RATE_XVID:
			if (rateValue > 1000000/DPxGetVidVFreq()) {
				DPxDebugPrint1("ERROR: DPxSetDacSchedRate() frequency too high %u\n", rateValue);
				DPxSetError(DPX_ERR_DAC_SCHED_TOO_FAST);
				return;
			}
			break;
		case DPXREG_SCHED_CTRL_RATE_NANO:
			if (rateValue < 1000) {
				DPxDebugPrint1("ERROR: DPxSetDacSchedRate() period too low %u\n", rateValue);
				DPxSetError(DPX_ERR_DAC_SCHED_TOO_FAST);
				return;
			}
			break;
		default:
			DPxDebugPrint1("ERROR: DPxSetDacSchedRate() unrecognized rateUnits %d\n", rateUnits);
			DPxSetError(DPX_ERR_DAC_SCHED_BAD_RATE_UNITS);
			return;
	}
	DPxSetReg32(DPXREG_DAC_SCHED_CTRL_L, (DPxGetReg32(DPXREG_DAC_SCHED_CTRL_L) & ~DPXREG_SCHED_CTRL_RATE_MASK) | rateUnits);
	DPxSetReg32(DPXREG_DAC_SCHED_RATE_L,  rateValue);
}


// Get DAC schedule update rate (and optionally get rate units)
unsigned DPxGetDacSchedRate(int *rateUnits)
{
	if (rateUnits)
		*rateUnits = DPxGetReg32(DPXREG_DAC_SCHED_CTRL_L) & DPXREG_SCHED_CTRL_RATE_MASK;
	return DPxGetReg32(DPXREG_DAC_SCHED_RATE_L);
}


// Set DAC schedule update count
void DPxSetDacSchedCount(unsigned count)
{
	DPxSetReg32(DPXREG_DAC_SCHED_COUNT_L,  count);
}


// Get DAC schedule update count
unsigned DPxGetDacSchedCount()
{
	return DPxGetReg32(DPXREG_DAC_SCHED_COUNT_L);
}


// SchedCount decrements at SchedRate, and schedule stops automatically when count hits 0
void DPxEnableDacSchedCountdown()
{
	DPxSetReg32(DPXREG_DAC_SCHED_CTRL_L, DPxGetReg32(DPXREG_DAC_SCHED_CTRL_L) | DPXREG_SCHED_CTRL_COUNTDOWN);
}


// SchedCount increments at SchedRate, and schedule is stopped by calling SchedStop
void DPxDisableDacSchedCountdown()
{
	DPxSetReg32(DPXREG_DAC_SCHED_CTRL_L, DPxGetReg32(DPXREG_DAC_SCHED_CTRL_L) & ~DPXREG_SCHED_CTRL_COUNTDOWN);
}


// Returns non-0 if SchedCount decrements to 0 and automatically stops schedule
int DPxIsDacSchedCountdown()
{
	return DPxGetReg32(DPXREG_DAC_SCHED_CTRL_L) & DPXREG_SCHED_CTRL_COUNTDOWN;
}


// Shortcut which assigns Onset/Rate/Count.
// If Count > 0, enables Countdown mode.
void DPxSetDacSched(unsigned onset, unsigned rateValue, int rateUnits, unsigned count)
{
	DPxSetDacSchedOnset(onset);
	DPxSetDacSchedRate(rateValue, rateUnits);
	DPxSetDacSchedCount(count);
	if (count)
		DPxEnableDacSchedCountdown();
	else
		DPxDisableDacSchedCountdown();
}


// Start running a DAC schedule
void DPxStartDacSched()
{
	DPxSetReg16(DPXREG_SCHED_STARTSTOP, (DPxGetReg16(DPXREG_SCHED_STARTSTOP) & ~(DPXREG_SCHED_STARTSTOP_MASK << DPXREG_SCHED_STARTSTOP_SHIFT_DAC)) |
										(DPXREG_SCHED_STARTSTOP_START << DPXREG_SCHED_STARTSTOP_SHIFT_DAC));
}


// Stop running a DAC schedule
void DPxStopDacSched()
{
	DPxSetReg16(DPXREG_SCHED_STARTSTOP, (DPxGetReg16(DPXREG_SCHED_STARTSTOP) & ~(DPXREG_SCHED_STARTSTOP_MASK << DPXREG_SCHED_STARTSTOP_SHIFT_DAC)) |
										(DPXREG_SCHED_STARTSTOP_STOP << DPXREG_SCHED_STARTSTOP_SHIFT_DAC));
}


// Returns non-0 if DAC schedule is currently running
int DPxIsDacSchedRunning()
{
	return DPxGetReg32(DPXREG_DAC_SCHED_CTRL_L) & DPXREG_SCHED_CTRL_RUNNING;
}


/********************************************************************************/
/*																				*/
/*	ADC Subsystem																*/
/*																				*/
/********************************************************************************/


// Returns number of ADC channels in system, excluding REF0/1
int DPxGetAdcNumChans()
{
	return DPX_ADC_NCHANS;
}


// Get the 16-bit 2's complement signed value for one ADC channel (0-17)
int DPxGetAdcValue(int channel)
{
	if (channel < 0 || channel > DPX_ADC_NCHANS+1) {
		DPxDebugPrint2("ERROR: DPxGetAdcValue() argument channel %d is not in range 0 to %d\n", channel, DPX_ADC_NCHANS+1);
		DPxSetError(DPX_ERR_ADC_GET_BAD_CHANNEL);
		return 0;
	}
	return (SInt16)DPxGetReg16(DPXREG_ADC_DATA0+channel*2);
}


// Get the voltage min/max range for an ADC channel (0-17).
// Note that the true max value will really be 1 LSB less than the reported max value.
void DPxGetAdcRange(int channel, double *minV, double *maxV)
{
	if (!minV) {
		DPxDebugPrint0("ERROR: DPxGetAdcRange() minV argument is null\n");
		DPxSetError(DPX_ERR_ADC_RANGE_NULL_PTR);
		return;
	}
	if (!maxV) {
		DPxDebugPrint0("ERROR: DPxGetAdcRange() maxV argument is null\n");
		DPxSetError(DPX_ERR_ADC_RANGE_NULL_PTR);
		return;
	}

	if (channel >= 0 && channel <= DPX_ADC_NCHANS+1) {
		*minV = -10;
		*maxV = 10;
	}
	else {
		*minV = -1;		// Use +-1 to protect user against divide by 0
		*maxV = 1;
		DPxDebugPrint2("ERROR: DPxGetAdcRange() argument channel %d is not in range 0 to %d\n", channel, DPX_ADC_NCHANS+1);
		DPxSetError(DPX_ERR_ADC_RANGE_BAD_CHANNEL);
	}
}


// Get the voltage for one ADC channel
double DPxGetAdcVoltage(int channel)
{
	int iValue;
	double minV, maxV;

	Return0IfError(iValue = DPxGetAdcValue(channel));
	Return0IfError(DPxGetAdcRange(channel, &minV, &maxV));
	return ((double)iValue + 32768) / 65536 * (maxV - minV) + minV;
}


// Set a channel's differential reference source (only valid for channels 0-15)
// chanRef is one of the following predefined constants:
//		DPXREG_ADC_CHANREF_GND		: Referenced to ground
//		DPXREG_ADC_CHANREF_DIFF		: Referenced to adjacent analog input 
//		DPXREG_ADC_CHANREF_REF0		: Referenced to REF0 analog input
//		DPXREG_ADC_CHANREF_REF1		: Referenced to REF1 analog input
void DPxSetAdcBuffChanRef(int channel, int chanRef)
{
	if (channel < 0 || channel > DPX_ADC_NCHANS-1) {
		DPxDebugPrint2("ERROR: DPxSetAdcBuffChanRef() argument channel %d is not in range 0 to %d\n", channel, DPX_ADC_NCHANS-1);
		DPxSetError(DPX_ERR_ADC_REF_BAD_CHANNEL);
		return;
	}
	
	switch (chanRef) {
		case DPXREG_ADC_CHANREF_GND:
		case DPXREG_ADC_CHANREF_DIFF:
		case DPXREG_ADC_CHANREF_REF0:
		case DPXREG_ADC_CHANREF_REF1:
			DPxSetReg32(DPXREG_ADC_CHANREF_L, (DPxGetReg32(DPXREG_ADC_CHANREF_L) & ~(3 << (channel*2))) | (chanRef << (channel*2)));
			break;
		default:
			DPxDebugPrint1("ERROR: DPxSetAdcBuffChanRef() unrecognized chanRef %d\n", chanRef);
			DPxSetError(DPX_ERR_ADC_BAD_CHAN_REF);
	}
}


// Get a channel's differential reference source (only valid for channels 0-15)
int DPxGetAdcBuffChanRef(int channel)
{
	if (channel < 0 || channel > DPX_ADC_NCHANS-1) {
		DPxDebugPrint2("ERROR: DPxGetAdcBuffChanRef() argument channel %d is not in range 0 to %d\n", channel, DPX_ADC_NCHANS-1);
		DPxSetError(DPX_ERR_ADC_REF_BAD_CHANNEL);
		return 0;
	}
	return (DPxGetReg32(DPXREG_ADC_CHANREF_L) >> (channel*2)) & 3;
}


// Enable RAM buffering of an ADC channel (only valid for channels 0-15)
void DPxEnableAdcBuffChan(int channel)
{
	if (channel < 0 || channel > DPX_ADC_NCHANS-1) {
		DPxDebugPrint2("ERROR: DPxEnableAdcBuffChan() argument channel %d is not in range 0 to %d\n", channel, DPX_ADC_NCHANS-1);
		DPxSetError(DPX_ERR_ADC_BUFF_BAD_CHANNEL);
		return;
	}
	DPxSetReg16(DPXREG_ADC_CHANSEL, DPxGetReg16(DPXREG_ADC_CHANSEL) | (1 << channel));	
}


// Disable RAM buffering of an ADC channel (only valid for channels 0-15)
void DPxDisableAdcBuffChan(int channel)
{
	if (channel < 0 || channel > DPX_ADC_NCHANS-1) {
		DPxDebugPrint2("ERROR: DPxDisableAdcBuffChan() argument channel %d is not in range 0 to %d\n", channel, DPX_ADC_NCHANS-1);
		DPxSetError(DPX_ERR_ADC_BUFF_BAD_CHANNEL);
		return;
	}
	DPxSetReg16(DPXREG_ADC_CHANSEL, DPxGetReg16(DPXREG_ADC_CHANSEL) & ~(1 << channel));	
}


// Disable RAM buffering of all ADC channels
void DPxDisableAdcBuffAllChans()
{
	DPxSetReg16(DPXREG_ADC_CHANSEL, 0);	
}


// Returns non-0 if RAM buffering is enabled for an ADC channel (only valid for channels 0-15)
int DPxIsAdcBuffChan(int channel)
{
	if (channel < 0 || channel > DPX_ADC_NCHANS-1) {
		DPxDebugPrint2("ERROR: DPxIsAdcBuffChan() argument channel %d is not in range 0 to %d\n", channel, DPX_ADC_NCHANS-1);
		DPxSetError(DPX_ERR_ADC_BUFF_BAD_CHANNEL);
		return 0;
	}
	return DPxGetReg16(DPXREG_ADC_CHANSEL) & (1 << channel);
}


// Enable ADC "raw" mode, causing ADC data to bypass hardware calibration
void DPxEnableAdcCalibRaw()
{
	DPxSetReg16(DPXREG_ADC_CTRL, DPxGetReg16(DPXREG_ADC_CTRL) | DPXREG_ADC_CTRL_CALIB_RAW);
}


// Disable ADC "raw" mode, causing normal ADC hardware calibration
void DPxDisableAdcCalibRaw()
{
	DPxSetReg16(DPXREG_ADC_CTRL, DPxGetReg16(DPXREG_ADC_CTRL) & ~DPXREG_ADC_CTRL_CALIB_RAW);
}


// Returns non-0 if ADC data is bypassing hardware calibration
int DPxIsAdcCalibRaw()
{
	return DPxGetReg16(DPXREG_ADC_CTRL) & DPXREG_ADC_CTRL_CALIB_RAW;
}


// ADC data readings are looped back internally from programmed DAC voltages:
//		DAC_DATA0 => ADC_DATA0/2/4/6/8/10/12/14
//		DAC_DATA1 => ADC_DATA1/3/5/7/9/11/13/15
//		DAC_DATA2 => ADC_REF0
//		DAC_DATA3 => ADC_REF1
void DPxEnableDacAdcLoopback()
{
	DPxSetReg16(DPXREG_ADC_CTRL, DPxGetReg16(DPXREG_ADC_CTRL) | DPXREG_ADC_CTRL_DAC_LOOPBACK);
}


// Disable ADC loopback, causing ADC readings to reflect real analog inputs
void DPxDisableDacAdcLoopback()
{
	DPxSetReg16(DPXREG_ADC_CTRL, DPxGetReg16(DPXREG_ADC_CTRL) & ~DPXREG_ADC_CTRL_DAC_LOOPBACK);
}


// Returns non-0 if ADC inputs are looped back from DAC outputs
int DPxIsDacAdcLoopback()
{
	return DPxGetReg16(DPXREG_ADC_CTRL) & DPXREG_ADC_CTRL_DAC_LOOPBACK;
}


// ADC's convert continuously (can add up to 4 microseconds random latency to scheduled samples)
void DPxEnableAdcFreeRun()
{
	DPxSetReg16(DPXREG_ADC_CTRL, DPxGetReg16(DPXREG_ADC_CTRL) | DPXREG_ADC_CTRL_FREE_RUN);
}


// ADC's only convert on schedule ticks (for microsecond-precise sampling)
void DPxDisableAdcFreeRun()
{
	DPxSetReg16(DPXREG_ADC_CTRL, DPxGetReg16(DPXREG_ADC_CTRL) & ~DPXREG_ADC_CTRL_FREE_RUN);
}


// Returns non-0 if ADC's are performing continuous conversions
int DPxIsAdcFreeRun()
{
	return DPxGetReg16(DPXREG_ADC_CTRL) & DPXREG_ADC_CTRL_FREE_RUN;
}


// Set ADC RAM buffer start address.  Must be an even value.
void DPxSetAdcBuffBaseAddr(unsigned buffBaseAddr)
{
	if (buffBaseAddr & 1) {
		DPxDebugPrint1("ERROR: DPxSetAdcBuffBaseAddr(0x%x) illegal odd address\n", buffBaseAddr);
		DPxSetError(DPX_ERR_ADC_BUFF_ODD_BASEADDR);
		return;
	}
	if (buffBaseAddr >= DPxGetRamSize()) {
		DPxDebugPrint1("ERROR: DPxSetAdcBuffBaseAddr(0x%x) exceeds DATAPixx RAM\n", buffBaseAddr);
		DPxSetError(DPX_ERR_ADC_BUFF_BASEADDR_TOO_HIGH);
		return;
	}
	DPxSetReg32(DPXREG_ADC_BUFF_BASEADDR_L, buffBaseAddr);
}


// Get ADC RAM buffer start address
unsigned DPxGetAdcBuffBaseAddr()
{
	return DPxGetReg32(DPXREG_ADC_BUFF_BASEADDR_L);
}


// Set RAM address to which next ADC datum will be written.  Must be an even value.
void DPxSetAdcBuffWriteAddr(unsigned buffWriteAddr)
{
	if (buffWriteAddr & 1) {
		DPxDebugPrint1("ERROR: DPxSetAdcBuffWriteAddr(0x%x) illegal odd address\n", buffWriteAddr);
		DPxSetError(DPX_ERR_ADC_BUFF_ODD_WRITEADDR);
		return;
	}
	if (buffWriteAddr >= DPxGetRamSize()) {
		DPxDebugPrint1("ERROR: DPxSetAdcBuffWriteAddr(0x%x) exceeds DATAPixx RAM\n", buffWriteAddr);
		DPxSetError(DPX_ERR_ADC_BUFF_WRITEADDR_TOO_HIGH);
		return;
	}
	DPxSetReg32(DPXREG_ADC_BUFF_WRITEADDR_L, buffWriteAddr);
}


// Get RAM address to which next ADC datum will be written
unsigned DPxGetAdcBuffWriteAddr()
{
	return DPxGetReg32(DPXREG_ADC_BUFF_WRITEADDR_L);
}


// Set ADC RAM buffer size in bytes.  Must be an even value.
// The hardware will automatically wrap the BuffWriteAddr, when it gets to BuffBaseAddr+BuffSize, back to BuffBaseAddr.
// This simplifies continuous spooled acquisition.
void DPxSetAdcBuffSize(unsigned buffSize)
{
	if (buffSize & 1) {
		DPxDebugPrint1("ERROR: DPxSetAdcBuffSize(0x%x) illegal odd size\n", buffSize);
		DPxSetError(DPX_ERR_ADC_BUFF_ODD_SIZE);
		return;
	}
	if (buffSize > DPxGetRamSize()) {
		DPxDebugPrint1("ERROR: DPxSetAdcBuffSize(0x%x) exceeds DATAPixx RAM\n", buffSize);
		DPxSetError(DPX_ERR_ADC_BUFF_TOO_BIG);
		return;
	}
	DPxSetReg32(DPXREG_ADC_BUFF_SIZE_L, buffSize);
}


// Get ADC RAM buffer size in bytes
unsigned DPxGetAdcBuffSize()
{
	return DPxGetReg32(DPXREG_ADC_BUFF_SIZE_L);
}


// Shortcut which assigns Size/BaseAddr/ReadAddr
void DPxSetAdcBuff(unsigned buffAddr, unsigned buffSize)
{
	DPxSetAdcBuffBaseAddr(buffAddr);
	DPxSetAdcBuffWriteAddr(buffAddr);
	DPxSetAdcBuffSize(buffSize);
}


// Set nanosecond delay between schedule start and first ADC sample
void DPxSetAdcSchedOnset(unsigned onset)
{
	DPxSetReg32(DPXREG_ADC_SCHED_ONSET_L, onset);
}


// Get nanosecond delay between schedule start and first ADC sample
unsigned DPxGetAdcSchedOnset()
{
	return DPxGetReg32(DPXREG_ADC_SCHED_ONSET_L);
}


// Set ADC schedule sample rate and units
// rateUnits is one of the following predefined constants:
//		DPXREG_SCHED_CTRL_RATE_HZ		: rateValue is samples per second, maximum 200 kHz
//		DPXREG_SCHED_CTRL_RATE_XVID		: rateValue is samples per video frame, maximum 200 kHz
//		DPXREG_SCHED_CTRL_RATE_NANO		: rateValue is sample period in nanoseconds, minimum 5000 ns
void DPxSetAdcSchedRate(unsigned rateValue, int rateUnits)
{
	switch (rateUnits) {
		case DPXREG_SCHED_CTRL_RATE_HZ:
			if (rateValue > 200000) {
				DPxDebugPrint1("ERROR: DPxSetAdcSchedRate() frequency too high %u\n", rateValue);
				DPxSetError(DPX_ERR_ADC_SCHED_TOO_FAST);
				return;
			}
			break;
		case DPXREG_SCHED_CTRL_RATE_XVID:
			if (rateValue > 200000/DPxGetVidVFreq()) {
				DPxDebugPrint1("ERROR: DPxSetAdcSchedRate() frequency too high %u\n", rateValue);
				DPxSetError(DPX_ERR_ADC_SCHED_TOO_FAST);
				return;
			}
			break;
		case DPXREG_SCHED_CTRL_RATE_NANO:
			if (rateValue < 5000) {
				DPxDebugPrint1("ERROR: DPxSetAdcSchedRate() period too low %u\n", rateValue);
				DPxSetError(DPX_ERR_ADC_SCHED_TOO_FAST);
				return;
			}
			break;
		default:
			DPxDebugPrint1("ERROR: DPxSetAdcSchedRate() unrecognized rateUnits %d\n", rateUnits);
			DPxSetError(DPX_ERR_ADC_SCHED_BAD_RATE_UNITS);
			return;
	}
	DPxSetReg32(DPXREG_ADC_SCHED_CTRL_L, (DPxGetReg32(DPXREG_ADC_SCHED_CTRL_L) & ~DPXREG_SCHED_CTRL_RATE_MASK) | rateUnits);
	DPxSetReg32(DPXREG_ADC_SCHED_RATE_L,  rateValue);
}


// Get ADC schedule update rate (and optionally get rate units)
unsigned DPxGetAdcSchedRate(int *rateUnits)
{
	if (rateUnits)
		*rateUnits = DPxGetReg32(DPXREG_ADC_SCHED_CTRL_L) & DPXREG_SCHED_CTRL_RATE_MASK;
	return DPxGetReg32(DPXREG_ADC_SCHED_RATE_L);
}


// Set ADC schedule update count
void DPxSetAdcSchedCount(unsigned count)
{
	DPxSetReg32(DPXREG_ADC_SCHED_COUNT_L,  count);
}


// Get ADC schedule update count
unsigned DPxGetAdcSchedCount()
{
	return DPxGetReg32(DPXREG_ADC_SCHED_COUNT_L);
}


// SchedCount decrements at SchedRate, and schedule stops automatically when count hits 0
void DPxEnableAdcSchedCountdown()
{
	DPxSetReg32(DPXREG_ADC_SCHED_CTRL_L, DPxGetReg32(DPXREG_ADC_SCHED_CTRL_L) | DPXREG_SCHED_CTRL_COUNTDOWN);
}


// SchedCount increments at SchedRate, and schedule is stopped by calling SchedStop
void DPxDisableAdcSchedCountdown()
{
	DPxSetReg32(DPXREG_ADC_SCHED_CTRL_L, DPxGetReg32(DPXREG_ADC_SCHED_CTRL_L) & ~DPXREG_SCHED_CTRL_COUNTDOWN);
}


// Returns non-0 if SchedCount decrements to 0 and automatically stops schedule
int DPxIsAdcSchedCountdown()
{
	return DPxGetReg32(DPXREG_ADC_SCHED_CTRL_L) & DPXREG_SCHED_CTRL_COUNTDOWN;
}


// Shortcut which assigns Onset/Rate/Count.
// If Count > 0, enables Countdown mode.
void DPxSetAdcSched(unsigned onset, unsigned rateValue, int rateUnits, unsigned count)
{
	DPxSetAdcSchedOnset(onset);
	DPxSetAdcSchedRate(rateValue, rateUnits);
	DPxSetAdcSchedCount(count);
	if (count)
		DPxEnableAdcSchedCountdown();
	else
		DPxDisableAdcSchedCountdown();
}


// Start running an ADC schedule
void DPxStartAdcSched()
{
	DPxSetReg16(DPXREG_SCHED_STARTSTOP, (DPxGetReg16(DPXREG_SCHED_STARTSTOP) & ~(DPXREG_SCHED_STARTSTOP_MASK << DPXREG_SCHED_STARTSTOP_SHIFT_ADC)) |
										(DPXREG_SCHED_STARTSTOP_START << DPXREG_SCHED_STARTSTOP_SHIFT_ADC));
}


// Stop running an ADC schedule
void DPxStopAdcSched()
{
	DPxSetReg16(DPXREG_SCHED_STARTSTOP, (DPxGetReg16(DPXREG_SCHED_STARTSTOP) & ~(DPXREG_SCHED_STARTSTOP_MASK << DPXREG_SCHED_STARTSTOP_SHIFT_ADC)) |
										(DPXREG_SCHED_STARTSTOP_STOP << DPXREG_SCHED_STARTSTOP_SHIFT_ADC));
}


// Returns non-0 if ADC schedule is currently running
int DPxIsAdcSchedRunning()
{
	return DPxGetReg32(DPXREG_ADC_SCHED_CTRL_L) & DPXREG_SCHED_CTRL_RUNNING;
}


// Each buffered ADC sample is preceeded with a 64-bit nanosecond timetag
void DPxEnableAdcLogTimetags()
{
	DPxSetReg32(DPXREG_ADC_SCHED_CTRL_L, DPxGetReg32(DPXREG_ADC_SCHED_CTRL_L) | DPXREG_SCHED_CTRL_LOG_TIMETAG);
}


// Buffered data has not timetags
void DPxDisableAdcLogTimetags()
{
	DPxSetReg32(DPXREG_ADC_SCHED_CTRL_L, DPxGetReg32(DPXREG_ADC_SCHED_CTRL_L) & ~DPXREG_SCHED_CTRL_LOG_TIMETAG);
}


// Returns non-0 if buffered datasets are preceeded with nanosecond timetag
int DPxIsAdcLogTimetags()
{
	return DPxGetReg32(DPXREG_ADC_SCHED_CTRL_L) & DPXREG_SCHED_CTRL_LOG_TIMETAG;
}


/********************************************************************************/
/*																				*/
/*	DOUT (Digital Output) Subsystem												*/
/*																				*/
/********************************************************************************/


// Returns number of digital output bits in system (24 in current implementation)
int DPxGetDoutNumBits()
{
	return 24;
}


// For each of the 24 bits set in bitMask, set the DOUT to the value in the corresponding bitValue.
void DPxSetDoutValue(int bitValue, int bitMask)
{
	// If user specified unimplemented bits, it's not a fatal error so don't return.
	// At least set the implemented bits.
	if (bitMask & 0xFF000000) {
		DPxDebugPrint2("ERROR: DPxSetDoutValue() argument bitMask %08X includes unimplemented bits %08X\n", bitMask, bitMask & 0xFF000000);
		DPxSetError(DPX_ERR_DOUT_SET_BAD_MASK);
	}

	// Internally, the 24 DOUT bits are implemented as a single 32-bit register.
	// Note that a user write, and a schedule, can step over each other.
	if (bitMask)
		DPxSetReg32(DPXREG_DOUT_DATA_L, (DPxGetReg32(DPXREG_DOUT_DATA_L) & ~bitMask) | (bitValue & bitMask));
}


// Get the values of the 24 DOUT bits
int DPxGetDoutValue()
{
	return DPxGetReg32(DPXREG_DOUT_DATA_L);
}


// Enable automatic DOUT schedules upon DIN button presses
void DPxEnableDoutButtonSchedules()
{
	DPxSetReg16(DPXREG_DOUT_CTRL, DPxGetReg16(DPXREG_DOUT_CTRL) | DPXREG_DOUT_CTRL_BUTTON_SCHEDULES);
}


// Disable automatic DOUT schedules upon DIN button presses
void DPxDisableDoutButtonSchedules()
{
	DPxSetReg16(DPXREG_DOUT_CTRL, DPxGetReg16(DPXREG_DOUT_CTRL) & ~DPXREG_DOUT_CTRL_BUTTON_SCHEDULES);
}


// Returns non-0 if automatic DOUT schedules occur upon DIN button presses
int DPxIsDoutButtonSchedules()
{
	return DPxGetReg16(DPXREG_DOUT_CTRL) & DPXREG_DOUT_CTRL_BUTTON_SCHEDULES;
}


// Set DOUT RAM buffer start address.  Must be an even value.
void DPxSetDoutBuffBaseAddr(unsigned buffBaseAddr)
{
	if (buffBaseAddr & 1) {
		DPxDebugPrint1("ERROR: DPxSetDoutBuffBaseAddr(0x%x) illegal odd address\n", buffBaseAddr);
		DPxSetError(DPX_ERR_DOUT_BUFF_ODD_BASEADDR);
		return;
	}
	if (buffBaseAddr >= DPxGetRamSize()) {
		DPxDebugPrint1("ERROR: DPxSetDoutBuffBaseAddr(0x%x) exceeds DATAPixx RAM\n", buffBaseAddr);
		DPxSetError(DPX_ERR_DOUT_BUFF_BASEADDR_TOO_HIGH);
		return;
	}
	DPxSetReg32(DPXREG_DOUT_BUFF_BASEADDR_L, buffBaseAddr);
}


// Get DOUT RAM buffer start address
unsigned DPxGetDoutBuffBaseAddr()
{
	return DPxGetReg32(DPXREG_DOUT_BUFF_BASEADDR_L);
}


// Set RAM address from which next DOUT datum will be read.  Must be an even value.
void DPxSetDoutBuffReadAddr(unsigned buffReadAddr)
{
	if (buffReadAddr & 1) {
		DPxDebugPrint1("ERROR: DPxSetDoutBuffReadAddr(0x%x) illegal odd address\n", buffReadAddr);
		DPxSetError(DPX_ERR_DOUT_BUFF_ODD_READADDR);
		return;
	}
	if (buffReadAddr >= DPxGetRamSize()) {
		DPxDebugPrint1("ERROR: DPxSetDoutBuffReadAddr(0x%x) exceeds DATAPixx RAM\n", buffReadAddr);
		DPxSetError(DPX_ERR_DOUT_BUFF_READADDR_TOO_HIGH);
		return;
	}
	DPxSetReg32(DPXREG_DOUT_BUFF_READADDR_L, buffReadAddr);
}


// Get RAM address from which next DOUT datum will be read
unsigned DPxGetDoutBuffReadAddr()
{
	return DPxGetReg32(DPXREG_DOUT_BUFF_READADDR_L);
}


// Set DOUT RAM buffer size in bytes.  Must be an even value.  Buffer wraps to Base after Size.
// The hardware will automatically wrap the BuffReadAddr, when it gets to BuffBaseAddr+BuffSize, back to BuffBaseAddr.
// This simplifies spooled playback, or the continuous playback of periodic waveforms.
void DPxSetDoutBuffSize(unsigned buffSize)
{
	if (buffSize & 1) {
		DPxDebugPrint1("ERROR: DPxSetDoutBuffSize(0x%x) illegal odd size\n", buffSize);
		DPxSetError(DPX_ERR_DOUT_BUFF_ODD_SIZE);
		return;
	}
	if (buffSize > DPxGetRamSize()) {
		DPxDebugPrint1("ERROR: DPxSetDoutBuffSize(0x%x) exceeds DATAPixx RAM\n", buffSize);
		DPxSetError(DPX_ERR_DOUT_BUFF_TOO_BIG);
		return;
	}
	DPxSetReg32(DPXREG_DOUT_BUFF_SIZE_L, buffSize);
}


// Get DOUT RAM buffer size in bytes
unsigned DPxGetDoutBuffSize()
{
	return DPxGetReg32(DPXREG_DOUT_BUFF_SIZE_L);
}


// Shortcut which assigns Size/BaseAddr/ReadAddr
void DPxSetDoutBuff(unsigned buffAddr, unsigned buffSize)
{
	DPxSetDoutBuffBaseAddr(buffAddr);
	DPxSetDoutBuffReadAddr(buffAddr);
	DPxSetDoutBuffSize(buffSize);
}


// Set nanosecond delay between schedule start and first DOUT update
void DPxSetDoutSchedOnset(unsigned onset)
{
	DPxSetReg32(DPXREG_DOUT_SCHED_ONSET_L, onset);
}


// Get nanosecond delay between schedule start and first DOUT update
unsigned DPxGetDoutSchedOnset()
{
	return DPxGetReg32(DPXREG_DOUT_SCHED_ONSET_L);
}


// Set DOUT schedule update rate and units.
// Documentation limits to 10 MHz (but in practice I've tested higher, even 100 MHz if waveform fits inside 1 64B cacheline).
// rateUnits is one of the following predefined constants:
//		DPXREG_SCHED_CTRL_RATE_HZ		: rateValue is samples per second, maximum 10 MHz
//		DPXREG_SCHED_CTRL_RATE_XVID		: rateValue is samples per video frame, maximum 10 MHz
//		DPXREG_SCHED_CTRL_RATE_NANO		: rateValue is sample period in nanoseconds, minimum 100 ns
void DPxSetDoutSchedRate(unsigned rateValue, int rateUnits)
{
	switch (rateUnits) {
		case DPXREG_SCHED_CTRL_RATE_HZ:
			if (rateValue > 10000000) {
				DPxDebugPrint1("ERROR: DPxSetDoutSchedRate() frequency too high %u\n", rateValue);
				DPxSetError(DPX_ERR_DOUT_SCHED_TOO_FAST);
				return;
			}
			break;
		case DPXREG_SCHED_CTRL_RATE_XVID:
			if (rateValue > 10000000/DPxGetVidVFreq()) {
				DPxDebugPrint1("ERROR: DPxSetDoutSchedRate() frequency too high %u\n", rateValue);
				DPxSetError(DPX_ERR_DOUT_SCHED_TOO_FAST);
				return;
			}
			break;
		case DPXREG_SCHED_CTRL_RATE_NANO:
			if (rateValue < 100) {
				DPxDebugPrint1("ERROR: DPxSetDoutSchedRate() period too low %u\n", rateValue);
				DPxSetError(DPX_ERR_DOUT_SCHED_TOO_FAST);
				return;
			}
			break;
		default:
			DPxDebugPrint1("ERROR: DPxSetDoutSchedRate() unrecognized rateUnits %d\n", rateUnits);
			DPxSetError(DPX_ERR_DOUT_SCHED_BAD_RATE_UNITS);
			return;
	}
	DPxSetReg32(DPXREG_DOUT_SCHED_CTRL_L, (DPxGetReg32(DPXREG_DOUT_SCHED_CTRL_L) & ~DPXREG_SCHED_CTRL_RATE_MASK) | rateUnits);
	DPxSetReg32(DPXREG_DOUT_SCHED_RATE_L,  rateValue);
}


// Get DOUT schedule update rate (and optionally get rate units)
unsigned DPxGetDoutSchedRate(int *rateUnits)
{
	if (rateUnits)
		*rateUnits = DPxGetReg32(DPXREG_DOUT_SCHED_CTRL_L) & DPXREG_SCHED_CTRL_RATE_MASK;
	return DPxGetReg32(DPXREG_DOUT_SCHED_RATE_L);
}


// Set DOUT schedule update count
void DPxSetDoutSchedCount(unsigned count)
{
	DPxSetReg32(DPXREG_DOUT_SCHED_COUNT_L,  count);
}


// Get DOUT schedule update count
unsigned DPxGetDoutSchedCount()
{
	return DPxGetReg32(DPXREG_DOUT_SCHED_COUNT_L);
}


// SchedCount decrements at SchedRate, and schedule stops automatically when count hits 0
void DPxEnableDoutSchedCountdown()
{
	DPxSetReg32(DPXREG_DOUT_SCHED_CTRL_L, DPxGetReg32(DPXREG_DOUT_SCHED_CTRL_L) | DPXREG_SCHED_CTRL_COUNTDOWN);
}


// SchedCount increments at SchedRate, and schedule is stopped by calling SchedStop
void DPxDisableDoutSchedCountdown()
{
	DPxSetReg32(DPXREG_DOUT_SCHED_CTRL_L, DPxGetReg32(DPXREG_DOUT_SCHED_CTRL_L) & ~DPXREG_SCHED_CTRL_COUNTDOWN);
}


// Returns non-0 if SchedCount decrements to 0 and automatically stops schedule
int DPxIsDoutSchedCountdown()
{
	return DPxGetReg32(DPXREG_DOUT_SCHED_CTRL_L) & DPXREG_SCHED_CTRL_COUNTDOWN;
}


// Shortcut which assigns Onset/Rate/Count.
// If Count > 0, enables Countdown mode.
void DPxSetDoutSched(unsigned onset, unsigned rateValue, int rateUnits, unsigned count)
{
	DPxSetDoutSchedOnset(onset);
	DPxSetDoutSchedRate(rateValue, rateUnits);
	DPxSetDoutSchedCount(count);
	if (count)
		DPxEnableDoutSchedCountdown();
	else
		DPxDisableDoutSchedCountdown();
}


// Start running a DOUT schedule
void DPxStartDoutSched()
{
	DPxSetReg16(DPXREG_SCHED_STARTSTOP, (DPxGetReg16(DPXREG_SCHED_STARTSTOP) & ~(DPXREG_SCHED_STARTSTOP_MASK << DPXREG_SCHED_STARTSTOP_SHIFT_DOUT)) |
										(DPXREG_SCHED_STARTSTOP_START << DPXREG_SCHED_STARTSTOP_SHIFT_DOUT));
}


// Stop running a DOUT schedule
void DPxStopDoutSched()
{
	DPxSetReg16(DPXREG_SCHED_STARTSTOP, (DPxGetReg16(DPXREG_SCHED_STARTSTOP) & ~(DPXREG_SCHED_STARTSTOP_MASK << DPXREG_SCHED_STARTSTOP_SHIFT_DOUT)) |
										(DPXREG_SCHED_STARTSTOP_STOP << DPXREG_SCHED_STARTSTOP_SHIFT_DOUT));
}


// Returns non-0 if DOUT schedule is currently running
int DPxIsDoutSchedRunning()
{
	return DPxGetReg32(DPXREG_DOUT_SCHED_CTRL_L) & DPXREG_SCHED_CTRL_RUNNING;
}


/********************************************************************************/
/*																				*/
/*	DIN (Digital Input) Subsystem																*/
/*																				*/
/********************************************************************************/


// Returns number of digital input bits in system (24 in current implementation)
int DPxGetDinNumBits()
{
	return 24;
}


// Get the values of the 24 DIN bits
int DPxGetDinValue()
{
	return DPxGetReg32(DPXREG_DIN_DATA_L);
}


// Set 24-bit port direction mask.  Set mask bits to 1 for each bit which should drive its port.
void DPxSetDinDataDir(int directionMask)
{
	// If user specified unimplemented bits, it's not a fatal error so don't return.
	// At least set the implemented bits.
	if (directionMask & 0xFF000000) {
		DPxDebugPrint2("ERROR: DPxSetDinDataDir() argument directionMask %08X includes unimplemented bits %08X\n", directionMask, directionMask & 0xFF000000);
		DPxSetError(DPX_ERR_DIN_SET_BAD_MASK);
	}
	DPxSetReg32(DPXREG_DIN_DIR_L, directionMask);
}


// Get 24-bit port direction mask
int DPxGetDinDataDir()
{
	return DPxGetReg32(DPXREG_DIN_DIR_L);
}


// Set the data which should be driven on each port whose output has been enabled by DPxSetDinDataDir()
void DPxSetDinDataOut(int dataOut)
{
	DPxSetReg32(DPXREG_DIN_DATAOUT_L, dataOut);
}


// Get the data which is being driven on each output port
int DPxGetDinDataOut()
{
	return DPxGetReg32(DPXREG_DIN_DATAOUT_L);
}


// Set drive strength of driven outputs.  Range is 0-1.  Implementation uses 1/16 up to 16/16.
void DPxSetDinDataOutStrength(double strength)
{
	int iStrength;

	if (strength < 0 || strength > 1) {
		DPxDebugPrint1("ERROR: DPxSetDinDataOutStrength(%f) illegal value\n", strength);
		DPxSetError(DPX_ERR_DIN_BAD_STRENGTH);
		return;
	}

	// Convert to 0/16 to 16/16.
	iStrength = (int)floor(strength * 16 + 0.5);
	
	// 0/16 has to map to 1/16 (the minimum value),
	// and 16/16 has to map to a register value of 0, which means full strength.
	if (iStrength == 0)
		iStrength = 1;
	else if (iStrength == 16)
		iStrength = 0;

	// And write the value to the register
	DPxSetReg16(DPXREG_DIN_CTRL, (DPxGetReg16(DPXREG_DIN_CTRL) & ~DPXREG_DIN_CTRL_PWM) | (iStrength << 8));
}


// Get drive strength of driven outputs.  Range is 0-1.  Implementation uses 1/16 up to 16/16.
double DPxGetDinDataOutStrength()
{
	int pwmReg = (DPxGetReg16(DPXREG_DIN_CTRL) & DPXREG_DIN_CTRL_PWM) >> 8;
	return pwmReg ? pwmReg/16.0 : 1.0;
}


// DIN transitions are only recognized after entire DIN bus has been stable for 80 ns.
// (good for deskewing parallel busses, and ignoring transmission line reflections).
void DPxEnableDinStabilize()
{
	DPxSetReg16(DPXREG_DIN_CTRL, DPxGetReg16(DPXREG_DIN_CTRL) | DPXREG_DIN_CTRL_STABILIZE);
}


// Immediately recognize all DIN transitions
void DPxDisableDinStabilize()
{
	DPxSetReg16(DPXREG_DIN_CTRL, DPxGetReg16(DPXREG_DIN_CTRL) & ~DPXREG_DIN_CTRL_STABILIZE);
}


// Returns non-0 if DIN transitions are being debounced
int DPxIsDinStabilize()
{
	return DPxGetReg16(DPXREG_DIN_CTRL) & DPXREG_DIN_CTRL_STABILIZE;
}


// When a DIN transitions, ignore further DIN transitions for next 30 milliseconds (good for response buttons)
void DPxEnableDinDebounce()
{
	DPxSetReg16(DPXREG_DIN_CTRL, DPxGetReg16(DPXREG_DIN_CTRL) | DPXREG_DIN_CTRL_DEBOUNCE);
}


// Immediately recognize all DIN transitions
void DPxDisableDinDebounce()
{
	DPxSetReg16(DPXREG_DIN_CTRL, DPxGetReg16(DPXREG_DIN_CTRL) & ~DPXREG_DIN_CTRL_DEBOUNCE);
}


// Returns non-0 if DIN transitions are being debounced
int DPxIsDinDebounce()
{
	return DPxGetReg16(DPXREG_DIN_CTRL) & DPXREG_DIN_CTRL_DEBOUNCE;
}


// Enable loopback between digital output ports and digital inputs
void DPxEnableDoutDinLoopback()
{
	DPxSetReg16(DPXREG_DIN_CTRL, DPxGetReg16(DPXREG_DIN_CTRL) | DPXREG_DIN_CTRL_DOUT_LOOPBACK);
}


// Disable loopback between digital outputs and digital inputs
void DPxDisableDoutDinLoopback()
{
	DPxSetReg16(DPXREG_DIN_CTRL, DPxGetReg16(DPXREG_DIN_CTRL) & ~DPXREG_DIN_CTRL_DOUT_LOOPBACK);
}


// Returns non-0 if digital inputs are driven by digital output ports
int DPxIsDoutDinLoopback()
{
	return DPxGetReg16(DPXREG_DIN_CTRL) & DPXREG_DIN_CTRL_DOUT_LOOPBACK;
}


// Set DIN RAM buffer start address.  Must be an even value.
void DPxSetDinBuffBaseAddr(unsigned buffBaseAddr)
{
	if (buffBaseAddr & 1) {
		DPxDebugPrint1("ERROR: DPxSetDinBuffBaseAddr(0x%x) illegal odd address\n", buffBaseAddr);
		DPxSetError(DPX_ERR_DIN_BUFF_ODD_BASEADDR);
		return;
	}
	if (buffBaseAddr >= DPxGetRamSize()) {
		DPxDebugPrint1("ERROR: DPxSetDinBuffBaseAddr(0x%x) exceeds DATAPixx RAM\n", buffBaseAddr);
		DPxSetError(DPX_ERR_DIN_BUFF_BASEADDR_TOO_HIGH);
		return;
	}
	DPxSetReg32(DPXREG_DIN_BUFF_BASEADDR_L, buffBaseAddr);
}


// Get DIN RAM buffer start address
unsigned DPxGetDinBuffBaseAddr()
{
	return DPxGetReg32(DPXREG_DIN_BUFF_BASEADDR_L);
}


// Set RAM address to which next DIN datum will be written.  Must be an even value.
void DPxSetDinBuffWriteAddr(unsigned buffWriteAddr)
{
	if (buffWriteAddr & 1) {
		DPxDebugPrint1("ERROR: DPxSetDinBuffWriteAddr(0x%x) illegal odd address\n", buffWriteAddr);
		DPxSetError(DPX_ERR_DIN_BUFF_ODD_WRITEADDR);
		return;
	}
	if (buffWriteAddr >= DPxGetRamSize()) {
		DPxDebugPrint1("ERROR: DPxSetDinBuffWriteAddr(0x%x) exceeds DATAPixx RAM\n", buffWriteAddr);
		DPxSetError(DPX_ERR_DIN_BUFF_WRITEADDR_TOO_HIGH);
		return;
	}
	DPxSetReg32(DPXREG_DIN_BUFF_WRITEADDR_L, buffWriteAddr);
}


// Get RAM address to which next DIN datum will be written
unsigned DPxGetDinBuffWriteAddr()
{
	return DPxGetReg32(DPXREG_DIN_BUFF_WRITEADDR_L);
}


// Set DIN RAM buffer size in bytes.  Must be an even value.
// The hardware will automatically wrap the BuffWriteAddr, when it gets to BuffBaseAddr+BuffSize, back to BuffBaseAddr.
// This simplifies continuous spooled acquisition.
void DPxSetDinBuffSize(unsigned buffSize)
{
	if (buffSize & 1) {
		DPxDebugPrint1("ERROR: DPxSetDinBuffSize(0x%x) illegal odd size\n", buffSize);
		DPxSetError(DPX_ERR_DIN_BUFF_ODD_SIZE);
		return;
	}
	if (buffSize > DPxGetRamSize()) {
		DPxDebugPrint1("ERROR: DPxSetDinBuffSize(0x%x) exceeds DATAPixx RAM\n", buffSize);
		DPxSetError(DPX_ERR_DIN_BUFF_TOO_BIG);
		return;
	}
	DPxSetReg32(DPXREG_DIN_BUFF_SIZE_L, buffSize);
}


// Get DIN RAM buffer size in bytes
unsigned DPxGetDinBuffSize()
{
	return DPxGetReg32(DPXREG_DIN_BUFF_SIZE_L);
}


// Shortcut which assigns Size/BaseAddr/ReadAddr
void DPxSetDinBuff(unsigned buffAddr, unsigned buffSize)
{
	DPxSetDinBuffBaseAddr(buffAddr);
	DPxSetDinBuffWriteAddr(buffAddr);
	DPxSetDinBuffSize(buffSize);
}


// Set nanosecond delay between schedule start and first DIN sample
void DPxSetDinSchedOnset(unsigned onset)
{
	DPxSetReg32(DPXREG_DIN_SCHED_ONSET_L, onset);
}


// Get nanosecond delay between schedule start and first DIN sample
unsigned DPxGetDinSchedOnset()
{
	return DPxGetReg32(DPXREG_DIN_SCHED_ONSET_L);
}


// Set DIN schedule sample rate and units
// rateUnits is one of the following predefined constants:
//		DPXREG_SCHED_CTRL_RATE_HZ		: rateValue is samples per second, maximum 1 MHz
//		DPXREG_SCHED_CTRL_RATE_XVID		: rateValue is samples per video frame, maximum 1 MHz
//		DPXREG_SCHED_CTRL_RATE_NANO		: rateValue is sample period in nanoseconds, minimum 1000 ns
// DIN scheduling is probably good to 2 MHz now.  I can certainly log edges at about 3 MHz.
// If I want to do any better, I'll have to stop flushing DPR cache to RAM after every sample.
void DPxSetDinSchedRate(unsigned rateValue, int rateUnits)
{
	switch (rateUnits) {
		case DPXREG_SCHED_CTRL_RATE_HZ:
			if (rateValue > 1000000) {
				DPxDebugPrint1("ERROR: DPxSetDinSchedRate() frequency too high %u\n", rateValue);
				DPxSetError(DPX_ERR_DIN_SCHED_TOO_FAST);
				return;
			}
			break;
		case DPXREG_SCHED_CTRL_RATE_XVID:
			if (rateValue > 1000000/DPxGetVidVFreq()) {
				DPxDebugPrint1("ERROR: DPxSetDinSchedRate() frequency too high %u\n", rateValue);
				DPxSetError(DPX_ERR_DIN_SCHED_TOO_FAST);
				return;
			}
			break;
		case DPXREG_SCHED_CTRL_RATE_NANO:
			if (rateValue < 1000) {
				DPxDebugPrint1("ERROR: DPxSetDinSchedRate() period too low %u\n", rateValue);
				DPxSetError(DPX_ERR_DIN_SCHED_TOO_FAST);
				return;
			}
			break;
		default:
			DPxDebugPrint1("ERROR: DPxSetDinSchedRate() unrecognized rateUnits %d\n", rateUnits);
			DPxSetError(DPX_ERR_DIN_SCHED_BAD_RATE_UNITS);
			return;
	}
	DPxSetReg32(DPXREG_DIN_SCHED_CTRL_L, (DPxGetReg32(DPXREG_DIN_SCHED_CTRL_L) & ~DPXREG_SCHED_CTRL_RATE_MASK) | rateUnits);
	DPxSetReg32(DPXREG_DIN_SCHED_RATE_L,  rateValue);
}


// Get DIN schedule update rate (and optionally get rate units)
unsigned DPxGetDinSchedRate(int *rateUnits)
{
	if (rateUnits)
		*rateUnits = DPxGetReg32(DPXREG_DIN_SCHED_CTRL_L) & DPXREG_SCHED_CTRL_RATE_MASK;
	return DPxGetReg32(DPXREG_DIN_SCHED_RATE_L);
}


// Set DIN schedule update count
void DPxSetDinSchedCount(unsigned count)
{
	DPxSetReg32(DPXREG_DIN_SCHED_COUNT_L,  count);
}


// Get DIN schedule update count
unsigned DPxGetDinSchedCount()
{
	return DPxGetReg32(DPXREG_DIN_SCHED_COUNT_L);
}


// SchedCount decrements at SchedRate, and schedule stops automatically when count hits 0
void DPxEnableDinSchedCountdown()
{
	DPxSetReg32(DPXREG_DIN_SCHED_CTRL_L, DPxGetReg32(DPXREG_DIN_SCHED_CTRL_L) | DPXREG_SCHED_CTRL_COUNTDOWN);
}


// SchedCount increments at SchedRate, and schedule is stopped by calling SchedStop
void DPxDisableDinSchedCountdown()
{
	DPxSetReg32(DPXREG_DIN_SCHED_CTRL_L, DPxGetReg32(DPXREG_DIN_SCHED_CTRL_L) & ~DPXREG_SCHED_CTRL_COUNTDOWN);
}


// Returns non-0 if SchedCount decrements to 0 and automatically stops schedule
int DPxIsDinSchedCountdown()
{
	return DPxGetReg32(DPXREG_DIN_SCHED_CTRL_L) & DPXREG_SCHED_CTRL_COUNTDOWN;
}


// Shortcut which assigns Onset/Rate/Count.
// If Count > 0, enables Countdown mode.
void DPxSetDinSched(unsigned onset, unsigned rateValue, int rateUnits, unsigned count)
{
	DPxSetDinSchedOnset(onset);
	DPxSetDinSchedRate(rateValue, rateUnits);
	DPxSetDinSchedCount(count);
	if (count)
		DPxEnableDinSchedCountdown();
	else
		DPxDisableDinSchedCountdown();
}


// Start running an DIN schedule
void DPxStartDinSched()
{
	DPxSetReg16(DPXREG_SCHED_STARTSTOP, (DPxGetReg16(DPXREG_SCHED_STARTSTOP) & ~(DPXREG_SCHED_STARTSTOP_MASK << DPXREG_SCHED_STARTSTOP_SHIFT_DIN)) |
										(DPXREG_SCHED_STARTSTOP_START << DPXREG_SCHED_STARTSTOP_SHIFT_DIN));
}


// Stop running an DIN schedule
void DPxStopDinSched()
{
	DPxSetReg16(DPXREG_SCHED_STARTSTOP, (DPxGetReg16(DPXREG_SCHED_STARTSTOP) & ~(DPXREG_SCHED_STARTSTOP_MASK << DPXREG_SCHED_STARTSTOP_SHIFT_DIN)) |
										(DPXREG_SCHED_STARTSTOP_STOP << DPXREG_SCHED_STARTSTOP_SHIFT_DIN));
}


// Returns non-0 if DIN schedule is currently running
int DPxIsDinSchedRunning()
{
	return DPxGetReg32(DPXREG_DIN_SCHED_CTRL_L) & DPXREG_SCHED_CTRL_RUNNING;
}


// Each buffered DIN sample is preceeded with a 64-bit nanosecond timetag
void DPxEnableDinLogTimetags()
{
	DPxSetReg32(DPXREG_DIN_SCHED_CTRL_L, DPxGetReg32(DPXREG_DIN_SCHED_CTRL_L) | DPXREG_SCHED_CTRL_LOG_TIMETAG);
}


// Buffered data has not timetags
void DPxDisableDinLogTimetags()
{
	DPxSetReg32(DPXREG_DIN_SCHED_CTRL_L, DPxGetReg32(DPXREG_DIN_SCHED_CTRL_L) & ~DPXREG_SCHED_CTRL_LOG_TIMETAG);
}


// Returns non-0 if buffered datasets are preceeded with nanosecond timetag
int DPxIsDinLogTimetags()
{
	return DPxGetReg32(DPXREG_DIN_SCHED_CTRL_L) & DPXREG_SCHED_CTRL_LOG_TIMETAG;
}


// Each DIN transition is automatically logged (no schedule is required.  Best way to log response buttons)
void DPxEnableDinLogEvents()
{
	DPxSetReg32(DPXREG_DIN_SCHED_CTRL_L, DPxGetReg32(DPXREG_DIN_SCHED_CTRL_L) | DPXREG_SCHED_CTRL_LOG_EVENTS);
}


// Disable automatic logging of DIN transitions
void DPxDisableDinLogEvents()
{
	DPxSetReg32(DPXREG_DIN_SCHED_CTRL_L, DPxGetReg32(DPXREG_DIN_SCHED_CTRL_L) & ~DPXREG_SCHED_CTRL_LOG_EVENTS);
}


// Returns non-0 if DIN transitions are being logged to RAM buffer
int DPxIsDinLogEvents()
{
	return DPxGetReg32(DPXREG_DIN_SCHED_CTRL_L) & DPXREG_SCHED_CTRL_LOG_EVENTS;
}


/********************************************************************************/
/*																				*/
/*	TOUCHPixx Subsystem															*/
/*																				*/
/********************************************************************************/


int DPxIsTouchpixx()
{
	return DPxGetReg16(DPXREG_DIN_CTRL) & DPXREG_DIN_CTRL_TOUCHPIXX;
}


void DPxEnableTouchpixx()
{
	DPxSetReg16(DPXREG_DIN_CTRL, DPxGetReg16(DPXREG_DIN_CTRL) | DPXREG_DIN_CTRL_TOUCHPIXX);
}


void DPxDisableTouchpixx()
{
	DPxSetReg16(DPXREG_DIN_CTRL, DPxGetReg16(DPXREG_DIN_CTRL) & ~DPXREG_DIN_CTRL_TOUCHPIXX);
}


double touchpixxStabilizeDuration = 0.01;   // Default to 10ms. A good tradeoff between response time and sensitivity.

void DPxSetTouchpixxStabilizeDuration(double duration)
{
	touchpixxStabilizeDuration = duration;
}


double DPxGetTouchpixxStabilizeDuration()
{
	return touchpixxStabilizeDuration;
}


int DPxIsTouchpixxLogContinuousMode()
{
	return DPxGetReg16(DPXREG_DIN_CTRL) & DPXREG_DIN_CTRL_TOUCHPIXX_CONT;
}


void DPxEnableTouchpixxLogContinuousMode()
{
	DPxSetReg16(DPXREG_DIN_CTRL, DPxGetReg16(DPXREG_DIN_CTRL) | DPXREG_DIN_CTRL_TOUCHPIXX_CONT);
}


void DPxDisableTouchpixxLogContinuousMode()
{
	DPxSetReg16(DPXREG_DIN_CTRL, DPxGetReg16(DPXREG_DIN_CTRL) & ~DPXREG_DIN_CTRL_TOUCHPIXX_CONT);
}


int DPxIsTouchpixxLogEvents()
{
	return DPxGetReg32(DPXREG_DIN_SCHED_CTRL_L) & DPXREG_SCHED_CTRL_LOG_TOUCHPIXX;
}


void DPxEnableTouchpixxLogEvents()
{
	DPxSetReg32(DPXREG_DIN_SCHED_CTRL_L, DPxGetReg32(DPXREG_DIN_SCHED_CTRL_L) | DPXREG_SCHED_CTRL_LOG_TOUCHPIXX);
}


void DPxDisableTouchpixxLogEvents()
{
	DPxSetReg32(DPXREG_DIN_SCHED_CTRL_L, DPxGetReg32(DPXREG_DIN_SCHED_CTRL_L) & ~DPXREG_SCHED_CTRL_LOG_TOUCHPIXX);
}


// Returns non-0 if touch panel is pressed
int DPxIsTouchpixxPressed()
{
	int x, y;
	DPxGetTouchpixxCoords(&x, &y);
    if (x == 0 && y == 0)
		return	0;
	else
		return	1;
}


#define	TOUCHPIXX_STABILIZE_DISTANCE 1500


void DPxGetTouchpixxCoords(int* x, int* y)
{
	static int lastXRead = 0, lastYRead = 0;
	static double startTime = 0;
	static int minValX, maxValX, minValY, maxValY;
	
	int currentX = 0, currentY = 0;
	double currentTimer;	

	currentTimer = DPxGetTime();
	currentX = DPxGetReg16(DPXREG_DIN_DATAOUT_L);
	currentY = DPxGetReg16(DPXREG_DIN_DATAOUT_H);

	if (currentX == 0 && currentY == 0)
		startTime = DPxGetTime();	// reset timer
		
	//printf("\nStart=%8.3f Now=%8.3f   X= %6d LastX= %6d  ***  Y= %6d  LastY= %6d", startTime, currentTimer, currentX, lastXRead, currentY, lastYRead);

	// New pressed touch screen detected
	if (lastXRead == 0 && lastYRead == 0 && currentX != 0 && currentY != 0)
	{
		startTime = DPxGetTime();
        if (DPxGetTouchpixxStabilizeDuration() == 0) {
            *x = currentX;
            *y = currentY;
        }
        else {
            *x = 0;
            *y = 0;
        }
	}
	
	//was touched and still touched
	else if (lastXRead != 0 && lastYRead != 0 && currentX != 0 && currentY != 0) 
	{
		// Outside if limits!
		if (currentX > maxValX || currentX < minValX || currentY > maxValY || currentY < minValY)
		{
            startTime = DPxGetTime();
			*x = 0;
			*y = 0;
		}
		else
		{
			// wanted time is reached?
			if (currentTimer >= (startTime + DPxGetTouchpixxStabilizeDuration()))
			{
				*x = currentX;
				*y = currentY;
			}
			else
			{
				// we still return 0s because time is not reached...
				*x = 0;
				*y = 0;
			}
		}
	}
	// was not touched and not still touched
	else
	{
		*x = 0;
		*y = 0;
	}

    lastXRead = currentX;
    lastYRead = currentY;
    minValX = currentX - TOUCHPIXX_STABILIZE_DISTANCE;
    maxValX = currentX + TOUCHPIXX_STABILIZE_DISTANCE;
    minValY = currentY - TOUCHPIXX_STABILIZE_DISTANCE;
    maxValY = currentY + TOUCHPIXX_STABILIZE_DISTANCE;
}


/********************************************************************************/
/*																				*/
/*	AUD (Audio Output) Subsystem												*/
/*																				*/
/********************************************************************************/

// Call DPxInitAudCodec() once before other Aud/Mic routines, to configure initial audio CODEC state.
// Can also call this at any time to return CODEC to its initial state.
// Note that the first time this routine is called after reset,
// it can pause up to 0.6 seconds while CODEC internal amplifiers are powering up.
// This delay garantees that the CODEC is ready for stable playback immediately upon return.
void DPxInitAudCodec()
{
	double timer;

	// Here's the thing.  It appears that the CODEC output can hang if we update timing registers while DACs are powered up.
	// I especially see this when going from non-double-rate to double-rate mode, but I also see this when only programming divisor.
	// When the CODEC hangs, it seems to never generate audio out until it has been reprogrammed back to non-double-rate mode.
	// It seems that I can prevent this from happening by powering down the DACs while reprogramming the rate or divisor.
	// ADC's also need to be powered down, or audio input and output can both get screwed up.
	// Optimal solution here is just to read the register.
	// InitAudCodec is called rarely, so don't worry about a few milliseconds to read register 2.
	// We take the time to read the register so that we can avoid the pop caused by DAC shutdown.
	if (DPxGetCodecReg(2) != 0x22) {
		DPxSetCodecReg(19, 0x78);	// Powerdown Left ADC
		DPxSetCodecReg(22, 0x78);	// Powerdown Right ADC
		DPxSetCodecReg(37, 0x20);	// Powerdown L/R DACs, configure HPLCOM as an independant output (goes to DP speaker)
	}

	// Stereo DAC outputs are routed to either DAC_L/R1 or DAC_L/R2 or DAC_L/R3.
	// DAC_L/R1 are general purpose internal routing, which can go to any of the output channels.
	// DAC_L/R2 are dedicated routings to the HPL/ROUT (high-power outputs).
	// DAC_L/R3 are dedicated routings to the LEFT/RIGHT_LO (line outputs).
	// So, we definitely have to route to DAC_L/R1.
	DPxSetCodecReg( 0, 0x00);	// Ensure that we are programming page 0
//	DPxSetCodecReg( 1, 0x80);	// Perform self-clearing software reset.  NOT.  Causes CODEC to fail later.  I would probably need a delay after this reset.
	DPxSetCodecReg( 2, 0x22);	// DAC/ADC Fs = Fsref/2.  This is what the DP configures itself to on powerup reset.
	DPxSetCodecReg( 3, 0x20);	// PLL disabled, Q=4 (4 is the minimum value for double-rate DAC mode)

	//  Not using CODEC PLL anymore, so just program with reset values
	DPxSetCodecReg( 4, 0x04);
	DPxSetCodecReg( 5, 0x00);
	DPxSetCodecReg( 6, 0x00);

	// CODEC can hang if it is programmed for dual mode,
	// and we reprogram for non-dual mode without powering down the DACs.
	// For this reason, we are ALWAYS in dual mode!
	DPxSetCodecReg( 7, 0x6A);	// L/R DAC datapaths play left/right channel input data, dual-rate mode. ***If I don't spec dual-rate here, and CODEC is doing dual-rate now, can hang CODEC!
	DPxSetCodecReg( 8, 0x00);	// BCLK and WCLK are inputs (slave mode)
	DPxSetCodecReg( 9, 0x4E);	// Serial bus uses DSP mode with 16-bit L/R data.  x256 BCLK, Resync DAC/ADC if group delay drifts (gives smaller catchup pops).
	DPxSetCodecReg(10, 0x00);	// Serial bus data has 0 BCLK offset from WCLK pulses
	DPxSetCodecReg(11, 0x01);	// PLL R=1
	DPxSetCodecReg(12, 0x00);	// Disable ADC highpass filters, DAC digital effects, DAC de-emphasis filters
	DPxSetCodecReg(14, 0x80);	// Configure high-power outputs for AC-coupled.  Don't know what this does, but headphones are AC coupled.

	// ADC setup
	DPxSetCodecReg(15,   80);	// Left ADC PGA not muted, and gain is 40 dB (good for microphone).
	DPxSetCodecReg(16,   80);	// Right ADC PGA not muted, and gain is also 40 dB.
	DPxSetCodecReg(17, 0xFF);	// MIC3 is not connected to Left ADC
	DPxSetCodecReg(18, 0xFF);	// MIC3 is not connected to Right ADC
	DPxSetCodecReg(19, 0x04);	// Connect LINE1L (MIC) to left ADC, and powerup ADC.
	DPxSetCodecReg(20, 0x78);	// LINE2L (audio line in left) not connected to Left ADC
	DPxSetCodecReg(21, 0x78);	// MIC1R/LINE1R not connected to Left ADC
	DPxSetCodecReg(22, 0x04);	// Connect LINE1R (MIC) to right ADC, and powerup ADC.
	DPxSetCodecReg(23, 0x78);	// LINE2R (audio line in right) not connected to Right ADC
	DPxSetCodecReg(24, 0x78);	// MIC1L/LINE1L not connected to Right ADC
	DPxSetCodecReg(25, 0x40);	// 2.0V MIC bias
	DPxSetCodecReg(26, 0x00);	// No AGC Left.  Online groups say AGC can go into space and never come back...
	DPxSetCodecReg(27, 0x00);	// No AGC Left
	DPxSetCodecReg(28, 0x00);	// No AGC Left
	DPxSetCodecReg(29, 0x00);	// No AGC Right
	DPxSetCodecReg(30, 0x00);	// No AGC Right
	DPxSetCodecReg(31, 0x00);	// No AGC Right
	DPxSetCodecReg(32, 0x00);	// Left AGC gain 0 dB
	DPxSetCodecReg(33, 0x00);	// Right AGC gain 0 dB
	DPxSetCodecReg(34, 0x00);	// Left AGC debounce off
	DPxSetCodecReg(35, 0x00);	// Right AGC debounce off

	//DPxSetCodecReg(36, 0x00);	// A read-only status register
	DPxSetCodecReg(37, 0xE0);	// Powerup L/R DACs, configure HPLCOM as an independant output (goes to DP speaker)
	DPxSetCodecReg(38, 0x1C);	// HPRCOM is differential of HPLCOM (goes to DP speaker), and enable short-circuit protection on HP outputs.
	DPxSetCodecReg(40, 0x80);	// Output common-mode voltage is 1.65V.  Should give greatest swing and power with 3.3V supplies.  Enable some volume soft-stepping to reduce pop when setting volume.
	DPxSetCodecReg(41, 0x00);	// Left/Right DAC outputs routed to DAC_L/R1 paths, and Left/Right DAC channels have independent volume controls.
	DPxSetCodecReg(42, 0x8C);	// 400 ms driver poweron, 4 ms driver rampup step.  Supposed to reduce pop.  I don't see any diff.
	DPxSetCodecReg(43, 0x00);	// Left DAC at full volume
	DPxSetCodecReg(44, 0x00);	// Right DAC at full volume
	DPxSetCodecReg(45, 0x00);	// LINE2L is not routed to HPLOUT
	DPxSetCodecReg(46, 0x00);	// PGA_L is not routed to HPLOUT
	DPxSetCodecReg(47, 0xA8);	// DAC_L1 is routed to HPLOUT at full volume.  NOPE.  Reducing to -8 dB removes a lot of hiss.  -20 dB for safely.
	DPxSetCodecReg(48, 0x00);	// LINE2R is not routed to HPLOUT
	DPxSetCodecReg(49, 0x00);	// PGA_R is not routed to HPLOUT
	DPxSetCodecReg(50, 0x00);	// DAC_R1 is not routed to HPLOUT
	DPxSetCodecReg(51, 0x09);	// HPLOUT is full power, no overdrive
	DPxSetCodecReg(52, 0x00);	// LINE2L is not routed to HPLCOM
	DPxSetCodecReg(53, 0x00);	// PGA_L is not routed to HPLCOM
	DPxSetCodecReg(54, 0x90);	// DAC_L1 is routed to HPLCOM at -8dB.  -6dB is half, but seems to saturate my speaker, peaks cause large oscillations.
	DPxSetCodecReg(55, 0x00);	// LINE2R is not routed to HPLCOM
	DPxSetCodecReg(56, 0x00);	// PGA_R is not routed to HPLCOM
	DPxSetCodecReg(57, 0x90);	// DAC_R1 is routed to HPLCOM at -8dB.  -6dB is half, but seems to saturate my speaker, peaks cause large oscillations.
//	DPxSetCodecReg(58, 0x01);	// Keep HPLCOM powered down until a schedule starts; otherwise FPGA is not driving I2S, and speaker gets a DC voltage and hisses.
	DPxSetCodecReg(58, 0x09);	// Now VHDL drives I2S from reset, so now HPLCOM is full power, no overdrive
	DPxSetCodecReg(59, 0x00);	// LINE2L is not routed to HPROUT
	DPxSetCodecReg(60, 0x00);	// PGA_L is not routed to HPROUT
	DPxSetCodecReg(61, 0x00);	// DAC_L1 is not routed to HPROUT
	DPxSetCodecReg(62, 0x00);	// LINE2R is not routed to HPROUT
	DPxSetCodecReg(63, 0x00);	// PGA_R is not routed to HPROUT
	DPxSetCodecReg(64, 0xA8);	// DAC_R1 is routed to HPROUT at full volume.  NOPE.  Reducing to -8 dB removes a lot of hiss.  -20 dB for safely.
	DPxSetCodecReg(65, 0x09);	// HPROUT is full power, no overdrive
	DPxSetCodecReg(66, 0x00);	// LINE2L is not routed to HPRCOM
	DPxSetCodecReg(67, 0x00);	// PGA_L is not routed to HPRCOM
	DPxSetCodecReg(68, 0x00);	// DAC_L1 is not routed to HPRCOM
	DPxSetCodecReg(69, 0x00);	// LINE2R is not routed to HPRCOM
	DPxSetCodecReg(70, 0x00);	// PGA_R is not routed to HPRCOM
	DPxSetCodecReg(71, 0x80);	// DAC_R1 is not routed to HPRCOM
	DPxSetCodecReg(72, 0x09);	// HPROUT is full power, no overdrive
	DPxSetCodecReg(101, 0x01);	// CODEC_CLKIN comes from CLKDIV_OUT, instead of PLL_OUT
	DPxSetCodecReg(102, 0x02);	// CLKDIV_IN comes from MCLK

	// The CODEC has internal subsystems which can be powered up and down (for power savings in mobile apps).
	// If the internal systems were powered down before the call to DPxInitAudCodec(), then they are now powering up.
	// We will wait here until the systems have fully powered up, so the user is free to start using the CODEC immediately upon return.
	// Measurements show that the DACs power up fast, but the HPLOUT/HPROUT/HPLCOM/HPPRCOM take about 0.6 seconds.
	// Note that this is not much of a concern now, because the CODEC system automatically configures itself,
	// and powers itself up at reset.
	// The only way it could be powered down would be if user did a direct I2C CODEC register write.
	ReturnIfError(DPxUpdateRegCache());
	timer = DPxGetTime();
	for ( ; ; ) {

		// Update timestamp _before_ reading registers,
		// so we know that the CODEC registers were definitely read _after_ the measured delay.
		ReturnIfError(DPxUpdateRegCache());
	
		// Check powerup bits for internal systems.  If all set, we're done.
		if ((DPxGetCodecReg(94) & 0xC6) == 0xC6 && (DPxGetCodecReg(95) & 0x0C) == 0x0C)
			break;

		// If not powered up after 1 second, something's probably wrong.
		if (DPxGetTime() - timer > 1) {
			DPxDebugPrint0("ERROR: DPxInitAudCodec() timeout waiting for CODEC to powerup\n");
			DPxSetError(DPX_ERR_AUD_CODEC_POWERUP);
			break;
		}
	}
}


// Set the 16-bit 2's complement signed value for left audio output channel
void DPxSetAudLeftValue(int value)
{
	if (value < -32768 || value > 32767) {	// Restrict to SInt16 range
		DPxDebugPrint1("ERROR: DPxSetAudLeftValue() argument value %d is out of signed 16-bit range\n", value);
		DPxSetError(DPX_ERR_AUD_SET_BAD_VALUE);
		return;
	}
	DPxSetReg16(DPXREG_AUD_DATA_LEFT , value);
}


// Set the 16-bit 2's complement signed value for right audio output channel
void DPxSetAudRightValue(int value)
{
	if (value < -32768 || value > 32767) {	// Restrict to SInt16 range
		DPxDebugPrint1("ERROR: DPxSetAudRightValue() argument value %d is out of signed 16-bit range\n", value);
		DPxSetError(DPX_ERR_AUD_SET_BAD_VALUE);
		return;
	}
	DPxSetReg16(DPXREG_AUD_DATA_RIGHT , value);
}


// Get the 16-bit 2's complement signed value for left audio output channel
int DPxGetAudLeftValue()
{
	return (SInt16)DPxGetReg16(DPXREG_AUD_DATA_LEFT);
}


// Get the 16-bit 2's complement signed value for right audio output channel
int DPxGetAudRightValue()
{
	return (SInt16)DPxGetReg16(DPXREG_AUD_DATA_RIGHT);
}


// Set volume for Left audio channel
void DPxSetAudLeftVolume(double volume)
{
	int iVolume;

	// Check for out-of-range values, and set resulting error state;
	// but still continue to set the clipped volume.
	if (volume < 0) {
		DPxDebugPrint1("ERROR: DPxSetAudLeftVolume() argument volume %g is under range 0 to 1\n", volume);
		DPxSetError(DPX_ERR_AUD_SET_BAD_VOLUME);
		volume = 0;
	}
	else if (volume > 1) {
		DPxDebugPrint1("ERROR: DPxSetAudLeftVolume() argument volume %g is over range 0 to 1\n", volume);
		DPxSetError(DPX_ERR_AUD_SET_BAD_VOLUME);
		volume = 1;
	}

	// round to the closest possible integer volume
	iVolume = (int)(volume * 65536 + 0.5);
	if (iVolume < 65536) {
		DPxSetReg16(DPXREG_AUD_CTRL, DPxGetReg16(DPXREG_AUD_CTRL) & ~DPXREG_AUD_CTRL_MAXVOL_LEFT);	// Enables volume control
		DPxSetReg16(DPXREG_AUD_VOLUME_LEFT , iVolume);
	}
	else {
		DPxSetReg16(DPXREG_AUD_CTRL, DPxGetReg16(DPXREG_AUD_CTRL) | DPXREG_AUD_CTRL_MAXVOL_LEFT);	// Forces maximum volume
		DPxSetReg16(DPXREG_AUD_VOLUME_LEFT , 65535);
	}
}


// Get volume for the Left audio output channel
double DPxGetAudLeftVolume()
{
	return DPxGetReg16(DPXREG_AUD_CTRL) & DPXREG_AUD_CTRL_MAXVOL_LEFT ? 1.0 : DPxGetReg16(DPXREG_AUD_VOLUME_LEFT) / 65536.0;
}


// Set volume for Right audio channel
void DPxSetAudRightVolume(double volume)
{
	int iVolume;

	// Check for out-of-range values, and set resulting error state;
	// but still continue to set the clipped volume.
	if (volume < 0) {
		DPxDebugPrint1("ERROR: DPxSetAudRightVolume() argument volume %g is under range 0 to 1\n", volume);
		DPxSetError(DPX_ERR_AUD_SET_BAD_VOLUME);
		volume = 0;
	}
	else if (volume > 1) {
		DPxDebugPrint1("ERROR: DPxSetAudRightVolume() argument volume %g is over range 0 to 1\n", volume);
		DPxSetError(DPX_ERR_AUD_SET_BAD_VOLUME);
		volume = 1;
	}

	// round to the closest possible integer volume
	iVolume = (int)(volume * 65536 + 0.5);
	if (iVolume < 65536) {
		DPxSetReg16(DPXREG_AUD_CTRL, DPxGetReg16(DPXREG_AUD_CTRL) & ~DPXREG_AUD_CTRL_MAXVOL_RIGHT);	// Enables volume control
		DPxSetReg16(DPXREG_AUD_VOLUME_RIGHT , iVolume);
	}
	else {
		DPxSetReg16(DPXREG_AUD_CTRL, DPxGetReg16(DPXREG_AUD_CTRL) | DPXREG_AUD_CTRL_MAXVOL_RIGHT);	// Forces maximum volume
		DPxSetReg16(DPXREG_AUD_VOLUME_RIGHT , 65535);
	}
}


// Get volume for the Right audio output channel
double DPxGetAudRightVolume()
{
	return DPxGetReg16(DPXREG_AUD_CTRL) & DPXREG_AUD_CTRL_MAXVOL_RIGHT ? 1.0 : DPxGetReg16(DPXREG_AUD_VOLUME_RIGHT) / 65536.0;
}


// Set volume for both Left/Right audio channels
void DPxSetAudVolume(double volume)
{
	DPxSetAudLeftVolume(volume);
	DPxSetAudRightVolume(volume);
}


// Get volume for both Left/Right audio channels (or Left channel, if Left/Right are different)
double DPxGetAudVolume()
{
	return DPxGetReg16(DPXREG_AUD_CTRL) & DPXREG_AUD_CTRL_MAXVOL_LEFT ? 1.0 : DPxGetReg16(DPXREG_AUD_VOLUME_LEFT) / 65536.0;
}


int DPxAudCodecVolumeToReg(double volume, int dBUnits)
{
	// Convert volume from ratio to dB
	if (!dBUnits)
		volume = 20 * log10(volume);

	// Return closest corresponding register value
	if (volume >= 0) return 0x80;
	if (volume <= -63.5) return 0xFF;
	return 0x80 + (int)floor(-2 * volume + 0.5);
}


double DPxAudCodecRegToVolume(int reg, int dBUnits)
{
	// Get the volume in dB
	double volumedB = (reg & 0x7F) / -2.0;
	return dBUnits ? volumedB : pow(10, volumedB / 20);
}


// Set volume for the DATAPixx Audio OUT Left channel, range 0-1
void DPxSetAudCodecOutLeftVolume(double volume, int dBUnits)
{
	DPxSetCodecReg(47, DPxAudCodecVolumeToReg(volume, dBUnits));
}


// Get volume for the DATAPixx Audio OUT Left channel, range 0-1
double DPxGetAudCodecOutLeftVolume(int dBUnits)
{
	return DPxAudCodecRegToVolume(DPxGetCodecReg(47), dBUnits);
}


// Set volume for the DATAPixx Audio OUT Right channel, range 0-1
void DPxSetAudCodecOutRightVolume(double volume, int dBUnits)
{
	DPxSetCodecReg(64, DPxAudCodecVolumeToReg(volume, dBUnits));
}


// Get volume for the DATAPixx Audio OUT Right channel, range 0-1
double DPxGetAudCodecOutRightVolume(int dBUnits)
{
	return DPxAudCodecRegToVolume(DPxGetCodecReg(64), dBUnits);
}


// Set volume for the DATAPixx Audio OUT Left and Right channels, range 0-1
void DPxSetAudCodecOutVolume(double volume, int dBUnits)
{
	DPxSetAudCodecOutLeftVolume(volume, dBUnits);
	DPxSetAudCodecOutRightVolume(volume, dBUnits);
}


// Get volume for the DATAPixx Audio OUT Left and Right channels (or Left channel, if Left/Right are different)
double DPxGetAudCodecOutVolume(int dBUnits)
{
	return DPxGetAudCodecOutLeftVolume(dBUnits);
}


// Set volume for the DATAPixx Speaker Left channel, range 0-1
void DPxSetAudCodecSpeakerLeftVolume(double volume, int dBUnits)
{
	DPxSetCodecReg(54, DPxAudCodecVolumeToReg(volume, dBUnits));
}


// Get volume for the DATAPixx Speaker Left channel, range 0-1
double DPxGetAudCodecSpeakerLeftVolume(int dBUnits)
{
	return DPxAudCodecRegToVolume(DPxGetCodecReg(54), dBUnits);
}


// Set volume for the DATAPixx Speaker Right channel, range 0-1
void DPxSetAudCodecSpeakerRightVolume(double volume, int dBUnits)
{
	DPxSetCodecReg(57, DPxAudCodecVolumeToReg(volume, dBUnits));
}


// Get volume for the DATAPixx Speaker Right channel, range 0-1
double DPxGetAudCodecSpeakerRightVolume(int dBUnits)
{
	return DPxAudCodecRegToVolume(DPxGetCodecReg(57), dBUnits);
}


// Set volume for the DATAPixx Speaker Left and Right channels, range 0-1
void DPxSetAudCodecSpeakerVolume(double volume, int dBUnits)
{
	DPxSetAudCodecSpeakerLeftVolume(volume, dBUnits);
	DPxSetAudCodecSpeakerRightVolume(volume, dBUnits);
}


// Get volume for the DATAPixx Speaker Left and Right channels (or Left channel, if Left/Right are different)
double DPxGetAudCodecSpeakerVolume(int dBUnits)
{
	return DPxGetAudCodecSpeakerLeftVolume(dBUnits);
}


// Configure how audio Left/Right channels are updated by schedule data
// lrMode is one of the following predefined constants:
//		DPXREG_AUD_CTRL_LRMODE_MONO		: Each AUD schedule datum goes to left and right channels
//		DPXREG_AUD_CTRL_LRMODE_LEFT		: Each AUD schedule datum goes to left channel only
//		DPXREG_AUD_CTRL_LRMODE_RIGHT	: Each AUD schedule datum goes to right channel only
//		DPXREG_AUD_CTRL_LRMODE_STEREO_1	: Pairs of AUD data are copied to left/right channels
//		DPXREG_AUD_CTRL_LRMODE_STEREO_2	: AUD data goes to left channel, AUX data goes to right
void DPxSetAudLRMode(int lrMode)
{
	switch (lrMode) {
		case DPXREG_AUD_CTRL_LRMODE_MONO:
		case DPXREG_AUD_CTRL_LRMODE_LEFT:
		case DPXREG_AUD_CTRL_LRMODE_RIGHT:
		case DPXREG_AUD_CTRL_LRMODE_STEREO_1:
		case DPXREG_AUD_CTRL_LRMODE_STEREO_2:
			DPxSetReg16(DPXREG_AUD_CTRL, (DPxGetReg16(DPXREG_AUD_CTRL) & ~DPXREG_AUD_CTRL_LRMODE_MASK) | lrMode);
			break;

		default:
			DPxDebugPrint1("ERROR: DPxSetAudLRMode() unrecognized lrMode %d\n", lrMode);
			DPxSetError(DPX_ERR_AUD_SET_BAD_LRMODE);
	}
}


int DPxGetAudLRMode()
{
	return DPxGetReg16(DPXREG_AUD_CTRL) & DPXREG_AUD_CTRL_LRMODE_MASK;
}


// Set AUD RAM buffer base address.  Must be an even value.
void DPxSetAudBuffBaseAddr(unsigned buffBaseAddr)
{
	if (buffBaseAddr & 1) {
		DPxDebugPrint1("ERROR: DPxSetAudBuffBaseAddr(0x%x) illegal odd address\n", buffBaseAddr);
		DPxSetError(DPX_ERR_AUD_BUFF_ODD_BASEADDR);
		return;
	}
	if (buffBaseAddr >= DPxGetRamSize()) {
		DPxDebugPrint1("ERROR: DPxSetAudBuffBaseAddr(0x%x) exceeds DATAPixx RAM\n", buffBaseAddr);
		DPxSetError(DPX_ERR_AUD_BUFF_BASEADDR_TOO_HIGH);
		return;
	}
	DPxSetReg32(DPXREG_AUD_BUFF_BASEADDR_L, buffBaseAddr);
}


// Get AUD RAM buffer base address
unsigned DPxGetAudBuffBaseAddr()
{
	return DPxGetReg32(DPXREG_AUD_BUFF_BASEADDR_L);
}


// Set RAM address from which next AUD datum will be read.  Must be an even value.
void DPxSetAudBuffReadAddr(unsigned buffReadAddr)
{
	if (buffReadAddr & 1) {
		DPxDebugPrint1("ERROR: DPxSetAudBuffReadAddr(0x%x) illegal odd address\n", buffReadAddr);
		DPxSetError(DPX_ERR_AUD_BUFF_ODD_READADDR);
		return;
	}
	if (buffReadAddr >= DPxGetRamSize()) {
		DPxDebugPrint1("ERROR: DPxSetAudBuffReadAddr(0x%x) exceeds DATAPixx RAM\n", buffReadAddr);
		DPxSetError(DPX_ERR_AUD_BUFF_READADDR_TOO_HIGH);
		return;
	}
	DPxSetReg32(DPXREG_AUD_BUFF_READADDR_L, buffReadAddr);
}


// Get RAM address from which next AUD datum will be read
unsigned DPxGetAudBuffReadAddr()
{
	return DPxGetReg32(DPXREG_AUD_BUFF_READADDR_L);
}


// Set AUD RAM buffer size in bytes.  Must be an even value.
// The hardware will automatically wrap the BuffReadAddr, when it gets to BuffBaseAddr+BuffSize, back to BuffBaseAddr.
// This simplifies spooled playback, or the continuous playback of periodic waveforms.
void DPxSetAudBuffSize(unsigned buffSize)
{
	if (buffSize & 1) {
		DPxDebugPrint1("ERROR: DPxSetAudBuffSize(0x%x) illegal odd size\n", buffSize);
		DPxSetError(DPX_ERR_AUD_BUFF_ODD_SIZE);
		return;
	}
	if (buffSize > DPxGetRamSize()) {
		DPxDebugPrint1("ERROR: DPxSetAudBuffSize(0x%x) exceeds DATAPixx RAM\n", buffSize);
		DPxSetError(DPX_ERR_AUD_BUFF_TOO_BIG);
		return;
	}
	DPxSetReg32(DPXREG_AUD_BUFF_SIZE_L, buffSize);
}


// Get AUD RAM buffer size in bytes
unsigned DPxGetAudBuffSize()
{
	return DPxGetReg32(DPXREG_AUD_BUFF_SIZE_L);
}


// Shortcut which assigns Size/BaseAddr/ReadAddr
void DPxSetAudBuff(unsigned buffAddr, unsigned buffSize)
{
	DPxSetAudBuffBaseAddr(buffAddr);
	DPxSetAudBuffReadAddr(buffAddr);
	DPxSetAudBuffSize(buffSize);
}


// Set AUX RAM buffer base address.  Must be an even value.
void DPxSetAuxBuffBaseAddr(unsigned buffBaseAddr)
{
	if (buffBaseAddr & 1) {
		DPxDebugPrint1("ERROR: DPxSetAuxBuffBaseAddr(0x%x) illegal odd address\n", buffBaseAddr);
		DPxSetError(DPX_ERR_AUX_BUFF_ODD_BASEADDR);
		return;
	}
	if (buffBaseAddr >= DPxGetRamSize()) {
		DPxDebugPrint1("ERROR: DPxSetAuxBuffBaseAddr(0x%x) exceeds DATAPixx RAM\n", buffBaseAddr);
		DPxSetError(DPX_ERR_AUX_BUFF_BASEADDR_TOO_HIGH);
		return;
	}
	DPxSetReg32(DPXREG_AUX_BUFF_BASEADDR_L, buffBaseAddr);
}


// Get AUX RAM buffer base address
unsigned DPxGetAuxBuffBaseAddr()
{
	return DPxGetReg32(DPXREG_AUX_BUFF_BASEADDR_L);
}


// Set RAM address from which next AUX datum will be read.  Must be an even value.
void DPxSetAuxBuffReadAddr(unsigned buffReadAddr)
{
	if (buffReadAddr & 1) {
		DPxDebugPrint1("ERROR: DPxSetAuxBuffReadAddr(0x%x) illegal odd address\n", buffReadAddr);
		DPxSetError(DPX_ERR_AUX_BUFF_ODD_READADDR);
		return;
	}
	if (buffReadAddr >= DPxGetRamSize()) {
		DPxDebugPrint1("ERROR: DPxSetAuxBuffReadAddr(0x%x) exceeds DATAPixx RAM\n", buffReadAddr);
		DPxSetError(DPX_ERR_AUX_BUFF_READADDR_TOO_HIGH);
		return;
	}
	DPxSetReg32(DPXREG_AUX_BUFF_READADDR_L, buffReadAddr);
}


// Get RAM address from which next AUX datum will be read
unsigned DPxGetAuxBuffReadAddr()
{
	return DPxGetReg32(DPXREG_AUX_BUFF_READADDR_L);
}


// Set AUX RAM buffer size in bytes.  Must be an even value.
// The hardware will automatically wrap the BuffReadAddr, when it gets to BuffBaseAddr+BuffSize, back to BuffBaseAddr.
// This simplifies spooled playback, or the continuous playback of periodic waveforms.
void DPxSetAuxBuffSize(unsigned buffSize)
{
	if (buffSize & 1) {
		DPxDebugPrint1("ERROR: DPxSetAuxBuffSize(0x%x) illegal odd size\n", buffSize);
		DPxSetError(DPX_ERR_AUX_BUFF_ODD_SIZE);
		return;
	}
	if (buffSize > DPxGetRamSize()) {
		DPxDebugPrint1("ERROR: DPxSetAuxBuffSize(0x%x) exceeds DATAPixx RAM\n", buffSize);
		DPxSetError(DPX_ERR_AUX_BUFF_TOO_BIG);
		return;
	}
	DPxSetReg32(DPXREG_AUX_BUFF_SIZE_L, buffSize);
}


// Get AUX RAM buffer size in bytes
unsigned DPxGetAuxBuffSize()
{
	return DPxGetReg32(DPXREG_AUX_BUFF_SIZE_L);
}


// Shortcut which assigns Size/BaseAddr/ReadAddr
void DPxSetAuxBuff(unsigned buffAddr, unsigned buffSize)
{
	DPxSetAuxBuffBaseAddr(buffAddr);
	DPxSetAuxBuffReadAddr(buffAddr);
	DPxSetAuxBuffSize(buffSize);
}


// Set nanosecond delay between schedule start and first AUD update
void DPxSetAudSchedOnset(unsigned onset)
{
	DPxSetReg32(DPXREG_AUD_SCHED_ONSET_L, onset);
}


// Get nanosecond delay between schedule start and first AUD update
unsigned DPxGetAudSchedOnset()
{
	return DPxGetReg32(DPXREG_AUD_SCHED_ONSET_L);
}


// Set AUD schedule update rate.  Range is 8-96 kHz.
// We'll limit maximum frequency to 96 kHz for 3 reasons:
// 1) This is the maximum spec'd frequency of the CODEC.
// 2) CODEC BCLK min high/low time specs are 35 ns, so I need 8 CLK100 = 12.5 MHz BCLK / 128 = 97.7 kHz max.
// 3) CODEC MCLK is spec'd for 50 MHz, but I get CODEC noise if I run in n=1.5 with MCLK > 25 MHz.
// rateUnits is one of the following predefined constants:
//		DPXREG_SCHED_CTRL_RATE_HZ		: rateValue is samples per second, maximum 96 kHz
//		DPXREG_SCHED_CTRL_RATE_XVID		: rateValue is samples per video frame, maximum 96 kHz
//		DPXREG_SCHED_CTRL_RATE_NANO		: rateValue is sample period in nanoseconds, minimum 10417 ns
void DPxSetAudSchedRate(unsigned rateValue, int rateUnits)
{
	int multMClk, pllDual;
	int regDivisor;
	//regPllDual;
	int modifyingDivisor;
	int savedReg19, savedReg22, savedReg37;
	double freq, divisor;

	switch (rateUnits) {
		case DPXREG_SCHED_CTRL_RATE_HZ:		freq = rateValue;						break;
		case DPXREG_SCHED_CTRL_RATE_XVID:	freq = rateValue * DPxGetVidVFreq();	break;
		case DPXREG_SCHED_CTRL_RATE_NANO:	freq = 1.0e9 / rateValue;				break;
		default:
			DPxDebugPrint1("ERROR: DPxSetAudSchedRate() unrecognized rateUnits %d\n", rateUnits);
			DPxSetError(DPX_ERR_AUD_SCHED_BAD_RATE_UNITS);
			return;
	}

	if (freq < 8000) {		// Min frequency supported by CODEC
		DPxDebugPrint1("ERROR: DPxSetAudSchedRate() frequency too low %g\n", freq);
		DPxSetError(DPX_ERR_AUD_SCHED_TOO_SLOW);
		return;
	}
	if (freq > 96000) {	// Max frequency supported by CODEC.  Also, 25 MHz MCLK / 256 = 97.7 kHz.
		DPxDebugPrint1("ERROR: DPxSetAudSchedRate() frequency too high %g\n", freq);
		DPxSetError(DPX_ERR_AUD_SCHED_TOO_FAST);
		return;
	}

	// If given the choice, we would like to generate all frequencies in double-rate mode.
	// This gives better interpolation of waveforms, pushing noise into higher frequencies.
	// CODEC datasheet says that Fsref should be within the range 39-53 kHz,
	// so the lowest frequency we can make in double-rate is 39 kHz * 2(for double-rate) / 6.
	// Actually, we'll just always force double-rate.
	// Otherwise CODEC can hang up when switching from non-double-rate to double-rate.
	// Empirical tests show that we can run CODEC with 8 kHz audio samples = 24 kHz Fsref w/o distortion.
//	if (freq >= 39000.0 / 3)	// 13000 Hz
		pllDual = 1;
//	else
//		pllDual = 0;

	// Scan through the 11 divisors from largest to smallest, looking for the first range which can generate the desired freq.
	// We want the largest possible divisor, because this will result in the smoothest interpolation between sample values.
	// The frequency ranges attainable for the different /n almost all overlap, except for 2 small holes at the top.
	// We fill these holes by allowing the Fsref min to go below 39 kHz.
	// The worst case is for frequencies just above 65104 Hz, which need an Fsref of 32552 Hz.
	// I think it's best to _reduce_ Fsref below its spec'd frequency, rather than increasing it.
	// I was getting some bad noise out of CODEC for MCLK's which exceeded 25 MHz.
	for (divisor = 6; divisor > 1; divisor -= 0.5)
		if (freq <= 25.0e6 / (pllDual ? 256 : 512) / divisor)
			break;

	// Ratio between CODEC MCLK frequency, and WCLK frequency.  Remember minimum Q is 4 in dual, so we always use Q = 4.
	multMClk = (int)((pllDual ? 256 : 512) * divisor);

	// TLV320AIC32 register values
//	regPllDual = (pllDual << 6) | (pllDual << 5) | 0x0A;					// Sets dual bits, and enables left/right DAC datapaths
	regDivisor = (int)(divisor * 2 - 2) | ((int)(divisor * 2 - 2) << 4);	// DAC and ADC get same divisor

	// Here's the thing.  It appears that the CODEC output can hang if we update timing registers while DACs are powered up.
	// I especially see this when going from non-double-rate to double-rate mode, but I also see this when only programming divisor.
	// When the CODEC hangs, it seems to never generate audio out until it has been reprogrammed back to non-double-rate mode.
	// It seems that I can prevent this from happening by powering down the DACs while reprogramming the rate or divisor.
	// ADC's also need to be powered down, or audio input and output can both get screwed up.
	savedReg19 = cachedCodecRegs[19];
	savedReg22 = cachedCodecRegs[22];
	savedReg37 = cachedCodecRegs[37];
	modifyingDivisor = (regDivisor != cachedCodecRegs[2]);
	if (modifyingDivisor) {
		DPxSetCodecReg(19, 0x78);	// Powerdown Left ADC
		DPxSetCodecReg(22, 0x78);	// Powerdown Right ADC
		DPxSetCodecReg(37, 0x20);	// Powerdown L/R DACs, configure HPLCOM as an independant output (goes to DP speaker)

		// Hmmm.  CODEC doesn't always power down when we tell it to.  Maybe when we've stopped MCLK?
		// The final solution is just to stay in double-rate mode.  It can present 8 kHz audio samples w/o distortion.
		// Also, user might program this rate during an animation.  We don't want to be hanging here.
		// ...Unfortunately, it started hanging again with VHDL rev 7.
		// Now I'm putting back this wait, and it doesn't seem to hang anymore.
		// I've counted that it takes anywhere from 3 to 21 reads of register 94 before it says IC has powered down.
		// Note that we only stay here when the user is actually _changing_ the frequency,
		// so the user can still call this function a million times during an animation,
		// and we'll only pause here if we're really changing the rate.
		// After long-run tests, the CODEC seems rock solid now that I've enabled this wait.
		// Never seems to stop producing sound.
		while ((DPxGetCodecReg(94) & 0xC0) != 0x00)
			(void)0;
	}

	// AUD channel scheduler holds frequency, and multiplier to get us up to MCLK frequency.
	DPxSetReg32(DPXREG_AUD_SCHED_CTRL_L, (DPxGetReg32(DPXREG_AUD_SCHED_CTRL_L) & ~DPXREG_SCHED_CTRL_RATE_MASK) | rateUnits);
	DPxSetReg32(DPXREG_AUD_SCHED_RATE_L,  rateValue);
	DPxSetReg16(DPXREG_AUD_CTRL, (DPxGetReg16(DPXREG_AUD_CTRL) & ~DPXREG_AUD_CTRL_BCLK_RATIO) | (multMClk >> 7));

	// AUX channel rate is tied to AUD rate.  They are supplying simultaneous L/R data to a single audio CODEC, so their rates can't be different.
	DPxSetReg32(DPXREG_AUX_SCHED_CTRL_L, (DPxGetReg32(DPXREG_AUX_SCHED_CTRL_L) & ~DPXREG_SCHED_CTRL_RATE_MASK) | rateUnits);
	DPxSetReg32(DPXREG_AUX_SCHED_RATE_L,  rateValue);

//	DPxSetCodecReg( 4, regPllJ);		// We're no longer using CODEC PLL.
//	DPxSetCodecReg( 5, regPllDH);
//	DPxSetCodecReg( 6, regPllDL);
//	DPxSetCodecReg( 7, regPllDual);		// Always keeps the 0x6A from init

	if (modifyingDivisor) {
		DPxSetCodecReg( 2, regDivisor);
		DPxSetCodecReg(19, savedReg19);	// Probably powering up Left ADC
		DPxSetCodecReg(22, savedReg22);	// Probably powering up Right ADC
		DPxSetCodecReg(37, savedReg37);	// Probably powering up L/R DACs

		// Wait until the 2 DACs are fully powered up before allowing user to start audio playback.
		// We don't have a timeout here, because we don't want to call DPxUpdateRegCache() for the user.
		// There doesn't seem to be an equivalent register to confirm ADC powerup.
		while ((DPxGetCodecReg(94) & 0xC0) != 0xC0)
			(void)0;
	}
}


// Get AUD schedule update rate (and optionally get rate units)
unsigned DPxGetAudSchedRate(int *rateUnits)
{
	if (rateUnits)
		*rateUnits = DPxGetReg32(DPXREG_AUD_SCHED_CTRL_L) & DPXREG_SCHED_CTRL_RATE_MASK;
	return DPxGetReg32(DPXREG_AUD_SCHED_RATE_L);
}


// Set AUD schedule update count
void DPxSetAudSchedCount(unsigned count)
{
	DPxSetReg32(DPXREG_AUD_SCHED_COUNT_L,  count);
}


// Get AUD schedule update count
unsigned DPxGetAudSchedCount()
{
	return DPxGetReg32(DPXREG_AUD_SCHED_COUNT_L);
}


// SchedCount decrements at SchedRate, and schedule stops automatically when count hits 0
void DPxEnableAudSchedCountdown()
{
	DPxSetReg32(DPXREG_AUD_SCHED_CTRL_L, DPxGetReg32(DPXREG_AUD_SCHED_CTRL_L) | DPXREG_SCHED_CTRL_COUNTDOWN);
}


// SchedCount increments at SchedRate, and schedule is stopped by calling SchedStop
void DPxDisableAudSchedCountdown()
{
	DPxSetReg32(DPXREG_AUD_SCHED_CTRL_L, DPxGetReg32(DPXREG_AUD_SCHED_CTRL_L) & ~DPXREG_SCHED_CTRL_COUNTDOWN);
}


// Returns non-0 if SchedCount decrements to 0 and automatically stops schedule
int DPxIsAudSchedCountdown()
{
	return DPxGetReg32(DPXREG_AUD_SCHED_CTRL_L) & DPXREG_SCHED_CTRL_COUNTDOWN;
}


// Shortcut which assigns Onset/Rate/Count.
// If Count > 0, enables Countdown mode.
void DPxSetAudSched(unsigned onset, unsigned rateValue, int rateUnits, unsigned count)
{
	DPxSetAudSchedOnset(onset);
	DPxSetAudSchedRate(rateValue, rateUnits);
	DPxSetAudSchedCount(count);
	if (count)
		DPxEnableAudSchedCountdown();
	else
		DPxDisableAudSchedCountdown();
}


// Start running an AUD schedule
void DPxStartAudSched()
{
	DPxSetReg16(DPXREG_SCHED_STARTSTOP, (DPxGetReg16(DPXREG_SCHED_STARTSTOP) & ~(DPXREG_SCHED_STARTSTOP_MASK << DPXREG_SCHED_STARTSTOP_SHIFT_AUD)) |
										(DPXREG_SCHED_STARTSTOP_START << DPXREG_SCHED_STARTSTOP_SHIFT_AUD));
}


// Stop running an AUD schedule
void DPxStopAudSched()
{
	DPxSetReg16(DPXREG_SCHED_STARTSTOP, (DPxGetReg16(DPXREG_SCHED_STARTSTOP) & ~(DPXREG_SCHED_STARTSTOP_MASK << DPXREG_SCHED_STARTSTOP_SHIFT_AUD)) |
										(DPXREG_SCHED_STARTSTOP_STOP << DPXREG_SCHED_STARTSTOP_SHIFT_AUD));
}


// Returns non-0 if AUD schedule is currently running
int DPxIsAudSchedRunning()
{
	return DPxGetReg32(DPXREG_AUD_SCHED_CTRL_L) & DPXREG_SCHED_CTRL_RUNNING;
}


// Set nanosecond delay between schedule start and first AUX update
void DPxSetAuxSchedOnset(unsigned onset)
{
	DPxSetReg32(DPXREG_AUX_SCHED_ONSET_L, onset);
}


// Get nanosecond delay between schedule start and first AUX update
unsigned DPxGetAuxSchedOnset()
{
	return DPxGetReg32(DPXREG_AUX_SCHED_ONSET_L);
}


// Set AUX (and AUD) schedule update rate.  Range is 8-96 kHz.
void DPxSetAuxSchedRate(unsigned rateValue, int rateUnits)
{
	DPxSetAudSchedRate(rateValue, rateUnits);	// Will assign same rate for both AUD and AUX
}


// Get AUX schedule update rate (and optionally get rate units)
unsigned DPxGetAuxSchedRate(int *rateUnits)
{
	if (rateUnits)
		*rateUnits = DPxGetReg32(DPXREG_AUX_SCHED_CTRL_L) & DPXREG_SCHED_CTRL_RATE_MASK;
	return DPxGetReg32(DPXREG_AUX_SCHED_RATE_L);
}


// Set AUX schedule update count
void DPxSetAuxSchedCount(unsigned count)
{
	DPxSetReg32(DPXREG_AUX_SCHED_COUNT_L,  count);
}


// Get AUX schedule update count
unsigned DPxGetAuxSchedCount()
{
	return DPxGetReg32(DPXREG_AUX_SCHED_COUNT_L);
}


// SchedCount decrements at SchedRate, and schedule stops automatically when count hits 0
void DPxEnableAuxSchedCountdown()
{
	DPxSetReg32(DPXREG_AUX_SCHED_CTRL_L, DPxGetReg32(DPXREG_AUX_SCHED_CTRL_L) | DPXREG_SCHED_CTRL_COUNTDOWN);
}


// SchedCount increments at SchedRate, and schedule is stopped by calling SchedStop
void DPxDisableAuxSchedCountdown()
{
	DPxSetReg32(DPXREG_AUX_SCHED_CTRL_L, DPxGetReg32(DPXREG_AUX_SCHED_CTRL_L) & ~DPXREG_SCHED_CTRL_COUNTDOWN);
}


// Returns non-0 if SchedCount decrements to 0 and automatically stops schedule
int DPxIsAuxSchedCountdown()
{
	return DPxGetReg32(DPXREG_AUX_SCHED_CTRL_L) & DPXREG_SCHED_CTRL_COUNTDOWN;
}


// Shortcut which assigns Onset/Count.
// If Count > 0, enables Countdown mode.
void DPxSetAuxSched(unsigned onset, unsigned rateValue, int rateUnits, unsigned count)
{
	DPxSetAuxSchedOnset(onset);
	DPxSetAuxSchedRate(rateValue, rateUnits);
	DPxSetAuxSchedCount(count);
	if (count)
		DPxEnableAuxSchedCountdown();
	else
		DPxDisableAuxSchedCountdown();
}


// Start running a AUX schedule
void DPxStartAuxSched()
{
	DPxSetReg16(DPXREG_SCHED_STARTSTOP, (DPxGetReg16(DPXREG_SCHED_STARTSTOP) & ~(DPXREG_SCHED_STARTSTOP_MASK << DPXREG_SCHED_STARTSTOP_SHIFT_AUX)) |
										(DPXREG_SCHED_STARTSTOP_START << DPXREG_SCHED_STARTSTOP_SHIFT_AUX));
	DPxSetCodecReg(58, 0x09);	// To prevent hiss, HPLCOM is powered down after Init().  Make sure it's on now.
}


// Stop running a AUX schedule
void DPxStopAuxSched()
{
	DPxSetReg16(DPXREG_SCHED_STARTSTOP, (DPxGetReg16(DPXREG_SCHED_STARTSTOP) & ~(DPXREG_SCHED_STARTSTOP_MASK << DPXREG_SCHED_STARTSTOP_SHIFT_AUX)) |
										(DPXREG_SCHED_STARTSTOP_STOP << DPXREG_SCHED_STARTSTOP_SHIFT_AUX));
}


// Returns non-0 if AUX schedule is currently running
int DPxIsAuxSchedRunning()
{
	return DPxGetReg32(DPXREG_AUX_SCHED_CTRL_L) & DPXREG_SCHED_CTRL_RUNNING;
}


// Returns CODEC Audio OUT group delay in seconds.
// This is the time between when a schedule sends a data sample to the CODEC,
// and when that sample has greatest output at the "Audio OUT" jack of the Datapixx.
// Due to the way in which CODECs operate, this delay is a function of the sample rate (eg: 48000).
// Note that my empirical data shows a slope of 23.665, not 21.665.
// That's because my test waveform started with 2 samples of "0" data.
double DPxGetAudGroupDelay(double sampleRate)
{
	return 21.665 / sampleRate + 7.86e-6;
}


/********************************************************************************/
/*																				*/
/*	MIC Subsystem																*/
/*																				*/
/********************************************************************************/


// Select the source of the microphone input.
// source is one of the following predefined constants:
//		DPX_MIC_SRC_MIC_IN	: Microphone level input
//		DPX_MIC_SRC_LINE_IN	: Line level audio input.
// Valid gain values are 1-1000, or 0-60 dB.
// Typical gain values would be around 100 for a microphone input,
// and probably 1 for line-level input.
void DPxSetMicSource(int source, double gain, int dBUnits)
{
	double gainDb, gainReg;

	// Convert gain to dB
	gainDb = dBUnits ? gain : 20 * log10(gain);

	// Convert gain to a valid register value
	gainReg = floor(gainDb * 2 + 0.5);
	if (gainReg < 0) {
		DPxDebugPrint1("ERROR: DPxSetMicSource() gain of %g is too low\n", gain);
		DPxSetError(DPX_ERR_MIC_SET_GAIN_TOO_LOW);
		return;
	}
	if (gainReg > 120) {	// 60 dB
		DPxDebugPrint1("ERROR: DPxSetMicSource() gain of %g is too high\n", gain);
		DPxSetError(DPX_ERR_MIC_SET_GAIN_TOO_HIGH);
		return;
	}

	// Select the requested source
	if (source == DPX_MIC_SRC_MIC_IN) {
		DPxSetCodecReg(19, 0x04);	// MIC1L connected to left ADC with no attenuation, and powerup ADC.
		DPxSetCodecReg(20, 0x78);	// LINE2L not connected to Left ADC
		DPxSetCodecReg(22, 0x04);	// MIC1R connected to right ADC with no attenuation, and powerup ADC.
		DPxSetCodecReg(23, 0x78);	// LINE2R not connected to Right ADC
	}
	else if (source == DPX_MIC_SRC_LINE_IN) {
		DPxSetCodecReg(19, 0x7C);	// MIC1L not connected to left ADC, and powerup ADC.
		DPxSetCodecReg(20, 0x00);	// LINE2L connected to Left ADC with no attenuation
		DPxSetCodecReg(22, 0x7C);	// MIC1R not connected to right ADC, and powerup ADC.
		DPxSetCodecReg(23, 0x00);	// LINE2R connected to Right ADC with no attenuation
	}
	else {
		DPxDebugPrint1("ERROR: DPxSetMicSource() %d is not a valid audio input source\n", source);
		DPxSetError(DPX_ERR_MIC_SET_BAD_SOURCE);
		return;
	}

	// Implement gain (only if source was valid).
	// For now, we use the same gain for both left/right channels.
	DPxSetCodecReg(15, (int)gainReg);	// Left ADC PGA gain setting
	DPxSetCodecReg(16, (int)gainReg);	// Right ADC PGA gain setting
}


// Get the source of the microphone input, and optionally return the source's gain.
// Set dBUnits to non-zero to return the gain in dB.
int DPxGetMicSource(double *gain, int dBUnits)
{
	double gainDb;

	// Get the gain.  Only need to read the left channel.
	if (gain) {
		gainDb = (DPxGetCodecReg(15) & 0x7F) / 2.0;
		*gain = dBUnits ? gainDb : pow(10, gainDb / 20);
	}

	// Return the input source
	if ((DPxGetCodecReg(19) & 0x78) != 0x78)
		return DPX_MIC_SRC_MIC_IN;
	if ((DPxGetCodecReg(20) & 0x78) != 0x78)
		return DPX_MIC_SRC_LINE_IN;
	return DPX_MIC_SRC_UNKNOWN;
}


// Get the 16-bit 2's complement signed value for left MIC channel
int DPxGetMicLeftValue()
{
	return (SInt16)DPxGetReg16(DPXREG_MIC_DATA_LEFT);
}


// Get the 16-bit 2's complement signed value for right MIC channel
int DPxGetMicRightValue()
{
	return (SInt16)DPxGetReg16(DPXREG_MIC_DATA_RIGHT);
}


// Configure how microphone Left/Right channels are stored to schedule buffer.
// lrMode is one of the following predefined constants:
//		DPXREG_MIC_CTRL_LRMODE_MONO		: Mono data is written to schedule buffer (average of Left/Right CODEC data)
//		DPXREG_MIC_CTRL_LRMODE_LEFT		: Left data is written to schedule buffer
//		DPXREG_MIC_CTRL_LRMODE_RIGHT	: Right data is written to schedule buffer
//		DPXREG_MIC_CTRL_LRMODE_STEREO	: Left and Right data are both written to schedule buffer
void DPxSetMicLRMode(int lrMode)
{
	switch (lrMode) {
		case DPXREG_MIC_CTRL_LRMODE_MONO:
		case DPXREG_MIC_CTRL_LRMODE_LEFT:
		case DPXREG_MIC_CTRL_LRMODE_RIGHT:
		case DPXREG_MIC_CTRL_LRMODE_STEREO:
			DPxSetReg16(DPXREG_MIC_CTRL, (DPxGetReg16(DPXREG_MIC_CTRL) & ~DPXREG_MIC_CTRL_LRMODE_MASK) | lrMode);
			break;

		default:
			DPxDebugPrint1("ERROR: DPxSetMicLRMode() unrecognized lrMode %d\n", lrMode);
			DPxSetError(DPX_ERR_MIC_SET_BAD_LRMODE);
	}
}


int DPxGetMicLRMode()
{
	return DPxGetReg16(DPXREG_MIC_CTRL) & DPXREG_MIC_CTRL_LRMODE_MASK;
}


// Enable loopback between audio outputs and microphone inputs
void DPxEnableAudMicLoopback()
{
	DPxSetReg16(DPXREG_MIC_CTRL, DPxGetReg16(DPXREG_MIC_CTRL) | DPXREG_MIC_CTRL_AUD_LOOPBACK);
}


// Disable loopback between audio outputs and microphone inputs
void DPxDisableAudMicLoopback()
{
	DPxSetReg16(DPXREG_MIC_CTRL, DPxGetReg16(DPXREG_MIC_CTRL) & ~DPXREG_MIC_CTRL_AUD_LOOPBACK);
}


// Returns non-0 if microphone inputs are driven by audio outputs
int DPxIsAudMicLoopback()
{
	return DPxGetReg16(DPXREG_MIC_CTRL) & DPXREG_MIC_CTRL_AUD_LOOPBACK;
}


// Set MIC RAM buffer start address.  Must be an even value.
void DPxSetMicBuffBaseAddr(unsigned buffBaseAddr)
{
	if (buffBaseAddr & 1) {
		DPxDebugPrint1("ERROR: DPxSetMicBuffBaseAddr(0x%x) illegal odd address\n", buffBaseAddr);
		DPxSetError(DPX_ERR_MIC_BUFF_ODD_BASEADDR);
		return;
	}
	if (buffBaseAddr >= DPxGetRamSize()) {
		DPxDebugPrint1("ERROR: DPxSetMicBuffBaseAddr(0x%x) exceeds DATAPixx RAM\n", buffBaseAddr);
		DPxSetError(DPX_ERR_MIC_BUFF_BASEADDR_TOO_HIGH);
		return;
	}
	DPxSetReg32(DPXREG_MIC_BUFF_BASEADDR_L, buffBaseAddr);
}


// Get MIC RAM buffer start address
unsigned DPxGetMicBuffBaseAddr()
{
	return DPxGetReg32(DPXREG_MIC_BUFF_BASEADDR_L);
}


// Set RAM address to which next MIC datum will be written.  Must be an even value.
void DPxSetMicBuffWriteAddr(unsigned buffWriteAddr)
{
	if (buffWriteAddr & 1) {
		DPxDebugPrint1("ERROR: DPxSetMicBuffWriteAddr(0x%x) illegal odd address\n", buffWriteAddr);
		DPxSetError(DPX_ERR_MIC_BUFF_ODD_WRITEADDR);
		return;
	}
	if (buffWriteAddr >= DPxGetRamSize()) {
		DPxDebugPrint1("ERROR: DPxSetMicBuffWriteAddr(0x%x) exceeds DATAPixx RAM\n", buffWriteAddr);
		DPxSetError(DPX_ERR_MIC_BUFF_WRITEADDR_TOO_HIGH);
		return;
	}
	DPxSetReg32(DPXREG_MIC_BUFF_WRITEADDR_L, buffWriteAddr);
}


// Get RAM address to which next MIC datum will be written
unsigned DPxGetMicBuffWriteAddr()
{
	return DPxGetReg32(DPXREG_MIC_BUFF_WRITEADDR_L);
}


// Set MIC RAM buffer size in bytes.  Must be an even value.
// The hardware will automatically wrap the BuffWriteAddr, when it gets to BuffBaseAddr+BuffSize, back to BuffBaseAddr.
// This simplifies continuous spooled acquisition.
void DPxSetMicBuffSize(unsigned buffSize)
{
	if (buffSize & 1) {
		DPxDebugPrint1("ERROR: DPxSetMicBuffSize(0x%x) illegal odd size\n", buffSize);
		DPxSetError(DPX_ERR_MIC_BUFF_ODD_SIZE);
		return;
	}
	if (buffSize > DPxGetRamSize()) {
		DPxDebugPrint1("ERROR: DPxSetMicBuffSize(0x%x) exceeds DATAPixx RAM\n", buffSize);
		DPxSetError(DPX_ERR_MIC_BUFF_TOO_BIG);
		return;
	}
	DPxSetReg32(DPXREG_MIC_BUFF_SIZE_L, buffSize);
}


// Get MIC RAM buffer size in bytes
unsigned DPxGetMicBuffSize()
{
	return DPxGetReg32(DPXREG_MIC_BUFF_SIZE_L);
}


// Shortcut which assigns Size/BaseAddr/ReadAddr
void DPxSetMicBuff(unsigned buffAddr, unsigned buffSize)
{
	DPxSetMicBuffBaseAddr(buffAddr);
	DPxSetMicBuffWriteAddr(buffAddr);
	DPxSetMicBuffSize(buffSize);
}


// Set nanosecond delay between schedule start and first MIC sample
void DPxSetMicSchedOnset(unsigned onset)
{
	DPxSetReg32(DPXREG_MIC_SCHED_ONSET_L, onset);
}


// Get nanosecond delay between schedule start and first MIC sample
unsigned DPxGetMicSchedOnset()
{
	return DPxGetReg32(DPXREG_MIC_SCHED_ONSET_L);
}


// Set MIC schedule sample rate and units
// rateUnits is one of the following predefined constants:
//		DPXREG_SCHED_CTRL_RATE_HZ		: rateValue is samples per second, maximum 96 kHz
//		DPXREG_SCHED_CTRL_RATE_XVID		: rateValue is samples per video frame, maximum 96 kHz
//		DPXREG_SCHED_CTRL_RATE_NANO		: rateValue is sample period in nanoseconds, minimum 10417 ns
// Note that the MIC system shares CODEC timing resources with the AUD system,
// and calling DPxSetMicSchedRate() must indirectly call DPxSetAudSchedRate() with the same frequency.
// I don't much like this relationship, and it may disappear in future hardware revs.
void DPxSetMicSchedRate(unsigned rateValue, int rateUnits)
{
	switch (rateUnits) {
		case DPXREG_SCHED_CTRL_RATE_HZ:
			if (rateValue > 96000) {
				DPxDebugPrint1("ERROR: DPxSetMicSchedRate() frequency too high %u\n", rateValue);
				DPxSetError(DPX_ERR_MIC_SCHED_TOO_FAST);
				return;
			}
			break;
		case DPXREG_SCHED_CTRL_RATE_XVID:
			if (rateValue > 96000/DPxGetVidVFreq()) {
				DPxDebugPrint1("ERROR: DPxSetMicSchedRate() frequency too high %u\n", rateValue);
				DPxSetError(DPX_ERR_MIC_SCHED_TOO_FAST);
				return;
			}
			break;
		case DPXREG_SCHED_CTRL_RATE_NANO:
			if (rateValue < 10417) {
				DPxDebugPrint1("ERROR: DPxSetMicSchedRate() period too low %u\n", rateValue);
				DPxSetError(DPX_ERR_MIC_SCHED_TOO_FAST);
				return;
			}
			break;
		default:
			DPxDebugPrint1("ERROR: DPxSetMicSchedRate() unrecognized rateUnits %d\n", rateUnits);
			DPxSetError(DPX_ERR_MIC_SCHED_BAD_RATE_UNITS);
			return;
	}
	DPxSetReg32(DPXREG_MIC_SCHED_CTRL_L, (DPxGetReg32(DPXREG_MIC_SCHED_CTRL_L) & ~DPXREG_SCHED_CTRL_RATE_MASK) | rateUnits);
	DPxSetReg32(DPXREG_MIC_SCHED_RATE_L,  rateValue);

	// Audio subsystem must absolutely run at the same rate as the MIC system,
	// since it's the AUD system which paces the CODEC I2S bus,
	// and configures CODEC registers.
	DPxSetAudSchedRate(rateValue, rateUnits);
}


// Get MIC schedule update rate (and optionally get rate units)
unsigned DPxGetMicSchedRate(int *rateUnits)
{
	if (rateUnits)
		*rateUnits = DPxGetReg32(DPXREG_MIC_SCHED_CTRL_L) & DPXREG_SCHED_CTRL_RATE_MASK;
	return DPxGetReg32(DPXREG_MIC_SCHED_RATE_L);
}


// Set MIC schedule update count
void DPxSetMicSchedCount(unsigned count)
{
	DPxSetReg32(DPXREG_MIC_SCHED_COUNT_L,  count);
}


// Get MIC schedule update count
unsigned DPxGetMicSchedCount()
{
	return DPxGetReg32(DPXREG_MIC_SCHED_COUNT_L);
}


// SchedCount decrements at SchedRate, and schedule stops automatically when count hits 0
void DPxEnableMicSchedCountdown()
{
	DPxSetReg32(DPXREG_MIC_SCHED_CTRL_L, DPxGetReg32(DPXREG_MIC_SCHED_CTRL_L) | DPXREG_SCHED_CTRL_COUNTDOWN);
}


// SchedCount increments at SchedRate, and schedule is stopped by calling SchedStop
void DPxDisableMicSchedCountdown()
{
	DPxSetReg32(DPXREG_MIC_SCHED_CTRL_L, DPxGetReg32(DPXREG_MIC_SCHED_CTRL_L) & ~DPXREG_SCHED_CTRL_COUNTDOWN);
}


// Returns non-0 if SchedCount decrements to 0 and automatically stops schedule
int DPxIsMicSchedCountdown()
{
	return DPxGetReg32(DPXREG_MIC_SCHED_CTRL_L) & DPXREG_SCHED_CTRL_COUNTDOWN;
}


// Shortcut which assigns Onset/Rate/Count.
// If Count > 0, enables Countdown mode.
void DPxSetMicSched(unsigned onset, unsigned rateValue, int rateUnits, unsigned count)
{
	DPxSetMicSchedOnset(onset);
	DPxSetMicSchedRate(rateValue, rateUnits);
	DPxSetMicSchedCount(count);
	if (count)
		DPxEnableMicSchedCountdown();
	else
		DPxDisableMicSchedCountdown();
}


// Start running an MIC schedule
void DPxStartMicSched()
{
	DPxSetReg16(DPXREG_SCHED_STARTSTOP, (DPxGetReg16(DPXREG_SCHED_STARTSTOP) & ~(DPXREG_SCHED_STARTSTOP_MASK << DPXREG_SCHED_STARTSTOP_SHIFT_MIC)) |
										(DPXREG_SCHED_STARTSTOP_START << DPXREG_SCHED_STARTSTOP_SHIFT_MIC));
}


// Stop running an MIC schedule
void DPxStopMicSched()
{
	DPxSetReg16(DPXREG_SCHED_STARTSTOP, (DPxGetReg16(DPXREG_SCHED_STARTSTOP) & ~(DPXREG_SCHED_STARTSTOP_MASK << DPXREG_SCHED_STARTSTOP_SHIFT_MIC)) |
										(DPXREG_SCHED_STARTSTOP_STOP << DPXREG_SCHED_STARTSTOP_SHIFT_MIC));
}


// Returns non-0 if MIC schedule is currently running
int DPxIsMicSchedRunning()
{
	return DPxGetReg32(DPXREG_MIC_SCHED_CTRL_L) & DPXREG_SCHED_CTRL_RUNNING;
}


// Returns CODEC Microphone IN group delay in seconds.
// This is the time between when a voltage appears at the MIC IN jack of the DATAPixx,
// and when an audio input schedule will acquire the voltage.
// Due to the way in which CODECs operate, this delay is a function of the sample rate (eg: 48000).
// Note that I measure the same group delay for both the "MIC IN" and the "Audio IN" jacks.
double DPxGetMicGroupDelay(double sampleRate)
{
	return 19.335 / sampleRate - 7.86e-6;
}


/********************************************************************************/
/*																				*/
/*	Video Subsystem																*/
/*																				*/
/********************************************************************************/


// Set the video processing mode.
// vidMode is one of the following predefined constants:
//		DPXREG_VID_CTRL_MODE_C24	Straight passthrough from DVI 8-bit (or HDMI "deep" 10/12-bit) RGB to VGA 8/10/12-bit RGB
//		DPXREG_VID_CTRL_MODE_L48	DVI RED[7:0] is used as an index into a 256-entry 16-bit RGB colour lookup table
//		DPXREG_VID_CTRL_MODE_M16	DVI RED[7:0] & GREEN[7:0] concatenate into a VGA 16-bit value sent to all three RGB components
//		DPXREG_VID_CTRL_MODE_C48	Even/Odd pixel RED/GREEN/BLUE[7:0] concatenate to generate 16-bit RGB components at half the horizontal resolution
//		DPXREG_VID_CTRL_MODE_L48D	DVI RED[7:4] & GREEN[7:4] concatenate to form an 8-bit index into a 256-entry 16-bit RGB colour lookup table
//		DPXREG_VID_CTRL_MODE_M16D	DVI RED[7:3] & GREEN[7:3] & BLUE[7:2] concatenate into a VGA 16-bit value sent to all three RGB components
//		DPXREG_VID_CTRL_MODE_C36D	Even/Odd pixel RED/GREEN/BLUE[7:2] concatenate to generate 12-bit RGB components at half the horizontal resolution
void DPxSetVidMode(int vidMode)
{
	if (vidMode & ~DPXREG_VID_CTRL_MODE_MASK) {
			DPxDebugPrint1("ERROR: DPxSetVidMode() unrecognized vidMode %d\n", vidMode);
			DPxSetError(DPX_ERR_VID_SET_BAD_MODE);
			return;
	}
	DPxSetReg16(DPXREG_VID_CTRL, (DPxGetReg16(DPXREG_VID_CTRL) & ~DPXREG_VID_CTRL_MODE_MASK) | vidMode);
}


// Get the video processing mode
int DPxGetVidMode()
{
	return DPxGetReg16(DPXREG_VID_CTRL) & DPXREG_VID_CTRL_MODE_MASK;
}


// Pass 256*3 = 768 16-bit values, in order R0,G0,B0,R1,G1,B1...
// DPxSetVidClut() returns immediately, and CLUT is implemented at next vertical blanking interval.
void DPxSetVidClut(UInt16* clutData)
{
	int payloadLength = 256 * 3 * 2;

	ep2out_Tram[0] = '^';
	ep2out_Tram[1] = EP2OUT_WRITECLUT;
	ep2out_Tram[2] = LSB(payloadLength);
	ep2out_Tram[3] = MSB(payloadLength);
	memcpy(ep2out_Tram+4, clutData, payloadLength);
	if (EZWriteEP2Tram(ep2out_Tram, 0, 0)) {
		DPxDebugPrint0("ERROR: DPxSetVidClut() call to EZWriteEP2Tram() failed\n");
		DPxSetError(DPX_ERR_VID_CLUT_WRITE_USB_ERROR);
	}
}


// Similar to DPxSetVidClut(), except pass 512*3 (=1536) 16-bit video DAC data to fill 2 channel CLUTs with independent data, in order R0,G0,B0,R1,G1,B1...
void DPxSetVidCluts(UInt16* clutData)
{
	int payloadLength = 512 * 3 * 2;

	ep2out_Tram[0] = '^';
	ep2out_Tram[1] = EP2OUT_WRITECLUT;
	ep2out_Tram[2] = LSB(payloadLength);
	ep2out_Tram[3] = MSB(payloadLength);
	memcpy(ep2out_Tram+4, clutData, payloadLength);
	if (EZWriteEP2Tram(ep2out_Tram, 0, 0)) {
		DPxDebugPrint0("ERROR: DPxSetVidCluts() call to EZWriteEP2Tram() failed\n");
		DPxSetError(DPX_ERR_VID_CLUT_WRITE_USB_ERROR);
	}
}


// VGA 1 shows left half of video image, VGA 2 shows right half of video image
void DPxEnableVidHorizSplit()
{
	DPxSetReg16(DPXREG_VID_CTRL, DPxGetReg16(DPXREG_VID_CTRL) | DPXREG_VID_CTRL_HSPLIT_MAN | DPXREG_VID_CTRL_HSPLIT);
}


// VGA 1 and VGA 2 both show entire video image (hardware video mirroring)
void DPxDisableVidHorizSplit()
{
	DPxSetReg16(DPXREG_VID_CTRL, (DPxGetReg16(DPXREG_VID_CTRL) | DPXREG_VID_CTRL_HSPLIT_MAN) & ~DPXREG_VID_CTRL_HSPLIT);
}


// DATAPixx will automatically split video across the two VGA outputs if the horizontal resolution is at least twice the vertical resolution (default mode)
void DPxAutoVidHorizSplit()
{
	DPxSetReg16(DPXREG_VID_CTRL, DPxGetReg16(DPXREG_VID_CTRL) & ~(DPXREG_VID_CTRL_HSPLIT_MAN | DPXREG_VID_CTRL_HSPLIT));
}


// Returns non-0 if video is being split across the two VGA outputs.
int DPxIsVidHorizSplit()
{
	return DPxGetReg16(DPXREG_VID_CTRL) & DPXREG_VID_CTRL_HSPLIT;
}


// Top/bottom halves of input image are output in two sequencial video frames.
// VESA L/R output is set to 1 when first frame (left eye) is displayed,
// and set to 0 when second frame (right eye) is displayed.
void DPxEnableVidVertStereo()
{
	DPxSetReg16(DPXREG_VID_CTRL, DPxGetReg16(DPXREG_VID_CTRL) | DPXREG_VID_CTRL_VSTEREO_MAN | DPXREG_VID_CTRL_VSTEREO);
}


// Normal display (no hardware vertical stereo)
void DPxDisableVidVertStereo()
{
	DPxSetReg16(DPXREG_VID_CTRL, (DPxGetReg16(DPXREG_VID_CTRL) | DPXREG_VID_CTRL_VSTEREO_MAN) & ~DPXREG_VID_CTRL_VSTEREO);
}


// Vertical stereo is enabled automatically when vertical resolution > horizontal resolution (default mode)
void DPxAutoVidVertStereo()
{
	DPxSetReg16(DPXREG_VID_CTRL, DPxGetReg16(DPXREG_VID_CTRL) & ~(DPXREG_VID_CTRL_VSTEREO_MAN | DPXREG_VID_CTRL_VSTEREO));
}


// Returns non-0 if DATAPixx is separating input into sequencial left/right stereo images.
int DPxIsVidVertStereo()
{
	return DPxGetReg16(DPXREG_VID_CTRL) & DPXREG_VID_CTRL_VSTEREO;
}


// VGA 1 and VGA 2 both show an overlay composite of the left/right halves of the video image
void DPxEnableVidHorizOverlay()
{
	DPxSetReg16(DPXREG_VID_CTRL, DPxGetReg16(DPXREG_VID_CTRL) | DPXREG_VID_CTRL_HOVERLAY);
}


// Horizontal overlay is disabled
void DPxDisableVidHorizOverlay()
{
	DPxSetReg16(DPXREG_VID_CTRL, DPxGetReg16(DPXREG_VID_CTRL) & ~DPXREG_VID_CTRL_HOVERLAY);
}


// Returns non-0 if the left/right halves of the video image are being overlayed
int DPxIsVidHorizOverlay()
{
	return DPxGetReg16(DPXREG_VID_CTRL) & DPXREG_VID_CTRL_HOVERLAY;
}


// Set bounding rectangle within left half image whose contents are composited with right half image
void DPxSetVidHorizOverlayBounds(int X1, int Y1, int X2, int Y2)
{
	DPxSetReg16(DPXREG_VID_HOVERLAY_X1, X1);
	DPxSetReg16(DPXREG_VID_HOVERLAY_Y1, Y1);
	DPxSetReg16(DPXREG_VID_HOVERLAY_X2, X2);
	DPxSetReg16(DPXREG_VID_HOVERLAY_Y2, Y2);
}


// Get bounding rectangle of horizontal overlay window
void DPxGetVidHorizOverlayBounds(int* X1, int* Y1, int* X2, int* Y2)
{
	*X1 = DPxGetReg16(DPXREG_VID_HOVERLAY_X1);
	*Y1 = DPxGetReg16(DPXREG_VID_HOVERLAY_Y1);
	*X2 = DPxGetReg16(DPXREG_VID_HOVERLAY_X2);
	*Y2 = DPxGetReg16(DPXREG_VID_HOVERLAY_Y2);
}


// Set 1024 16-bit video alpha values, in order X0,X1..X511,Y0,Y1...Y511
void DPxSetVidHorizOverlayAlpha(UInt16* alphaData)
{
	int payloadLength = 2048;

	ep2out_Tram[0] = '^';
	ep2out_Tram[1] = EP2OUT_WRITEALPHA;
	ep2out_Tram[2] = LSB(payloadLength);
	ep2out_Tram[3] = MSB(payloadLength);
	memcpy(ep2out_Tram+4, alphaData, payloadLength);
	if (EZWriteEP2Tram(ep2out_Tram, 0, 0)) {
		DPxDebugPrint0("ERROR: DPxSetVidHorizOverlayAlpha() call to EZWriteEP2Tram() failed\n");
		DPxSetError(DPX_ERR_VID_ALPHA_WRITE_USB_ERROR);
	}
}


// Get number of video dot times in one horizontal scan line (includes horizontal blanking interval).
// Note that this register is already multiplied by 2 if dual-link is active.
int DPxGetVidHTotal()
{
	return DPxGetReg16(DPXREG_VID_HTOTAL);
}


// Get number of video lines in one vertical frame (includes vertical blanking interval)
int DPxGetVidVTotal()
{
	return DPxGetReg16(DPXREG_VID_VTOTAL);
}


// Get number of visible pixels in one horizontal scan line
int DPxGetVidHActive()
{
	return DPxGetReg16(DPXREG_VID_HACTIVE);
}


// Get number of visible lines in one vertical frame
int DPxGetVidVActive()
{
	return DPxGetReg16(DPXREG_VID_VACTIVE);
}


// Get video vertical frame period in nanoseconds
unsigned DPxGetVidVPeriod()
{
	return DPxGetReg32(DPXREG_VID_VPERIOD_L) * 10;	// The DP register counts units of 10 ns.
}


// Get video vertical frame rate in Hz
double DPxGetVidVFreq()
{
	return 1.0e9 / DPxGetVidVPeriod();
}


// Get video horizontal line rate in Hz
double DPxGetVidHFreq()
{
	return DPxGetVidVFreq() * DPxGetVidVTotal();
}


// Get video dot frequency in Hz
double DPxGetVidDotFreq()
{
	return DPxGetVidHFreq() * DPxGetVidHTotal();
}


// Returns non-0 if DATAPixx is currently receiving video data over DVI link
int DPxIsVidDviActive()
{
	return DPxGetReg16(DPXREG_VID_STATUS) & DPXREG_VID_STATUS_DVI_ACTIVE;
}


// Returns non-0 if DATAPixx is currently receiving video data over dual-link DVI
int DPxIsVidDviActiveDual()
{
	return DPxGetReg16(DPXREG_VID_STATUS) & DPXREG_VID_STATUS_DVI_ACTIVE_DUAL;
}


// Returns non-0 if VIEWPixx is currently receiving video whose timing can directly drive display.
// Resolution must be 1920x1200, with refresh rate in the range 100-120Hz.
int DPxIsVidDviLockable()
{
	return DPxGetReg16(DPXREG_VID_STATUS) & DPXREG_VID_STATUS_DVI_LOCKABLE;
}


// Returns non-0 if DATAPixx is receiving video at too high a clock frequency
int DPxIsVidOverClocked()
{
	double dotFreq;
	
	// OK if we're unplugged
	if (!DPxIsVidDviActive())
		return 0;

	// DVI standard says that maximum DVI_CLK is 165 MHz,
	// but I think an HDMI source could provide digital data up to 225 MHz.
	// Our DVI receiver can decode it, but FPGA DVI_CLK fmax is 165 MHz.
	dotFreq = DPxGetVidDotFreq();
	if (!DPxIsVidDviActiveDual())
		return dotFreq > 165e6;
		
	// OK, so we're receiving dual link DVI (HDMI is only single link).
	// If we are outputting pixels at half the input pixel rate, then we're OK up to 330 MHz.
	// This happens when in C48/C36D modes, or in horizontal split screen.
	if (DPxGetVidMode() == DPXREG_VID_CTRL_MODE_C48 ||
		DPxGetVidMode() == DPXREG_VID_CTRL_MODE_C36D ||
		DPxIsVidHorizSplit())
		return dotFreq > 330e6;

	// We're in dual link DVI, and we're outputting pixels at the input pixel rate.
	// FPGA calls this "turbo" mode, and its fmax is up around 300 MHz.
	// The limiting factor however is the video DAC ASIC which is spec'd at 200 MHz.
	// (In practice, the video DACs seem to be good for up to 240-250 MHz).
    // Of course, this is only a limit on the original DATAPixx.  The VIEWPixx isn't affected.
    if (!(DPxIsViewpixx() || DPxIsPropixx()))
        return dotFreq > 200e6;
    
    // Otherwise, we're not overclocked
    return 0;
}


// VESA connector outputs left-eye signal
void DPxSetVidVesaLeft()
{
    // Now all VESA writes are done at DPXREG_VID_VESA, and writing VESA_LR bit requires setting a write-enable bit
    DPxSetReg16(DPXREG_VID_VESA, DPxGetReg16(DPXREG_VID_VESA) | DPXREG_VID_VESA_LEFT | DPXREG_VID_VESA_LEFT_WEN);
}


// VESA connector outputs right-eye signal
void DPxSetVidVesaRight()
{
//    if (DPxIsViewpixx() || DPxIsPropixx())
//        DPxSetReg16(DPXREG_VID_CTRL, DPxGetReg16(DPXREG_VID_CTRL) & ~DPXREG_VID_CTRL_VESA_LEFT);
//    else
//        DPxSetReg16(DPXREG_VID_VESA, DPxGetReg16(DPXREG_VID_VESA) & ~DPXREG_VID_VESA_LEFT);

    // Now all VESA writes are done at DPXREG_VID_VESA, and writing VESA_LR bit requires setting a write-enable bit
    DPxSetReg16(DPXREG_VID_VESA, (DPxGetReg16(DPXREG_VID_VESA) & ~DPXREG_VID_VESA_LEFT) | DPXREG_VID_VESA_LEFT_WEN);
}


// Returns non-0 if VESA connector has left-eye signal
int DPxIsVidVesaLeft()
{
    if (DPxIsViewpixx() && DPxGetFirmwareRev() <= 12)
        return DPxGetReg16(DPXREG_VID_CTRL) & DPXREG_VID_CTRL_VESA_LEFT;
    else
        return DPxGetReg16(DPXREG_VID_VESA) & DPXREG_VID_VESA_LEFT;
}


// VESA 3D output interprets middle pixel on last raster line as a blueline code
void DPxEnableVidVesaBlueline()
{
	DPxSetReg16(DPXREG_VID_VESA, DPxGetReg16(DPXREG_VID_VESA) | DPXREG_VID_VESA_BLUELINE);
}


// VESA 3D output is not dependent on video content
void DPxDisableVidVesaBlueline()
{
	DPxSetReg16(DPXREG_VID_VESA, DPxGetReg16(DPXREG_VID_VESA) & ~DPXREG_VID_VESA_BLUELINE);
}


// Returns non-0 if VESA 3D output is dependent on video blueline codes
int DPxIsVidVesaBlueline()
{
	return DPxGetReg16(DPXREG_VID_VESA) & DPXREG_VID_VESA_BLUELINE;
}


// Set the waveform which will be sent to the DATAPixx VESA 3D port
// waveform is one of the following predefined constants:
//      DPXREG_VID_VESA_WAVEFORM_LR             : VESA port drives straight L/R squarewave for 3rd party emitter
//      DPXREG_VID_VESA_WAVEFORM_CRYSTALEYES    : VESA port drives 3DPixx IR emitter for CrystalEyes 3D goggles
//      DPXREG_VID_VESA_WAVEFORM_NVIDIA         : VESA port drives 3DPixx IR emitter for NVIDIA 3D goggles
// We also set a reasonable VESA phase for the given waveform.
// User can override this phase afterwards by calling DPxSetVidVesaPhase().
void DPxSetVidVesaWaveform(int waveform)
{
	DPxSetReg16(DPXREG_VID_VESA, (DPxGetReg16(DPXREG_VID_VESA) & ~DPXREG_VID_VESA_WAVEFORM_MASK) | waveform);

    // Set phase of 3D glasses
    if (DPxIsViewpixx())
        DPxSetVidVesaPhase(100);  // For VIEWPixx, delay goggles 78% of video frame to wait for scanning backlight
    else
        DPxSetVidVesaPhase(245);  // For DATAPixx, flip goggles 9% of video frame early so they finish transitioning during vertical blanking
}


// Get the waveform which is being sent to the DATAPixx VESA 3D port
int DPxGetVidVesaWaveform()
{
	return DPxGetReg16(DPXREG_VID_VESA) & DPXREG_VID_VESA_WAVEFORM_MASK;
}


// Set the 8-bit unsigned phase of the VESA 3D waveform
void DPxSetVidVesaPhase(int phase)
{
	DPxSetReg16(DPXREG_VID_VESA, (DPxGetReg16(DPXREG_VID_VESA) & 0x00FF) | (phase << 8));    
}


// Get the 8-bit unsigned phase of the VESA 3D waveform
int DPxGetVidVesaPhase()
{
	return (DPxGetReg16(DPXREG_VID_VESA) & 0xFF00) >> 8;
}


// Read pixels from the DATAPixx line buffer, and return a pointer to the data.
// For each pixel, the buffer contains 16 bit R/G/B/U (where U is unused).
// The returned data could be overwritten by the next DPx* call.
UInt16* DPxGetVidLine()
{
	ep2out_Tram[0] = '^';
	ep2out_Tram[1] = EP2OUT_READVIDLINE;
	ep2out_Tram[2] = 0;
	ep2out_Tram[3] = 0;
	if (EZWriteEP2Tram(ep2out_Tram, EP6IN_READVIDLINE, 16384)) {
		DPxDebugPrint0("ERROR: DPxGetVidLine() call to EZWriteEP2Tram() failed\n");
		DPxSetError(DPX_ERR_RAM_READ_USB_ERROR);
		return 0;
	}

	return (UInt16*)(ep6in_Tram+4);
}


// Set the raster line on which pixel sync sequence is expected
void DPxSetVidPsyncRasterLine(int line)
{
	if (line & ~DPXREG_VID_PSYNC_RASTER_LINE) {
		DPxDebugPrint1("ERROR: DPxSetVidPsyncRasterLine() line %d out of range\n", line);
		DPxSetError(DPX_ERR_VID_PSYNC_LINE_ARG_ERROR);
		return;
	}
	DPxSetReg16(DPXREG_VID_PSYNC, (DPxGetReg16(DPXREG_VID_PSYNC) & ~DPXREG_VID_PSYNC_RASTER_LINE) | line);
}


// Get the raster line on which pixel sync sequence is expected
int DPxGetVidPsyncRasterLine()
{
	return DPxGetReg16(DPXREG_VID_PSYNC) & DPXREG_VID_PSYNC_RASTER_LINE;
}


// Pixel sync is only recognized on a single raster line
void DPxEnableVidPsyncSingleLine()
{
	DPxSetReg16(DPXREG_VID_PSYNC, DPxGetReg16(DPXREG_VID_PSYNC) | DPXREG_VID_PSYNC_SINGLE_LINE);
}


// Pixel sync is recognized on any raster line
void DPxDisableVidPsyncSingleLine()
{
	DPxSetReg16(DPXREG_VID_PSYNC, DPxGetReg16(DPXREG_VID_PSYNC) & ~DPXREG_VID_PSYNC_SINGLE_LINE);
}


// Returns non-0 if pixel sync is only recognized on a single raster line
int DPxIsVidPsyncSingleLine()
{
	return DPxGetReg16(DPXREG_VID_PSYNC) & DPXREG_VID_PSYNC_SINGLE_LINE;
}


// Pixel sync raster line is always displayed black
void DPxEnableVidPsyncBlankLine()
{
	DPxSetReg16(DPXREG_VID_PSYNC, DPxGetReg16(DPXREG_VID_PSYNC) | DPXREG_VID_PSYNC_BLANK_LINE);
}


// Pixel sync raster line is displayed normally
void DPxDisableVidPsyncBlankLine()
{
	DPxSetReg16(DPXREG_VID_PSYNC, DPxGetReg16(DPXREG_VID_PSYNC) & ~DPXREG_VID_PSYNC_BLANK_LINE);
}


// Returns non-0 if pixel sync raster line is always displayed black
int DPxIsVidPsyncBlankLine()
{
	return DPxGetReg16(DPXREG_VID_PSYNC) & DPXREG_VID_PSYNC_BLANK_LINE;
}


// Enable VIEWPixx scanning backlight
void DPxEnableVidScanningBacklight()
{
    if (DPxIsViewpixx()) {
        DPxSetReg16(DPXREG_VID_BL_SCAN_CTRL, 0xD5FF);
        DPxSetReg16(DPXREG_VID_CTRL2, DPxGetReg16(DPXREG_VID_CTRL2) | DPXREG_VID_CTRL2_PIXELDRIVE | DPXREG_VID_CTRL2_PIXELDRIVE_ACCUM);
    }
}


// Disable VIEWPixx scanning backlight
void DPxDisableVidScanningBacklight()
{
    if (DPxIsViewpixx()) {
        DPxSetReg16(DPXREG_VID_BL_SCAN_CTRL, 0x00FF);
        DPxSetReg16(DPXREG_VID_CTRL2, DPxGetReg16(DPXREG_VID_CTRL2) & ~(DPXREG_VID_CTRL2_PIXELDRIVE | DPXREG_VID_CTRL2_PIXELDRIVE_ACCUM));
    }
}


// Returns non-0 if VIEWPixx scanning backlight is enabled
int DPxIsVidScanningBacklight()
{
    return DPxIsViewpixx() ? DPxGetReg16(DPXREG_VID_BL_SCAN_CTRL) & 0x8000 : 0;
}


// Set source of video pattern to be displayed
void DPxSetVidSource(int vidSource)
{
	DPxSetReg16(DPXREG_VID_SRC, vidSource);
}


// Get source of video pattern being displayed
int DPxGetVidSource()
{
	return DPxGetReg16(DPXREG_VID_SRC);
}


// Shortcut to stop running all DAC/ADC/DOUT/DIN/AUD/AUX/MIC schedules
void DPxStopAllScheds()
{
	DPxSetReg16(DPXREG_SCHED_STARTSTOP, 0xAAAA);	// High 2 bits aren't currently used, but no harm in setting them
}


typedef struct {
    UInt16          ctrl;       // 15:Unused, 14:DE, 13:HSync, 12:VSync, 11-8:BlueLSB, 7-4:GreenLSB, 3-0:RedLSB
    unsigned char   redE;
    unsigned char   greenE;
    unsigned char   blueE;
    unsigned char   redO;
    unsigned char   greenO;
    unsigned char   blueO;
} ScopePixel;

// VScope video timing bit locations
#define SCOPE_CTRL_DE       0x4000
#define SCOPE_CTRL_HSYNC    0x2000
#define SCOPE_CTRL_VSYNC    0x1000

#define N_SCOPE_TEST_FRAMES 10
#define MAX_SCOPE_HMSGS     20
#define SCOPE_BUFF_SIZE ((165000000/120)*(N_SCOPE_TEST_FRAMES+2))      // Make sure we read in enough data to get all the frames we need, even under bizarre video format problems.
ScopePixel scopePixelBuff[SCOPE_BUFF_SIZE]; 

FILE *fpVScope;
    
static void PrintScopePixels(int inBuffIndex, int nPixels);
void DPxVideoScope(int toFile)
{
    char *displayName;

    int regVidCtrl2;
    int timHActive, timHBl, timHFp, timHSync, timHBp, timHTotal, timVActive, timVBl, timVFp, timVSync, timVTotal, timFTotal;    
    int i, j, k;
    int inVBlank, vFrameEnd, vFrame, vFrameMin, vFrameMax, nVFrame, nVFrameErrors;
    int hActiveStart, hActiveEnd, hActive, hActiveMin, hActiveMax, nHActive, nHActiveErrors;
    int hFPEnd, hFP, hFPMin, hFPMax, nHFP, nHFPErrors;
    int hSyncEnd, hSync, hSyncMin, hSyncMax, nHSync, nHSyncErrors;
    int hBPEnd, hBP, hBPMin, hBPMax, nHBP, nHBPErrors;
    int hTotalEnd, hTotal, hTotalMin, hTotalMax, nHTotal, nHTotalErrors;
    double hActiveSum, hFPSum, hSyncSum, hBPSum, hTotalSum, vFrameSum;
    int hLineNumber, hLastErrorLine, enableHMessages, hMsgNumber;
    int yCoord;
    UInt16* vidLineData;
    int vertState, lineIsActive, vertLineCount, vertFpStartLine, vertSyncStartLine, vertBpStartLine;
    int vertFp, vertSync, vertBp, vertFpMin, vertFpMax, vertSyncMin, vertSyncMax, vertBpMin, vertBpMax;
    int i2, vSyncStartPhase, vSyncStartPhaseMin, vSyncStartPhaseMax, vSyncEndPhase, vSyncEndPhaseMin, vSyncEndPhaseMax;
    double hiddenRed, hiddenGrn, hiddenBlu;

    // Get expected video characteristics
    if (DPxIsViewpixx3D()) {
        displayName = "VIEWPixx3D";
        timHActive  = 1920 / 2;
        timHBl      = 80 / 2;
        timHFp      = 16 / 2;
        timHSync    = 32 / 2;
        timVActive  = 1080;
        timVBl      = DPxGetReg16(DPXREG_VID_VTOTAL) < 1080 + (212+470)/2 ? 212 : 470;  // OS could be running us at 100Hz or 120Hz
        timVFp      = 3;
        timVSync    = 6;
    }
    else if (DPxIsViewpixx()) {
        displayName = "VIEWPixx";
        timHActive  = 1920 / 2;
        timHBl      = 160 / 2;
        timHFp      = 48 / 2;
        timHSync    = 32 / 2;
        timVActive  = 1200;
        timVBl      = DPxGetReg16(DPXREG_VID_VTOTAL) < 1200 + (35+281)/2 ? 35 : 281;  // OS could be running us at 100Hz or 120Hz
        timVFp      = 3;
        timVSync    = 6;
    }
    else if (DPxIsPropixx()) {
        displayName = "PROPixx";
        timHActive  = 1920 / 2;
        timHBl      = 280 / 2;
        timHFp      = 88 / 2;
        timHSync    = 40 / 2;
        timVActive  = 1080;
        timVBl      = 47;
        timVFp      = 3;
        timVSync    = 6;
    }
    else {
        printf("ERROR: Unknown display type\n");
        return;
    }

#if 1
    displayName = "VIEWPixx3D";
    timHActive  = 1920 / 2;
    timHBl      = 160 / 2;
    timHFp      = 64 / 2;
    timHSync    = 32 / 2;
    timVActive  = 1080;
    timVBl      = 202;
    timVFp      = 2;
    timVSync    = 2;
#endif
    
    timHBp      = timHBl - timHFp - timHSync;
    timHTotal   = timHActive + timHBl;
    timVTotal   = timVActive + timVBl;
    timFTotal   = timHTotal * timVTotal;    

    if (toFile)
        fpVScope = fopen("listing.txt", "wt");
    else
        fpVScope = stdout;
    
    inVBlank        = 0;
    vFrameEnd       = 0;
    vFrameMin       = 0x7FFFFFFF;
    vFrameMax       = -1;
    nVFrame         = 0;
    nVFrameErrors   = 0;
    vFrameSum       = 0;

    hActiveStart    = 0;
    hActiveEnd      = 0;
    hActiveMin      = 0x7FFFFFFF;
    hActiveMax      = -1;
    nHActive        = 0;
    nHActiveErrors  = 0;
    hActiveSum      = 0;

    hFPEnd          = 0;
    hFPMin          = 0x7FFFFFFF;
    hFPMax          = -1;
    nHFP            = 0;
    nHFPErrors      = 0;
    hFPSum          = 0;

    hSyncEnd        = 0;
    hSyncMin        = 0x7FFFFFFF;
    hSyncMax        = -1;
    nHSync          = 0;
    nHSyncErrors    = 0;
    hSyncSum        = 0;

    hBPEnd          = 0;
    hBPMin          = 0x7FFFFFFF;
    hBPMax          = -1;
    nHBP            = 0;
    nHBPErrors      = 0;
    hBPSum          = 0;

    hTotalEnd       = 0;
    hTotalMin       = 0x7FFFFFFF;
    hTotalMax       = -1;
    nHTotal         = 0;
    nHTotalErrors   = 0;
    hTotalSum       = 0;

    hLineNumber     = 0;
    hLastErrorLine  = -1;
    hMsgNumber       = 0;
    enableHMessages  = 1;

    yCoord = 0;

    vertState = 0;
    lineIsActive = 0;
    vertLineCount = 0;
    vertFpMin = 1000000;
    vertFpMax = -1;
    vertSyncMin = 1000000;
    vertSyncMax = -1;
    vertBpMin = 1000000;
    vertBpMax = -1;

    vSyncStartPhaseMin = 1000000000;
    vSyncStartPhaseMax = -1;
    vSyncEndPhaseMin = 1000000000;
    vSyncEndPhaseMax = -1;

    hiddenRed = 0.0;
    hiddenGrn = 0.0;
    hiddenBlu = 0.0;

    // Pixel drive will clobber VScope, so turn it off
    regVidCtrl2 = DPxGetReg16(DPXREG_VID_CTRL2);
    DPxSetReg16(DPXREG_VID_CTRL2, regVidCtrl2 & !(DPXREG_VID_CTRL2_PIXELDRIVE | DPXREG_VID_CTRL2_PIXELDRIVE_ACCUM));
    DPxUpdateRegCache();
    
    // Initiate frame grab
    DPxSetReg16(DPXREG_VID_SCOPE, 1);
    DPxUpdateRegCache();

    // Wait until frame grab done
    do {
        DPxUpdateRegCache();
    } while (DPxGetReg16(DPXREG_VID_SCOPE));

    // Get buffer
    DPxReadRam(0, sizeof(scopePixelBuff), scopePixelBuff);
    
    // Restore normal operation
    DPxSetReg16(DPXREG_VID_CTRL2, regVidCtrl2);
    DPxUpdateRegCache();

    // Get first video line from line grabber
    vidLineData = DPxGetVidLine();

    // Parse the buffer
    for (i = 0; nVFrame < N_SCOPE_TEST_FRAMES; i++) {

        // Did we reach the end of our buffer without finding the desired number of video frames?
        if (i >= SCOPE_BUFF_SIZE) {
            if (nVFrame == 0) {
                fprintf(fpVScope, "***ERROR: No VSYNC found.  Is %s connected to video source?\n", displayName);
                goto end;
            }
            else {
                fprintf(fpVScope, "***ERROR: Only %d of %d VSYNC found in buffer.\n", nVFrame, N_SCOPE_TEST_FRAMES);
                goto end;
            }
        }        
        
        // We will use the convention that the first active pixel after vertical blanking is the start of a video frame, and the start of a video line
        if (scopePixelBuff[i].ctrl & SCOPE_CTRL_VSYNC)
            inVBlank = 1;
        if (inVBlank && (scopePixelBuff[i+1].ctrl & SCOPE_CTRL_DE)) {   // We're in the last VBL pixel before a new frame
            inVBlank = 0;
            yCoord = 0;
            if (vFrameEnd == 0) {   // Will this be the first frame we analyze?
                fprintf(fpVScope, "First frame starts at address 0x%x\n", (unsigned int)((i+1)*sizeof(ScopePixel)));
                vFrameEnd = i;
                hTotalEnd = i;      // So that first video line can calculate HTOTAL
                continue;           // Don't process last pixel in VBL
            }
            else {                  // This is not the first frame we process, so we can do frame length analysis
                vFrame = i - vFrameEnd;
                vFrameSum += vFrame;
                nVFrame++;
                if (vFrame != timFTotal) {
                    nVFrameErrors++;
                    fprintf(fpVScope, "***ERROR: Frame %d FTOTAL[nom=%d] = %d\n", nVFrame, timFTotal, vFrame);
                }
                if (vFrameMin > vFrame)
                    vFrameMin = vFrame;
                if (vFrameMax < vFrame)
                    vFrameMax = vFrame;
                vFrameEnd = i;
            }
        }

        // We will not do any more processing of the buffer data until we have found the first frame start
        if (!vFrameEnd)
            continue;

        // We are adding simplified calculation of vertical timing, updated on leading edge of each HSYNC
        if ((scopePixelBuff[i].ctrl & SCOPE_CTRL_HSYNC) && !(scopePixelBuff[i-1].ctrl & SCOPE_CTRL_HSYNC)) {
            vertLineCount++;
            lineIsActive = scopePixelBuff[i-480].ctrl & SCOPE_CTRL_DE;  // 200 has to be 
            switch (vertState) {
                case 0: // Startup, waiting for active video before beginning processing
                    if (lineIsActive)
                        vertState = 1;
                    break;
                    
                case 1:     // In active region, waiting for start of VBL
                    if (!lineIsActive) {
                        vertFpStartLine = vertLineCount;
                        vertState = 2;
                    }
                    else    // Don't break if in VFP, in case VFP = 0
                        break;
                    
                case 2:     // In vertical front porch, waiting for VSYNC
                    if (scopePixelBuff[i-100].ctrl & SCOPE_CTRL_VSYNC) {
                        vertSyncStartLine = vertLineCount;
                        vertState = 3;
                    }
                    break;
                    
                case 3:     // In vertical sync, waiting for vertical back porch
                    if (!(scopePixelBuff[i-100].ctrl & SCOPE_CTRL_VSYNC)) {
                        vertBpStartLine = vertLineCount;
                        vertState = 4;
                    }
                    else    // Don't break if going into VBP, in case VBP = 0
                        break;
                    
                case 4:     // In vertical back porch, waiting for active
                    if (lineIsActive) {
                        vertFp = vertSyncStartLine - vertFpStartLine;
                        vertSync = vertBpStartLine - vertSyncStartLine;
                        vertBp = vertLineCount - vertBpStartLine;
                        if (vertFpMin > vertFp)
                            vertFpMin = vertFp;
                        if (vertFpMax < vertFp)
                            vertFpMax = vertFp;
                        if (vertSyncMin > vertSync)
                            vertSyncMin = vertSync;
                        if (vertSyncMax < vertSync)
                            vertSyncMax = vertSync;
                        if (vertBpMin > vertBp)
                            vertBpMin = vertBp;
                        if (vertBpMax < vertBp)
                            vertBpMax = vertBp;
                        vertState = 1;
                    }
                    break;
            }

            lineIsActive = 0;   // Reset for active test for next line
        }
        else if (scopePixelBuff[i].ctrl & SCOPE_CTRL_DE)    // Detect if line leading up to HSYNC is active
            lineIsActive = 1;

        // What's the phase relationship between VSYNC and HSYNC
        if ((scopePixelBuff[i].ctrl & SCOPE_CTRL_VSYNC) && !(scopePixelBuff[i-1].ctrl & SCOPE_CTRL_VSYNC)) {
            for (i2 = i; i2 > 0; i2--) {
                if ((scopePixelBuff[i2].ctrl & SCOPE_CTRL_HSYNC) && !(scopePixelBuff[i2-1].ctrl & SCOPE_CTRL_HSYNC)) {
                    vSyncStartPhase = i - i2;
                    printf("vSyncStartPhase = %d, i = %d, i2 = %d\n", vSyncStartPhase, i, i2);
                    if (vSyncStartPhaseMin > vSyncStartPhase)
                        vSyncStartPhaseMin = vSyncStartPhase;
                    if (vSyncStartPhaseMax < vSyncStartPhase)
                        vSyncStartPhaseMax = vSyncStartPhase;
                    break;
                }
            }
        }
        else if (!(scopePixelBuff[i].ctrl & SCOPE_CTRL_VSYNC) && (scopePixelBuff[i-1].ctrl & SCOPE_CTRL_VSYNC)) {
            for (i2 = i; i2 > 0; i2--) {
                if ((scopePixelBuff[i2].ctrl & SCOPE_CTRL_HSYNC) && !(scopePixelBuff[i2-1].ctrl & SCOPE_CTRL_HSYNC)) {
                    vSyncEndPhase = i - i2;
                    if (vSyncEndPhaseMin > vSyncEndPhase)
                        vSyncEndPhaseMin = vSyncEndPhase;
                    if (vSyncEndPhaseMax < vSyncEndPhase)
                        vSyncEndPhaseMax = vSyncEndPhase;
                    break;
                }
            }
        }

        // Report non-zero RGB data received during blanking
        if (!(scopePixelBuff[i].ctrl & SCOPE_CTRL_DE) && scopePixelBuff[i].redE)
            hiddenRed++;
        if (!(scopePixelBuff[i].ctrl & SCOPE_CTRL_DE) && scopePixelBuff[i].redO)
            hiddenRed++;
        if (!(scopePixelBuff[i].ctrl & SCOPE_CTRL_DE) && scopePixelBuff[i].greenE)
            hiddenGrn++;
        if (!(scopePixelBuff[i].ctrl & SCOPE_CTRL_DE) && scopePixelBuff[i].greenO)
            hiddenGrn++;
        if (!(scopePixelBuff[i].ctrl & SCOPE_CTRL_DE) && scopePixelBuff[i].blueE)
            hiddenBlu++;
        if (!(scopePixelBuff[i].ctrl & SCOPE_CTRL_DE) && scopePixelBuff[i].blueO)
            hiddenBlu++;

        // Detect start of Horizontal Active.
        if (!(scopePixelBuff[i-1].ctrl & SCOPE_CTRL_DE) && (scopePixelBuff[i].ctrl & SCOPE_CTRL_DE))
            hActiveStart = i;

        // Horizontal Active.
        if ((scopePixelBuff[i].ctrl & SCOPE_CTRL_DE) && !(scopePixelBuff[i+1].ctrl & SCOPE_CTRL_DE)) {
            hActiveEnd = i;
            if (hActiveStart) {
                hActive = hActiveEnd-hActiveStart+1;
                hActiveSum += hActive;
                nHActive++;
                if (hActive != timHActive) {
                    nHActiveErrors++;
                    if (enableHMessages) {
                        if (hLastErrorLine != hLineNumber) {
                            hLastErrorLine = hLineNumber;
                            fprintf(fpVScope, "***ERROR: Line %d, y=%d: ", hLineNumber, yCoord);
                        }
                        else
                            fprintf(fpVScope, ", ");
                        fprintf(fpVScope, "HACTIVE[nom=%d] = %d", timHActive, hActive);
                    }
                }
                if (hActiveMin > hActive)
                    hActiveMin = hActive;
                if (hActiveMax < hActive)
                    hActiveMax = hActive;
            }
        }

        // Horizontal Front Porch
        if (!(scopePixelBuff[i].ctrl & SCOPE_CTRL_HSYNC) && (scopePixelBuff[i+1].ctrl & SCOPE_CTRL_HSYNC)) {
            hFPEnd = i;
            if (hActiveEnd) {
                hFP = hFPEnd-hActiveEnd;
                if (hFP < timHTotal) {     // Ignore vertical blank periods
                    hFPSum += hFP;
                    nHFP++;
                    if (hFP != timHFp) {
                        nHFPErrors++;
                        if (enableHMessages) {
                            if (hLastErrorLine != hLineNumber) {
                                hLastErrorLine = hLineNumber;
                                fprintf(fpVScope, "***ERROR: Line %d, y=%d: ", hLineNumber, yCoord);
                            }
                            else
                                fprintf(fpVScope, ", ");
                            fprintf(fpVScope, "HFP[nom=%d] = %d", timHFp, hFP);
                        }
                    }
                    if (hFPMin > hFP)
                        hFPMin = hFP;
                    if (hFPMax < hFP)
                        hFPMax = hFP;
                }
            }
        }

        // Horizontal Sync
        if ((scopePixelBuff[i].ctrl & SCOPE_CTRL_HSYNC) && !(scopePixelBuff[i+1].ctrl & SCOPE_CTRL_HSYNC)) {
            hSyncEnd = i;
            if (hFPEnd) {
                hSync = hSyncEnd-hFPEnd;
                hSyncSum += hSync;
                nHSync++;
                if (hSync != timHSync) {
                    nHSyncErrors++;
                    if (enableHMessages) {
                        if (hLastErrorLine != hLineNumber) {
                            hLastErrorLine = hLineNumber;
                            fprintf(fpVScope, "***ERROR: Line %d, y=%d: ", hLineNumber, yCoord);
                        }
                        else
                            fprintf(fpVScope, ", ");
                        fprintf(fpVScope, "HSYNC[nom=%d] = %d", timHSync, hSync);
                    }
                }
                if (hSyncMin > hSync)
                    hSyncMin = hSync;
                if (hSyncMax < hSync)
                    hSyncMax = hSync;
            }
        }

        // Horizontal Back Porch
        if (!(scopePixelBuff[i].ctrl & SCOPE_CTRL_DE) && (scopePixelBuff[i+1].ctrl & SCOPE_CTRL_DE)) {
            hBPEnd = i;
            if (hSyncEnd) {
                hBP = hBPEnd-hSyncEnd;
                hBPSum += hBP;
                nHBP++;
                if (hBP != timHBp) {
                    nHBPErrors++;
                    if (enableHMessages) {
                        if (hLastErrorLine != hLineNumber) {
                            hLastErrorLine = hLineNumber;
                            fprintf(fpVScope, "***ERROR: Line %d, y=%d: ", hLineNumber, yCoord);
                        }
                        else
                            fprintf(fpVScope, ", ");
                        fprintf(fpVScope, "HBP[nom=%d] = %d", timHBp, hBP);
                    }
                }
                if (hBPMin > hBP)
                    hBPMin = hBP;
                if (hBPMax < hBP)
                    hBPMax = hBP;
            }

            // While we're at the end of the back porch, we'll also collects stats for entire lines
            if (hTotalEnd) {
                hTotal = i - hTotalEnd;
                if (hTotal < timHTotal*timVSync) {     // Ignore vertical blank periods
                    hTotalSum += hTotal;
                    nHTotal++;
                    if (hTotal != timHTotal) {
                        nHTotalErrors++;
                        if (enableHMessages) {
                            if (hLastErrorLine != hLineNumber) {
                                hLastErrorLine = hLineNumber;
                                fprintf(fpVScope, "***ERROR: Line %d, y=%d: ", hLineNumber, yCoord);
                            }
                            else
                                fprintf(fpVScope, ", ");
                            fprintf(fpVScope, "HTOTAL[nom=%d] = %d", timHTotal, hTotal);
                        }
                    }
                    if (hTotalMin > hTotal)
                        hTotalMin = hTotal;
                    if (hTotalMax < hTotal)
                        hTotalMax = hTotal;
                }
            }
            hTotalEnd = i;

            // End-of-line message processing
            if (hLastErrorLine == hLineNumber) {
                fprintf(fpVScope, ", RGB[");
                PrintScopePixels(hActiveStart, 2);
                fprintf(fpVScope, "]..[");
                PrintScopePixels(hActiveEnd-1, 3);
                fprintf(fpVScope, "]\n");
                if (++hMsgNumber >= MAX_SCOPE_HMSGS)
                    enableHMessages = 0;
            }
            if (hLineNumber < 4) { // Just so we can get some baseline video data
                fprintf(fpVScope, "Line %d RGB[", hLineNumber);
                PrintScopePixels(hActiveStart, 2);
                fprintf(fpVScope, "]..[");
                PrintScopePixels(hActiveEnd-1, 3);
                fprintf(fpVScope, "]\n");
            }

            // Print out one complete line if we're writing to a file
            if (toFile && hLineNumber == 8) {
                for (j = hActiveStart; j <= hActiveEnd; j += 2) {
                    fprintf(fpVScope, "2clk[%d]=[", j-hActiveStart);
                    PrintScopePixels(j, 2);
                    fprintf(fpVScope, "]\n");
                }
             }

            // A quick self-test to see if video line readback works.
            if (hLineNumber == 0) {
                for (j = 0; j < (hActiveEnd-hActiveStart+1)/2; j++) {
                    k = DPxIsVidDviActiveDual() ? j : j*2+1;
                    if (scopePixelBuff[hActiveStart+k].redE   != vidLineData[j*8+0] >> 8 ||
                        scopePixelBuff[hActiveStart+k].greenE != vidLineData[j*8+1] >> 8 ||
                        scopePixelBuff[hActiveStart+k].blueE  != vidLineData[j*8+2] >> 8 ||
                        scopePixelBuff[hActiveStart+k].redO   != vidLineData[j*8+4] >> 8 ||
                        scopePixelBuff[hActiveStart+k].greenO != vidLineData[j*8+5] >> 8 ||
                        scopePixelBuff[hActiveStart+k].blueO  != vidLineData[j*8+6] >> 8) {
                        printf("***LineBuff error on frame %d, pixel pair %d***\n", nVFrame, j);
                        printf("DDR: (%02X,%02X,%02X),(%02X,%02X,%02X)\n", scopePixelBuff[hActiveStart+k].redE, scopePixelBuff[hActiveStart+k].greenE, scopePixelBuff[hActiveStart+k].blueE,
                                scopePixelBuff[hActiveStart+k].redO, scopePixelBuff[hActiveStart+k].greenO, scopePixelBuff[hActiveStart+k].blueO);
                        printf("LIN: (%02X,%02X,%02X),(%02X,%02X,%02X)\n", vidLineData[j*8+0] >> 8, vidLineData[j*8+1] >> 8, vidLineData[j*8+2] >> 8, vidLineData[j*8+4] >> 8, vidLineData[j*8+5] >> 8, vidLineData[j*8+6] >> 8);
                    }
                }
            }

            // Prep for next line
            hLineNumber++;
            yCoord++;
        }
    }

    // Print summary stats
    fprintf(fpVScope, "\n");
    if (nVFrameErrors == 0)
        fprintf(fpVScope, "All %d VFRAME=%d\n", nVFrame, timFTotal);
    else
        fprintf(fpVScope, "***ERROR: VFRAME[nom=%d] range=%d-%d, avg=%.3f, %d/%d errors\n", timFTotal, vFrameMin, vFrameMax, vFrameSum/nVFrame, nVFrameErrors, nVFrame);

    if (nHActiveErrors == 0)
        fprintf(fpVScope, "All %d HACTIVE=%d\n", nHActive, timHActive);
    else
        fprintf(fpVScope, "***ERROR: HACTIVE[nom=%d] range=%d-%d, avg=%.3f, %d/%d errors\n", timHActive, hActiveMin, hActiveMax, hActiveSum/nHActive, nHActiveErrors, nHActive);
    if (nHActive != N_SCOPE_TEST_FRAMES*timVActive)
        fprintf(fpVScope, "***ERROR: Expected %d HACTIVE, but recorded %d\n", N_SCOPE_TEST_FRAMES*timVActive, nHActive);

    if (nHFPErrors == 0)
        fprintf(fpVScope, "All %d HFP=%d\n", nHFP, timHFp);
    else
        fprintf(fpVScope, "***ERROR: HFP[nom=%d] range=%d-%d, avg=%.3f, %d/%d errors\n", timHFp, hFPMin, hFPMax, hFPSum/nHFP, nHFPErrors, nHFP);
    if (nHFP != N_SCOPE_TEST_FRAMES*timVActive)
        fprintf(fpVScope, "***ERROR: Expected %d HFP, but recorded %d\n", N_SCOPE_TEST_FRAMES*timVActive, nHFP);

    if (nHSyncErrors == 0)
        fprintf(fpVScope, "All %d HSYNC=%d\n", nHSync, timHSync);
    else
        fprintf(fpVScope, "***ERROR: HSYNC[nom=%d] range=%d-%d, avg=%.3f, %d/%d errors\n", timHSync, hSyncMin, hSyncMax, hSyncSum/nHSync, nHSyncErrors, nHSync);
    if (nHSync != N_SCOPE_TEST_FRAMES*timVTotal)
        fprintf(fpVScope, "***ERROR: Expected %d HSYNC, but recorded %d\n", N_SCOPE_TEST_FRAMES*timVTotal, nHSync);

    if (nHBPErrors == 0)
        fprintf(fpVScope, "All %d HBP=%d\n", nHBP, timHBp);
    else
        fprintf(fpVScope, "***ERROR: HBP[nom=%d] range=%d-%d, avg=%.3f, %d/%d errors\n", timHBp, hBPMin, hBPMax, hBPSum/nHBP, nHBPErrors, nHBP);
    if (nHBP != N_SCOPE_TEST_FRAMES*timVActive)
        fprintf(fpVScope, "***ERROR: Expected %d HBP, but recorded %d\n", N_SCOPE_TEST_FRAMES*timVActive, nHBP);

    if (nHTotalErrors == 0)
        fprintf(fpVScope, "All %d HTOTAL=%d\n", nHTotal, timHTotal);
    else
        fprintf(fpVScope, "***ERROR: HTOTAL[nom=%d] range=%d-%d, avg=%.3f, %d/%d errors\n", timHTotal, hTotalMin, hTotalMax, hTotalSum/nHTotal, nHTotalErrors, nHTotal);
    if (nHTotal != N_SCOPE_TEST_FRAMES*(timVActive-1)) // VBL scraps one of our HTOTAL data
        fprintf(fpVScope, "***ERROR: Expected %d HTOTAL, but recorded %d\n", N_SCOPE_TEST_FRAMES*(timVActive-1), nHTotal);

    fprintf(fpVScope, "VFP range=%d-%d\n", vertFpMin, vertFpMax);
    fprintf(fpVScope, "VSYNC range=%d-%d\n", vertSyncMin, vertSyncMax);
    fprintf(fpVScope, "VBP range=%d-%d\n", vertBpMin, vertBpMax);
    fprintf(fpVScope, "VSYNC start phase range=%d-%d\n", vSyncStartPhaseMin, vSyncStartPhaseMax);
    fprintf(fpVScope, "VSYNC end phase range=%d-%d\n", vSyncEndPhaseMin, vSyncEndPhaseMax);
    
    if (hiddenRed > 0 || hiddenGrn > 0 || hiddenBlu > 0)
        fprintf(fpVScope, "***Hidden (R,G,B) = (%g,%g,%g)\n", hiddenRed, hiddenGrn, hiddenBlu);

end:
    if (fpVScope != stdout)
        fclose(fpVScope);
}


void PrintScopePixels(int inBuffIndex, int nPixels)
{
    int i;
    
    for (i = inBuffIndex; i < inBuffIndex+nPixels; i++) {
        if (i > inBuffIndex)
            fprintf(fpVScope, ",");
        fprintf(fpVScope, "(%02X,%02X,%02X),(%02X,%02X,%02X)", scopePixelBuff[i].redE, scopePixelBuff[i].greenE, scopePixelBuff[i].blueE,
                                                      scopePixelBuff[i].redO, scopePixelBuff[i].greenO, scopePixelBuff[i].blueO);
    }
}

