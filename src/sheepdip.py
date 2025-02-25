# -*- coding: utf-8 -*-
'''
Created on Jan 21, 2025

@author: mchobbit

# print(key.get_base64())  # print public key
# key.write_private_key(sys.stdout)


import cProfile
from pstats import Stats
pr = cProfile.Profile()
pr.enable()
alice_harem.put(bob_pk, b"HELLO")
pr.disable()
stats = Stats(pr)
stats.sort_stats('tottime').print_stats(10)
bob_harem.get()

'''

from Crypto.PublicKey import RSA
from my.irctools.cryptoish import *
from my.stringtools import *
from my.globals import *
from my.irctools.jaracorocks.harem import HaremOfPrateBots
from time import sleep
from my.irctools.jaracorocks.pratebot import PrateBot
import datetime
from queue import Queue, Empty
from my.audiotools import MyMic, raw_to_ogg
import os
from my.classes.exceptions import IrcInitialConnectionTimeoutError

the_room = '#room' + generate_random_alphanumeric_string(5)
alice_rsa_key = RSA.generate(2048)
bob_rsa_key = RSA.generate(2048)
alice_pk = alice_rsa_key.public_key()
bob_pk = bob_rsa_key.public_key()
# for i in range(0, len(ALL_REALWORLD_IRC_NETWORK_NAMES)):
i = 2
alice_nick = 'alice%d' % randint(111, 999)
bob_nick = 'bob%d' % randint(111, 999)
alice_harem = HaremOfPrateBots([the_room], alice_nick, ALL_REALWORLD_IRC_NETWORK_NAMES[:i], alice_rsa_key, autohandshake=False)
bob_harem = HaremOfPrateBots([the_room], bob_nick, ALL_REALWORLD_IRC_NETWORK_NAMES[:i], bob_rsa_key, autohandshake=False)
while not (alice_harem.ready and bob_harem.ready):
    sleep(1)

sleep(5)
alice_harem.trigger_handshaking()  # ...making bob_harem.trigger_handshaking() unnecessary.
sleep(5)
bob_harem.trigger_handshaking()
while len(alice_harem.connected_homies_lst) < i - 1:
    sleep(1)

while len(bob_harem.connected_homies_lst) < i - 1:
    sleep(1)

alice_harem.put(bob_pk, b"HELLO WORLD!")
who_said_it, what_did_they_say = bob_harem.get()
alice_harem.put(bob_pk, b"HELLO WIBBLE!")
who_said_it, what_did_they_say = bob_harem.get()

with open("/Users/mchobbit/Downloads/top_panel.stl", "rb") as f:
    datablock = f.read()

assert(alice_harem.connected_homies_lst[0].fernetkey == bob_harem.connected_homies_lst[0].fernetkey)
alice_harem.put(bob_pk, datablock)
who_said_it, what_did_they_say = bob_harem.get()

# import datetime
# t = datetime.datetime.now()
# alice_harem.put(bob_rsa_key.public_key(), outdat)
# u = datetime.datetime.now()
# sender, in_dat = bob_harem.get()
# v = datetime.datetime.now()

