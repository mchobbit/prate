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

import datetime

from queue import Empty
from Crypto.PublicKey import RSA
from time import sleep
from my.stringtools import generate_random_alphanumeric_string
from random import randint, shuffle
from my.globals import ALL_REALWORLD_IRC_NETWORK_NAMES, ALL_SANDBOX_IRC_NETWORK_NAMES, RSA_KEY_SIZE, STARTUP_TIMEOUT
from my.irctools.jaracorocks.harem import Harem
from my.globals.poetry import BORN_TO_DIE_IN_BYTES
from my.irctools.cryptoish import int_64bit_cksum, bytes_64bit_cksum
from dns.rdataclass import NONE

alices_rsa_key = RSA.generate(RSA_KEY_SIZE)
bobs_rsa_key = RSA.generate(RSA_KEY_SIZE)
carols_rsa_key = RSA.generate(RSA_KEY_SIZE)
alices_PK = alices_rsa_key.public_key()
bobs_PK = bobs_rsa_key.public_key()
carols_PK = carols_rsa_key.public_key()
some_random_rsa_key = RSA.generate(RSA_KEY_SIZE)
some_random_PK = some_random_rsa_key.public_key()

noof_servers = 20
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
a2ice_corrido2 = alice_harem.open(bobs_PK)
sleep(5)
bob_corridor = bob_harem.open(alices_PK)
b2b_corrid_2 = bob_harem.open(alices_PK)
assert(bob_corridor == b2b_corrid_2)
assert(alice_corridor == a2ice_corrido2)
assert(bob_corridor != alice_corridor)

# with open("/Users/mchobbit/Downloads/top_panel.stl", "rb") as f:
#    all_data = f.read()

all_data = BORN_TO_DIE_IN_BYTES
alice_corridor.put(all_data)

sleep(10)

frames_lst = [None]
timenow = datetime.datetime.now()
received_data = bytearray()
while (datetime.datetime.now() - timenow).seconds < 20:
    try:
        rxd_dat = bob_corridor.get_nowait()
#        print("Rx'd =>", rxd_dat)
        received_data += rxd_dat
    except Empty:
        sleep(.1)

print("Total received:", received_data)
assert(received_data == all_data)
sleep(1)

#
# assert(bob_corridor.get() == b"MARCO?")
#
# sleep(2)
# bob_corridor.put(b"POLO!")
# sleep(2)
# assert(alice_corridor.get() == b"POLO!")
# sleep(2)
#
# print("                                                 Closing corridors")
# alice_corridor.close()
# sleep(2)
# bob_corridor.close()
# print("                                                 <FIN>")
# alice_harem.quit()
# bob_harem.quit()

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

