#!/usr/bin/python2 -O

import sys

args = sys.argv[1:]

if args[0] == 'tests':
    if args[1] == 'simple':
        import hrl.util.tests.simple
