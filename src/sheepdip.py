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
from my.globals import ALL_SANDBOX_IRC_NETWORK_NAMES, RSA_KEY_SIZE, STARTUP_TIMEOUT
from my.irctools.jaracorocks.harem import Harem, wait_for_harem_to_stabilize
from random import randint
from my.stringtools import generate_random_alphanumeric_string
from my.classes.exceptions import RookeryCorridorTimeoutError
from my.irctools.jaracorocks.pratebot import PrateBot
import sys


def do_big_timing_test(data_to_send, corridor1, corridor2, timeout):
    t_0 = datetime.datetime.now()
    corridor1.put(data_to_send)
    sleep(10)
    t_0b = datetime.datetime.now()
    t_1 = datetime.datetime.now()
    received_data = bytearray()
    while (datetime.datetime.now() - t_1).seconds < timeout:
        if len(bytes(received_data)) == len(bytes(data_to_send)):
            break
        try:
            rxd_dat = corridor2.get_nowait()
            print("Rx'd =>", rxd_dat)
            received_data += rxd_dat
            t_1 = datetime.datetime.now()
        except Empty:
            sleep(.1)
    t_2 = datetime.datetime.now()
    print("Time to send %d bytes: %d seconds" % (len(data_to_send), (t_0b - t_0).seconds))
    print("Time to recv %d bytes: %d seconds" % (len(data_to_send), (t_2 - t_0b).seconds))
    # print("Total received:", received_data)
    i = 0
    while i < min(len(received_data), len(data_to_send)) and received_data[i] == data_to_send[i]:
        i += 1
    if i < min(len(received_data), len(data_to_send)):
        print("WARNING -- mismatch @ #%d" % i)
        print("The final %d chars do not match" % max(len(received_data), len(data_to_send)) - i)


alices_rsa_key = RSA.generate(RSA_KEY_SIZE)
bobs_rsa_key = RSA.generate(RSA_KEY_SIZE)
carols_rsa_key = RSA.generate(RSA_KEY_SIZE)
alices_PK = alices_rsa_key.public_key()
bobs_PK = bobs_rsa_key.public_key()
carols_PK = carols_rsa_key.public_key()
some_random_rsa_key = RSA.generate(RSA_KEY_SIZE)
some_random_PK = some_random_rsa_key.public_key()

bot1 = PrateBot(channels=['#prate'], nickname='mac1', irc_server='cinqcent.local', port=6667, rsa_key=alices_rsa_key,
                startup_timeout=30, maximum_reconnections=2, strictly_nick=True, autoreconnect=True, autohandshake=True)
bot2 = PrateBot(channels=['#prate'], nickname='mac2', irc_server='cinqcent.local', port=6667, rsa_key=bobs_rsa_key,
                startup_timeout=30, maximum_reconnections=2, strictly_nick=True, autoreconnect=True, autohandshake=True)

while not (bot1.connected_and_joined and bot2.connected_and_joined):
    sleep(1)

while not bot1.is_handshook_with(bot2.pubkey):
    sleep(1)

assert(bot1.connected is True)
assert(bot1.joined is True)
assert(bot2.connected is True)
assert(bot2.joined is True)
assert(bot1.is_handshook_with(bot2.pubkey))
assert(bot2.is_handshook_with(bot1.pubkey))
bot1.quit()
bot2.quit()
sys.exit(0)

noof_servers = 5
my_list_of_all_irc_servers = ALL_SANDBOX_IRC_NETWORK_NAMES[:noof_servers]  # ALL_REALWORLD_IRC_NETWORK_NAMES
the_room = '#room' + generate_random_alphanumeric_string(5)
alice_nick = 'alice%d' % randint(111, 999)
bob_nick = 'bob%d' % randint(111, 999)

alice_harem = Harem([the_room], alice_nick, my_list_of_all_irc_servers, alices_rsa_key, autohandshake=False, return_immediately=False)
bob_harem = Harem([the_room], bob_nick, my_list_of_all_irc_servers, bobs_rsa_key, autohandshake=False, return_immediately=False)

while not (alice_harem.connected_and_joined and bob_harem.connected_and_joined):
    sleep(1)

alice_harem.trigger_handshaking()
bob_harem.trigger_handshaking()
wait_for_harem_to_stabilize(alice_harem)
alice_corridor = alice_harem.open(bobs_PK)
bob_corridor = bob_harem.open(alices_PK)
sleep(5)
alice_corridor.dupes = 5  # dupes
alice_corridor.frame_size = 256  # frame_size
datalen_lst = [32, 0]

for datalen in datalen_lst:
    print("%s servers=%d; dupes=%d; frame_size=%d; datalen=%d" % ('-' * 33, noof_servers, alice_corridor.dupes, alice_corridor.frame_size, datalen))
    all_data = generate_random_alphanumeric_string(datalen).encode()
    alice_corridor.put(all_data)
    rxd_data = "WE NEVER GOT THERE"
    try:
        rxd_data = bob_corridor.get(timeout=60)
    except Empty as e:
        raise RookeryCorridorTimeoutError("Transfer took too long! --- %s servers=%d; dupes=%d; frame_size=%d; datalen=%d; FAILED" % ('-' * 33, noof_servers, alice_corridor.dupes, alice_corridor.frame_size, datalen)) from e
    if all_data != rxd_data:
        print("%s servers=%d; dupes=%d; frame_size=%d; datalen=%d; FAILED" % ('-' * 33, noof_servers, alice_corridor.dupes, alice_corridor.frame_size, datalen))
        if all_data != rxd_data:
            print("%s != %s" % (all_data, rxd_data))
    assert(bob_corridor.empty() is True)
alice_corridor.close()
bob_corridor.close()
alice_harem.quit()
bob_harem.quit()

print("                                                 Creating harems for Alice and Bob")
alice_harem = Harem([the_room], alice_nick, my_list_of_all_irc_servers, alices_rsa_key, autohandshake=False)
bob_harem = Harem([the_room], bob_nick, my_list_of_all_irc_servers, bobs_rsa_key, autohandshake=False)
while not (alice_harem.connected_and_joined and bob_harem.connected_and_joined):
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

# all_data = BORN_TO_DIE_IN_BYTES
all_data = b"1234567 ABCDEFG IJKLMNO QRSTUVW YZ543210"
alice_corridor.frame_size = 8
alice_corridor.put(all_data)
sleep(10)
recvd = bob_corridor.get()
print("Sent %d bytes; received %d bytes" % (len(all_data), len(recvd)))
# do_big_timing_test(open("/Users/mchobbit/Downloads/cushion.stl", "rb").read(), alice_corridor, bob_corridor, 20)
# do_big_timing_test(open("/Users/mchobbit/Downloads/t1-printer-files.cfg.tar.gz", "rb").read(), alice_corridor, bob_corridor, 20)
# do_big_timing_test(open("/Users/mchobbit/Downloads/side_cushion.stl", "rb").read(), alice_corridor, bob_corridor, 20)
assert(all_data == recvd)
sleep(1)
'''

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
'''
