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
from my.globals import ALL_SANDBOX_IRC_NETWORK_NAMES, RSA_KEY_SIZE
from random import randint
from my.stringtools import generate_random_alphanumeric_string
import sys
from my.irctools.jaracorocks.harem import Harem, wait_for_harem_to_stabilize
from my.globals.poetry import BORN_TO_DIE_IN_BYTES


def do_big_timing_test(data_to_send, simpipe1, simpipe2, timeout):
    t_0 = datetime.datetime.now()
    simpipe1.put(data_to_send)
    sleep(10)
    t_0b = datetime.datetime.now()
    t_1 = datetime.datetime.now()
    received_data = bytearray()
    while (datetime.datetime.now() - t_1).seconds < timeout:
        if len(bytes(received_data)) == len(bytes(data_to_send)):
            break
        try:
            rxd_dat = simpipe2.get_nowait()
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

# my_list_of_all_irc_servers = ALL_SANDBOX_IRC_NETWORK_NAMES[:10]  # ALL_REALWORLD_IRC_NETWORK_NAMES
alice_nick = 'alice%d' % randint(111, 999)
bob_nick = 'bob%d' % randint(111, 999)
the_room = '#room' + generate_random_alphanumeric_string(5)
# alice_harem = Harem([the_room], alice_nick, my_list_of_all_irc_servers, alices_rsa_key)
# bob_harem = Harem([the_room], bob_nick, my_list_of_all_irc_servers, bobs_rsa_key)
# while not (alice_harem.connected_and_joined and bob_harem.connected_and_joined):
#     sleep(1)
#
# wait_for_harem_to_stabilize(alice_harem)
# alice_corridor = alice_harem.open(bobs_PK)
# sleep(10)
# bob_corridor = bob_harem.open(alices_PK)
# assert(bob_corridor.uid == alice_corridor.uid)
# alice_corridor.frame_size = 256
# all_data = open("/Users/mchobbit/Downloads/t1-printer-files.cfg.tar.gz", "rb").read()  # BORN_TO_DIE_IN_BYTES
# alice_corridor.put(all_data)
# recvd = bob_corridor.get()
# print("Sent %d bytes; received %d bytes" % (len(all_data), len(recvd)))
# assert(all_data == recvd)
# # do_big_timing_test(open("/Users/mchobbit/Downloads/cushion.stl", "rb").read(), alice_simpipe, bob_simpipe, 20)
# # do_big_timing_test(open("/Users/mchobbit/Downloads/t1-printer-files.cfg.tar.gz", "rb").read(), alice_simpipe, bob_simpipe, 20)
# # do_big_timing_test(open("/Users/mchobbit/Downloads/side_cushion.stl", "rb").read(), alice_simpipe, bob_simpipe, 20)
#
# alice_corridor.close()
# alice_harem.quit()
# bob_harem.quit()

for noof_servers in range(5, 10):
    print("NOOF SERVERS =", noof_servers)
    my_list_of_all_irc_servers = ALL_SANDBOX_IRC_NETWORK_NAMES[:noof_servers]  # ALL_REALWORLD_IRC_NETWORK_NAMES
    alice_harem = Harem([the_room], alice_nick, my_list_of_all_irc_servers, alices_rsa_key)  # , autohandshake=False)
    bob_harem = Harem([the_room], bob_nick, my_list_of_all_irc_servers, bobs_rsa_key)
    sleep(20)
    wait_for_harem_to_stabilize(alice_harem)
    assert(alice_harem.corridors == [])
    assert(bob_harem.corridors == [])
    sleep(30)
    alice_corridor = alice_harem.open(bobs_PK)
    sleep(10)
    bob_corridor = bob_harem.open(alices_PK)
    alice_corridor.put(b"MARCO?")
    sleep(5)
    assert(bob_corridor.get(timeout=30) == b"MARCO?")
    sleep(5)
    bob_corridor.put(b"POLO!")
    sleep(5)
    assert(alice_corridor.get(timeout=30) == b"POLO!")
    sleep(5)
    # if list(alice_harem.bots.keys()) != list(alice_corridor.irc_servers):
    #     assert(list(alice_corridor.irc_servers) == list(alice_harem.bots.keys()))
    # if list(bob_harem.bots.keys()) != bob_corridor.irc_servers:
    #     assert(list(bob_corridor.irc_servers) == list(bob_harem.bots.keys()))
    alice_corridor.close()
    bob_corridor.close()
    alice_harem.quit()
    bob_harem.quit()
    print("Pausing ... because I can.")
    sleep(20)

sleep(10)
print("<<<<<FIN>>>>>")
sys.exit(0)

