#!/usr/bin/env python

import distutils.core

if __name__ == '__main__':
    distutils.core.setup(
        name='hrl',
        description='Library for designing psychophysics experiments',
        version='0.3',
        author='Sacha Sokoloski',
        author_email='sacha@cs.toronto.edu',
        license='GPL2',
        url='https://github.com/TUBvision/hrl',
        packages=('hrl','hrl.graphics','hrl.inputs','hrl.util','hrl.util.tests'),
        scripts=['scripts/hrl-util'])
