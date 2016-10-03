import httphandlers
import time

def do_get(clisock, uri, content_length):
    clisock.write(b'HTTP/1.0 200 OK\r\n'
        b'Content-type: text/html; charset=utf-8\r\n'
        b'\r\n')
    clisock.write(b'<!DOCTYPE html><html><head><title>Current time</title></head>')
    clisock.write(b'<body>The current time is:')
    timestr ='{}-{:02d}-{:02d} {:02d}:{:02d}:{:02d}'.format(*time.localtime())
    clisock.write(timestr.encode('ascii'))
    
def do_post(clisock, uri, content_length):
    fields = httphandlers.parse_post(clisock, uri, content_length)
    raise Exception("Not implemented")
    
