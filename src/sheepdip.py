# -*- coding: utf-8 -*-
'''
Created on Jan 21, 2025

@author: mchobbit

# print(key.get_base64())  # print public key
# key.write_private_key(sys.stdout)
'''

from random import shuffle, randint
from my.stringtools import generate_irc_handle
from Crypto.PublicKey import RSA
from my.globals import PARAGRAPH_OF_ALL_IRC_NETWORK_NAMES
from time import sleep
from queue import Queue

from Crypto.PublicKey import RSA
from time import sleep
from my.stringtools import *
from my.globals import *
import os
import socket
import datetime
from my.irctools.cryptoish import squeeze_da_keez
from my.irctools.jaracorocks.harem import HaremOfPrateBots
my_nickname = socket.gethostname().replace('.', '_')[:MAX_NICKNAME_LENGTH]
the_room = "#prattling"
alice_rsa_key = RSA.generate(2048)
bob_rsa_key = RSA.generate(2048)
the_irc_server_URLs = ALL_SANDBOX_IRC_NETWORK_NAMES
alice_harem = HaremOfPrateBots([the_room], my_nickname, the_irc_server_URLs, alice_rsa_key)
bob_harem = HaremOfPrateBots([the_room], my_nickname, the_irc_server_URLs, bob_rsa_key)
print("Opening harems")
while len(alice_harem.users) < 2 and len(bob_harem.users) < 2:
    sleep(1)

while len(alice_harem.ipaddrs) < 1 and len(bob_harem.ipaddrs) < 1:
    sleep(1)

sleep(5)
print("Sending a file from %s to %s" % (alice_harem.desired_nickname, bob_harem.desired_nickname))
alice_harem.put(bob_rsa_key.public_key(), b"HELLO WELLO")
src, msg = bob_harem.get()

t = datetime.datetime.now()
with open("/Users/mchobbit/Downloads/pi_holder.stl", "rb") as f:
    alice_harem.put(bob_rsa_key.public_key(), f.read())

u = datetime.datetime.now()

pk, dat = bob_harem.get()
pass
