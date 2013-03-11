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
 
//	-API functions take "int" arguments and return "int" values whenever the value fits in a SInt32.
//	 UInt32 data does not fit in a SInt32, so it is passed as type "unsigned".
//	 This strategy minimizes the number of type casts required by API users.
//	-This API should work OK with both 32-bit and 64-bit integers.
//	-Unless otherwise specified, the reset value for all DPxSet*() parameters is 0, and all "DPxEnable*()" are disabled.
//	-This API assumes it is being compiled for a LITTLE-ENDIAN architecture; eg: Intel Mac or PC.
//	 This assumption comes into play when reading and writing little-endian USB messages.
//

#include "libdpx_i.h"					// internal API includes field definitions; eg: DPXREG_SCHED_CTRL_RATE_HZ

//	Setup functions
void		DPxOpen(void);							// Call before any other DPx*() functions
void		DPxClose(void);							// Call when finished with DATAPixx
int			DPxIsReady(void);						// Returns non-0 if a DATAPixx has been successfully opened

//	Functions for reading and writing DATAPixx RAM
void		DPxReadRam(unsigned address, unsigned length, void* buffer);	// Read a block of DATAPixx RAM into a local buffer
void		DPxWriteRam(unsigned address, unsigned length, void* buffer);	// Write a local buffer to DATAPixx RAM
size_t		DPxGetReadRamBuffAddr(void);									// Address of API internal read RAM buffer
int			DPxGetReadRamBuffSize(void);									// Number of bytes in internal read RAM buffer
size_t		DPxGetWriteRamBuffAddr(void);									// Address of API internal write RAM buffer
int			DPxGetWriteRamBuffSize(void);									// Number of bytes in internal write RAM buffer

//	The DPxSet*() DPxEnable*(), and DPxDisable*() functions write new register values to a local cache, then flag these registers as "modified".
//	DPxWriteRegCache() downloads modified registers in the local cache back to the DATAPixx.
//	Averages about 125 microseconds (probably one 125us USB microframe) on a Mac Pro.
//	DPxUpdateRegCache() does a DPxWriteRegCache(),
//	then uploads a snapshot of the DATAPixx register map back into the local register cache.
//	Once in the local cache, DPxGet*() and DPxIs*() functions can quickly examine the cached values.
//	This averages about 250 microseconds (probably 2 x 125us USB microframes) on a Mac Pro.
//	The AfterVideoSync() versions do the same thing, except that the Datapixx waits until
//	the leading edge of the next vertical sync pulse before treating the command.
//	The AfterPixelSync() works similarly, except that it waits for a specific pixel sequence.
void		DPxWriteRegCache(void);					// Write local register cache to Datapixx over USB
void		DPxUpdateRegCache(void);				// DPxWriteRegCache, then readback registers over USB into local cache
void		DPxWriteRegCacheAfterVideoSync(void);	// Like DPxWriteRegCache, but Datapixx only writes the registers on leading edge of next vertical sync pulse
void		DPxUpdateRegCacheAfterVideoSync(void);	// Like DPxUpdateRegCache, but Datapixx only writes the registers on leading edge of next vertical sync pulse
void		DPxWriteRegCacheAfterPixelSync(int nPixels, unsigned char* pixelData, int timeout);	// Like DPxWriteRegCache, but waits for a pixel sync sequence.
																								// pixelData is passed in order R0,G0,B0,R1,G1,B1...
																								// A pixel sync sequence may contain a maximum of 8 pixels.
                                                                                                // Timeout is in video frames.
void		DPxUpdateRegCacheAfterPixelSync(int nPixels, unsigned char* pixelData, int timeout);// Like DPxUpdateRegCache, but waits for a pixel sync sequence

//	API to read and write individual fields within the local register cache.
//	First set of registers is global system information.
int			DPxGetID(void);							// Get the DATAPixx identifier code
int			DPxIsViewpixx(void);					// Returns non-0 if DATAPixx is embedded in a VIEWPixx OR a VIEWPixx3D
int			DPxIsViewpixx3D(void);					// Returns non-0 if DATAPixx is embedded in a VIEWPixx3D
int			DPxIsPropixx(void);                     // Returns non-0 if DATAPixx is embedded in a PROPixx
int			DPxGetRamSize(void);					// Get the number of bytes of RAM in the DATAPixx system
int			DPxGetPartNumber(void);					// Get the integer part number of this DATAPixx
int			DPxGetFirmwareRev(void);				// Get the DATAPixx firmware revision
double		DPxGetSupplyVoltage(void);				// Get voltage being supplied from +5V supply
double		DPxGetSupplyCurrent(void);				// Get current being supplied from +5V supply
double		DPxGetSupply2Voltage(void);				// Get voltage being supplied from +12V supply
double		DPxGetSupply2Current(void);				// Get current being supplied from +12V supply
int			DPxIs5VFault(void);						// Returns non-0 if VESA and Analog I/O +5V pins are trying to draw more than 500 mA
int			DPxIsPsyncTimeout(void);				// Returns non-0 if last pixel sync wait timed out
int			DPxIsRamOffline(void);					// Returns non-0 if DDR SDRAM controller has not yet brought memory system online
double		DPxGetTempCelcius(void);				// Get temperature inside of DATAPixx chassis, in degrees Celcius
double		DPxGetTemp2Celcius(void);				// Get temperature2 inside of VIEWPixx chassis, in degrees Celcius
double		DPxGetTemp3Celcius(void);				// Get temperature of VIEWPixx FPGA die, in degrees Celcius
double		DPxGetTempFarenheit(void);				// Get temperature inside of DATAPixx chassis, in degrees Farenheit
double		DPxGetTime(void);						// Get double precision seconds since powerup
void		DPxSetMarker(void);						// Latch the current time value into the marker register
double		DPxGetMarker(void);						// Get double precision seconds when DPxSetMarker() was last called
void		DPxGetNanoTime(unsigned *nanoHigh32, unsigned *nanoLow32); // Get high/low UInt32 nanoseconds since powerup
void		DPxGetNanoMarker(unsigned *nanoHigh32, unsigned *nanoLow32); // Get high/low UInt32 nanosecond marker

//	DAC (Digital to Analog Converter) subsystem
//	4 16-bit DACs can be written directly by user, or updated by a DAC schedule.
//	A DAC schedule is used to automatically copy a waveform from DATAPixx RAM to the DACs.
//	Typical scheduling steps are:
//		-DPxWriteRam() to write one or more 16-bit waveforms into DATAPixx RAM
//		-DPxSetDacBuffReadAddr() specifies the RAM address where the first DAC datum should be read
//		-If the waveform buffer is expected to wrap, then DPxSetDacBuffBaseAddr() and DPxSetDacBuffSize() controls buffer address wrapping
//		-DPxEnableDacBuffChan() for each DAC channel which should be updated from RAM buffer
//		-DPxSetDacSchedOnset() specifies nanosecond onset delay between schedule start and first update of DACs enabled in mask
//		-DPxSetDacSchedRate() sets rate at which schedule should update enabled DACs.  Interpretation of rateValue depends on rateUnits:
//		-To schedule a fixed number of DAC updates, call DPxEnableDacSchedCountdown() and set DPxSetDacSchedCount() to desired number of DAC updates;
//		 or for an unlimited number of DAC updates, call DPxDisableDacSchedCountdown() to count updates forever.
//		-DPxDacSchedStart()
//		-The schedule will now wait for the onset delay, then copy the RAM waveform to the enabled DACs at the requested rate
//		-If Countdown mode is disabled, then manually DPxDacSchedStop() when desired
//
int			DPxGetDacNumChans(void);								// Returns number of DAC channels in system (4 in current implementation)
void		DPxSetDacValue(int value, int channel);					// Set the 16-bit 2's complement signed value for one DAC channel
int			DPxGetDacValue(int channel);							// Get the 16-bit 2's complement signed value for one DAC channel
void        DPxGetDacRange(int channel, double *minV, double *maxV); // Return voltage range; For VIEWPixx: +-10V, for DATAPixx: +-10V for ch0/1, +-5V for ch2/3
void        DPxSetDacVoltage(double voltage, int channel);			// Set the voltage for one DAC channel (+-10V for ch0/1, +-5V for ch2/3)
double		DPxGetDacVoltage(int channel);							// Get the voltage for one DAC channel (+-10V for ch0/1, +-5V for ch2/3)
void		DPxEnableDacCalibRaw(void);								// Enable DAC "raw" mode, causing DAC data to bypass hardware calibration
void		DPxDisableDacCalibRaw(void);							// Disable DAC "raw" mode, causing normal DAC hardware calibration
int			DPxIsDacCalibRaw(void);									// Returns non-0 if DAC data is bypassing hardware calibration
void		DPxEnableDacBuffChan(int channel);						// Enable RAM buffering of a DAC channel
void		DPxDisableDacBuffChan(int channel);						// Disable RAM buffering of a DAC channel
void		DPxDisableDacBuffAllChans(void);						// Disable RAM buffering of all DAC channels
int			DPxIsDacBuffChan(int channel);							// Returns non-0 if RAM buffering is enabled for a DAC channel
void		DPxSetDacBuffBaseAddr(unsigned buffBaseAddr);			// Set DAC RAM buffer start address.  Must be an even value.
unsigned	DPxGetDacBuffBaseAddr(void);							// Get DAC RAM buffer start address
void		DPxSetDacBuffReadAddr(unsigned buffReadAddr);			// Set RAM address from which next DAC datum will be read.  Must be an even value.
unsigned	DPxGetDacBuffReadAddr(void);							// Get RAM address from which next DAC datum will be read
void		DPxSetDacBuffSize(unsigned buffSize);					// Set DAC RAM buffer size in bytes.  Must be an even value.  Buffer wraps to Base after Size.
unsigned	DPxGetDacBuffSize(void);								// Get DAC RAM buffer size in bytes
void		DPxSetDacBuff(unsigned buffAddr, unsigned buffSize);	// Shortcut which assigns Size/BaseAddr/ReadAddr
void		DPxSetDacSchedOnset(unsigned onset);					// Set nanosecond delay between schedule start and first DAC update
unsigned	DPxGetDacSchedOnset(void);								// Get nanosecond delay between schedule start and first DAC update
void		DPxSetDacSchedRate(unsigned rateValue, int rateUnits);	// Set DAC schedule update rate and units
																	// rateUnits is one of the following predefined constants:
																	//		DPXREG_SCHED_CTRL_RATE_HZ		: rateValue is updates per second, maximum 1 MHz
																	//		DPXREG_SCHED_CTRL_RATE_XVID		: rateValue is updates per video frame, maximum 1 MHz
																	//		DPXREG_SCHED_CTRL_RATE_NANO		: rateValue is update period in nanoseconds, minimum 1000 ns
