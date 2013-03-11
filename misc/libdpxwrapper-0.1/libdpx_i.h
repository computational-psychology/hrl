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

//	Most users will have no need to reference the contents of this file.
//	The interfaces presented in libdpx.h are sufficient for most purposes.
//
// The DATAPixx device has a register space of 480 bytes.
// Adding framing, one register set fits nicely into a 512-byte USB endpoint payload.
#define DPX_REG_SPACE 480

// The following is a detailed description of each register.
// Some of the registers are 16-bit quantities.  This is the atomic R/W size for the register space.
// Some of the registers are 32-bit quantities.  These are identified by REGNAME_L, REGNAME_H.  The API will R/W these atomically.
// The NANOTIME register is a read-only 64-bit quantity.
// Note that the register #define's are byte addresses, which must be divided by 2 before indexing dp_readreg_cache.
// First 16 bytes contain system information.
#define DPXREG_DPID					0x00			// DATAPixx Identification register.
	#define DPXREG_DPID_DP				0x4450		// = ASCII "DP" for original DATAPixx
    #define DPXREG_DPID_VP				0x5650		// = ASCII "VP" for VIEWPixx with embedded DATAPixx
	#define DPXREG_DPID_PP				0x5050		// = ASCII "PP" for PROPixx with embedded DATAPixx
#define DPXREG_OPTIONS				0x02			// Hardware option summary, read-only.
	//	BITS
	//	15:8	PART
	//			0x30: DATAPixx/VIEWPixx Lite
	//			0x31: DATAPixx/VIEWPixx Full (includes audio and analog I/O functionality)
    //			0x34: VIEWPixx/3D Lite
    //			0x35: VIEWPixx/3D Full
	//	2:0		RAM: Quantity of volatile memory installed into DATAPixx system
	//			000:  Unrecognized RAM, or RAM failed internal self-test
	//			001:  32 MB, initial DATAPixx productions
	//			010:  64 MB
	//			011: 128 MB, latest DATAPixx productions
	//			100: 256 MB, VIEWPixx productions
	#define DPXREG_OPTIONS_PART_MASK	0xFF00
	#define DPXREG_OPTIONS_PART_LITE	0x3000
	#define DPXREG_OPTIONS_PART_FULL	0x3100
    #define DPXREG_OPTIONS_PART_3DLITE	0x3400
    #define DPXREG_OPTIONS_PART_3DFULL	0x3500
	#define DPXREG_OPTIONS_RAM_MASK		0x0007
	#define DPXREG_OPTIONS_RAM_32M		0x0001
	#define DPXREG_OPTIONS_RAM_64M		0x0002
	#define DPXREG_OPTIONS_RAM_128M		0x0003
	#define DPXREG_OPTIONS_RAM_256M		0x0004
#define DPXREG_FIRMWARE_REV			0x04			// Increments with each firmware revision
#define DPXREG_STATUS				0x06			// System status flags
	//	BITS
	//	15:8	TEMP_FPGA
	//			Temperature of FPGA die in degrees Celcius
    //  3       RAM_OFFLINE (Implemented in VIEWPixx, not DATAPixx)
    //          1: DDR SDRAM controller has not yet brought memory system online
	//	2		PSYNC_TIMEOUT
	//			1: Last pixel sync wait timed out
	//	1		5V_FAULT
	//			1: +5V output supplies (on VESA and Analog I/O connectors) attempting to draw more than 500 mA combined
	//	0		USER_FW
	//			1:	User firmware load (never used)
	//			0:	Factory firmware load
	#define DPXREG_STATUS_RAM_OFFLINE	0x0008
	#define DPXREG_STATUS_PSYNC_TIMEOUT	0x0004
	#define DPXREG_STATUS_5V_FAULT		0x0002
#define DPXREG_POWER				0x08			// +5V system power supply voltage and current
	//	BITS
	//	15:8	VOLTAGE
	//			+5V power supply voltage measurement in increments of 25.977 mV
	//	7:0		CURRENT
	//			+5V power supply current measurement in increments of 41.344 mA for DATAPixx, or 82.688 mA for VIEWPixx
#define DPXREG_TEMP					0x0A			// PCB temperature in degrees Celcius
	//	BITS
	//	15:8	TEMP_PCB2
	//			PCB temperature probe 2
	//	7:0		TEMP_PCB1
	//			PCB temperature probe 1
#define DPXREG_POWER2				0x0C			// +12V system power supply voltage and current, only available on VIEWPixx
	//	BITS
	//	15:8	VOLTAGE
	//			+12V power supply voltage measurement in increments of 103.59 mV
	//	7:0		CURRENT
	//			+12V power supply current measurement in increments of 82.688 mA
#define DPXREG_CTRL					0x0E
	//	BITS
	//	15		ASMI_OFF, Set to 1 to use home-grown SPI interface (more reliable for writes), 0 for ASMI interface
	//	0		CALIB_RELOAD
	//			Write a 1 to this bit to reload EEPROM data (calibration tables, EDID, etc).  Self clearing.
	#define DPXREG_CTRL_CALIB_RELOAD		0x0001

// 16 bytes which apply to all I/O subsystems
#define DPXREG_NANOTIME_15_0		0x10	// Low word of nanosecond timer
#define DPXREG_NANOTIME_31_16		0x12	// Mid-low word of nanosecond timer
#define DPXREG_NANOTIME_47_32		0x14	// Mid-high word of nanosecond timer
#define DPXREG_NANOTIME_63_48		0x16	// High word of nanosecond timer
#define DPXREG_NANOMARKER_15_0		0x18	// Low word of nanosecond marker
#define DPXREG_NANOMARKER_31_16		0x1A	// Mid-low word of nanosecond marker
#define DPXREG_NANOMARKER_47_32		0x1C	// Mid-high word of nanosecond marker
#define DPXREG_NANOMARKER_63_48		0x1E	// High word of nanosecond marker

// 48 bytes for DAC subsystem.
// First register block has DAC data.
// Writes to these registers will immediately update DAC outputs.
#define DPXREG_DAC_DATA0			0x20	// DAC0 output data, 16-bit 2's complement, +-10V range
#define DPXREG_DAC_DATA1			0x22	// DAC1 output data, 16-bit 2's complement, +-10V range
#define DPXREG_DAC_DATA2			0x24	// DAC2 output data, 16-bit 2's complement, +-5V range on DATAPixx, +-10V range on VIEWPixx
#define DPXREG_DAC_DATA3			0x26	// DAC3 output data, 16-bit 2's complement, +-5V range on DATAPixx, +-10V range on VIEWPixx
#define DPXREG_DAC_28				0x28
#define DPXREG_DAC_2A				0x2A
#define DPXREG_DAC_CHANSEL			0x2C	// Channel selector for buffering
	//	BITS
	//	3	DAC_DATA3 channel enable
	//		0: DAC_DATA3 is not updated with RAM buffer data
	//		1: DAC_DATA3 is updated with RAM buffer data
	// 2:0	Same for DAC_DATA2 - DAC_DATA0 channels
#define DPXREG_DAC_CTRL				0x2E
	//	BITS
	//	0		CALIB_RAW
	//			0: Generate calibrated DAC outputs
	//			1: Disable DAC calibration transformation
	#define DPXREG_DAC_CTRL_CALIB_RAW	0x0001

// 4 32-bit registers for RAM buffers containing data to write to DAC channels
#define DPXREG_DAC_BUFF_BASEADDR_L	0x30	// DAC RAM buffer start address.  Must be an even value.
#define DPXREG_DAC_BUFF_BASEADDR_H	0x32
#define DPXREG_DAC_BUFF_READADDR_L	0x34	// DAC RAM buffer address from which next DAC sample will be read.
#define DPXREG_DAC_BUFF_READADDR_H	0x36	//	When READADDR = BASEADDR + SIZE, READADDR wraps back to BASEADDR.
#define DPXREG_DAC_BUFF_WRITEADDR_L	0x38	// Unused for now
#define DPXREG_DAC_BUFF_WRITEADDR_H	0x3A
#define DPXREG_DAC_BUFF_SIZE_L		0x3C	// DAC RAM buffer size in bytes.  Must be an even value.
#define DPXREG_DAC_BUFF_SIZE_H		0x3E

