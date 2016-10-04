#
# Super-small http server, suitable for Micropython.
#
# NOTES:
# 1. Can only serve 1 request at a time.
# 2. mime-types hard-coded.

import socket
import os
import gc
import sys
import time
import network
import ntptime
from httphandlers import send_err, send_bad_request, handle_bad_method, handle_put

def accept_conn(sock):
    try:
        clisock, *junk = sock.accept()
        del junk
    except OSError:
        # Timeout?
        return
    # Set a timeout, so that if we don't receive a proper request
    # in the time, we can close the socket and serve someone else.
    clisock.settimeout(10.0)
    
    handler = handle_bad_method
    content_length = 0
    try:            
        # Try read a HTTP/1.0 request.
        # We need to find where the GET line ends - this should be the
        # first \r or \n char.
        # Because we are incredibly short of memory, limit the length of this.
        firstline = clisock.readline(60)
        if not (b'\r' in firstline or b'\n' in firstline):
            # Request too long.
            return send_bad_request(clisock)
        # Try to parse out URI and http version.
        space0 = firstline.find(b' ')
        space1 = firstline.rfind(b' ')
        http_ver = firstline[space1 + 1:]
        uri = firstline[space0 + 1 : space1]
        method = firstline[:space0]
        # Consume rest of headers. Ignore.
        while True:
            line = clisock.readline(60)
            if len(line) == 0 or line[0] in (10, 13): # cr or lf: end of headers
                break
            # Get content-length.
            line = line.lower()
            if line.startswith(b'content-length:'):
                content_length = int(line[line.find(b':') + 1:])
        del line
        # Check for bad things.
        if not http_ver.startswith(b'HTTP'): # http 0.9 request?
            return send_bad_request(clisock)
        # Check for some types of bad uri.
        if (b'\0' in uri or
            b'../' in uri or
            b'/./' in uri):
                return send_err(clisock, 403, b'Denied')

        if method == b'GET':
            handler = handle_get
        if method == b'PUT':
            handler = handle_put
        if method == b'POST':
            handler = handle_post
            
        print(firstline)
        if not uri.startswith(b'/'):
            return send_err(clisock, 404, b'Not found0')
        # So far so good.
    except OSError:
        # Timeout reading uri?
        clisock.close()
        return
    return handler(clisock, uri, content_length)
        
def handle_post(clisock, uri, content_length):
    # Serve uri to client.
    if maybe_despatch_module(clisock, uri, content_length, 'do_post'):
        return # OK
    # Otherwise bad method.
    return handle_bad_method(clisock, uri, content_length)     
        
def handle_get(clisock, uri, content_length):
    # Serve uri to client.
    # If we are despatching a module, do that instead.
    if maybe_despatch_module(clisock, uri, content_length, 'do_get'):
        return
     
    # Check file exists.
    uri_without_slash = uri
    ends_with_slash = False
    if uri.endswith(b'/'):
        ends_with_slash = True
        uri_without_slash = uri[:-1]
    try:
        s = os.stat(uri_without_slash)
    except OSError:
        # Probably does not exist.
        return send_err(clisock, 404, b'File not found')
    # If it's a directory?
    if s[0] & 0x4000:
        if ends_with_slash:
            # Dir listing
            return dir_index(clisock, uri_without_slash)
        else:
            return dir_redirect(clisock, uri)
    file_size = s[6]
    # Ok, it's a plain file.
    try:
        fh = open(uri, 'rb')
    except OSError:
        return send_err(clisock, 404, b'Cannot open file')
    with fh:
        # Send HTTP response: static file.
        clisock.write(b'HTTP/1.0 200 OK\r\n')
        # response headers
        clisock.write(b'Content-length: %d\r\n' % (file_size,))
        clisock.write(b'Content-type: %s\r\n' % (get_content_type(uri),))
        # Cause file to be cached by browser: this is important to avoid
        # delays when the same file must be fetched repeatedly.
        # 
        # But it's also important to avoid stale files. Ideally only
        # do this for files which are not likely to change.
        clisock.write(b'Cache-control: public, max-age=3600\r\n')
        clisock.write(b'\r\n')
        while True:
            chunk = fh.read(64)
            if len(chunk) == 0:
                break # EOF
            clisock.write(chunk)
        clisock.close()
    
def get_content_type(uri):
    ct = b'text/plain' # default
    dotpos = uri.rindex(b'.')
    if dotpos > -1:
        ext = uri[dotpos + 1:]
        ext = ext.lower()
        if ext.startswith(b'htm'):
            ct = b'text/html'
        if ext in (b'jpeg', b'jpg'):
            ct = b'image/jpeg'
        if ext in (b'png', b'gif'):
            ct = b'image/' + ext
        if ext == b'css':
            ct = b'text/css'
        if ext == b'js':
            ct = b'application/x-javascript'
            
    if ct.startswith(b'text'):
        ct += b'; charset=utf-8'
            
    return ct
        