unsigned	DPxGetDacSchedRate(int *rateUnits);						// Get DAC schedule update rate (and optionally get rate units)
void		DPxSetDacSchedCount(unsigned count);					// Set DAC schedule update count
unsigned	DPxGetDacSchedCount(void);								// Get DAC schedule update count
void		DPxEnableDacSchedCountdown(void);						// SchedCount decrements at SchedRate, and schedule stops automatically when count hits 0
void		DPxDisableDacSchedCountdown(void);						// SchedCount increments at SchedRate, and schedule is stopped by calling SchedStop
int			DPxIsDacSchedCountdown(void);							// Returns non-0 if SchedCount decrements to 0 and automatically stops schedule
void		DPxSetDacSched(unsigned onset, unsigned rateValue, int rateUnits, unsigned count);	// Shortcut which assigns Onset/Rate/Count. If Count > 0, enables Countdown mode.
void		DPxStartDacSched(void);									// Start running a DAC schedule
void		DPxStopDacSched(void);									// Stop running a DAC schedule
int			DPxIsDacSchedRunning(void);								// Returns non-0 if DAC schedule is currently running

//	ADC (Analog to Digital Converter) subsystem
//	The ADC subsystem has 18 simultaneously sampled analog inputs.
//	Inputs 0-15 make up the channel dataset, whose samples can be scheduled and stored to RAM.
//	Inputs 16-17 can be used as differential reference inputs for the 16 data channels.
//	For each of the 16 channels, call DPxSetAdcBuffChanRef() to specify what it's analog refence should be.
//	An ADC schedule is used to automatically store ADC samples into RAM.
//	Typical usage steps are the same as for DAC schedules,
//	except that DPxReadRam() should be used to copy the acquired data from the DATAPixx back to host memory.
//	A schedule can optionally store a 64-bit nanosecond timetag with each sample.
//
int			DPxGetAdcNumChans(void);								// Returns number of ADC channels in system (18 in current implementation)
int			DPxGetAdcValue(int channel);							// Get the 16-bit 2's complement signed value for one ADC channel (0-17)
void		DPxGetAdcRange(int channel, double *minV, double *maxV); // Return voltage range (+-10V for all channels)
double		DPxGetAdcVoltage(int channel);							// Get the voltage for one ADC channel
void		DPxSetAdcBuffChanRef(int channel, int chanRef);			// Set a channel's differential reference source (only valid for channels 0-15)
																	// chanRef is one of the following predefined constants:
																	//		DPXREG_ADC_CHANREF_GND		: Referenced to ground
																	//		DPXREG_ADC_CHANREF_DIFF		: Referenced to adjacent analog input 
																	//		DPXREG_ADC_CHANREF_REF0		: Referenced to REF0 analog input
																	//		DPXREG_ADC_CHANREF_REF1		: Referenced to REF1 analog input
int			DPxGetAdcBuffChanRef(int channel);						// Get a channel's differential reference source (only valid for channels 0-15)
void		DPxEnableAdcBuffChan(int channel);						// Enable RAM buffering of an ADC channel (only valid for channels 0-15)
void		DPxDisableAdcBuffChan(int channel);						// Disable RAM buffering of an ADC channel (only valid for channels 0-15)
void		DPxDisableAdcBuffAllChans(void);						// Disable RAM buffering of all ADC channels
int			DPxIsAdcBuffChan(int channel);							// Returns non-0 if RAM buffering is enabled for an ADC channel (only valid for channels 0-15)
void		DPxEnableAdcCalibRaw(void);								// Enable ADC "raw" mode, causing ADC data to bypass hardware calibration
void		DPxDisableAdcCalibRaw(void);							// Disable ADC "raw" mode, causing normal ADC hardware calibration
int			DPxIsAdcCalibRaw(void);									// Returns non-0 if ADC data is bypassing hardware calibration
void		DPxEnableDacAdcLoopback(void);							// ADC data readings are looped back internally from programmed DAC voltages:
																	//		DAC_DATA0 => ADC_DATA0/2/4/6/8/10/12/14
																	//		DAC_DATA1 => ADC_DATA1/3/5/7/9/11/13/15
																	//		DAC_DATA2 => ADC_REF0
																	//		DAC_DATA3 => ADC_REF1
void		DPxDisableDacAdcLoopback(void);							// Disable ADC loopback, causing ADC readings to reflect real analog inputs
int			DPxIsDacAdcLoopback(void);								// Returns non-0 if ADC inputs are looped back from DAC outputs
void		DPxEnableAdcFreeRun(void);								// ADC's convert continuously (can add up to 4 microseconds random latency to scheduled samples)
void		DPxDisableAdcFreeRun(void);								// ADC's only convert on schedule ticks (for microsecond-precise sampling)
int			DPxIsAdcFreeRun(void);									// Returns non-0 if ADC's are performing continuous conversions
void		DPxSetAdcBuffBaseAddr(unsigned buffBaseAddr);			// Set ADC RAM buffer start address.  Must be an even value.
unsigned	DPxGetAdcBuffBaseAddr(void);							// Get ADC RAM buffer start address
void		DPxSetAdcBuffWriteAddr(unsigned buffWriteAddr);			// Set RAM address to which next ADC datum will be written.  Must be an even value.
unsigned	DPxGetAdcBuffWriteAddr(void);							// Get RAM address to which next ADC datum will be written
void		DPxSetAdcBuffSize(unsigned buffSize);					// Set ADC RAM buffer size in bytes.  Must be an even value.  Buffer wraps after Size.
unsigned	DPxGetAdcBuffSize(void);								// Get ADC RAM buffer size in bytes
void		DPxSetAdcBuff(unsigned buffAddr, unsigned buffSize);	// Shortcut which assigns Size/BaseAddr/ReadAddr
void		DPxSetAdcSchedOnset(unsigned onset);					// Set nanosecond delay between schedule start and first ADC sample
unsigned	DPxGetAdcSchedOnset(void);								// Get nanosecond delay between schedule start and first ADC sample
void		DPxSetAdcSchedRate(unsigned rateValue, int rateUnits);	// Set ADC schedule sample rate and units
																	// rateUnits is one of the following predefined constants:
																	//		DPXREG_SCHED_CTRL_RATE_HZ		: rateValue is samples per second, maximum 200 kHz
																	//		DPXREG_SCHED_CTRL_RATE_XVID		: rateValue is samples per video frame, maximum 200 kHz
																	//		DPXREG_SCHED_CTRL_RATE_NANO		: rateValue is sample period in nanoseconds, minimum 5000 ns
unsigned	DPxGetAdcSchedRate(int *rateUnits);						// Get ADC schedule sample rate (and optionally get rate units)
void		DPxSetAdcSchedCount(unsigned count);					// Set ADC schedule sample count
unsigned	DPxGetAdcSchedCount(void);								// Get ADC schedule sample count
void		DPxEnableAdcSchedCountdown(void);						// SchedCount decrements at SchedRate, and schedule stops automatically when count hits 0
void		DPxDisableAdcSchedCountdown(void);						// SchedCount increments at SchedRate, and schedule is stopped by calling SchedStop
int			DPxIsAdcSchedCountdown(void);							// Returns non-0 if SchedCount decrements to 0 and automatically stops schedule
void		DPxSetAdcSched(unsigned onset, unsigned rateValue, int rateUnits, unsigned count);	// Shortcut which assigns Onset/Rate/Count. If Count > 0, enables Countdown mode.
void		DPxStartAdcSched(void);									// Start running an ADC schedule
void		DPxStopAdcSched(void);									// Stop running an ADC schedule
int			DPxIsAdcSchedRunning(void);								// Returns non-0 if ADC schedule is currently running
void		DPxEnableAdcLogTimetags(void);							// Each buffered ADC sample is preceeded with a 64-bit nanosecond timetag
void		DPxDisableAdcLogTimetags(void);							// Buffered data has no timetags
int			DPxIsAdcLogTimetags(void);								// Returns non-0 if buffered datasets are preceeded with nanosecond timetag

