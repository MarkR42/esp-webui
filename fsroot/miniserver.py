#
# Super-small http server, suitable for Micropython.
#
# NOTES:
# 1. Can only serve 1 request at a time.
# 2. mime-types hard-coded.

import socket
import os

def send_err(clisock, code, reason):
    print(code, reason)
    clisock.write('HTTP/1.0 ')
    clisock.write(str(code).encode('ascii'))
    clisock.write(' ')
    clisock.write(reason)
    clisock.write('\r\n\r\n')
    clisock.write(reason)
    clisock.close()
    
def send_bad_request(clisock):
    return(send_err(clisock, 400, b'Bad request'))
        
def accept_conn(sock):
    clisock, *junk = sock.accept()
    del junk
    clisock.settimeout(10.0)
    
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
            if len(line) == 0:
                break
            if line[0] in (10, 13): # cr or lf: end of headers
                break
        del line
        # Check for bad things.
        if not http_ver.startswith(b'HTTP'): # http 0.9 request?
            return send_bad_request(clisock)
        if method != b'GET':
            return send_err(clisock, 405, b'Bad Method')
        print(firstline)
        if not uri.startswith(b'/'):
            return send_err(clisock, 404, b'Not found0')
        # So far so good.
    except OSError:
        # Timeout reading uri?
        clisock.close()
        return
    return serve_response(clisock, uri)
        
def serve_response(clisock, uri):
    # Serve uri to client.
    # Check for some types of bad uri.
    if (b'\0' in uri or
        b'../' in uri or
        b'/./' in uri):
            return send_err(clisock, 403, b'Denied')
     
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
        # Send HTTP response
        clisock.write(b'HTTP/1.0 200 OK\r\n')
        # response headers
        clisock.write(b'Content-length: %d\r\n' % (file_size,))
        clisock.write(b'Content-type: %s\r\n' % (get_content_type(uri),))
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
        
def dir_index(clisock, uri):
    clisock.write(b'HTTP/1.0 200 OK\r\n')
    clisock.write(b'Content-type: text/html; charset=utf-8\r\n')        
    clisock.write(b'\r\n')
    
    title = b'Directory listing ' + escape_filename(uri) + b'/'
    clisock.write(b'<!DOCTYPE html><html><head><title>')
    clisock.write(title)
    clisock.write(b'</title></head><body>')
    clisock.write(b'<h1>');clisock.write(title);
    clisock.write(b'</h1><ul>')
    # Parent directory (if not top)
    if len(uri) >0:
        clisock.write(b'<li><a href="../">../</a> (parent dir)</li>')
    # List files in the dir from uri.
    fnames = sorted(os.listdir(uri))
    # Show directories first.
    for show_dir in (True, False):
        for fn in fnames:
            # Stat it, to check if it's a file or another
            # directory.
            s = os.stat(b'/'.join( (uri, fn)))
            is_dir = bool(s[0] & 0x4000)
            if is_dir == show_dir:
                fn_escaped = escape_filename(fn)
                if show_dir:
                    fn_escaped += b'/'
                clisock.write(b'<li><a href="')
                clisock.write(fn_escaped)
                clisock.write(b'">')
                clisock.write(fn_escaped)
                clisock.write(b'</a></li>\n')
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

def start_server():
    print("Starting web server")
    sock = socket.socket()
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind( ('', 80) ); sock.listen(1)
    
    if False:
        # Set asynchronous handler
        sock.setsockopt(socket.SOL_SOCKET, 20, accept_conn)
        print("Asynchronous web server setup.")
    else:
        print("Synchronous web server running...")
        try:
            while True:
                accept_conn(sock)
        finally:
            sock.close()
