#!/usr/bin/python2 -O

import sys

args = sys.argv[1:]

if len(args) == 0 or args[0] == '--help':

    print("""
    Welcome to the HRL utility program. From here, various scripts can be
    accessed for calibrating and testing configurations of experiment hardware.
    Type \'hrl-util [command]\' in order to access the provided functionality.
    Adding the switch --help at the end will display the command specific help
    text.

    Provided commands are:

        tests - Simple hardware and software tests
        lut - Scripts for generating gamma correction lookup tables
    """)

else:

    if args[0] == 'tests':

        if len(args) == 1 or args[1] == '--help':
            print("""
    Tests are simple scripts to ensure that HRL software and hardware
    is working correctly.

    Currently implemented commands are:

        standard - Basic test for a normal computer
        datapixx - Basic test for a computer with DATApixx
        optical - Take a single reading from an OptiCAL
        class - Tests the HRL class with normal hardware
            """)
        elif args[1] == 'standard':
            import hrl.util.tests.standard
        elif args[1] == 'datapixx':
            import hrl.util.tests.datapixx
        elif args[1] == 'optical':
            import hrl.util.tests.optical
        elif args[1] == 'class':
            import hrl.util.tests.classtest

    elif args[0] == 'lut':

        if len(args) == 1 or args[1] == '--help':

            print("""
    When considering monitors, one may distinguish between the actual
    luminance produced by the monitor, and the scale free 'intensity'
    that the software and computer request of the monitor. In general,
    luminance is not a simple, linear function of the requested
    intensity (typically it's a so called 'gamma function') which means
    that it is not immediately clear what luminances subjects are being
    subjected to.

    The scripts provided here can be used to generate a lookup table
    (LUT) which can in turn be used in combination with the HRL
    library to linearize the relationship between intensity and
    luminance. This allows more precise control of displayed
    luminances.

    Currently implemented commands are:

        measure - Measure the relationship between intensity and luminance
            creates: 'samples.csv'
        smooth - Apply kernel smoothing to generate an approximate function
            creates: 'gamma.csv'
        linearize - Invert the function approximation to generate a final lookup table
            creates: 'lut.csv'
        plot - Generate helpful plots for the three generated csv files
        verify - Take luminance measures given a lookup table
            """)
        elif args[1] == 'measure':
            from hrl.util.lut.measure import measure
            measure(args[2:])

        elif args[1] == 'smooth':
            from hrl.util.lut.smooth import smooth
            smooth(args[2:])

        elif args[1] == 'linearize':
            from hrl.util.lut.linearize import linearize
            linearize(args[2:])

        elif args[1] == 'plot':
            from hrl.util.lut.plot import plot
            plot(args[2:])

        elif args[1] == 'verify':
            from hrl.util.lut.verify import verify
            verify(args[2:])