//	DOUT (Digital Output) subsystem
//	The DATAPixx has 24 TTL outputs.
//	The low 16 bits can be written directly by the user, or updated by a DOUT schedule.
//	The high 8 bits can only be written by the user, not by a schedule.
//	A DOUT schedule is used to automatically copy a waveform from DATAPixx RAM to the low 16 digital outputs.
//	Typical usage steps are the same as for DAC schedules.
//
int			DPxGetDoutNumBits(void);								// Returns number of digital output bits in system (24 in current implementation)
void		DPxSetDoutValue(int bitValue, int bitMask);				// For each of the 24 bits set in bitMask, set the DOUT to the value in the corresponding bitValue
int			DPxGetDoutValue(void);									// Get the values of the 24 DOUT bits
void		DPxEnableDoutButtonSchedules(void);						// Enable automatic DOUT schedules upon DIN button presses
void		DPxDisableDoutButtonSchedules(void);					// Disable automatic DOUT schedules upon DIN button presses
int			DPxIsDoutButtonSchedules(void);							// Returns non-0 if automatic DOUT schedules occur upon DIN button presses
void		DPxSetDoutBuffBaseAddr(unsigned buffBaseAddr);			// Set DOUT RAM buffer start address.  Must be an even value.
unsigned	DPxGetDoutBuffBaseAddr(void);							// Get DOUT RAM buffer start address
void		DPxSetDoutBuffReadAddr(unsigned buffReadAddr);			// Set RAM address from which next DOUT datum will be read.  Must be an even value.
unsigned	DPxGetDoutBuffReadAddr(void);							// Get RAM address from which next DOUT datum will be read
void		DPxSetDoutBuffSize(unsigned buffSize);					// Set DOUT RAM buffer size in bytes.  Must be an even value.  Buffer wraps to Base after Size.
unsigned	DPxGetDoutBuffSize(void);								// Get DOUT RAM buffer size in bytes
void		DPxSetDoutBuff(unsigned buffAddr, unsigned buffSize);	// Shortcut which assigns Size/BaseAddr/ReadAddr
void		DPxSetDoutSchedOnset(unsigned onset);					// Set nanosecond delay between schedule start and first DOUT update
unsigned	DPxGetDoutSchedOnset(void);								// Get nanosecond delay between schedule start and first DOUT update
void		DPxSetDoutSchedRate(unsigned rateValue, int rateUnits);	// Set DOUT schedule update rate and units
																	// rateUnits is one of the following predefined constants:
																	//		DPXREG_SCHED_CTRL_RATE_HZ		: rateValue is updates per second, maximum 10 MHz
																	//		DPXREG_SCHED_CTRL_RATE_XVID		: rateValue is updates per video frame, maximum 10 MHz
																	//		DPXREG_SCHED_CTRL_RATE_NANO		: rateValue is update period in nanoseconds, minimum 100 ns
unsigned	DPxGetDoutSchedRate(int *rateUnits);					// Get DOUT schedule update rate (and optionally get rate units)
void		DPxSetDoutSchedCount(unsigned count);					// Set DOUT schedule update count
unsigned	DPxGetDoutSchedCount(void);								// Get DOUT schedule update count
void		DPxEnableDoutSchedCountdown(void);						// SchedCount decrements at SchedRate, and schedule stops automatically when count hits 0
void		DPxDisableDoutSchedCountdown(void);						// SchedCount increments at SchedRate, and schedule is stopped by calling SchedStop
int			DPxIsDoutSchedCountdown(void);							// Returns non-0 if SchedCount decrements to 0 and automatically stops schedule
void		DPxSetDoutSched(unsigned onset, unsigned rateValue, int rateUnits, unsigned count);	// Shortcut which assigns Onset/Rate/Count. If Count > 0, enables Countdown mode.
void		DPxStartDoutSched(void);								// Start running a DOUT schedule
void		DPxStopDoutSched(void);									// Stop running a DOUT schedule
int			DPxIsDoutSchedRunning(void);							// Returns non-0 if DOUT schedule is currently running

//	DIN (Digital Input) subsystem
//	The DATAPixx has 24 TTL inputs.
//	Transitions on the low 16 bits can be acquired to a RAM buffer.
//	Alternatively, the low 16 bits can be acquired at a fixed frequency using a DIN schedule.
//	Typical usage steps for DIN schedules are the same as for DAC schedules.
//	A 64-bit nanosecond timetag can optionally be stored with each sample in the RAM buffer.
//	The DIN ports are actually bidirectional, and each bit can be programmed to drive its port.
//	Users can program a drive strength, which could be used to vary the intensity of driven LEDs.
//
int			DPxGetDinNumBits(void);									// Returns number of digital input bits in system (24 in current implementation)
int			DPxGetDinValue(void);									// Get the values of the 24 DIN bits
void		DPxSetDinDataDir(int directionMask);					// Set 24-bit port direction mask.  Set mask bits to 1 for each bit which should drive its port.
int			DPxGetDinDataDir(void);									// Get 24-bit port direction mask
void		DPxSetDinDataOut(int dataOut);							// Set the data which should be driven on each port whose output has been enabled by DPxSetDinDataDir()
int			DPxGetDinDataOut(void);									// Get the data which is being driven on each output port
void		DPxSetDinDataOutStrength(double strength);				// Set strength of driven outputs.  Range is 0-1.  Implementation uses 1/16 up to 16/16.
double		DPxGetDinDataOutStrength(void);							// Get strength of driven outputs.  Range is 0-1.  Implementation uses 1/16 up to 16/16.
void		DPxEnableDinStabilize(void);							// DIN transitions are only recognized after entire DIN bus has been stable for 80 ns (good for deskewing parallel busses, and ignoring transmission line reflections).
void		DPxDisableDinStabilize(void);							// Immediately recognize all DIN transitions, possibly with debouncing.
int			DPxIsDinStabilize(void);								// Returns non-0 if DIN transitions are being stabilized
void		DPxEnableDinDebounce(void);								// When a DIN transitions, ignore further DIN transitions for next 30 milliseconds (good for response buttons)
void		DPxDisableDinDebounce(void);							// Immediately recognize all DIN transitions (after possible stabilization)
int			DPxIsDinDebounce(void);									// Returns non-0 if DIN transitions are being debounced
void		DPxEnableDoutDinLoopback(void);							// Enable loopback between digital output ports and digital inputs
void		DPxDisableDoutDinLoopback(void);						// Disable loopback between digital outputs and digital inputs
int			DPxIsDoutDinLoopback(void);								// Returns non-0 if digital inputs are driven by digital output ports
void		DPxSetDinBuffBaseAddr(unsigned buffBaseAddr);			// Set DIN RAM buffer start address.  Must be an even value.
unsigned	DPxGetDinBuffBaseAddr(void);							// Get DIN RAM buffer start address
void		DPxSetDinBuffWriteAddr(unsigned buffWriteAddr);			// Set RAM address to which next DIN datum will be written.  Must be an even value.
unsigned	DPxGetDinBuffWriteAddr(void);							// Get RAM address to which next DIN datum will be written
void		DPxSetDinBuffSize(unsigned buffSize);					// Set DIN RAM buffer size in bytes.  Must be an even value.  Buffer wraps after Size.
unsigned	DPxGetDinBuffSize(void);								// Get DIN RAM buffer size in bytes
void		DPxSetDinBuff(unsigned buffAddr, unsigned buffSize);	// Shortcut which assigns Size/BaseAddr/ReadAddr
void		DPxSetDinSchedOnset(unsigned onset);					// Set nanosecond delay between schedule start and first DIN sample
unsigned	DPxGetDinSchedOnset(void);								// Get nanosecond delay between schedule start and first DIN sample
void		DPxSetDinSchedRate(unsigned rateValue, int rateUnits);	// Set DIN schedule sample rate and units
																	// rateUnits is one of the following predefined constants:
																	//		DPXREG_SCHED_CTRL_RATE_HZ		: rateValue is samples per second, maximum 1 MHz
																	//		DPXREG_SCHED_CTRL_RATE_XVID		: rateValue is samples per video frame, maximum 1 MHz
																	//		DPXREG_SCHED_CTRL_RATE_NANO		: rateValue is sample period in nanoseconds, minimum 1000 ns
unsigned	DPxGetDinSchedRate(int *rateUnits);						// Get DIN schedule sample rate (and optionally get rate units)
void		DPxSetDinSchedCount(unsigned count);					// Set DIN schedule sample count
unsigned	DPxGetDinSchedCount(void);								// Get DIN schedule sample count
void		DPxEnableDinSchedCountdown(void);						// SchedCount decrements at SchedRate, and schedule stops automatically when count hits 0
void		DPxDisableDinSchedCountdown(void);						// SchedCount increments at SchedRate, and schedule is stopped by calling SchedStop
int			DPxIsDinSchedCountdown(void);							// Returns non-0 if SchedCount decrements to 0 and automatically stops schedule
void		DPxSetDinSched(unsigned onset, unsigned rateValue, int rateUnits, unsigned count);	// Shortcut which assigns Onset/Rate/Count. If Count > 0, enables Countdown mode.
void		DPxStartDinSched(void);									// Start running an DIN schedule
void		DPxStopDinSched(void);									// Stop running an DIN schedule
int			DPxIsDinSchedRunning(void);								// Returns non-0 if DIN schedule is currently running
void		DPxEnableDinLogTimetags(void);							// Each buffered DIN sample is preceeded with a 64-bit nanosecond timetag
void		DPxDisableDinLogTimetags(void);							// Buffered data has no timetags
int			DPxIsDinLogTimetags(void);								// Returns non-0 if buffered datasets are preceeded with nanosecond timetag
void		DPxEnableDinLogEvents(void);							// Each DIN transition is automatically logged (no schedule is required.  Best way to log response buttons)
void		DPxDisableDinLogEvents(void);							// Disable automatic logging of DIN transitions
int			DPxIsDinLogEvents(void);								// Returns non-0 if DIN transitions are being logged to RAM buffer

