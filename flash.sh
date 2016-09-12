
# Older versions of Micropython used 561152
FS_OFFSET=589824

esptool.py --baud 38400 write_flash $FS_OFFSET fs.img