// 4 32-bit registers for scheduling regular DAC updates from RAM buffer
#define DPXREG_DAC_SCHED_ONSET_L	0x40	// Delay between schedule start and first DAC update tick, in nanoseconds
#define DPXREG_DAC_SCHED_ONSET_H	0x42
#define DPXREG_DAC_SCHED_RATE_L		0x44	// Tick rate in ticks/second or ticks/frame, or tick period in nanoseconds
#define DPXREG_DAC_SCHED_RATE_H		0x46
#define DPXREG_DAC_SCHED_COUNT_L	0x48	// Tick counter
#define DPXREG_DAC_SCHED_COUNT_H	0x4A
#define DPXREG_DAC_SCHED_CTRL_L		0x4C	// Control register
#define DPXREG_DAC_SCHED_CTRL_H		0x4E
	//	Definitions of SCHED_CTRL register bits are similar for all I/O classes.
	//	Differences between I/O classes are indicated for each bit definition.
	//	BITS
	//  21	TOUCHPIXX_LOG_EVENT, implemented for DIN input classes only
	//		0: Do not log Touchpixx detections to acquisition buffer
	//		1: Touchpixx detections are logged to acquisition buffer
	//	20	LOG_EVENTS, implemented for DIN
	//		0: Do not log digital input (DIN) transitions to acquisition buffer
	//		1: DIN transitions are logged to acquisition buffer
	//	16	LOG_TIMETAG, implemented in all input classes: ADC/DIN/MIC/TOUCHPIXX
	//		0: Do not write timetag to acquisition buffer
	//		1: For each sample, write a 64-bit nanosecond timetag to acquisition buffer
	//	8	COUNTDOWN, implemented in all I/O classes
	//		0: SCHED_COUNT increments at SCHED_RATE, and schedule is stopped by writing 0 to RUN bit
	//		1: SCHED_COUNT decrements at SCHED_RATE, and schedule stops automatically when count hits 0
	//	5:4	RATE, implemented in all I/O classes
	//		00: SCHED_RATE contains tick frequency in ticks / second
	//		01: SCHED_RATE contains tick frequency in ticks / video frame
	//		10: SCHED_RATE contains tick period in nanoseconds
	//		11: Reserved
	//	0	RUNNING, read-only, implemented in all I/O classes
	//		0: Schedule is not running. To start schedule, write to the DPXREG_SCHED_STARTSTOP register.
	//		1: Schedule is currently running. To manually stop schedule, write to the DPXREG_SCHED_STARTSTOP register.

	#define DPXREG_SCHED_CTRL_LOG_TOUCHPIXX	0x00200000 
	#define DPXREG_SCHED_CTRL_LOG_EVENTS	0x00100000
	#define DPXREG_SCHED_CTRL_LOG_TIMETAG	0x00010000
	#define DPXREG_SCHED_CTRL_COUNTDOWN		0x00000100
	#define DPXREG_SCHED_CTRL_RATE_MASK		0x00000030
	#define DPXREG_SCHED_CTRL_RATE_HZ		0x00000000
	#define DPXREG_SCHED_CTRL_RATE_XVID		0x00000010
	#define DPXREG_SCHED_CTRL_RATE_NANO		0x00000020
	#define DPXREG_SCHED_CTRL_RUNNING		0x00000001

// 80 bytes for ADC subsystem.
// First 16 registers have immediate ADC data.
#define DPXREG_ADC_DATA0			0x50	// ADC  0 input data, 16-bit 2's complement
#define DPXREG_ADC_DATA1			0x52	// ADC  1 input data
#define DPXREG_ADC_DATA2			0x54	// ADC  2 input data
#define DPXREG_ADC_DATA3			0x56	// ADC  3 input data
#define DPXREG_ADC_DATA4			0x58	// ADC  4 input data
#define DPXREG_ADC_DATA5			0x5A	// ADC  5 input data
#define DPXREG_ADC_DATA6			0x5C	// ADC  6 input data
#define DPXREG_ADC_DATA7			0x5E	// ADC  7 input data
#define DPXREG_ADC_DATA8			0x60	// ADC  8 input data
#define DPXREG_ADC_DATA9			0x62	// ADC  9 input data
#define DPXREG_ADC_DATA10			0x64	// ADC 10 input data
#define DPXREG_ADC_DATA11			0x66	// ADC 11 input data
#define DPXREG_ADC_DATA12			0x68	// ADC 12 input data
#define DPXREG_ADC_DATA13			0x6A	// ADC 13 input data
#define DPXREG_ADC_DATA14			0x6C	// ADC 14 input data
#define DPXREG_ADC_DATA15			0x6E	// ADC 15 input data

// 8 registers related to differential ADC inputs, and control
#define DPXREG_ADC_REF0				0x70	// ADC REF0 input data
#define DPXREG_ADC_REF1				0x72	// ADC REF1 input data
#define DPXREG_ADC_74				0x74
#define DPXREG_ADC_76				0x76
#define DPXREG_ADC_CHANREF_L		0x78	// Differential reference selector register for ADC channels 0-7
#define DPXREG_ADC_CHANREF_H		0x7A	// Differential reference selector register for ADC channels 8-15
	//	BITS
	//	31:30 ADC_DATA15 differential reference selector
	//		00: referenced to PCB GND
	//		01: differential input referenced to adjacent channel (ADC_DATA14)
	//		10: differential input referenced to REF0
	//		11: differential input referenced to REF1
	//	29:28 ADC_DATA14 differential reference selector
	//		00: referenced to PCB GND
	//		01: differential input referenced to adjacent channel (ADC_DATA15)
	//		10: differential input referenced to REF0
	//		11: differential input referenced to REF1
	//	27:26 ADC_DATA13 differential reference selector
	//		00: referenced to PCB GND
	//		01: differential input referenced to adjacent channel (ADC_DATA12)
	//		10: differential input referenced to REF0
	//		11: differential input referenced to REF1
	//	25:24 ADC_DATA12 differential reference selector
	//		00: referenced to PCB GND
	//		01: differential input referenced to adjacent channel (ADC_DATA13)
	//		10: differential input referenced to REF0
	//		11: differential input referenced to REF1
	// ...same pattern down to...
	//	 1:0 ADC_DATA0 differential reference selector
	//		00: referenced to PCB GND
	//		01: differential input referenced to adjacent channel (ADC_DATA1)
	//		10: differential input referenced to REF0
	//		11: differential input referenced to REF1
	#define DPXREG_ADC_CHANREF_GND		0	// These values are used in the VPixx program
	#define DPXREG_ADC_CHANREF_DIFF		1
	#define DPXREG_ADC_CHANREF_REF0		2
	#define DPXREG_ADC_CHANREF_REF1		3
#define DPXREG_ADC_CHANSEL			0x7C	// Channel selector for buffering
	//	BITS
	//	15:0 ADC channel enables
	//		0: Scheduler does not write channel to RAM
	//		1: Scheduler does write channel to RAM
#define DPXREG_ADC_CTRL				0x7E
	//	BITS
	//	2		FREE_RUN
	//			0: ADC's only convert on schedule ticks (for microsecond-precise sampling)
	//			1: ADC's convert continuously (can add up to 4 microseconds random latency to scheduled samples)
	//	1		DAC_LOOPBACK
	//			0: ADC data readings come from voltages on DATAPixx external "Analog I/O" db-25 connector pins
	//			1: ADC data readings are looped back internally from programmed DAC voltages:
	//				DAC_DATA0 => ADC_DATA0/2/4/6/8/10/12/14
	//				DAC_DATA1 => ADC_DATA1/3/5/7/9/11/13/15
	//				DAC_DATA2 => ADC_REF0
	//				DAC_DATA3 => ADC_REF1
	//	0		CALIB_RAW
	//			0: Generate calibrated ADC inputs
	//			1: Disable ADC calibration transformation
	#define DPXREG_ADC_CTRL_FREE_RUN		0x0004
	#define DPXREG_ADC_CTRL_DAC_LOOPBACK	0x0002
	#define DPXREG_ADC_CTRL_CALIB_RAW		0x0001

// 4 32-bit registers for RAM buffers which will fill with ADC data
#define DPXREG_ADC_BUFF_BASEADDR_L	0x80	// ADC RAM buffer start address.  Must be an even value.
#define DPXREG_ADC_BUFF_BASEADDR_H	0x82
#define DPXREG_ADC_BUFF_READADDR_L	0x84	// Unused for now
#define DPXREG_ADC_BUFF_READADDR_H	0x86
#define DPXREG_ADC_BUFF_WRITEADDR_L	0x88	// ADC RAM buffer address to which next ADC sample will be written.
#define DPXREG_ADC_BUFF_WRITEADDR_H	0x8A	//	When WRITEADDR = BASEADDR + SIZE, WRITEADDR wraps back to BASEADDR.
#define DPXREG_ADC_BUFF_SIZE_L		0x8C	// ADC RAM buffer size in bytes.  Must be an even value.
#define DPXREG_ADC_BUFF_SIZE_H		0x8E

