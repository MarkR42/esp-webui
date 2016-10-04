import httphandlers
import time
import machine
import esp
import sys
import network

def do_get(clisock, uri, content_length):
    clisock.write(b'HTTP/1.0 200 OK\r\n'
        b'Content-type: text/html; charset=utf-8\r\n'
        b'\r\n')
    clisock.write(b'<!DOCTYPE html><html><head><title>Current time</title></head>')
    clisock.write(b'<body>The current time is: ')
    timestr ='{}-{:02d}-{:02d} {:02d}:{:02d}:{:02d}'.format(*time.localtime())
    clisock.write(timestr.encode('ascii'))
    del timestr
    uptime_s = int(time.ticks_ms() / 1000)
    uptime_h = int(uptime_s / 3600)
    uptime_m = int(uptime_s / 60)
    uptime_m = uptime_m % 60
    uptime_s = uptime_s % 60
    
    clisock.write(b'<p>Uptime: {:02d}h {:02d}:{:02d}'.format(
        uptime_h, uptime_m, uptime_s))

    clisock.write(b'<p>Flash ID: {:x}'.format(esp.flash_id()))
    clisock.write(b'<p>Flash size: {:d}'.format(esp.flash_size()))
    clisock.write(b'<p>Python: {:s} on {:s} '.format(str(sys.implementation), sys.platform))
    clisock.write(b'<p>Unique ID: ')
    for b in machine.unique_id():
        clisock.write(b'{:02x}'.format(b))
    clisock.write(b'\n<h2>Network interfaces</h2>\n')
    clisock.write(b'\n<table><tr><th>mac<th>active</th><th>connected</th><th>IP</th><th>Gateway</th>')
    for i in network.STA_IF, network.AP_IF:
        wlan = network.WLAN(i)
        # Show MAC address.
        clisock.write(b'<tr>')
        clisock.write(b'<td>')
        for b in wlan.config('mac'):
            clisock.write(b'{:02X}'.format(b))

        clisock.write(b'<td>{:}</td>'.format(wlan.active()))
        clisock.write(b'<td>{:}</td>'.format(wlan.isconnected()))
        ifconfig = wlan.ifconfig() #ip, netmask, gateway, dns
        ifconfig = (ifconfig[0], ifconfig[2]) # ip, gw
        for item in ifconfig:
            clisock.write(b'<td>{:}</td>'.format(item))

    clisock.write(b'\n</table>\n')
    
def do_post(clisock, uri, content_length):
    fields = httphandlers.parse_post(clisock, uri, content_length)
    raise Exception("Not implemented")
    