//	TOUCHPixx Subsystem	

int			DPxIsTouchpixx(void);									// 				
void		DPxEnableTouchpixx(void);								// 
void		DPxDisableTouchpixx(void);								// 

int			DPxIsTouchpixxLogContinuousMode(void);					// 
void		DPxEnableTouchpixxLogContinuousMode(void);				// 
void		DPxDisableTouchpixxLogContinuousMode(void);				// 

int			DPxIsTouchpixxLogEvents(void);							// 
void		DPxEnableTouchpixxLogEvents(void);						// 
void		DPxDisableTouchpixxLogEvents(void);						// 

int         DPxIsTouchpixxPressed(void);                            // Returns non-0 if touch panel is pressed
void		DPxGetTouchpixxCoords(int* x, int* y);                  // Get the current touch panel X/Y coordinates

void        DPxSetTouchpixxStabilizeDuration(double duration);      // Duration in seconds that TOUCHPixx coordinates must be stable before being recognized as a touch
double      DPxGetTouchpixxStabilizeDuration(void);


//	AUD (Audio Output) subsystem
//	The DATAPixx has a stereo output system, viewed as two output channels (Left/Right).
//	Data should be provided in 16-bit 2's complement format, typically as a playback schedule.
//	Typical schedule usage steps are the same as for DAC schedules.
//	An AUD buffer and schedule can supply data to both the Left/Right channels;
//	or, AUD can supply just the Left channel, and a second AUX buffer and schedule can supply the Right channel.
//	Use the AUX channel to implement separate RAM buffers for Left/Right data streams,
//	and separate schedule onset delays for Left/Right waveforms.
//
//	Call DPxInitAudCodec() once before other Aud/Mic routines, to configure initial audio CODEC state.
//	Can also call this at any time to return CODEC to its initial state.
//	Note that the first time this routine is called after reset,
//	it can pause up to 0.6 seconds while CODEC internal amplifiers are powering up.
//	This delay garantees that the CODEC is ready for stable playback immediately upon return.
void		DPxInitAudCodec(void);									// Call this once before other Aud/Mic routines to configure initial audio CODEC state

// There's really no point in manually setting audio output values.
// The hardware audio outputs are AC coupled,
// and even the register values slew to 0 when there is no audio schedule running
// (to prevent pop when next audio schedule starts).
void		DPxSetAudLeftValue(int value);							// Set the 16-bit 2's complement signed value for the Left audio output channel
void		DPxSetAudRightValue(int value);							// Set the 16-bit 2's complement signed value for the Right audio output channel
int			DPxGetAudLeftValue(void);								// Get the 16-bit 2's complement signed value for the Left audio output channel
int			DPxGetAudRightValue(void);								// Get the 16-bit 2's complement signed value for the Right audio output channel

			// The audio output API has two groups of volume control functions.
			// This first group digitally attenuates audio data within the FPGA _before_ sending it to the CODEC.
			// As such, volume manipulations here are very precise, and affect both the DATAPixx speaker and Audio OUT ports.
void		DPxSetAudLeftVolume(double volume);						// Set volume for the Left audio output channel, range 0-1
double		DPxGetAudLeftVolume(void);								// Get volume for the Left audio output channel, range 0-1
void		DPxSetAudRightVolume(double volume);					// Set volume for the Right audio output channel, range 0-1
double		DPxGetAudRightVolume(void);								// Get volume for the Right audio output channel, range 0-1
void		DPxSetAudVolume(double volume);							// Set volume for both Left/Right audio channels, range 0-1
double		DPxGetAudVolume(void);									// Get volume for both Left/Right audio channels (or Left channel, if Left/Right are different)
																	// The floating point volume parameter is in the range 0-1.
																	// The actual Left/Right volume controls are implemented as 16-bit unsigned FPGA registers.
																	// The audio samples read from the RAM buffer are multiplied by the volume registers
																	// (then right-shifted 16 bits) before forwarding the samples to the CODEC.
																	// Volume value 1.0 is a special case which bypasses this multiplication.
																	// NOTE: For safety's sake, reset value of L/R volumes = 0, so must set volume before playback.

			// The audio output API has two groups of volume control functions.
			// See the above paragraph for a description of the first group of volume control functions.
			// This second group uses CODEC internal registers to independently attenuate L/R audio outputs to the DATAPixx speaker and Audio OUT ports.
			// These CODEC volume registers have a precision (step size) of about 0.5 dB (see TI TLV320AIC32 datasheet for details).
			// These routines can use either ratio units (0 to 1), or the corresponding dB values (-inf to 0).
			// To minimize hiss, it is a good idea to do ball-park attenuation using these CODEC registers.
			// Then, for ultra-precise stimulus volume manipulation, use the above SetAudVolume() functions.
			// Those functions very precisely attenuate the digital audio data _before_ sending to the CODEC.
void		DPxSetAudCodecOutLeftVolume(double volume, int dBUnits);		// Set volume for the DATAPixx Audio OUT Left channel, range 0-1 (or dB)
double		DPxGetAudCodecOutLeftVolume(int dBUnits);						// Get volume for the DATAPixx Audio OUT Left channel, range 0-1 (or dB)
void		DPxSetAudCodecOutRightVolume(double volume, int dBUnits);		// Set volume for the DATAPixx Audio OUT Right channel, range 0-1 (or dB)
double		DPxGetAudCodecOutRightVolume(int dBUnits);						// Get volume for the DATAPixx Audio OUT Right channel, range 0-1 (or dB)
void		DPxSetAudCodecOutVolume(double volume, int dBUnits);			// Set volume for the DATAPixx Audio OUT Left and Right channels, range 0-1 (or dB)
double		DPxGetAudCodecOutVolume(int dBUnits);							// Get volume for the DATAPixx Audio OUT Left and Right channels (or Left channel, if Left/Right are different)
void		DPxSetAudCodecSpeakerLeftVolume(double volume, int dBUnits);	// Set volume for the DATAPixx Speaker Left channel, range 0-1 (or dB)
double		DPxGetAudCodecSpeakerLeftVolume(int dBUnits);					// Get volume for the DATAPixx Speaker Left channel, range 0-1 (or dB)
void		DPxSetAudCodecSpeakerRightVolume(double volume, int dBUnits);	// Set volume for the DATAPixx Speaker Right channel, range 0-1 (or dB)
double		DPxGetAudCodecSpeakerRightVolume(int dBUnits);					// Get volume for the DATAPixx Speaker Right channel, range 0-1 (or dB)
void		DPxSetAudCodecSpeakerVolume(double volume, int dBUnits);		// Set volume for the DATAPixx Speaker Left and Right channels, range 0-1 (or dB)
double		DPxGetAudCodecSpeakerVolume(int dBUnits);						// Get volume for the DATAPixx Speaker Left and Right channels (or Left channel, if Left/Right are different)

void		DPxSetAudLRMode(int lrMode);							// Configure how audio Left/Right channels are updated by schedule data
																	// lrMode is one of the following predefined constants:
																	//		DPXREG_AUD_CTRL_LRMODE_MONO		: Each AUD schedule datum goes to left and right channels
																	//		DPXREG_AUD_CTRL_LRMODE_LEFT		: Each AUD schedule datum goes to left channel only
																	//		DPXREG_AUD_CTRL_LRMODE_RIGHT	: Each AUD schedule datum goes to right channel only
																	//		DPXREG_AUD_CTRL_LRMODE_STEREO_1	: Pairs of AUD data are copied to left/right channels
																	//		DPXREG_AUD_CTRL_LRMODE_STEREO_2	: AUD data goes to left channel, AUX data goes to right
int			DPxGetAudLRMode(void);									// Get the audio Left/Right configuration mode
void		DPxSetAudBuffBaseAddr(unsigned buffBaseAddr);			// Set AUD RAM buffer start address.  Must be an even value.
unsigned	DPxGetAudBuffBaseAddr(void);							// Get AUD RAM buffer start address
void		DPxSetAudBuffReadAddr(unsigned buffReadAddr);			// Set RAM address from which next AUD datum will be read.  Must be an even value.
unsigned	DPxGetAudBuffReadAddr(void);							// Get RAM address from which next AUD datum will be read
void		DPxSetAudBuffSize(unsigned buffSize);					// Set AUD RAM buffer size in bytes.  Must be an even value.  Buffer wraps to Base after Size.
unsigned	DPxGetAudBuffSize(void);								// Get AUD RAM buffer size in bytes
void		DPxSetAudBuff(unsigned buffAddr, unsigned buffSize);	// Shortcut which assigns Size/BaseAddr/ReadAddr
void		DPxSetAuxBuffBaseAddr(unsigned buffBaseAddr);			// Set AUX RAM buffer start address.  Must be an even value.
unsigned	DPxGetAuxBuffBaseAddr(void);							// Get AUX RAM buffer start address
void		DPxSetAuxBuffReadAddr(unsigned buffReadAddr);			// Set RAM address from which next AUX datum will be read.  Must be an even value.
unsigned	DPxGetAuxBuffReadAddr(void);							// Get RAM address from which next AUX datum will be read
void		DPxSetAuxBuffSize(unsigned buffSize);					// Set AUX RAM buffer size in bytes.  Must be an even value.  Buffer wraps to Base after Size.
unsigned	DPxGetAuxBuffSize(void);								// Get AUX RAM buffer size in bytes
void		DPxSetAuxBuff(unsigned buffAddr, unsigned buffSize);	// Shortcut which assigns Size/BaseAddr/ReadAddr
void		DPxSetAudSchedOnset(unsigned onset);					// Set nanosecond delay between schedule start and first AUD update
unsigned	DPxGetAudSchedOnset(void);								// Get nanosecond delay between schedule start and first AUD update
void		DPxSetAudSchedRate(unsigned rateValue, int rateUnits);	// Set AUD (and AUX) schedule update rate and units
																	// rateUnits is one of the following predefined constants:
																	//		DPXREG_SCHED_CTRL_RATE_HZ		: rateValue is updates per second, maximum 96 kHz
																	//		DPXREG_SCHED_CTRL_RATE_XVID		: rateValue is updates per video frame, maximum 96 kHz
																	//		DPXREG_SCHED_CTRL_RATE_NANO		: rateValue is update period in nanoseconds, minimum 10417 ns
