# -*- coding: utf-8 -*-
'''
Created on Jan 21, 2025

@author: mchobbit

# print(key.get_base64())  # print public key
# key.write_private_key(sys.stdout)


from random import shuffle, randint
from my.stringtools import generate_irc_handle
from Crypto.PublicKey import RSA
from my.globals import PARAGRAPH_OF_ALL_IRC_NETWORK_NAMES, JOINING_IRC_SERVER_TIMEOUT
from my.classes.exceptions import MyIrcInitialConnectionTimeoutError, MyIrcFingerprintMismatchCausedByServer
from time import sleep
from queue import Queue


import os
import socket
from my.irctools.jaracorocks.harem import HaremOfPrateBots
from Crypto.PublicKey import RSA
from time import sleep
from my.stringtools import *
from my.globals import *
import datetime
my_rsa_key = RSA.generate(2048)
nickname = socket.gethostname()
the_room = "#prate%d" % datetime.datetime.now().day

harem = HaremOfPrateBots(['#prate'], nickname, ALL_SANDBOX_IRC_NETWORK_NAMES, my_rsa_key)
buddies = harem.users

h2 = HaremOfPrateBots(['#prate'], 'mac2222', ALL_IRC_NETWORK_NAMES, my_rsa_key2)
while len(h1.ready_bots(my_rsa_key2.public_key())) < 3 and len(h2.ready_bots(my_rsa_key2.public_key())) < 3:
    sleep(A_TICK)

h1.ready_bots(my_rsa_key2.public_key())
for _ in range(0, 10):
    h1.put(my_rsa_key2.public_key(), b"HELLO WORLD")
    h2.get() == (my_rsa_key1.public_key(), b"HELLO WORLD")

with open("/Users/mchobbit/Downloads/pi_holder.stl", "rb") as f:
    h1.put(my_rsa_key2.public_key(), f.read())

pk, dat = h2.get()

'''
