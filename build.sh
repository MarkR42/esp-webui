
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
mkfs.fat -C -f 1 -S 4096 -s 1 fs.img 1024 -i 0000002b -n 'ESP-WEBUI'

# Make tmp directory to build the fs.
rm -rf tmp
mkdir tmp

# Create a file with the build time
# In seconds since 1/1/2000
TZ=UTC python3 -c 'import time; print(int(time.time() - time.mktime( (2000,1,1,0,0,0,0,0,0))))' > tmp/build.tim

cp -vr fsroot/* tmp/
rm -rf tmp/__pycache__
mcopy -i fs.img -s tmp/* :: 

# Create some directories
# mmd -i fs.img data1 data2

minfo -i fs.img :: 
mdir -i fs.img :: 

./truncate_image.py fs.img