// 4 32-bit registers for scheduling regular ADC sample writes to RAM buffer
#define DPXREG_ADC_SCHED_ONSET_L	0x90	// Delay between schedule start and first ADC update tick, in nanoseconds
#define DPXREG_ADC_SCHED_ONSET_H	0x92
#define DPXREG_ADC_SCHED_RATE_L		0x94	// Tick rate in ticks/second or ticks/frame, or tick period in nanoseconds
#define DPXREG_ADC_SCHED_RATE_H		0x96
#define DPXREG_ADC_SCHED_COUNT_L	0x98	// Tick counter
#define DPXREG_ADC_SCHED_COUNT_H	0x9A
#define DPXREG_ADC_SCHED_CTRL_L		0x9C	// Bits are defined in DPXREG_DAC_SCHED_CTRL register
#define DPXREG_ADC_SCHED_CTRL_H		0x9E


// 48 bytes for DOUT (digital output) subsystem.
// First register block has DOUT data.
// Writes to these registers will immediately update digital outputs.
#define DPXREG_DOUT_DATA_L			0xA0	// DOUT bits 15:0
#define DPXREG_DOUT_DATA_H			0xA2	// DOUT bits 23:16 are R/W through DPXREG_DOUT_H bits 7:0
#define DPXREG_DOUT_A4				0xA4
#define DPXREG_DOUT_A6				0xA6
#define DPXREG_DOUT_A8				0xA8
#define DPXREG_DOUT_AA				0xAA
#define DPXREG_DOUT_AC				0xAC
#define DPXREG_DOUT_CTRL			0xAE
//	BITS
//	0		DOUT_CTRL_BUTTON_SCHEDULES (DATAPixx only)
//			1: Button presses (falling edges) from DIN will automatically initiate DOUT schedules.
//             Schedule buffers are assumed to be located at 4kB offsets from DOUT_BUFF_BASEADDR.
#define DPXREG_DOUT_CTRL_BUTTON_SCHEDULES   0x0001

// 8 registers for RAM buffers containing DOUT waveform data.
#define DPXREG_DOUT_BUFF_BASEADDR_L	0xB0	// DOUT RAM buffer start address.  Must be an even value.
#define DPXREG_DOUT_BUFF_BASEADDR_H	0xB2
#define DPXREG_DOUT_BUFF_READADDR_L	0xB4	// DOUT RAM buffer address from which next DOUT sample will be read.
#define DPXREG_DOUT_BUFF_READADDR_H	0xB6	//	When READADDR = BASEADDR + SIZE, READADDR wraps back to BASEADDR.
#define DPXREG_DOUT_BUFF_WRITEADDR_L 0xB8	// Unused for now
#define DPXREG_DOUT_BUFF_WRITEADDR_H 0xBA
#define DPXREG_DOUT_BUFF_SIZE_L		0xBC	// DOUT RAM buffer size in bytes.  Must be an even value.
#define DPXREG_DOUT_BUFF_SIZE_H		0xBE

// 8 registers for scheduling regular DOUT updates from RAM buffer.
#define DPXREG_DOUT_SCHED_ONSET_L	0xC0	// Delay between schedule start and first DAC update tick, in nanoseconds
#define DPXREG_DOUT_SCHED_ONSET_H	0xC2
#define DPXREG_DOUT_SCHED_RATE_L	0xC4	// Tick rate in ticks/second or ticks/frame, or tick period in nanoseconds
#define DPXREG_DOUT_SCHED_RATE_H	0xC6
#define DPXREG_DOUT_SCHED_COUNT_L	0xC8	// Tick counter
#define DPXREG_DOUT_SCHED_COUNT_H	0xCA
#define DPXREG_DOUT_SCHED_CTRL_L	0xCC	// Bits are defined in DPXREG_DAC_SCHED_CTRL register
#define DPXREG_DOUT_SCHED_CTRL_H	0xCE


// 24 registers for DIN (digital input) subsystem.
// Note that the DIN bits are actually bidirectional, and can be programmed as outputs on a bit-by-bit basis
// First register block has immediate DIN data.
#define DPXREG_DIN_DATA_L			0xD0	// DIN bits 15:0. Touch Panel X position when TOUCHPixx is enable
#define DPXREG_DIN_DATA_H			0xD2	// DIN bits 23:16 are read through DPXREG_DIN_H bits 7:0. Touch Panel Y position when TOUCHPixx is enable
#define DPXREG_DIN_DIR_L			0xD4	// Set any of 24 DIN_DIR bits high to turn the bit into an output port
#define DPXREG_DIN_DIR_H			0xD6
#define DPXREG_DIN_DATAOUT_L		0xD8	// Values to be driven onto ports when DIN_DIR bits are high
#define DPXREG_DIN_DATAOUT_H		0xDA
#define DPXREG_DIN_DC				0xDC
#define DPXREG_DIN_CTRL				0xDE
	//	BITS
	//  13		TOUCHPixx Continuous Logging mode Enable/Disable bit
	//  12		TOUCHPixx Enable/Disable bit
	//	11:8	PWM, 100 MHz Pulse Width Modulation used to reduce intensity of driven outputs
	//			0000: PWM disabled, Output ports are driven continuously
	//			0001: Output ports are driven 1/16 of the time, and are high-impedance 15/16 of the time
	//			0010: Output ports are driven 2/16 of the time, and are high-impedance 14/16 of the time
	//			...
	//			1111: Output ports are driven 15/16 of the time, and are high-impedance 1/16 of the time
	//	5		DEBOUNCE
	//			0: DIN inputs are passed directly to read register
	//			1: DIN inputs are frozen for 30 ms after each transition
	//	4		STABILIZE
	//			0: DIN inputs are passed without stabilization
	//			1: DIN bus must have a constant value for 80 ns before change is passed on
	//	1		DOUT_LOOPBACK
	//			0: DIN inputs come from DATAPixx external "Digital IN" db-25 connector pins
	//			1: DIN inputs are looped back internally from programmed DOUT values

	#define DPXREG_DIN_CTRL_TOUCHPIXX_CONT		0x2000	
	#define DPXREG_DIN_CTRL_TOUCHPIXX			0x1000
	#define DPXREG_DIN_CTRL_PWM					0x0F00
	#define DPXREG_DIN_CTRL_DEBOUNCE			0x0020
	#define DPXREG_DIN_CTRL_STABILIZE			0x0010
	#define DPXREG_DIN_CTRL_DOUT_LOOPBACK		0x0002

// 8 registers for RAM buffers which will fill with DIN data.
#define DPXREG_DIN_BUFF_BASEADDR_L	0xE0	// DIN RAM buffer start address.  Must be an even value.
#define DPXREG_DIN_BUFF_BASEADDR_H	0xE2
#define DPXREG_DIN_BUFF_READADDR_L	0xE4	// Unused for now
#define DPXREG_DIN_BUFF_READADDR_H	0xE6
#define DPXREG_DIN_BUFF_WRITEADDR_L	0xE8	// DIN RAM buffer address to which next DIN sample will be written.
#define DPXREG_DIN_BUFF_WRITEADDR_H	0xEA	//	When WRITEADDR = BASEADDR + SIZE, WRITEADDR wraps back to BASEADDR.
#define DPXREG_DIN_BUFF_SIZE_L		0xEC	// DIN RAM buffer size in bytes.  Must be an even value.
#define DPXREG_DIN_BUFF_SIZE_H		0xEE

// 8 registers for scheduling regular DIN sample writes to RAM buffer
#define DPXREG_DIN_SCHED_ONSET_L	0xF0	// Delay between schedule start and first DAC update tick, in nanoseconds
#define DPXREG_DIN_SCHED_ONSET_H	0xF2
#define DPXREG_DIN_SCHED_RATE_L		0xF4	// Tick rate in ticks/second or ticks/frame, or tick period in nanoseconds
#define DPXREG_DIN_SCHED_RATE_H		0xF6
#define DPXREG_DIN_SCHED_COUNT_L	0xF8	// Tick counter
#define DPXREG_DIN_SCHED_COUNT_H	0xFA
#define DPXREG_DIN_SCHED_CTRL_L		0xFC	// Bits are defined in DPXREG_DAC_SCHED_CTRL register
#define DPXREG_DIN_SCHED_CTRL_H		0xFE