unsigned	DPxGetAudSchedRate(int *rateUnits);						// Get AUD schedule update rate (and optionally get rate units)
void		DPxSetAudSchedCount(unsigned count);					// Set AUD schedule update count
unsigned	DPxGetAudSchedCount(void);								// Get AUD schedule update count
void		DPxEnableAudSchedCountdown(void);						// SchedCount decrements at SchedRate, and schedule stops automatically when count hits 0
void		DPxDisableAudSchedCountdown(void);						// SchedCount increments at SchedRate, and schedule is stopped by calling SchedStop
int			DPxIsAudSchedCountdown(void);							// Returns non-0 if SchedCount decrements to 0 and automatically stops schedule
void		DPxSetAudSched(unsigned onset, unsigned rateValue, int rateUnits, unsigned count);	// Shortcut which assigns Onset/Rate/Count. If Count > 0, enables Countdown mode.
void		DPxStartAudSched(void);									// Start running a AUD schedule
void		DPxStopAudSched(void);									// Stop running a AUD schedule
int			DPxIsAudSchedRunning(void);								// Returns non-0 if AUD schedule is currently running
void		DPxSetAuxSchedOnset(unsigned onset);					// Set nanosecond delay between schedule start and first AUX update
unsigned	DPxGetAuxSchedOnset(void);								// Get nanosecond delay between schedule start and first AUX update
void		DPxSetAuxSchedRate(unsigned rateValue, int rateUnits);	// Set AUX (and AUD) schedule update rate and units
																	// rateUnits is one of the following predefined constants:
																	//		DPXREG_SCHED_CTRL_RATE_HZ		: rateValue is updates per second, maximum 96 kHz
																	//		DPXREG_SCHED_CTRL_RATE_XVID		: rateValue is updates per video frame, maximum 96 kHz
																	//		DPXREG_SCHED_CTRL_RATE_NANO		: rateValue is update period in nanoseconds, minimum 10417 ns
unsigned	DPxGetAuxSchedRate(int *rateUnits);						// Get AUX schedule update rate (and optionally get rate units)
void		DPxSetAuxSchedCount(unsigned count);					// Set AUX schedule update count
unsigned	DPxGetAuxSchedCount(void);								// Get AUX schedule update count
void		DPxEnableAuxSchedCountdown(void);						// SchedCount decrements at SchedRate, and schedule stops automatically when count hits 0
void		DPxDisableAuxSchedCountdown(void);						// SchedCount increments at SchedRate, and schedule is stopped by calling SchedStop
int			DPxIsAuxSchedCountdown(void);							// Returns non-0 if SchedCount decrements to 0 and automatically stops schedule
void		DPxSetAuxSched(unsigned onset, unsigned rateValue, int rateUnits, unsigned count);	 // Shortcut which assigns Onset/Rate/Count. If Count > 0, enables Countdown mode.
void		DPxStartAuxSched(void);									// Start running a AUX schedule
void		DPxStopAuxSched(void);									// Stop running a AUX schedule
int			DPxIsAuxSchedRunning(void);								// Returns non-0 if AUX schedule is currently running

double		DPxGetAudGroupDelay(double sampleRate);					// Returns CODEC Audio OUT group delay in seconds

//	MIC (Microphone/Audio Input) subsystem.
//	The DATAPixx has a stereo microphone input system, viewed as two input channels (Left/Right).
//	Data is returned in 16-bit 2's complement format.
//	Typical usage steps for MIC schedules are the same as for ADC schedules.
//	DPxInitAudCodec() must be called once before using any other Aud/Mic routines.
//	MIC data can actually come from two electrical sources.
//	One is a high-impedance microphone input with 2V bias.  This is for unpowered microphones.
//	Second is a line level (1V RMS) audio input for connection to powered microphones,
//	or any standard line out from audio equipment.
//	NOTE: MIC and AUD subsystem share timing resources within CODEC,
//	so MIC and AUD must have the same rate.
//	Calling DPxSetMicSchedRate() or DPxSetMicSched() also indirectly calls DPxSetAudSchedRate().
void		DPxSetMicSource(int source, double gain, int dBUnits);	// Select the source and gain of the microphone input
																	// source is one of the following predefined constants:
																	//		DPX_MIC_SRC_MIC_IN	: Microphone level input
																	//		DPX_MIC_SRC_LINE_IN	: Line level input
int			DPxGetMicSource(double *gain, int dBUnits);				// Get the source (and optionally the gain) of the microphone input
int			DPxGetMicLeftValue(void);								// Get the 16-bit 2's complement signed value for left MIC channel
int			DPxGetMicRightValue(void);								// Get the 16-bit 2's complement signed value for right MIC channel
void		DPxSetMicLRMode(int lrMode);							// Configure how microphone Left/Right channels are stored to schedule buffer
																	// lrMode is one of the following predefined constants:
																	//		DPXREG_MIC_CTRL_LRMODE_MONO		: Mono data is written to schedule buffer (average of Left/Right CODEC data)
																	//		DPXREG_MIC_CTRL_LRMODE_LEFT		: Left data is written to schedule buffer
																	//		DPXREG_MIC_CTRL_LRMODE_RIGHT	: Right data is written to schedule buffer
																	//		DPXREG_MIC_CTRL_LRMODE_STEREO	: Left and Right data are both written to schedule buffer
int			DPxGetMicLRMode(void);									// Get the microphone Left/Right configuration mode
void		DPxEnableAudMicLoopback(void);							// Enable loopback between audio outputs and microphone inputs
void		DPxDisableAudMicLoopback(void);							// Disable loopback between audio outputs and microphone inputs
int			DPxIsAudMicLoopback(void);								// Returns non-0 if microphone inputs are driven by audio outputs
void		DPxSetMicBuffBaseAddr(unsigned buffBaseAddr);			// Set MIC RAM buffer start address.  Must be an even value.
unsigned	DPxGetMicBuffBaseAddr(void);							// Get MIC RAM buffer start address
void		DPxSetMicBuffWriteAddr(unsigned buffWriteAddr);			// Set RAM address to which next MIC datum will be written.  Must be an even value.
unsigned	DPxGetMicBuffWriteAddr(void);							// Get RAM address to which next MIC datum will be written
void		DPxSetMicBuffSize(unsigned buffSize);					// Set MIC RAM buffer size in bytes.  Must be an even value.  Buffer wraps after Size.
unsigned	DPxGetMicBuffSize(void);								// Get MIC RAM buffer size in bytes
void		DPxSetMicBuff(unsigned buffAddr, unsigned buffSize);	// Shortcut which assigns Size/BaseAddr/ReadAddr
void		DPxSetMicSchedOnset(unsigned onset);					// Set nanosecond delay between schedule start and first MIC sample
unsigned	DPxGetMicSchedOnset(void);								// Get nanosecond delay between schedule start and first MIC sample
void		DPxSetMicSchedRate(unsigned rateValue, int rateUnits);	// Set MIC schedule sample rate and units
																	// rateUnits is one of the following predefined constants:
																	//		DPXREG_SCHED_CTRL_RATE_HZ		: rateValue is samples per second, maximum 102.4 kHz
																	//		DPXREG_SCHED_CTRL_RATE_XVID		: rateValue is samples per video frame, maximum 102.4 kHz
																	//		DPXREG_SCHED_CTRL_RATE_NANO		: rateValue is sample period in nanoseconds, minimum 9750 ns
unsigned	DPxGetMicSchedRate(int *rateUnits);						// Get MIC schedule sample rate (and optionally get rate units)
void		DPxSetMicSchedCount(unsigned count);					// Set MIC schedule sample count
unsigned	DPxGetMicSchedCount(void);								// Get MIC schedule sample count
void		DPxEnableMicSchedCountdown(void);						// SchedCount decrements at SchedRate, and schedule stops automatically when count hits 0
void		DPxDisableMicSchedCountdown(void);						// SchedCount increments at SchedRate, and schedule is stopped by calling SchedStop
int			DPxIsMicSchedCountdown(void);							// Returns non-0 if SchedCount decrements to 0 and automatically stops schedule
void		DPxSetMicSched(unsigned onset, unsigned rateValue, int rateUnits, unsigned count);	// Shortcut which assigns Onset/Rate/Count. If Count > 0, enables Countdown mode.
void		DPxStartMicSched(void);									// Start running an MIC schedule
void		DPxStopMicSched(void);									// Stop running an MIC schedule
int			DPxIsMicSchedRunning(void);								// Returns non-0 if MIC schedule is currently running

double		DPxGetMicGroupDelay(double sampleRate);					// Returns CODEC MIC IN group delay in seconds

