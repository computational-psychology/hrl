#!/usr/bin/env python

import distutils.core
import os

if __name__ == '__main__':
    distutils.core.setup(
        name='hrl',
        description='Library for psychophysics experiments, with support for high-resolution luminance CRT monitors (Siemens SMM series) ',
        version='0.8.2',
        author='Sacha Sokoloski',
        author_email='sacha@cs.toronto.edu',
        maintainer='Guillermo Aguilar',
        maintainer_email='guillermo.aguilar@tu-berlin.de',
        license='GPL2',
        url='https://github.com/computational-psychology/hrl',
        package_dir = {'hrl' : 'lib', 'hrl.util' : 'bin/util'},
        packages=('hrl','hrl.graphics','hrl.inputs','hrl.photometer'
            ,'hrl.util','hrl.util.tests','hrl.util.lut'),
        scripts=['bin/hrl-util'])


        