// 24 registers for stereo audio CODEC output subsystem
// First 8-register block has audio DAC data
#define DPXREG_AUD_DATA_LEFT		0x100	// Audio Left output data, 16-bit 2's complement signed
#define DPXREG_102					0x102	// Reserved for future support of >16-bit audio data
#define DPXREG_AUD_DATA_RIGHT		0x104	// Audio Right output data, 16-bit 2's complement signed
#define DPXREG_106					0x106	// Reserved for future support of >16-bit audio data
#define DPXREG_AUD_VOLUME_LEFT		0x108	// Volume control for Left channel, unsigned 16-bit multiplier
#define DPXREG_AUD_VOLUME_RIGHT		0x10A	// Volume control for Right channel, unsigned 16-bit multiplier
#define DPXREG_10C					0x10C
#define DPXREG_AUD_CTRL				0x10E
	//	BITS
	//	13		MAXVOL_RIGHT
	//			0: Right waveform data is attenuated by the contents of the DPXREG_AUD_VOLUME_RIGHT register
	//			1: Right waveform data is played at full volume
	//	12		MAXVOL_LEFT
	//  10:8	LRMODE, Left/Right audio channel update mode
	//			000: Left and Right are both updated with the same AUD buffer datum (mono mode)
	//			001: Left is updated from AUD buffer, and Right remains unchanged
	//			010: Left is unchanged, and Right is updated from AUD buffer
	//			011: Left and Right are updated with alternate AUD buffer data (stereo 1 mode)
	//			100: Left and Right are updated independantly by AUD and AUX schedules (stereo 2 mode)
	//			Note that this last mode permits completely independent control over phase between audio Left/Right playback
	//	4:0		BCLK_RATIO, Ratio between CODEC BCLK frequency, and audio sample frequency, /64
	#define DPXREG_AUD_CTRL_MAXVOL_RIGHT	0x2000
	#define DPXREG_AUD_CTRL_MAXVOL_LEFT		0x1000
	#define DPXREG_AUD_CTRL_LRMODE_MASK		0x0700
	#define DPXREG_AUD_CTRL_LRMODE_MONO		0x0000
	#define DPXREG_AUD_CTRL_LRMODE_LEFT		0x0100
	#define DPXREG_AUD_CTRL_LRMODE_RIGHT	0x0200
	#define DPXREG_AUD_CTRL_LRMODE_STEREO_1	0x0300
	#define DPXREG_AUD_CTRL_LRMODE_STEREO_2	0x0400
	#define DPXREG_AUD_CTRL_BCLK_RATIO		0x001F

// 8 registers for RAM buffers containing audio waveform data
#define DPXREG_AUD_BUFF_BASEADDR_L	0x110	// AUD RAM buffer start address.  Must be an even value.
#define DPXREG_AUD_BUFF_BASEADDR_H	0x112
#define DPXREG_AUD_BUFF_READADDR_L	0x114	// AUD RAM buffer address from which next AUD sample will be read.
#define DPXREG_AUD_BUFF_READADDR_H	0x116	//	When READADDR = BASEADDR + SIZE, READADDR wraps back to BASEADDR.
#define DPXREG_AUD_BUFF_WRITEADDR_L	0x118	// Unused for now
#define DPXREG_AUD_BUFF_WRITEADDR_H	0x11A
#define DPXREG_AUD_BUFF_SIZE_L		0x11C	// AUD RAM buffer size in bytes.  Must be an even value.
#define DPXREG_AUD_BUFF_SIZE_H		0x11E

// 8 registers for RAM buffers containing auxiliary audio waveform data (for independent L/R buffers)
#define DPXREG_AUX_BUFF_BASEADDR_L	0x120	// AUX RAM buffer start address.  Must be an even value.
#define DPXREG_AUX_BUFF_BASEADDR_H	0x122
#define DPXREG_AUX_BUFF_READADDR_L	0x124	// AUX RAM buffer address from which next AUX sample will be read.
#define DPXREG_AUX_BUFF_READADDR_H	0x126	//	When READADDR = BASEADDR + SIZE, READADDR wraps back to BASEADDR.
#define DPXREG_AUX_BUFF_WRITEADDR_L	0x128	// Unused for now
#define DPXREG_AUX_BUFF_WRITEADDR_H	0x12A
#define DPXREG_AUX_BUFF_SIZE_L		0x12C	// AUX RAM buffer size in bytes.  Must be an even value.
#define DPXREG_AUX_BUFF_SIZE_H		0x12E

// 8 registers for scheduling regular audio updates from RAM buffer
#define DPXREG_AUD_SCHED_ONSET_L	0x130	// Delay between schedule start and first DAC update tick, in nanoseconds
#define DPXREG_AUD_SCHED_ONSET_H	0x132
#define DPXREG_AUD_SCHED_RATE_L		0x134	// Tick rate in ticks/second or ticks/frame, or tick period in nanoseconds
#define DPXREG_AUD_SCHED_RATE_H		0x136
#define DPXREG_AUD_SCHED_COUNT_L	0x138	// Tick counter
#define DPXREG_AUD_SCHED_COUNT_H	0x13A
#define DPXREG_AUD_SCHED_CTRL_L		0x13C	// Bits are defined in DPXREG_DAC_SCHED_CTRL register
#define DPXREG_AUD_SCHED_CTRL_H		0x13E

// 8 registers for scheduling auxiliary audio updates from RAM buffer
#define DPXREG_AUX_SCHED_ONSET_L	0x140	// Delay between schedule start and first DAC update tick, in nanoseconds
#define DPXREG_AUX_SCHED_ONSET_H	0x142
#define DPXREG_AUX_SCHED_RATE_L		0x144	// Tick rate in ticks/second or ticks/frame, or tick period in nanoseconds
#define DPXREG_AUX_SCHED_RATE_H		0x146
#define DPXREG_AUX_SCHED_COUNT_L	0x148	// Tick counter
#define DPXREG_AUX_SCHED_COUNT_H	0x14A
#define DPXREG_AUX_SCHED_CTRL_L		0x14C	// Bits are defined in DPXREG_DAC_SCHED_CTRL register
#define DPXREG_AUX_SCHED_CTRL_H		0x14E


// 24 registers for stereo audio CODEC microphone input subsystem.
// First register block has immediate DIN data.
#define DPXREG_MIC_DATA_LEFT		0x150	// Microphone Left input data, 16-bit 2's complement
#define DPXREG_152					0x152	// Reserved for future support of >16-bit microphone data
#define DPXREG_MIC_DATA_RIGHT		0x154	// Microphone Right input data
#define DPXREG_156					0x156	// Reserved for future support of >16-bit microphone data
#define DPXREG_158					0x158
#define DPXREG_15A					0x15A
#define DPXREG_15C					0x15C
#define DPXREG_MIC_CTRL				0x15E
	//	BITS
	//  5:4	LRMODE, Left/Right MIC acquisition mode
	//		00: Mono data is written to schedule buffer (average of Left/Right CODEC data)
	//		01: Left data is written to schedule buffer
	//		10: Right data is written to schedule buffer
	//		11: Left and Right data are both written to schedule buffer (stereo mode)
	//	1	AUD_LOOPBACK
	//		0: MIC data readings come from voltages on DATAPixx external "Audio IN" or "MIC IN" jacks
	//		1: MIC data readings are looped back internally from programmed AUD voltages:
	#define DPXREG_MIC_CTRL_LRMODE_MASK		0x0030
	#define DPXREG_MIC_CTRL_LRMODE_MONO		0x0000
	#define DPXREG_MIC_CTRL_LRMODE_LEFT		0x0010
	#define DPXREG_MIC_CTRL_LRMODE_RIGHT	0x0020
	#define DPXREG_MIC_CTRL_LRMODE_STEREO	0x0030
	#define DPXREG_MIC_CTRL_AUD_LOOPBACK	0x0002

// 8 registers for RAM buffers which will fill with MIC data.
#define DPXREG_MIC_BUFF_BASEADDR_L	0x160	// MIC RAM buffer start address.  Must be an even value.
#define DPXREG_MIC_BUFF_BASEADDR_H	0x162
#define DPXREG_MIC_BUFF_READADDR_L	0x164	// Unused for now
#define DPXREG_MIC_BUFF_READADDR_H	0x166
#define DPXREG_MIC_BUFF_WRITEADDR_L	0x168	// MIC RAM buffer address to which next MIC sample will be written.
#define DPXREG_MIC_BUFF_WRITEADDR_H	0x16A	//	When WRITEADDR = BASEADDR + SIZE, WRITEADDR wraps back to BASEADDR.
#define DPXREG_MIC_BUFF_SIZE_L		0x16C	// MIC RAM buffer size in bytes.  Must be an even value.
#define DPXREG_MIC_BUFF_SIZE_H		0x16E

// 8 registers for scheduling regular MIC sample writes to RAM buffer
#define DPXREG_MIC_SCHED_ONSET_L	0x170	// Delay between schedule start and first DAC update tick, in nanoseconds
#define DPXREG_MIC_SCHED_ONSET_H	0x172
#define DPXREG_MIC_SCHED_RATE_L		0x174	// Tick rate in ticks/second or ticks/frame, or tick period in nanoseconds
#define DPXREG_MIC_SCHED_RATE_H		0x176
#define DPXREG_MIC_SCHED_COUNT_L	0x178	// Tick counter
#define DPXREG_MIC_SCHED_COUNT_H	0x17A
#define DPXREG_MIC_SCHED_CTRL_L		0x17C	// Bits are defined in DPXREG_DAC_SCHED_CTRL register
#define DPXREG_MIC_SCHED_CTRL_H		0x17E