//	Video subsystem
void		DPxSetVidMode(int vidMode);								// Set the video processing mode
																	// vidMode is one of the following predefined constants:
																	//		DPREG_VID_CTRL_MODE_C24		Straight passthrough from DVI 8-bit (or HDMI "deep" 10/12-bit) RGB to VGA 8/10/12-bit RGB
																	//		DPREG_VID_CTRL_MODE_L48		DVI RED[7:0] is used as an index into a 256-entry 16-bit RGB colour lookup table
																	//		DPREG_VID_CTRL_MODE_M16		DVI RED[7:0] & GREEN[7:0] concatenate into a VGA 16-bit value sent to all three RGB components
																	//		DPREG_VID_CTRL_MODE_C48		Even/Odd pixel RED/GREEN/BLUE[7:0] concatenate to generate 16-bit RGB components at half the horizontal resolution
																	//		DPREG_VID_CTRL_MODE_L48D	DVI RED[7:4] & GREEN[7:4] concatenate to form an 8-bit index into a 256-entry 16-bit RGB colour lookup table
																	//		DPREG_VID_CTRL_MODE_M16D	DVI RED[7:3] & GREEN[7:3] & BLUE[7:2] concatenate into a VGA 16-bit value sent to all three RGB components
																	//		DPREG_VID_CTRL_MODE_C36D	Even/Odd pixel RED/GREEN/BLUE[7:2] concatenate to generate 12-bit RGB components at half the horizontal resolution
int			DPxGetVidMode(void);									// Get the video processing mode
void		DPxSetVidClut(UInt16* clutData);						// Pass 256*3 (=768) 16-bit video DAC data, in order R0,G0,B0,R1,G1,B1...
																	// DPxSetVidClut() returns immediately, and CLUT is implemented at next vertical blanking interval.
void		DPxSetVidCluts(UInt16* clutData);						// Pass 512*3 (=1536) 16-bit video DAC data to fill 2 channel CLUTs with independent data, in order R0,G0,B0,R1,G1,B1...
void		DPxEnableVidHorizSplit(void);							// VGA 1 shows left half of video image, VGA 2 shows right half of video image.  The two VGA outputs are perfectly synchronized.
void		DPxDisableVidHorizSplit(void);							// VGA 1 and VGA 2 both show entire video image (hardware video mirroring)
void		DPxAutoVidHorizSplit(void);								// DATAPixx will automatically split video across the two VGA outputs if the horizontal resolution is at least twice the vertical resolution (default mode)
int			DPxIsVidHorizSplit(void);								// Returns non-0 if video is being split across the two VGA outputs.
void		DPxEnableVidVertStereo(void);							// Top/bottom halves of input image are output in two sequencial video frames.
																	// VESA L/R output is set to 1 when first frame (left eye) is displayed,
																	// and set to 0 when second frame (right eye) is displayed.
void		DPxDisableVidVertStereo(void);							// Normal display
void		DPxAutoVidVertStereo(void);								// Vertical stereo is enabled automatically when vertical resolution > horizontal resolution (default mode)
int			DPxIsVidVertStereo(void);								// Returns non-0 if DATAPixx is separating input into sequencial left/right stereo images.
void		DPxEnableVidHorizOverlay(void);							// VGA 1 and VGA 2 both show an overlay composite of the left/right halves of the video image
void		DPxDisableVidHorizOverlay(void);						// Horizontal overlay is disabled
int			DPxIsVidHorizOverlay(void);								// Returns non-0 if the left/right halves of the video image are being overlayed
void		DPxSetVidHorizOverlayBounds(int X1, int Y1, int X2, int Y2); // Set bounding rectangle within left half image whose contents are composited with right half image
void		DPxGetVidHorizOverlayBounds(int* X1, int* Y1, int* X2, int* Y2); // Get bounding rectangle of horizontal overlay window
void		DPxSetVidHorizOverlayAlpha(UInt16* alphaData);			// Set 1024 16-bit video horizontal overlay alpha values, in order X0,X1..X511,Y0,Y1...Y511
int			DPxGetVidHTotal(void);									// Get number of video dot times in one horizontal scan line (includes horizontal blanking interval)
int			DPxGetVidVTotal(void);									// Get number of video lines in one vertical frame (includes vertical blanking interval)
int			DPxGetVidHActive(void);									// Get number of visible pixels in one horizontal scan line
int			DPxGetVidVActive(void);									// Get number of visible lines in one vertical frame
unsigned	DPxGetVidVPeriod(void);									// Get video vertical frame period in nanoseconds
double		DPxGetVidVFreq(void);									// Get video vertical frame rate in Hz
double		DPxGetVidHFreq(void);									// Get video horizontal line rate in Hz
double		DPxGetVidDotFreq(void);									// Get video dot frequency in Hz
int			DPxIsVidDviActive(void);								// Returns non-0 if DATAPixx is currently receiving video data over DVI link
int			DPxIsVidDviActiveDual(void);							// Returns non-0 if DATAPixx is currently receiving video data over dual-link DVI
int         DPxIsVidDviLockable(void);                              // Returns non-0 if VIEWPixx is currently receiving video whose timing can directly drive display.
int			DPxIsVidOverClocked(void);								// Returns non-0 if DATAPixx is receiving video at too high a clock frequency
void		DPxSetVidVesaLeft(void);								// VESA connector outputs left-eye signal
void		DPxSetVidVesaRight(void);								// VESA connector outputs right-eye signal
int			DPxIsVidVesaLeft(void);									// Returns non-0 if VESA connector has left-eye signal
void		DPxEnableVidVesaBlueline(void);                         // VESA 3D output interprets middle pixel on last raster line as a blueline code
void		DPxDisableVidVesaBlueline(void);						// VESA 3D output is not dependent on video content
int			DPxIsVidVesaBlueline(void);								// Returns non-0 if VESA 3D output is dependent on video blueline codes
void        DPxSetVidVesaWaveform(int waveform);                    // Set the waveform which will be sent to the DATAPixx VESA 3D connector
                                                                    // waveform is one of the following predefined constants:
                                                                    //      DPXREG_VID_VESA_WAVEFORM_LR             : VESA port drives straight L/R squarewave for 3rd party emitter
                                                                    //      DPXREG_VID_VESA_WAVEFORM_CRYSTALEYES    : VESA port drives 3DPixx IR emitter for CrystalEyes 3D goggles
                                                                    //      DPXREG_VID_VESA_WAVEFORM_NVIDIA         : VESA port drives 3DPixx IR emitter for NVIDIA 3D goggles
int         DPxGetVidVesaWaveform(void);                            // Get the waveform which is being sent to the DATAPixx VESA 3D connector
void        DPxSetVidVesaPhase(int phase);                          // Set the 8-bit unsigned phase of the VESA 3D waveform
                                                                    // Varying this phase from 0-255 will fine tune phase relationship between stereo video and 3D goggle switching
                                                                    // The following combinations have been found to work well:
                                                                    // Waveform=DPXREG_VID_VESA_WAVEFORM_NVIDIA, Phase=100, for VIEWPixx/3D + scanning backlight + 3DPixx IR emitter + NVIDIA 3D Vision glasses
                                                                    // Waveform=DPXREG_VID_VESA_WAVEFORM_NVIDIA, Phase=245, for DATAPixx + CRT + 3DPixx IR emitter + NVIDIA 3D Vision glasses
                                                                    // Waveform=DPXREG_VID_VESA_WAVEFORM_CRYSTALEYES, Phase=100, for VIEWPixx/3D + scanning backlight + 3DPixx  IR emitter + CrystalEyes glasses

int         DPxGetVidVesaPhase(void);                               // Get the 8-bit unsigned phase of the VESA 3D waveform
UInt16*		DPxGetVidLine(void);									// Read pixels from the DATAPixx line buffer, and return a pointer to the data.
																	// For each pixel, the buffer contains 16 bit R/G/B/U (where U is unused).
																	// The returned data could be overwritten by the next DPx* call, so copy data if needed.
void		DPxSetVidPsyncRasterLine(int line);						// Set the raster line on which pixel sync sequence is expected
int			DPxGetVidPsyncRasterLine(void);							// Get the raster line on which pixel sync sequence is expected
void		DPxEnableVidPsyncSingleLine(void);						// Pixel sync is only recognized on a single raster line
void		DPxDisableVidPsyncSingleLine(void);						// Pixel sync is recognized on any raster line
int			DPxIsVidPsyncSingleLine(void);							// Returns non-0 if pixel sync is only recognized on a single raster line
void		DPxEnableVidPsyncBlankLine(void);						// Pixel sync raster line is always displayed black
void		DPxDisableVidPsyncBlankLine(void);						// Pixel sync raster line is displayed normally
int			DPxIsVidPsyncBlankLine(void);							// Returns non-0 if pixel sync raster line is always displayed black
void        DPxSetVidSource(int vidSource);                         // Set source of video pattern to be displayed
int         DPxGetVidSource(void);                                  // Get source of video pattern being displayed
void        DPxEnableVidScanningBacklight(void);                    // Enable VIEWPixx scanning backlight
void        DPxDisableVidScanningBacklight(void);                   // Disable VIEWPixx scanning backlight
int         DPxIsVidScanningBacklight(void);                        // Returns non-0 if VIEWPixx scanning backlight is enabled
void        DPxVideoScope(int toFile);                              // VIEWPixx video source analysis

