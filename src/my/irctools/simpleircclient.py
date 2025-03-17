# -*- coding: utf-8 -*-
"""
Created on Jan 22, 2025

@author: mchobbit

IRC Tools for test purposes

Todo:
    * Finish docs
    * WRITE UNIT TESTS!
from my.globals import *
from my.irctools import *
import base64
pubslim = skinny_key(MY_RSAKEY.public_key())
b85slim = pubkey_to_b85(MY_RSAKEY.public_key())
b64slim = pubkey_to_b64(MY_RSAKEY.public_key())
assert(b85_to_pubkey(b85slim) == MY_RSAKEY.public_key())
assert(b64_to_pubkey(b64slim) == MY_RSAKEY.public_key())
assert(unskin_key(pubslim) == MY_RSAKEY.public_key())
print("pubslim: %d chars" % len(pubslim))
print("b85    : %d chars" % len(b85slim))
print("b64    : %d chars" % len(b64slim))
"""


def superduper_simple_irc_client():
    import socket
    my_input = """cinqcent.local:6667
    clyde
    clyde
    John Doe"""

    # Parse input.
    ping = 'PING '
    pong = 'PONG '
    lines = my_input.split('\n')
    host = lines[0].split(':')

    # Connect.
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((host[0], int(host[1])))

    # Handshake.
    client.send(('NICK ' + lines[1] + '\r\n').encode())
    client.send(('USER ' + lines[2] + ' 0 * :' + lines[3] + '\r\n').encode())

    # Output and ping/pong.
    while True:
        data = client.recv(1024)
        print(data)

        if data.startswith(ping):
            resp = data.strip(ping)
            client.send(pong + resp)
            print(pong + resp)