// 24 registers for video subsystem
#define DPXREG_VID_VPERIOD_L		0x180
#define DPXREG_VID_VPERIOD_H		0x182
#define DPXREG_VID_HTOTAL			0x184
#define DPXREG_VID_VTOTAL			0x186
#define DPXREG_VID_HACTIVE			0x188
#define DPXREG_VID_VACTIVE			0x18A
#define DPXREG_VID_CLK_CTRL			0x18C
#define DPXREG_VID_STATUS			0x18E
	//	BITS
    //  11	DVI_DIRECT_ACTIVE
    //		0: LCD is showing test patterns, or rescanned DVI video
    //		1: LCD is showing frame-synchronous DVI video
    //  10	DVI_STRETCH_DE
    //		0: DVI DE input has correct timing
    //		1: DVI DE input is descending 1 DVI_CLK too early, VIEWPixx is correcting
	//  9	DVI_LOCKABLE
	//		0: DVI receiver is inactive, or is receiving video which must be buffered and rescanned
	//		1: DVI is receiving video which can directly drive display
    //  8	LCD_HIFREQ
    //		0: LCD is being driven at 100Hz
    //		1: LCD is being driven at 120Hz
    //  3	SLEEP (VIEWPixx only)
    //		0: VIEWPixx is showing video or a test pattern
    //		1: No input video, and no test pattern, so VIEWPixx has gone to sleep
	//  2	TURBO
	//		0: Output VGA video is clocking at same rate as incoming DVI video
	//		1: Output VGA video is clocking at 2x rate of incoming DVI video
	//  1	DVI_ACTIVE_DUAL
	//		0: DVI receiver is inactive, or is receiving single link video
	//		1: DVI is receiving dual link video
	//	0	DVI_ACTIVE
	//		0: DVI receiver is inactive
	//		1: DVI is receiving video over a single or dual link
    #define DPXREG_VID_STATUS_DVI_DIRECT_ACTIVE 0x0800
    #define DPXREG_VID_STATUS_DVI_STRETCH_DE    0x0400
	#define DPXREG_VID_STATUS_DVI_LOCKABLE      0x0200
    #define DPXREG_VID_STATUS_LCD_HIFREQ        0x0100
    #define DPXREG_VID_STATUS_SLEEP				0x0008
	#define DPXREG_VID_STATUS_TURBO				0x0004
	#define DPXREG_VID_STATUS_DVI_ACTIVE_DUAL	0x0002
	#define DPXREG_VID_STATUS_DVI_ACTIVE		0x0001
#define DPXREG_VID_HOVERLAY_X1		0x190
#define DPXREG_VID_HOVERLAY_Y1		0x192
#define DPXREG_VID_HOVERLAY_X2		0x194
#define DPXREG_VID_HOVERLAY_Y2		0x196
#define DPXREG_VID_SCOPE			0x198
#define DPXREG_VID_PSYNC			0x19A
	//	BITS
	//  15	SINGLE_LINE
	//		0: PSYNC can be recognized on any raster line
	//		1: PSYNC can only be recognized on RASTER_LINE
	//  14	BLANK_LINE
	//		0: RASTER_LINE is displayed as normal video
	//		1: RASTER_LINE is always displayed in black
	// 11:0	RASTER_LINE, indicates raster line dedicated to PSYNC
	#define DPXREG_VID_PSYNC_SINGLE_LINE	0x8000
	#define DPXREG_VID_PSYNC_BLANK_LINE		0x4000
	#define DPXREG_VID_PSYNC_RASTER_LINE	0x0FFF
#define DPXREG_VID_VESA				0x19C
	//	BITS
    // 15:8     PHASE, goggle phase wrt video
    //          0x64 = 100 is optimal for VIEWPixx3D with scanning backlight and fast shutter glasses
    //          0xF5 = 245 is optimal for DATAPixx/CRT and fast shutter glasses
    //  6:4     WAVEFORM
    //          0: Straight L/R squarewave for 3rd party shutter driver
    //          1: CrystalEyes glasses driven by 3DPixx shutter driver
    //          2: NVIDIA glasses driven by 3DPixx shutter driver
    //          3: NVIDIA_1MS, engineering test only.
    //	2       BLUELINE
    //          0: VESA 3D output is not dependent on video content
    //          1: VESA 3D output interprets middle pixel on last raster line as a blueline code
    //	1       LEFT_WEN, Write-enable bit to write the LEFT bit
    //          0: A write to DPXREG_VID_VESA with LEFT_WEN cleared will have no effect on the LEFT bit
    //          1: A write to DPXREG_VID_VESA with LEFT_WEN set will write to the LEFT bit
	//	0       LEFT
	//          0: VESA connector outputs signal for right eye
	//          1: VESA connector outputs signal for left eye
    #define DPXREG_VID_VESA_PHASE_MASK              0xFF00
    #define DPXREG_VID_VESA_WAVEFORM_MASK           0x0070
    #define DPXREG_VID_VESA_WAVEFORM_LR             0x0000
    #define DPXREG_VID_VESA_WAVEFORM_CRYSTALEYES    0x0010
    #define DPXREG_VID_VESA_WAVEFORM_NVIDIA         0x0020
	#define DPXREG_VID_VESA_BLUELINE                0x0004
    #define DPXREG_VID_VESA_LEFT_WEN                0x0002
    #define DPXREG_VID_VESA_LEFT                    0x0001
#define DPXREG_VID_CTRL				0x19E
	//	BITS
	//	15	VESA_LEFT (obsolete, VIEWPixx only; all systems now use LEFT bit in DPXREG_VID_VESA), read-only
	//		0: VESA connector outputs signal for right eye
	//		1: VESA connector outputs signal for left eye
	//	14	NATIVE100HZ (VIEWPixx and VIEWPixx/3D only)
    //		0: Display is driven at 120Hz when unlocked or showing test patterns
    //		1: Display is driven at 100Hz when unlocked or showing test patterns
	//	13	DUAL_GCD (DATAPixx only)
	//		0: Disable dual-display gaze-contingent display
	//		1: Haploscope with independent left/right 256-pixel gaze-contingent insets
	//	12	HOVERLAY
	//		0: Disable horizontal overlay
	//		1: Right half of HSPLIT display overlays left half
	//	11	BLANK_2
	//		0: Video output 2 is outputting video
	//		1: Video output 2 is blanked
	//	10	TESTPAT_2
	//		0: Video output 2 is determined by MODE field
	//		1: Video output 2 contains an RGB test pattern
	//	 9	BLANK_1
	//	 8	TESTPAT_1
	//	 7	VSTEREO_MAN, specify manual control of vertical stereo function
	//		0: Vertical stereo is enabled automatically when DPXREG_VID_HACTIVE < DPXREG_VID_VACTIVE, and VSTEREO bit is read-only
	//		1: Vertical stereo functionality is enabled/disabled manually by writing VSTEREO bit
	//	 6	VSTEREO, vertical stereo mode, R/W if VSTEREO_MAN = 1, or RO if VSTEREO_MAN = 0
	//		0: Normal display
	//		1: Top/bottom halves of input image are output in two sequencial video frames.
	//		   VESA L/R output is set to 1 when first frame (left eye) is displayed, and set to 0 when second frame (right eye) is displayed
	//	 5	HSPLIT_MAN, specify manual control of horizontal split function
	//		0: Horizontal split is enabled automatically when DPXREG_VID_HACTIVE >= 2xDPXREG_VID_VACTIVE, and HSPLIT bit is read-only
	//		1: Horizontal split functionality is enabled/disabled manually by writing HSPLIT bit
	//	 4	HSPLIT, horizontal split screen, R/W if HSPLIT_MAN = 1, or RO if HSPLIT_MAN = 0
	//		0: Video image is mirrored on video outputs 1 and 2
	//		1: Left half of image is on video output 1, right half of image is on video output 2
	//	 2:0 MODE, video mode
	//		000:	C24			Straight passthrough from DVI 8-bit (or HDMI "deep" 10/12-bit) RGB to VGA 8/10/12-bit RGB
	//		001:	L48			DVI RED[7:0] is used as an index into a 256-entry 16-bit RGB colour lookup table
	//		010:	M16			DVI RED[7:0] & GREEN[7:0] concatenate into a VGA 16-bit value sent to all three RGB components
	//							Also implements a CLUT overlay which is indexed by a non-zero blue component
	//		011:	C48			Even/Odd pixel RED/GREEN/BLUE[7:0] concatenate to generate 16-bit RGB components at half the horizontal resolution
	//		100:	RSVD		Reserved for future use.  Same as VMODE_C24_c for now.
	//		101:	L48D		DVI RED[7:4] & GREEN[7:4] concatenate to form an 8-bit index into a 256-entry 16-bit RGB colour lookup table
	//		110:	M16D		DVI RED[7:3] & GREEN[7:3] & BLUE[7:2] concatenate into a VGA 16-bit value sent to all three RGB components
	//		111:	C36D		Even/Odd pixel RED/GREEN/BLUE[7:2] concatenate to generate 12-bit RGB components at half the horizontal resolution
	#define DPXREG_VID_CTRL_VESA_LEFT	0x8000
    #define DPXREG_VID_CTRL_NATIVE100HZ	0x4000
	#define DPXREG_VID_CTRL_DUAL_GCD	0x2000
	#define DPXREG_VID_CTRL_HOVERLAY	0x1000
	#define DPXREG_VID_CTRL_BLANK_2		0x0800
	#define DPXREG_VID_CTRL_TESTPAT_2	0x0400
	#define DPXREG_VID_CTRL_BLANK_1		0x0200
	#define DPXREG_VID_CTRL_TESTPAT_1	0x0100
	#define DPXREG_VID_CTRL_VSTEREO_MAN	0x0080
	#define DPXREG_VID_CTRL_VSTEREO		0x0040
	#define DPXREG_VID_CTRL_HSPLIT_MAN	0x0020
	#define DPXREG_VID_CTRL_HSPLIT		0x0010
	#define DPXREG_VID_CTRL_MODE_MASK	0x0007
	#define DPXREG_VID_CTRL_MODE_C24	0x0000
	#define DPXREG_VID_CTRL_MODE_L48	0x0001
	#define DPXREG_VID_CTRL_MODE_M16	0x0002
	#define DPXREG_VID_CTRL_MODE_C48	0x0003
	#define DPXREG_VID_CTRL_MODE_L48D	0x0005
	#define DPXREG_VID_CTRL_MODE_M16D	0x0006
	#define DPXREG_VID_CTRL_MODE_C36D	0x0007
