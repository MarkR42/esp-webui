ESP-WEBUI
---------

What is it?

It's a Micropython implementation of a HTTP 1.0 web server which has the following features:

* Serves static content from the filesystem
* Handles uploads using PUT method
* Javascript drag-and-drop and form-based uploads (which uses the PUT method)

It is written in 100% pure Micropython for the ESP-8266. 

How do I use it?

1. Install Micropython on your ESP-8266. 

2. Run the script "build.sh" - this generates a file "fs.img" which is a DOS FAT12
    filesystem image.

    Copy the contents of fs.img into the ESP flash at the appropriate offset.

    I've written a script "flash.sh" which might work. It works for me.

    The offset might change in future versions of Micropython. I don't know how
    to find it dynamically (yet)

3. Restart your ESP, and connect to its web server with a web browser, e.g.
    (default) http://192.168.1.4/

You can then see a directory listing, and you can drag & drop files to upload them,
click on files to download them etc.

Who wrote it?

Unless otherwise indicated, all code written by me, Mark Robson <markxr@gmail.com>

What is the licence?

It is licenced unless otherwise indicated, under the permissive MIT licence. See 
file LICENSE.txt for more details.

