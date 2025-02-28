# -*- coding: utf-8 -*-
"""
Created on Jan 21, 2025

@author: mchobbit

# print(key.get_base64())  # print public key
# key.write_private_key(sys.stdout)


import cProfile
from pstats import Stats
pr = cProfile.Profile()
pr.enable()
alice_rookery.put(bob_pk, b"HELLO")
pr.disable()
stats = Stats(pr)
stats.sort_stats('tottime').print_stats(10)
bob_rookery.get()

"""

from Crypto.PublicKey import RSA
# from my.irctools.cryptoish import *
# from my.stringtools import *
# from my.globals import *
from time import sleep
# from my.irctools.jaracorocks.pratebot import PrateBot
# import datetime
# from queue import Queue, Empty
# from my.audiotools import MyMic, raw_to_ogg
# import os
# from my.classes.exceptions import IrcInitialConnectionTimeoutError
from my.irctools.jaracorocks.praterookery import PrateRookery
from my.stringtools import generate_random_alphanumeric_string
from random import randint
from my.globals import ALL_REALWORLD_IRC_NETWORK_NAMES, ALL_SANDBOX_IRC_NETWORK_NAMES, RSA_KEY_SIZE, STARTUP_TIMEOUT
from my.irctools.jaracorocks.harem import Harem

alices_rsa_key = RSA.generate(RSA_KEY_SIZE)
bobs_rsa_key = RSA.generate(RSA_KEY_SIZE)
carols_rsa_key = RSA.generate(RSA_KEY_SIZE)
alices_PK = alices_rsa_key.public_key()
bobs_PK = bobs_rsa_key.public_key()
carols_PK = carols_rsa_key.public_key()
some_random_rsa_key = RSA.generate(RSA_KEY_SIZE)
some_random_PK = some_random_rsa_key.public_key()

noof_servers = 1
my_list_of_all_irc_servers = ALL_SANDBOX_IRC_NETWORK_NAMES[:noof_servers]  # ALL_REALWORLD_IRC_NETWORK_NAMES
the_room = '#room' + generate_random_alphanumeric_string(5)
alice_nick = 'alice%d' % randint(111, 999)
bob_nick = 'bob%d' % randint(111, 999)

print("                                                 Creating harems for Alice and Bob")
alice_harem = Harem([the_room], alice_nick, my_list_of_all_irc_servers, alices_rsa_key, autohandshake=False)
bob_harem = Harem([the_room], bob_nick, my_list_of_all_irc_servers, bobs_rsa_key, autohandshake=False)
while not (alice_harem.ready and bob_harem.ready):
    sleep(1)

print("                                                 Waiting for harems to shake hands")
alice_harem.trigger_handshaking()
bob_harem.trigger_handshaking()
the_noof_homies = -1
while the_noof_homies != len(alice_harem.get_homies_list(True)):
    the_noof_homies = len(alice_harem.get_homies_list(True))
    sleep(STARTUP_TIMEOUT // 2 + 1)

print("                                                 Opening a corridor between Alice and Bob")
alice_corridor = alice_harem.open(bobs_PK)
sleep(2)
bob_corridor = bob_harem.open(alices_PK)
sleep(2)

# print("                                                 Write data from Alice to Bob and from Bob to Alice")
# alice_corridor.write(b"MARCO?")
# assert(bob_corridor.read() == b"MARCO?")
# bob_corridor.write(b"POLO!")
# assert(alice_corridor.read() == b"POLO!")

sleep(2)
print("                                                 Closing corridors")
alice_corridor.close()
sleep(2)
bob_corridor.close()
print("                                                 <FIN>")
alice_harem.quit()
bob_harem.quit()
# with open("/Users/mchobbit/Downloads/top_panel.stl", "rb") as f:
#     datablock = f.read()
#
# assert(alice_rookery.connected_homies_lst[0].fernetkey == bob_rookery.connected_homies_lst[0].fernetkey)
# alice_rookery.put(bob_pk, datablock)
# who_said_it, what_did_they_say = bob_rookery.get()

# import datetime
# t = datetime.datetime.now()
# alice_rookery.put(bob_rsa_key.public_key(), outdat)
# u = datetime.datetime.now()
# sender, in_dat = bob_rookery.get()
# v = datetime.datetime.now()

