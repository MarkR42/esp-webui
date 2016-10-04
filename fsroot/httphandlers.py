import os
import gc

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

chr_eq = b'='
chr_amp = b'&'

def decode_urlencoded(inbytes, tempbuf):
    """
        Decode the url encoded bytes string inbytes,
        into a proper unicode string.
        
        tempbuf should be a caller-allocated bytearray.
    """
    tempbuf[::] = b'' # init buffer without realloc
    pos = 0
    while pos < len(inbytes):
        # Handle e.g. %2a
        if inbytes[pos] == b'%'[0]:
            # decode the following two hex chars.
            tempbuf.append(int(inbytes[pos+1: pos+3], 16))
            pos += 2
        elif inbytes[pos] == b'+'[0]:
            tempbuf.append(b' '[0])
        else:
            tempbuf.append(inbytes[pos])
        pos += 1
    # Decode the utf8 which should now be in fieldbuf.
    return str(tempbuf, 'utf-8')

def show_free():
    print("free ram:", gc.mem_free())

def parse_post(clisock, uri, content_length):
    print("handle_post: content_length = ", content_length)
    if content_length > 1024:
        # Definitely going to be too big.
        return send_err(clisock, 500)
    # Read the whole post body.
    postbody = clisock.read(content_length)
    # Now we need to split this into fields.
    fieldtups = [] # array of name, value tuples.
    pos = 0
    while pos < len(postbody):
        # Find first "=" sign.
        eqpos = postbody.find(chr_eq, pos)
        if eqpos == -1:
            # No = sign.
            break
        fieldname = postbody[pos:eqpos]
        # Find next &
        amppos = postbody.find(chr_amp, eqpos)
        if amppos == -1:
            # None found? imagine there is & at the end.
            amppos = len(postbody)
        fieldvalue = postbody[eqpos+1:amppos]
        fieldtups.append( (fieldname, fieldvalue) )
        del fieldname, fieldvalue
        pos = amppos + 1
    del postbody # free memory from the whole post.
    print(repr(fieldtups))
    show_free()
    # Now we need to tweak the values to be in proper unicode and
    # unescape them.
    tempbuf = bytearray()
    fields = {}
    # Break into a dict, which will have multiple values
    # if there is >1 entry per field.
    for fieldname, fieldvalue in fieldtups:
        s = decode_urlencoded(fieldvalue, tempbuf)
        oldval = fields.get(fieldname)
        if oldval is None:
            fields[fieldname] = s
        else:
            if isinstance(oldval,str):
                fields[fieldname] = [oldval, s]
            else:
                # Append to existing
                oldval.append(s)
    del tempbuf, fieldtups, fieldname, fieldvalue
    show_free()
    print("post fields:")
    print(repr(fields))
    return fields