def dir_redirect(clisock, uri):
    # Send a redirect from /something to /something/
    clisock.write(b'HTTP/1.0 301 Moved\r\n')
    newuri = uri + b'/'
    clisock.write(b'Location: ' + newuri)
    clisock.write(b'\r\n\r\n')
    clisock.close()        

def maybe_despatch_module(clisock, uri, content_length, handler_name):
    # For GET, call a module.
    # URI could be /mod/somemodule/some junk.
    if not uri.startswith(b'/mod/'):
        return False
    modname = uri[5:]
    slashpos = modname.find(b'/')
    if slashpos != -1:
        modname = modname[:slashpos]

    # Ensure module name starts with mod_ and is a unicode str.
    modname = 'mod_' + str(modname, 'ascii')
    # Try to load module.
    try:
        # Use empty dict for globals, so we don't have a ref.
        exec('import ' + modname, {})
    except ImportError:
        send_err(clisock, 404, 'no module')
        return True
    
    try:
        handler = getattr(sys.modules[modname], handler_name)
    except AttributeError:
        send_err(clisock, 404, 'no handler')
        return True
    
    # despatch handler.
    try:
        handler(clisock, uri, content_length)
    finally:
        # Free module.
        del sys.modules[modname]
    clisock.close()
    return True

# Show a directory index, for an existing directory.    
def dir_index(clisock, uri):
    clisock.write(b'HTTP/1.0 200 OK\r\n'
        b'Content-type: text/html; charset=utf-8\r\n'
        b'\r\n')
    
    title = b'Directory listing ' + escape_filename(uri) + b'/'
    clisock.write(b'<!DOCTYPE html><html><head><title>')
    clisock.write(title)
    clisock.write(b"""</title>
        <link rel="stylesheet" href="/webui/ui.css">
        <script src="/webui/ui.js" defer></script></head><body>""")
    clisock.write(b'<h1>');clisock.write(title);
    clisock.write(b'</h1><ul>')
    # Parent directory (if not top)
    if len(uri) >0:
        clisock.write(b'<li><a href="../">../</a> (parent dir)</li>')
    # List files in the dir from uri.
    fnames = sorted(os.listdir(uri))
    # Show directories first.
    odd = False
    for show_dir in (True, False):
        for fn in fnames:
            # Stat it, to check if it's a file or another
            # directory.
            s = os.stat(b'/'.join( (uri, fn)))
            is_dir = bool(s[0] & 0x4000)
            if is_dir == show_dir:
                fn_escaped = escape_filename(fn)
                if odd:
                    cssclass = b'odd'
                else:
                    cssclass = b''
                if show_dir:
                    fn_escaped += b'/'
                    cssclass += b' d'
                else:
                    cssclass += b' f'
                clisock.write(b'<li class="%s"><a href="' % (cssclass,))
                clisock.write(fn_escaped)
                clisock.write(b'">')
                clisock.write(fn_escaped)
                clisock.write(b'</a>')
                # file size:
                if not is_dir:
                    clisock.write(b'<span class="filemeta">%d b</span>'
                        % (s[6],) )
                clisock.write(b'</li>\n')
                odd = (not odd)
        if show_dir:
            # Space between dirs and files
            clisock.write(b'</ul><ul>')
    clisock.close()

def escape_filename(fn):
    b = bytearray()
    for c in fn:
        # Entites we must map: ", &, < 
        if c in (34, 38, 60):
            # use decimal entity 
            # e.g. &#34;
            b += b'&#'
            b += str(c)
            b += b';'
        else:
            b.append(c)
    return b
    
def periodic_tasks():
    # Called every few seconds
    # Check if the time has been set.
    epoch = time.mktime((2016,1,1,0,0,0,0,0,0))
    time_is_set = ( time.time() > epoch )
    if not time_is_set:
        # Check if the network STA is configured.
        sta = network.WLAN(network.STA_IF)
        if sta.isconnected():
            #Trying to sync with ntp
            try:
                ntptime.settime()
            except OSError:
                print("Failed to sync with ntp")

def start_server():
    print("Starting web server")
    sock = socket.socket()
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind( ('', 80) ); sock.listen(1)
    sock.settimeout(5.0)
    
    print("Synchronous web server running...")
    gc.collect()
    print("gc.mem_free=", gc.mem_free())
    t0 = time.ticks_ms()
    try:
        while True:
            accept_conn(sock)
            now = time.ticks_ms()
            if (now - t0) > 8000:
                periodic_tasks()
                t0 = now
    finally:
        sock.close()