//	-If an API function detects an error, it will assign a unique error code to a global error variable.
//	This strategy permits DPxGet*() functions to conveniently return requested values directly,
//	and still make available a global error code which can be checked when desired.
void		DPxSetError(int error);
void		DPxClearError(void);
int			DPxGetError(void);


//	-Debugging level controls verbosity of debug and trace messages.
//	Set to:
//		0 to disabled messages
//		1 to print libdpx debug messages
//		2 to also print libusb debug messages
void		DPxSetDebug(int level);
int			DPxGetDebug(void);


// Save/RestoreRegs can be used to save and restore the DATAPixx register state.
// Note that these routines use a single local copy (not a stack), so only do 1-deep save/restore.
void		DPxSaveRegs(void);										// Get all DATAPixx registers, and save them in a local copy
void		DPxRestoreRegs(void);									// Write the local copy back to the DATAPixx


// Miscellaneous routines
void		DPxStopAllScheds(void);									// Shortcut to stop running all DAC/ADC/DOUT/DIN/AUD/AUX/MIC schedules


//	-API global error codes
//	Pretty much each API function usage error sets a unique global error code for easier debugging of user apps
#define DPX_SUCCESS								0		// Function executed successfully
#define DPX_FAIL								-1		// Generic failure code

#define DPX_ERR_USB_NO_DATAPIXX					-1000	// No DATAPixx was found
#define DPX_ERR_USB_RAW_EZUSB					-1001	// EZ-USB appears to have no firmware
#define DPX_ERR_USB_RAW_FPGA					-1002	// FPGA appears to be unconfigured
#define DPX_ERR_USB_OPEN						-1003	// An error occurred while opening a USB channel
#define DPX_ERR_USB_OPEN_FPGA					-1004	// An FPGA detection error occurred while opening DATAPixx
#define DPX_ERR_USB_SET_CONFIG					-1005	// Could not set the USB configuration
#define DPX_ERR_USB_CLAIM_INTERFACE				-1006	// Could not claim the USB interface
#define DPX_ERR_USB_ALT_INTERFACE				-1007	// Could not set the USB alternate interface
#define DPX_ERR_USB_UNKNOWN_DPID				-1008	// Unrecognized DATAPixx ID register value
#define DPX_ERR_USB_REG_BULK_WRITE				-1009	// USB error while writing register set
#define DPX_ERR_USB_REG_BULK_READ				-1010	// USB error while reading register set

#define DPX_ERR_SPI_START						-1100	// SPI communication startup error
#define DPX_ERR_SPI_STOP						-1101	// SPI communication termination error
#define DPX_ERR_SPI_READ						-1102	// SPI communication read error
#define DPX_ERR_SPI_WRITE						-1103	// SPI communication write error
#define DPX_ERR_SPI_ERASE						-1104	// SPI communication erase error
#define DPX_ERR_SPI_WAIT_DONE					-1105	// SPI communication error while waiting for SPI write to complete

#define DPX_ERR_SETREG16_ADDR_ODD				-1200	// DPxSetReg16 passed an odd address
#define DPX_ERR_SETREG16_ADDR_RANGE				-1201	// DPxSetReg16 passed an address which was out of range
#define DPX_ERR_SETREG16_DATA_RANGE				-1202	// DPxSetReg16 passed a datum which was out of range
#define DPX_ERR_GETREG16_ADDR_ODD				-1203	// DPxGetReg16 passed an odd address
#define DPX_ERR_GETREG16_ADDR_RANGE				-1204	// DPxGetReg16 passed an address which was out of range
#define DPX_ERR_SETREG32_ADDR_ALIGN				-1205	// DPxSetReg32 passed an address which was not 32-bit aligned
#define DPX_ERR_SETREG32_ADDR_RANGE				-1206	// DPxSetReg32 passed an address which was out of range
#define DPX_ERR_GETREG32_ADDR_ALIGN				-1207	// DPxGetReg32 passed an address which was not 32-bit aligned
#define DPX_ERR_GETREG32_ADDR_RANGE				-1208	// DPxGetReg32 passed an address which was out of range

#define DPX_ERR_NANO_TIME_NULL_PTR				-1300	// A pointer argument was null
#define DPX_ERR_NANO_MARK_NULL_PTR				-1301	// A pointer argument was null
#define DPX_ERR_UNKNOWN_PART_NUMBER				-1302	// Unrecognized part number

#define DPX_ERR_RAM_UNKNOWN_SIZE				-1400	// Unrecognized RAM configuration
#define DPX_ERR_RAM_WRITEREAD_FAIL				-1401	// RAM read did not return same value written
#define DPX_ERR_RAM_WRITE_ADDR_ODD				-1402	// RAM write buffer address must be even
#define DPX_ERR_RAM_WRITE_LEN_ODD				-1403	// RAM write buffer length must be even
#define DPX_ERR_RAM_WRITE_TOO_HIGH				-1404	// RAM write block exceeds end of DATAPixx memory
#define DPX_ERR_RAM_WRITE_BUFFER_NULL			-1405	// RAM write source buffer pointer is null
#define DPX_ERR_RAM_WRITE_USB_ERROR				-1406	// A USB error occurred while writing the RAM buffer
#define DPX_ERR_RAM_READ_ADDR_ODD				-1407	// RAM read buffer address must be even
#define DPX_ERR_RAM_READ_LEN_ODD				-1408	// RAM read buffer length must be even
#define DPX_ERR_RAM_READ_TOO_HIGH				-1409	// RAM read block exceeds end of DATAPixx memory
#define DPX_ERR_RAM_READ_BUFFER_NULL			-1410	// RAM read destination buffer pointer is null
#define DPX_ERR_RAM_READ_USB_ERROR				-1411	// A USB error occurred while reading the RAM buffer

#define DPX_ERR_DAC_SET_BAD_CHANNEL				-1500	// Valid channels are 0-3
#define DPX_ERR_DAC_SET_BAD_VALUE				-1501	// Value falls outside DAC's output range
#define DPX_ERR_DAC_GET_BAD_CHANNEL				-1502	// Valid channels are 0-3
#define DPX_ERR_DAC_RANGE_NULL_PTR				-1503	// A pointer argument was null
#define DPX_ERR_DAC_RANGE_BAD_CHANNEL			-1504	// Valid channels are 0-3
#define DPX_ERR_DAC_BUFF_BAD_CHANNEL			-1505	// Valid channels are 0-3
#define DPX_ERR_DAC_BUFF_ODD_BASEADDR			-1506	// An odd buffer base was requested
#define DPX_ERR_DAC_BUFF_BASEADDR_TOO_HIGH		-1507	// The requested buffer is larger than the DATAPixx RAM
#define DPX_ERR_DAC_BUFF_ODD_READADDR			-1508	// An odd buffer read address was requested
#define DPX_ERR_DAC_BUFF_READADDR_TOO_HIGH		-1509	// The requested read address exceeds the DATAPixx RAM
#define DPX_ERR_DAC_BUFF_ODD_WRITEADDR			-1510	// An odd buffer write address was requested
#define DPX_ERR_DAC_BUFF_WRITEADDR_TOO_HIGH		-1511	// The requested write address exceeds the DATAPixx RAM
#define DPX_ERR_DAC_BUFF_ODD_SIZE				-1512	// An odd buffer size was requested
#define DPX_ERR_DAC_BUFF_TOO_BIG				-1513	// The requested buffer is larger than the DATAPixx RAM
#define DPX_ERR_DAC_SCHED_TOO_FAST				-1514	// The requested schedule rate is too fast
#define DPX_ERR_DAC_SCHED_BAD_RATE_UNITS		-1515	// Unnrecognized schedule rate units parameter

#define DPX_ERR_ADC_GET_BAD_CHANNEL				-1600	// Valid channels are 0-17
#define DPX_ERR_ADC_RANGE_NULL_PTR				-1601	// A pointer argument was null
#define DPX_ERR_ADC_RANGE_BAD_CHANNEL			-1602	// Valid channels are 0-17
#define DPX_ERR_ADC_REF_BAD_CHANNEL				-1603	// Valid channels are 0-15
#define DPX_ERR_ADC_BAD_CHAN_REF				-1604	// Unrecognized channel reference parameter
#define DPX_ERR_ADC_BUFF_BAD_CHANNEL			-1605	// Valid channels are 0-15
#define DPX_ERR_ADC_BUFF_ODD_BASEADDR			-1606	// An odd buffer base was requested
#define DPX_ERR_ADC_BUFF_BASEADDR_TOO_HIGH		-1607	// The requested buffer is larger than the DATAPixx RAM
#define DPX_ERR_ADC_BUFF_ODD_READADDR			-1608	// An odd buffer read address was requested
#define DPX_ERR_ADC_BUFF_READADDR_TOO_HIGH		-1609	// The requested read address exceeds the DATAPixx RAM
#define DPX_ERR_ADC_BUFF_ODD_WRITEADDR			-1610	// An odd buffer write address was requested
#define DPX_ERR_ADC_BUFF_WRITEADDR_TOO_HIGH		-1611	// The requested write address exceeds the DATAPixx RAM
#define DPX_ERR_ADC_BUFF_ODD_SIZE				-1612	// An odd buffer size was requested
#define DPX_ERR_ADC_BUFF_TOO_BIG				-1613	// The requested buffer is larger than the DATAPixx RAM
#define DPX_ERR_ADC_SCHED_TOO_FAST				-1614	// The requested schedule rate is too fast
#define DPX_ERR_ADC_SCHED_BAD_RATE_UNITS		-1615	// Unnrecognized schedule rate units parameter

