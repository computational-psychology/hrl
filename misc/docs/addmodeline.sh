#!/bin/sh

cvt 1024 766 133
xrandr --newmode "1024x766_133.00"  155.25  1024 1112 1216 1408  766 769 779 830 -hsync +vsync
xrandr --addmode DVI1 1024x766_133.00
xrandr --output DVI1 --mode 1024x766_133.00

#xgamma -gamma 2.305
