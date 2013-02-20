#!/usr/bin/python2 -O

import sys

if len(sys.argv) == 1:

    print("""
    Welcome to the HRL utility program. From here, various scripts can be
    accessed for calibrating and testing configurations of experiment hardware.
    Type \'hrl-util [command]\' in order to access the provided functionality. 

    Provided commands are:

        tests - Simple hardware and software tests
    """)

else:

    args = sys.argv[1:]

    if args[0] == 'tests':

        if len(args) == 1:
            print("""
            Tests are simple programs to ensure that HRL software and hardware
            is working correctly.

            Currently implemented commands are:

                standard - Basic test for a normal computer
                datapixx - Basic test for a computer with DATApixx
            """)
        elif args[1] == 'standard':
            import hrl.util.tests.standard
        elif args[1] == 'datapixx':
            import hrl.util.tests.datapixx