#define DPX_ERR_DOUT_SET_BAD_MASK				-1700	// Valid masks set bits 23 downto 0
#define DPX_ERR_DOUT_BUFF_ODD_BASEADDR			-1701	// An odd buffer base was requested
#define DPX_ERR_DOUT_BUFF_BASEADDR_TOO_HIGH		-1702	// The requested buffer is larger than the DATAPixx RAM
#define DPX_ERR_DOUT_BUFF_ODD_READADDR			-1703	// An odd buffer read address was requested
#define DPX_ERR_DOUT_BUFF_READADDR_TOO_HIGH		-1704	// The requested read address exceeds the DATAPixx RAM
#define DPX_ERR_DOUT_BUFF_ODD_WRITEADDR			-1705	// An odd buffer write address was requested
#define DPX_ERR_DOUT_BUFF_WRITEADDR_TOO_HIGH	-1706	// The requested write address exceeds the DATAPixx RAM
#define DPX_ERR_DOUT_BUFF_ODD_SIZE				-1707	// An odd buffer size was requested
#define DPX_ERR_DOUT_BUFF_TOO_BIG				-1708	// The requested buffer is larger than the DATAPixx RAM
#define DPX_ERR_DOUT_SCHED_TOO_FAST				-1709	// The requested schedule rate is too fast
#define DPX_ERR_DOUT_SCHED_BAD_RATE_UNITS		-1710	// Unnrecognized schedule rate units parameter

#define DPX_ERR_DIN_SET_BAD_MASK				-1800	// Valid masks set bits 23 downto 0
#define DPX_ERR_DIN_BUFF_ODD_BASEADDR			-1801	// An odd buffer base was requested
#define DPX_ERR_DIN_BUFF_BASEADDR_TOO_HIGH		-1802	// The requested buffer is larger than the DATAPixx RAM
#define DPX_ERR_DIN_BUFF_ODD_READADDR			-1803	// An odd buffer read address was requested
#define DPX_ERR_DIN_BUFF_READADDR_TOO_HIGH		-1804	// The requested read address exceeds the DATAPixx RAM
#define DPX_ERR_DIN_BUFF_ODD_WRITEADDR			-1805	// An odd buffer write address was requested
#define DPX_ERR_DIN_BUFF_WRITEADDR_TOO_HIGH		-1806	// The requested write address exceeds the DATAPixx RAM
#define DPX_ERR_DIN_BUFF_ODD_SIZE				-1807	// An odd buffer size was requested
#define DPX_ERR_DIN_BUFF_TOO_BIG				-1808	// The requested buffer is larger than the DATAPixx RAM
#define DPX_ERR_DIN_SCHED_TOO_FAST				-1809	// The requested schedule rate is too fast
#define DPX_ERR_DIN_SCHED_BAD_RATE_UNITS		-1810	// Unnrecognized schedule rate units parameter
#define DPX_ERR_DIN_BAD_STRENGTH				-1811	// Strength is in the range 0-1

#define DPX_ERR_AUD_SET_BAD_VALUE				-1900	// Value falls outside AUD's output range
#define DPX_ERR_AUD_SET_BAD_VOLUME				-1901	// Valid volumes are in the range 0-1
#define DPX_ERR_AUD_SET_BAD_LRMODE				-1902	// See DPxSetAudLRMode() for valid values
#define DPX_ERR_AUD_BUFF_ODD_BASEADDR			-1903	// An odd buffer base was requested
#define DPX_ERR_AUD_BUFF_BASEADDR_TOO_HIGH		-1904	// The requested buffer is larger than the DATAPixx RAM
#define DPX_ERR_AUD_BUFF_ODD_READADDR			-1905	// An odd buffer read address was requested
#define DPX_ERR_AUD_BUFF_READADDR_TOO_HIGH		-1906	// The requested read address exceeds the DATAPixx RAM
#define DPX_ERR_AUD_BUFF_ODD_WRITEADDR			-1907	// An odd buffer write address was requested
#define DPX_ERR_AUD_BUFF_WRITEADDR_TOO_HIGH		-1908	// The requested write address exceeds the DATAPixx RAM
#define DPX_ERR_AUD_BUFF_ODD_SIZE				-1909	// An odd buffer size was requested
#define DPX_ERR_AUD_BUFF_TOO_BIG				-1910	// The requested buffer is larger than the DATAPixx RAM
#define DPX_ERR_AUX_BUFF_ODD_BASEADDR			-1911	// An odd buffer base was requested
#define DPX_ERR_AUX_BUFF_BASEADDR_TOO_HIGH		-1912	// The requested buffer is larger than the DATAPixx RAM
#define DPX_ERR_AUX_BUFF_ODD_READADDR			-1913	// An odd buffer read address was requested
#define DPX_ERR_AUX_BUFF_READADDR_TOO_HIGH		-1914	// The requested read address exceeds the DATAPixx RAM
#define DPX_ERR_AUX_BUFF_ODD_WRITEADDR			-1915	// An odd buffer write address was requested
#define DPX_ERR_AUX_BUFF_WRITEADDR_TOO_HIGH		-1916	// The requested write address exceeds the DATAPixx RAM
#define DPX_ERR_AUX_BUFF_ODD_SIZE				-1917	// An odd buffer size was requested
#define DPX_ERR_AUX_BUFF_TOO_BIG				-1918	// The requested buffer is larger than the DATAPixx RAM
#define DPX_ERR_AUD_SCHED_TOO_FAST				-1919	// The requested schedule rate is too fast
#define DPX_ERR_AUD_SCHED_TOO_SLOW				-1920	// The requested schedule rate is too slow
#define DPX_ERR_AUD_SCHED_BAD_RATE_UNITS		-1921	// Unnrecognized schedule rate units parameter
#define DPX_ERR_AUD_CODEC_POWERUP				-1922	// The CODEC didn't set its internal powerup bits.

#define DPX_ERR_MIC_SET_GAIN_TOO_LOW			-2000	// See DPxSetMicSource() for valid values
#define DPX_ERR_MIC_SET_GAIN_TOO_HIGH			-2001	// See DPxSetMicSource() for valid values
#define DPX_ERR_MIC_SET_BAD_SOURCE				-2002	// See DPxSetMicSource() for valid values
#define DPX_ERR_MIC_SET_BAD_LRMODE				-2003	// See DPxSetMicLRMode() for valid values
#define DPX_ERR_MIC_BUFF_ODD_BASEADDR			-2004	// An odd buffer base was requested
#define DPX_ERR_MIC_BUFF_BASEADDR_TOO_HIGH		-2005	// The requested buffer is larger than the DATAPixx RAM
#define DPX_ERR_MIC_BUFF_ODD_READADDR			-2006	// An odd buffer read address was requested
#define DPX_ERR_MIC_BUFF_READADDR_TOO_HIGH		-2007	// The requested read address exceeds the DATAPixx RAM
#define DPX_ERR_MIC_BUFF_ODD_WRITEADDR			-2008	// An odd buffer write address was requested
#define DPX_ERR_MIC_BUFF_WRITEADDR_TOO_HIGH		-2009	// The requested write address exceeds the DATAPixx RAM
#define DPX_ERR_MIC_BUFF_ODD_SIZE				-2010	// An odd buffer size was requested
#define DPX_ERR_MIC_BUFF_TOO_BIG				-2011	// The requested buffer is larger than the DATAPixx RAM
#define DPX_ERR_MIC_SCHED_TOO_FAST				-2012	// The requested schedule rate is too fast
#define DPX_ERR_MIC_SCHED_BAD_RATE_UNITS		-2013	// Unnrecognized schedule rate units parameter

#define DPX_ERR_VID_SET_BAD_MODE				-2000	// See DPxSetVidMode() for valid values
#define DPX_ERR_VID_CLUT_WRITE_USB_ERROR		-2101	// A USB error occurred while writing a video CLUT
#define DPX_ERR_VID_VSYNC_USB_ERROR				-2102	// A USB error occurred while waiting for vertical sync
#define DPX_ERR_VID_EDID_WRITE_USB_ERROR		-2103	// A USB error occurred while writing EDID data
#define DPX_ERR_VID_LINE_READ_USB_ERROR			-2104	// A USB error occurred while reading the video line buffer
#define DPX_ERR_VID_PSYNC_NPIXELS_ARG_ERROR		-2105	// Pixel sync nPixels argument must be in the range 1-8
#define DPX_ERR_VID_PSYNC_TIMEOUT_ARG_ERROR		-2106	// Pixel sync timeout argument must be in the range 0-65535
#define DPX_ERR_VID_PSYNC_LINE_ARG_ERROR		-2107	// Pixel sync raster line argument must be in the range 0-4095
#define DPX_ERR_VID_ALPHA_WRITE_USB_ERROR		-2108	// A USB error occurred while writing video horizontal overlay alpha data
#define DPX_ERR_VID_BASEADDR_ALIGN_ERROR		-2109	// The requested base address was not aligned on a 64kB boundary
#define DPX_ERR_VID_BASEADDR_TOO_HIGH           -2110	// The requested base address exceeds the DATAPixx RAM
#define DPX_ERR_VID_VSYNC_WITHOUT_VIDEO         -2111   // The API was told to block until VSYNC; but DATAPixx is not receiving any video

// Convenient target macro.
// Note that something like "#define TARGET_WINDOWS (defined(_MSC_VER) || defined(WIN_BUILD))" does not work.
#if (defined(_MSC_VER) || defined(WIN_BUILD))
#define TARGET_WINDOWS 1
#else
#define TARGET_WINDOWS 0
#endif