#define DPXREG_VID_CTRL2            0x1A0
	//	BITS
    //	 15	ENABLE_PIXELDRIVE
    //	 14	ENABLE_PIXELDRIVE_ACCUM
    //	 12	ENABLE_DVI_TX_1080P
    //	  7	DISABLE_DVI_TX
    //	  6	DISABLE_SBL_BRIGHT_EDGE
    //	  5	DISABLE_EXTPOL
	//	  4	DISABLE_VLOCK_LAMP
	//	  3	DISABLE_VLOCK
	//	  2	DISABLE_VCALIB
	//	  1	DISABLE_VDITHER
	//	  0	DISABLE_HDITHER
    #define DPXREG_VID_CTRL2_PIXELDRIVE         0x8000
    #define DPXREG_VID_CTRL2_PIXELDRIVE_ACCUM   0x4000
    #define DPXREG_VID_CTRL2_PIXELDRIVE_MARKERS 0x2000  // R&D
    #define DPXREG_VID_CTRL2_TX_DVI_1080P       0x1000
    #define DPXREG_VID_CTRL2_NO_SBL_BRIGHT_EDGE 0x0040  // R&D
    #define DPXREG_VID_CTRL2_NO_EXTPOL          0x0020
	#define DPXREG_VID_CTRL2_NO_VLOCK_LAMP      0x0010
	#define DPXREG_VID_CTRL2_NO_VLOCK           0x0008
	#define DPXREG_VID_CTRL2_NO_VCALIB          0x0004
	#define DPXREG_VID_CTRL2_NO_VDITHER         0x0002
	#define DPXREG_VID_CTRL2_NO_HDITHER         0x0001
#define DPXREG_VID_SRC              0x1A2
    //  0x0000  DVI input
    //  0x1000  LVDS input
    //  0x4nn0  Software test pattern showing image from VRAM base address of 0x0nn00000
    //  0x5n00  3D Software test pattern flipping between left/right eye images from VRAM base address of 0x0n000000/0x0n800000
    //  0x8000  Hardware test pattern with RGB ramps
    //  0x9xxx  Hardware test pattern with uniform gray display having 12-bit intensity = xxx
    //  0xAxyz  Hardware drifting bar test pattern with bar advancing x*2 pixels per video frame, and bar/background luminance of y/z (0=black, 0xF=white)
    //  0xBxyz  Same as 0xBxyz, with 2 raster lines out of 4 forced to background colour
    //  0xCxyz  Drifting dots, with dots advancing x*2 pixels per video frame, and bar/background luminance of y/z (0=black, 0xF=white)
    #define DPXREG_VID_SRC_MASK                 0xF000
    #define DPXREG_VID_SRC_DVI                  0x0000
    #define DPXREG_VID_SRC_LVDS                 0x1000
    #define DPXREG_VID_SRC_SWTP                 0x4000
    #define DPXREG_VID_SRC_SWTP_3D              0x5000
    #define DPXREG_VID_SRC_HWTP_RGB_SQUARES     0x8000
    #define DPXREG_VID_SRC_HWTP_GRAY            0x9000
    #define DPXREG_VID_SRC_HWTP_DRIFTING_BAR    0xA000
    #define DPXREG_VID_SRC_HWTP_DRIFTING_BAR2   0xB000
    #define DPXREG_VID_SRC_HWTP_DRIFTING_DOTS   0xC000
#define DPXREG_VID_UNUSED1          0x1A4   // R&D PIXELDRIVE
#define DPXREG_VID_LCD_TIMING       0x1A6
    // Read-only LCD blanking timing
	//	BITS
    //  15:8    HBLANK in steps of 16 pixels
    //   7:0    VBLANK in steps of 1 raster line
#define DPXREG_VID_UNUSED2          0x1A8
    //	BITS
    //   3:0    VBLANK[11:8]
#define DPXREG_VID_BL_POWER_DATA    0x1AA
	//	BITS
	//	15:8	I2C_ADDR
	//	 7:0	I2C_DATA
#define DPXREG_VID_BL_POWER_CTRL    0x1AC
	//	BITS
	//	 15     FAULT, high if any mSilica is reporting LED string faults.
    //  14:10   Unused
    //   9      I2C_WRITE
    //   8      I2C_READ
    //   5:4    I2C_PCB_SEL
	//          0:  Top PCB
	//          ..
	//          3:  Bottom PCB
    //   3:0    I2C_DEV_SEL
    //          0: row1 red mSilica
    //          1: row1 green/blue mSilica
    //          2: row2 red mSilica
    //          3: row2 green/blue mSilica
    //          4: row1 light sensorA
    //          5: row1 light sensorB
    //          6: row2 light sensorA
    //          7: row2 light sensorB
    //          8: row1 temp sensor
    //          9: row2 temp sensor
    #define DPXREG_VID_BL_POWER_FAULT   0x80
#define DPXREG_VID_BL_SCAN_CTRL     0x1AE
	//	BITS
    //  15      Scanning backlight enable
    //  14:12   Scanning backlight phase (in steps of 16 raster lines)
    //  11:8    Scanning backlight width (in steps of 32 raster lines).  As of VHDL rev 10, width is hardcoded to 160 for VP, 148 for VP3D, register readback is 0.
	//	 7:0	PWM inputs for 8 scanning backlight channels

// 8 registers which can accumulate system statistics
#define DPXREG_STATS0               0x1C0
#define DPXREG_STATS1               0x1C2
#define DPXREG_STATS2               0x1C4
#define DPXREG_STATS3               0x1C6
#define DPXREG_STATS4               0x1C8
#define DPXREG_STATS5               0x1CA
#define DPXREG_STATS6               0x1CC
#define DPXREG_STATS7               0x1CE

#define DPXREG_DDR_CSR              0x1DC
	//	BITS
    //  15      INCLUDE_VBL default value of 0 will freeze tachometer calculations during video VBL
    //  11      Overdrive DDR read underflow occurred.  Over/Underflow flags are cleared same time as DDR stats registers.
    //  10      Overdrive DDR write overflow occurred.
    //   9      Video DDR read underflow occurred.
    //   8      Video DDR write overflow occurred.
	//	 7:0	TACH varies from 0-255 as DDR bandwidth usage varies from 0-100%

