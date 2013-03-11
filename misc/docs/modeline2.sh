#!/bin/sh

#xrandr --newmode "1280x1024_60.00"  109.00  1280 1368 1496 1712  1024 1027 1034 1063 -hsync +vsync
#xrandr --addmode DVI1 1280x1024_60.00
#xrandr --output DVI1 --mode 1280x1024_60.00

xrandr --newmode "1024x766_66.50"   71.25  1024 1080 1184 1344  766 769 779 799 -hsync +vsync
xrandr --addmode DVI1 1024x766_66.50
xrandr --output DVI1 --mode 1024x766_66.50

