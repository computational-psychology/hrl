#!/usr/bin/env python

import distutils.core
import os

if __name__ == '__main__':
    distutils.core.setup(
        name='hrl',
        description='Library for designing psychophysics experiments',
        version='0.5',
        author='Sacha Sokoloski',
        author_email='sacha@cs.toronto.edu',
        license='GPL2',
        url='https://github.com/TUBvision/hrl',
        package_dir = {'hrl' : 'lib', 'hrl.util' : 'bin/util'},
        packages=('hrl','hrl.graphics','hrl.inputs','hrl.photometer'
            ,'hrl.util','hrl.util.tests','hrl.util.lut'),
        scripts=['bin/hrl-util'])


        
