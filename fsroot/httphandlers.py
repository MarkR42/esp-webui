
import os

def send_err(clisock, code, reason = b'Internal error'):
    print(code, reason)
    clisock.write(b'HTTP/1.0 ')
    clisock.write(str(code).encode('ascii'))
    clisock.write(b' ')
    clisock.write(reason)
    clisock.write(b'\r\nContent-type: text/plain; charset=utf-8\r\n\r\n')
    clisock.write(reason)
    clisock.close()
    
def send_bad_request(clisock):
    return(send_err(clisock, 400, b'Bad request'))
    
def handle_bad_method(clisock, uri, content_length):
    return send_err(clisock, 405, b'Bad Method')
        
def maybe_delete(fn):
    try:
        os.remove(fn)
    except OSError as e:
        pass
    
def handle_put(clisock, uri, content_length):
    # Process a PUT request.
    # Upload content into a temporary file.
    uri_parent = uri[: uri.rindex(b'/') ]
    temp_filename = uri_parent + '/put.tmp'
    maybe_delete(temp_filename)
    bytesleft = content_length
    try:
        outf = open(temp_filename, 'wb')
    except OSError as e:
        print(e)
        return send_err(clisock, 500)
    while bytesleft > 0:
        chunk = clisock.read(min(bytesleft, 64))
        bytesleft -= len(chunk)
        try:
            print("writing chunk of len %d (remaining %d)" % (len(chunk), bytesleft))
            outf.write(chunk)
        except OSError:
            # FAILED to write.
            outf.close()
            return send_err(clisock, 500)
    outf.flush()
    outf.close()
    # Try to rename,
    maybe_delete(uri) # remove destination.
    try:
        os.rename(temp_filename, uri)
    except OSError:
        return send_err(clisock, 500)
    # Good:
    send_err(clisock, 201, 'Created') 
