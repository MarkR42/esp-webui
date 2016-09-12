#!/usr/bin/env python3
#
# Truncate an image file so that it stops after the last
# non-empty sector.

import os
import sys

def truncate_image(imgfn):
    f = open(imgfn, 'rb+')
    sector_size = 4096
    
    empty_sector = b'\0' * sector_size 
    last_nonempty = 0
    while True:
        sectorpos = f.tell()
        sector = f.read(sector_size)
        if len(sector) < sector_size:
            break
        if sector != empty_sector:
            last_nonempty = sectorpos
    print("Last nonempty sector begins at %d" % (last_nonempty))
    f.truncate(last_nonempty + sector_size)
    f.close()
    
    
truncate_image(sys.argv[1])