#define DPXREG_SCHED_STARTSTOP		0x1DE
	// Write "01" or "10" bit pairs to 2-bit fields to generate strobes which start or stop the corresponding schedule.
	// The bits are self-clearing, and the entire register always reads back 0.
	// Using a single STARTSTOP register ensures synchronous operation of different schedule classes.
	//	BITS
	//	13:12	MIC
	//			00: Has no effect on schedule run status
	//			01: Starts schedule
	//			10: Stops schedule
	//			11: Reserved
	//	11:10	AUX
	//	 9:8	AUD
	//	 7:6	DIN
	//	 5:4	DOUT
	//	 3:2	ADC
	//	 1:0	DAC
	#define DPXREG_SCHED_STARTSTOP_MASK			3
	#define DPXREG_SCHED_STARTSTOP_START		1
	#define DPXREG_SCHED_STARTSTOP_STOP			2
	#define DPXREG_SCHED_STARTSTOP_SHIFT_DAC	0
	#define DPXREG_SCHED_STARTSTOP_SHIFT_ADC	2
	#define DPXREG_SCHED_STARTSTOP_SHIFT_DOUT	4
	#define DPXREG_SCHED_STARTSTOP_SHIFT_DIN	6
	#define DPXREG_SCHED_STARTSTOP_SHIFT_AUD	8
	#define DPXREG_SCHED_STARTSTOP_SHIFT_AUX	10
	#define DPXREG_SCHED_STARTSTOP_SHIFT_MIC	12


// Constants which don't correspond to register bits
#define	DPX_DAC_NCHANS	4
#define	DPX_ADC_NCHANS	16

#define	DPX_MIC_SRC_UNKNOWN	0
#define	DPX_MIC_SRC_MIC_IN	1
#define	DPX_MIC_SRC_LINE_IN	2


// USB identification codes
#define DPX_VID	0x04b4
#define DPX_PID	0x4450
#define DPX_DID	0x0000
#define VPX_PID	0x5650
#define PPX_PID	0x5050

// Some EZ-USB internal register addresses
#define EZ_SFR_IOA 0x80
#define EZ_SFR_IOC 0xA0
#define EZ_SFR_OEC 0xB4
#define EZ_SFR_IOE 0xB1
#define EZ_SFR_OEE 0xB6

// USB EP1IN/OUT tram codes, followed by payload descriptions
#define EP1OUT_CONSOLE		'C'		// Console stream from host.  Not really used by EZ FW now.
#define EP1IN_CONSOLE		'c'		// Console stream from EZ FW printf().  Not used anymore.
#define EP1OUT_WRITEBYTE	'W'		// Write byte to EZ SFR or memory.  <addr><datum> for SFR's, or <addr_low><addr_high><datum> for mem.
#define EP1OUT_READBYTE		'R'		// Read byte from EZ SFR or memory.  <addr><datum> for SFR's, or <addr_low><addr_high><datum> for mem.  Datum returned in ^r msg.
#define EP1IN_READBYTE		'r'		// Single data byte returned from 'R' command.
#define EP1OUT_SPI			'S'		// SPI command from host.  All data bytes are sent to SPI, same number of bytes are returned in ^s msg.
#define EP1IN_SPI			's'		// SPI data returned to host.
#define EP1OUT_JTAG			'J'		// JTAG string
#define EP1OUT_RESET		'B'		// EZ will disconnect, wait 1.5 seconds, cause 200 microsecond hardware reset, wait 1.5 seconds, then reconnect
#define EP1OUT_FLUSH		0xFF	// Tram is ignored.  Used by FW to ignore a message, and flush data.

// EP2OUT tram codes.
#define EP2OUT_WRITEALPHA	'A'		// Write video horizontal overlay alpha function table.
#define EP2OUT_WRITEOVD     'D'     // Write pixeldrive LUT (R&D)
#define EP2OUT_WRITEEDID	'E'		// Write EDID bytes.
#define EP2OUT_READREGS		'G'		// Read register set from FPGA.  Data returned in ^g msg.
#define EP2OUT_WRITEREGS	'H'		// Write 16-bit registers. <first_reg_num><data0_low><data0_high><data1_low>...
#define EP2OUT_READRAM		'M'		// Read DDR RAM.  <addr_low><addr_midl><addr_midh><addr_high><len_low><len_high>.  Data returned in ^m msg.
#define EP2OUT_WRITERAM		'N'		// Write DDR RAM. <addr><data0><data1><data2>...
#define EP2OUT_READI2C		'I'		// Read one I2C register from CODEC.  Data returned in ^i msg.
#define EP2OUT_WRITEI2C		'J'		// Write one or more I2C registers in CODEC. <first_reg_num><data0><data1>...
#define EP2OUT_READVIDLINE	'L'		// Read 16k byte video line buffer.  Data returned in ^l msg.
#define EP2OUT_WRITEPSYNC	'O'		// Define sequence of pixels which make up a pixel sync event.
#define EP2OUT_PSYNC		'P'		// Pause USB command processing until a pixel sync event, passing 16-bit vsync timeout.
#define EP2OUT_SPI			'S'		// Commands/Data sent to FPGA for accessing SPI
#define EP2OUT_WRITECLUT	'T'		// Write 256 R/G/B entries
#define EP2OUT_VSYNC		'V'		// Pause USB command processing until next leading edge of video vertical sync pulse.
									// Note that users could synchronize their program to VSYNC by following this command with a read register command.
// EP6IN tram codes.
#define EP6IN_READREGS		'g'		// 480 byte register set returned from 'G' command.
#define EP6IN_READRAM		'm'		// RAM data returned from 'M' command.
#define EP6IN_READI2C		'i'		// I2C data returned from 'I' command.
#define EP6IN_READVIDLINE	'l'		// 16k byte video line buffer returned from 'L' command.
#define EP6IN_SPI			's'		// SPI data returned to host from FPGA.

// Special characters sent from EZ to host console.
// Could use this for errors that would occur in large burst, so no point in trying to print nice strings.
#define EP1IN_ERR_HAT		1		// EP1OUT tram interpreter was expecting a hat, but got something else
#define EP1IN_ERR_NOP		2		// EP1OUT tram interpreter received a command code of 0
#define EP1IN_ERR_LEN		3		// EP1OUT tram interpreter received an unexpected tram length
#define EP1IN_ERR_CMD		4		// EP1OUT tram interpreter received an unrecognized command code

// This is the largest payload that can be written with a single EP2OUT_WRITERAM command.
// (since we limit trams to 64 kB, and EP2OUT_WRITERAM has an 8-byte header).
// EP2OUT_READRAM could take a slightly larger payload (0xfffc), since its header is only 4 bytes,
// but I'll simplify my life and make the maximum payload the same for both directions.
#define DPX_RWRAM_BLOCK_SIZE	0xfff8

// VIEWPixx/DATAPixx SPI address map
#define SPI_ADDR_VPX_FPGA   0x000000
#define SPI_ADDR_VPX_LEDCUR 0x7B0000
#define SPI_ADDR_VPX_VCALIB 0x7C0000
#define SPI_ADDR_VPX_ANALOG 0x7D0000
#define SPI_ADDR_VPX_EDID   0x7E0000        // Only used by DATAPixx
#define SPI_ADDR_VPX_TEXT   0x7F0000

#define SPI_ADDR_DPX_FPGA   0x010000		// For DATAPixx Lattice SPIm primary image;
#define SPI_ADDR_DPX_TEXT   0x1F0000
#define SPI_ADDR_DPX_EDID   0x3E0000
#define SPI_ADDR_DPX_ANALOG 0x3F0000


// Some C types
#ifndef NULL
	#define NULL 0
#endif

// Define fixed length data types.
// Be careful here, because "short" and "long" types do not have fixed length.
// For example, a "long" can be implemented as 64 bits on some systems.
// We'll try to map to existing fixed-length types whenever possible.
// Use typedef's instead of define's for multi-word,
// so that it works for C++ function style type casts.
// MacTypes.h defines these values as typedef's which I can't detect,
// so just leave these defs out if MacTypes.h has already been included.
#ifndef __MACTYPES__

#ifndef UInt16
#ifdef uint16_t
#define UInt16 uint16_t
#else
typedef unsigned short UInt16;
#endif
#endif

#ifndef SInt16
#ifdef int16_t
#define SInt16 int16_t
#else
typedef signed short SInt16;
#endif
#endif

#ifndef UInt32
#ifdef uint32_t
#define UInt32 uint32_t
#else
#if __LP64__
typedef unsigned int UInt32;
#else
typedef unsigned long UInt32;
#endif
#endif
#endif
#endif

// 2MB is enough for DP, but VP requires 2,772,349 bytes.  We'll allocate 3MB.
#define CONFIG_BUFFER_SIZE  0x00300000
extern unsigned char configBuffer[CONFIG_BUFFER_SIZE];
extern unsigned char configBuffer2[CONFIG_BUFFER_SIZE];

