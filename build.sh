
# Create a msdos floppy disc image, which we will write to the
# flash of the esp8266.

rm -f fs.img

# Micropython uses a dos fs at a hard-coded (?) offset.

# Use a wacky mformat command to initialise the drive.

# Note that we seem to need a 4096 sector size, or Micropython
# won't access the fs.
# -S = sector size.
# -s = sectors per cluster (smaller is better usually)
# -i = volume id, -n = volume name
# Note that the block count, appears to be in kilobytes, not
# the sector size (of 4096).
#
# This filesystem image must not be bigger than the free space
# in the ESP's flash. My ESP12 modules all have 4096k flash, but
# some of that is reserved for use by the ESP firmware (very close to the end)
# and some is used already by Micropython (the first ~ 512k)
mkfs.fat -C -f 1 -S 4096 -s 1 fs.img 1024 -i 0000002b -n 'ESP-WEBUI'

# Make tmp directory to build the fs.
rm -rf tmp
mkdir tmp

# Create a file with the build time
# In seconds since 1/1/2000
TZ=UTC python3 -c 'import time; print(int(time.time() - time.mktime( (2000,1,1,0,0,0,0,0,0))))' > tmp/build.tim

cp -vr fsroot/* tmp/
# Remove any pycache created by "real" python3 
rm -rf tmp/__pycache__
# Remove test.html, it's not needed on the device.
rm -f tmp/test.html
mcopy -i fs.img -s tmp/* :: 

# Create some directories
# mmd -i fs.img data1 data2

minfo -i fs.img :: 
mdir -i fs.img :: 

./truncate_image.py fs.img