extern int				dpxError;								// Global error return
extern int				dpxDebugLevel;							// Global debug level
extern int				dpxActivePSyncTimeout;					// When not -1, gives the current psync register readback timeout.
extern unsigned short	dpxSavedRegisters[DPX_REG_SPACE/2];		// Local copy of DATAPixx register for save/restore
extern unsigned short	dpxRegisterCache[DPX_REG_SPACE/2];		// Local copy of DATAPixx register set read over USB
extern int				dpxRegisterModified[DPX_REG_SPACE/2];	// When set, means that value in dpRegisterCache[] must be written back to DATAPixx.

// Get number of USB retries/fails for each endpoint and direction
int				DPxGetEp1WrRetries(void);
int				DPxGetEp1RdRetries(void);
int				DPxGetEp2WrRetries(void);
int				DPxGetEp6RdRetries(void);
int				DPxGetEp1WrFails(void);
int				DPxGetEp1RdFails(void);
int				DPxGetEp2WrFails(void);
int				DPxGetEp6RdFails(void);

void			EZUploadRam(unsigned char *buf, int start, int len);
void			EZUploadByte(int addr, unsigned char val);
int				EZWriteByte(unsigned short addr, unsigned char val);
int				EZReadByte(unsigned short addr);
int				EZWriteSFR(unsigned char addr, unsigned char val);
int				EZReadSFR(unsigned char addr);
int				EZWriteEP1Tram(unsigned char* txTram, unsigned char expectedRxTram, int expectedRxLen);
int				EZReadEP1Tram(unsigned char expectedTram, int expectedLen);
int				EZWriteEP2Tram(unsigned char* txTram, unsigned char expectedRxTram, int expectedRxLen);
int				EZReadEP6Tram(unsigned char expectedTram, int expectedLen);
void			EZPrintConsoleTram(unsigned char* tram);

// Callback functions
typedef         void (*PercentCompletionCallback)(int percentCompletion);
typedef			void (*StringCallback)(const char* string);

// Low-level SPI access
int             DPxSpiHasVpxFpgaCtrl(void);
int             DPxSpiStart(void);
int             DPxSpiStop(void);
int             DPxSpiRead(int spiAddr, int nReadBytes, unsigned char* readBuffer, PercentCompletionCallback percentCompletionCallback);
int             DPxSpiReadNoStartStop(int spiAddr, int nReadBytes, unsigned char* readBuffer, PercentCompletionCallback percentCompletionCallback);
int             DPxSpiWrite(int spiAddr, int nWriteBytes, unsigned char* writeBuffer, PercentCompletionCallback percentCompletionCallback);
int             DPxSpiErase(int spiAddr, int nEraseBytes, PercentCompletionCallback percentCompletionCallback);
void            DPxSpiModify(int spiAddr, int nWriteBytes, unsigned char* writeBuffer);

int				DPxIsOpen(void);
int				DPxHasRawUsb(void);
void			DPxReset(void);
int				DPxProgramFPGA(unsigned char* configBuff, int configFileSize, int doProgram, int doVerify, int reconfigFpga, StringCallback statusCallback);
void			DPxEdidWrite(int mode);
void			DPxCalibRead(void);
void			DPxCalibWrite(void);
void			DPxEnableCalibReload(void);						// Reload DAC and ADC hardware calibration tables
int				DPxStringToInt(char* string);

void			DPxUsbScan(int doPrint);						// Scan USB tree looking for a DATAPixx
void			DPxBuildUsbMsgBegin(void);						// Start accumulating a composite USB message
void			DPxBuildUsbMsgWriteRegs(void);					// Append USB message to write modified registers from local cache to DATAPixx
void			DPxBuildUsbMsgReadRegs(void);					// Append composite USB message to read Datapixx register set
void			DPxBuildUsbMsgVideoSync(void);					// Append message to freeze Datapixx USB message treatment until vertical sync
void			DPxBuildUsbMsgPixelSync(int nPixels, unsigned char* pixelData, int timeout); // Append message to freeze USB message treatment until pixel sync
void			DPxBuildUsbMsgEnd(void);						// Transmit the composite USB message we just built

void			DPxSetReg16(int regAddr, int regValue);			// Set a 16-bit register's value in dpRegisterCache[]
int				DPxGetReg16(int regAddr);						// Read a 16-bit register's value from dpRegisterCache[]
void			DPxSetReg32(int regAddr, unsigned regValue);	// Set a 32-bit register's value in dpRegisterCache[]
unsigned		DPxGetReg32(int regAddr);						// Read a 32-bit register's value from dpRegisterCache[]
int				DPxGetRegSize(int regAddr);						// Returns the size of a register in bytes

void			DPxSetCodecReg(int regAddr, int regValue);		// Set an 8-bit I2C register in audio CODEC IC
int				DPxGetCodecReg(int regAddr);					// Read an 8-bit I2C register from audio CODEC IC
int				DPxGetCachedCodecReg(int regAddr);				// Read an 8-bit I2C register from CODEC write cache, instead of from hardware
int				DPxAudCodecVolumeToReg(double volume, int dBUnits); // Conversions between volume and CODEC register representation
double			DPxAudCodecRegToVolume(int reg, int dBUnits);
void			DPxSetDviReg(int regAddr, int regValue);		// Set an 8-bit I2C register in Silicon Image DVI IC
int				DPxGetDviReg(int regAddr);						// Read an 8-bit I2C register from Silicon Image DVI IC
void			DPxSetI2cReg(int regAddr, int regValue);		// Set an 8-bit I2C register
int				DPxGetI2cReg(int regAddr);						// Read an 8-bit I2C register

void			DPxStartSPI(void);								// Setup SPI flash operation
void			DPxStopSPI(void);								// Close SPI flash operation
void			DPxSpiWaitWriteDone(void);						// Wait until "Write In Progress" bit in SPI flash is inactive

double			DPxMakeFloat64FromTwoUInt32(UInt32 highUInt32, UInt32 lowUInt32);	// Concatenate two unsigned 32-bit numbers and return as a 64-bit floating point number
                                                                                    // Note that there may be some loss of precision, as an IEEE 64-bit float only has a 53 bit mantissa.


//	Some convenient error macros
#define AssertFalse(value)																	\
	do {																					\
		if (value) {																		\
			DPxDebugPrint1("Fail: [%s] was true\n", #value);								\
			return;																			\
		}																					\
	} while (0)

#define AssertTrue(value)																	\
	do {																					\
		if (!(value)) {																		\
			DPxDebugPrint1("Fail: [%s] was false\n", #value);								\
			return;																			\
		}																					\
	} while (0)

#define ReturnIfError(value)																\
	do {																					\
		(value);																			\
		if (DPxGetError() != DPX_SUCCESS) {													\
			DPxDebugPrint2("Fail: [%s] failed with error %d\n", #value, DPxGetError());		\
			return;																			\
		}																					\
	} while (0)

#define Return0IfError(value)																\
	do {																					\
		(value);																			\
		if (DPxGetError() != DPX_SUCCESS) {													\
			DPxDebugPrint2("Fail: [%s] failed with error %d\n", #value, DPxGetError());		\
			return 0;																		\
		}																					\
	} while (0)

#define CheckUsb() do { if (!dpxHdl) DPxDebugPrint0("Fail: dpxHdl is NULL!\n"); } while (0)

//	Convenient macros for conditional printing of debug messages.
//	GNU supports __VA_ARGS__ macro (also called Variadic macros) which allow a variable number of macros.
//	Unfortunately, MS only supports the construct since Visual Studio 2005.
//	Only way to support previous MS compilers is to make macros which explicitly state the number of arguments.  Ugly, but true.
//#define DPxDebugString(string)					do { if (DPxGetDebug()) fprintf(stderr, string); } while (0)
//#define DPxDebugPrint(format, ...)				do { if (DPxGetDebug()) fprintf(stderr, format, __VA_ARGS__); } while (0)
#define DPxDebugPrint0(string)						do { if (DPxGetDebug()) fprintf(stderr, string); } while (0)
#define DPxDebugPrint1(format, arg1)				do { if (DPxGetDebug()) fprintf(stderr, format, arg1); } while (0)
#define DPxDebugPrint2(format, arg1, arg2)			do { if (DPxGetDebug()) fprintf(stderr, format, arg1, arg2); } while (0)
#define DPxDebugPrint3(format, arg1, arg2, arg3)	do { if (DPxGetDebug()) fprintf(stderr, format, arg1, arg2, arg3); } while (0)


//	Miscellaneous convenience macros
#define LSB(x)	((unsigned  char)(((unsigned short)(x) >>  0) & 0x00FF))
#define MSB(x)	((unsigned  char)(((unsigned short)(x) >>  8) & 0x00FF))
#define LSW(x)	((unsigned short)(((unsigned long )(x) >>  0) & 0xFFFF))
#define MSW(x)	((unsigned short)(((unsigned long )(x) >> 16) & 0xFFFF))

