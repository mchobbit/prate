# -*- coding: utf-8 -*-
"""
Created on Feb 9, 2025

@author: mchobbit


"""

import unittest
from Crypto.PublicKey import RSA
from time import sleep
from queue import Empty
from my.stringtools import generate_random_alphanumeric_string
from my.globals import ALL_SANDBOX_IRC_NETWORK_NAMES, MAX_NICKNAME_LENGTH, MAX_PRIVMSG_LENGTH, MAX_CRYPTO_MSG_LENGTH, ALL_REALWORLD_IRC_NETWORK_NAMES, RSA_KEY_SIZE, STARTUP_TIMEOUT
from random import randint
import datetime
import socket
from my.irctools.jaracorocks.harem import Harem, receive_data_from_corridor
from my.classes.exceptions import RookeryCorridorAlreadyClosedError
from my.globals.poetry import HAMLET, BORN_TO_DIE_IN_BYTES, CICERO

alices_rsa_key = RSA.generate(RSA_KEY_SIZE)
bobs_rsa_key = RSA.generate(RSA_KEY_SIZE)
carols_rsa_key = RSA.generate(RSA_KEY_SIZE)
alices_PK = alices_rsa_key.public_key()
bobs_PK = bobs_rsa_key.public_key()
carols_PK = carols_rsa_key.public_key()
some_random_rsa_key = RSA.generate(RSA_KEY_SIZE)
some_random_PK = some_random_rsa_key.public_key()


class TestHaremZero(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def testPutGetGetnowaitAndEmpty(self):
        the_room = '#room' + generate_random_alphanumeric_string(5)
        noof_servers = 1
        list_of_all_irc_servers = ALL_SANDBOX_IRC_NETWORK_NAMES[:noof_servers]
        alice_nick = 'alice%d' % randint(111, 999)
        bob_nick = 'bob%d' % randint(111, 999)
        h1 = Harem([the_room], alice_nick, list_of_all_irc_servers, alices_rsa_key, startup_timeout=5, maximum_reconnections=2)
        h2 = Harem([the_room], bob_nick, list_of_all_irc_servers, bobs_rsa_key, startup_timeout=5, maximum_reconnections=2)
        while not (h1.ready and h2.ready):
            sleep(1)
        noof_loops = 0
        while len(h1.find_nickname_by_pubkey(bobs_rsa_key.public_key())) < noof_servers and len(h2.find_nickname_by_pubkey(alices_rsa_key.public_key())) < noof_servers:
            sleep(1)
            noof_loops += 1
            if noof_loops > 180:
                raise TimeoutError("testTwoitemsServerList() ran out of time")
        self.assertRaises(ValueError, h1.put, 1, 2, 3, 4)
        # self.assertRaises(AttributeError, h1.empty)
        # self.assertRaises(AttributeError, h1.get)
        # self.assertRaises(AttributeError, h1.get_nowait)
        h1.quit()
        h2.quit()


class TestHaremOne(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def testOneitemServerList(self):
        the_room = '#room' + generate_random_alphanumeric_string(5)
        noof_servers = 1
        list_of_all_irc_servers = ALL_SANDBOX_IRC_NETWORK_NAMES[:noof_servers]
        alice_nick = 'alice%d' % randint(111, 999)
        bob_nick = 'bob%d' % randint(111, 999)
        h1 = Harem([the_room], alice_nick, list_of_all_irc_servers, alices_rsa_key, startup_timeout=5, maximum_reconnections=2)
        h2 = Harem([the_room], bob_nick, list_of_all_irc_servers, bobs_rsa_key, startup_timeout=5, maximum_reconnections=2)
        while not (h1.ready and h2.ready):
            sleep(1)
        noof_loops = 0
        while len(h1.find_nickname_by_pubkey(bobs_rsa_key.public_key())) < noof_servers and len(h2.find_nickname_by_pubkey(alices_rsa_key.public_key())) < noof_servers:
            sleep(1)
            noof_loops += 1
            if noof_loops > 180:
                raise TimeoutError("testTwoitemsServerList() ran out of time")
        h1.quit()
        h2.quit()

    def testTwoitemsServerList(self):
        the_room = '#room' + generate_random_alphanumeric_string(5)
        noof_servers = 2
        list_of_all_irc_servers = ALL_SANDBOX_IRC_NETWORK_NAMES[:noof_servers]
        alice_nick = 'alice%d' % randint(111, 999)
        bob_nick = 'bob%d' % randint(111, 999)
        h1 = Harem([the_room], alice_nick, list_of_all_irc_servers, alices_rsa_key, startup_timeout=5, maximum_reconnections=2)
        h2 = Harem([the_room], bob_nick, list_of_all_irc_servers, bobs_rsa_key, startup_timeout=5, maximum_reconnections=2)
        while not (h1.ready and h2.ready):
            sleep(1)
        print("testTwoitemsServerList is waiting for handshaking to complete")
        noof_loops = 0
        while len(h1.find_nickname_by_pubkey(bobs_rsa_key.public_key())) < noof_servers and len(h2.find_nickname_by_pubkey(alices_rsa_key.public_key())) < noof_servers:
            sleep(1)
            noof_loops += 1
            if noof_loops > 180:
                raise TimeoutError("testTwoitemsServerList() ran out of time")
        h1.quit()
        h2.quit()

    def testTwoitemsPLUStotallyUnecessaryTriggeringOfHandshaking(self):
        the_room = '#room' + generate_random_alphanumeric_string(5)
        noof_servers = 2
        list_of_all_irc_servers = ALL_SANDBOX_IRC_NETWORK_NAMES[:noof_servers]
        alice_nick = 'alice%d' % randint(111, 999)
        bob_nick = 'bob%d' % randint(111, 999)
        h1 = Harem([the_room], alice_nick, list_of_all_irc_servers, alices_rsa_key, startup_timeout=5, maximum_reconnections=2)
        h2 = Harem([the_room], bob_nick, list_of_all_irc_servers, bobs_rsa_key, startup_timeout=5, maximum_reconnections=2)
        while not (h1.ready and h2.ready):
            sleep(1)
        print("testTwoitemsPLUStotallyUnecessaryTriggeringOfHandshaking is waiting for handshaking to complete")
        noof_loops = 0
        while len(h1.find_nickname_by_pubkey(bobs_rsa_key.public_key())) < noof_servers and len(h2.find_nickname_by_pubkey(alices_rsa_key.public_key())) < noof_servers:
            sleep(1)
            noof_loops += 1
            if noof_loops > 180:
                raise TimeoutError("testTwoitemsPLUStotallyUnecessaryTriggeringOfHandshaking() ran out of time")
        h1.trigger_handshaking()
        h2.trigger_handshaking()
        noof_loops = 0
        while len(h1.find_nickname_by_pubkey(bobs_rsa_key.public_key())) < noof_servers and len(h2.find_nickname_by_pubkey(alices_rsa_key.public_key())) < noof_servers:
            sleep(1)
            noof_loops += 1
            if noof_loops > 30:
                raise TimeoutError("testTwoitemsServerList() ran out of time (SECOND)")
        h1.quit()
        h2.quit()


class TestHaremTwo(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def testServerListOfOneGoodAndOneNonexistent(self):
        the_room = '#room' + generate_random_alphanumeric_string(5)
        list_of_all_irc_servers = ['cinqcent.local', 'rpi0irc99.local']
        noof_servers = len(list_of_all_irc_servers)
        alice_nick = 'alice%d' % randint(111, 999)
        bob_nick = 'bob%d' % randint(111, 999)
        h1 = Harem([the_room], alice_nick, list_of_all_irc_servers, alices_rsa_key, startup_timeout=5, maximum_reconnections=2)
        h2 = Harem([the_room], bob_nick, list_of_all_irc_servers, bobs_rsa_key, startup_timeout=5, maximum_reconnections=2)
        while not (h1.ready and h2.ready):
            sleep(1)
        print("testServerListOfOneGoodAndOneNonexistent is waiting for handshaking to complete")
        noof_loops = 0
        while len(h1.find_nickname_by_pubkey(bobs_rsa_key.public_key())) < noof_servers - 1 and len(h2.find_nickname_by_pubkey(alices_rsa_key.public_key())) < noof_servers - 1:
            sleep(1)
            noof_loops += 1
            if noof_loops > 180:
                raise TimeoutError("testServerListOfOneGoodAndOneNonexistent() ran out of time")
        h1.quit()
        h2.quit()

    def testServerListOfTwoNonexistent(self):
        the_room = '#room' + generate_random_alphanumeric_string(5)
        list_of_all_irc_servers = ['rpi0irc98.local', 'rpi0irc99.local']
        alice_nick = 'alice%d' % randint(111, 999)
        bob_nick = 'bob%d' % randint(111, 999)
        h1 = Harem([the_room], alice_nick, list_of_all_irc_servers, alices_rsa_key, startup_timeout=5, maximum_reconnections=2)
        h2 = Harem([the_room], bob_nick, list_of_all_irc_servers, bobs_rsa_key, startup_timeout=5, maximum_reconnections=2)
        while not (h1.ready and h2.ready):
            sleep(1)
        sleep(5)
        self.assertEqual(0, len(h1.bots))
        self.assertEqual(0, len(h2.bots))
        h1.quit()
        h2.quit()

    def testFouritemsServerList(self):
        the_room = '#room' + generate_random_alphanumeric_string(5)
        noof_servers = 4
        print("testFouritemsServerList with %d channels" % noof_servers)
        list_of_all_irc_servers = ALL_SANDBOX_IRC_NETWORK_NAMES[:noof_servers]
        alice_nick = 'alice%d' % randint(111, 999)
        bob_nick = 'bob%d' % randint(111, 999)
        h1 = Harem([the_room], alice_nick, list_of_all_irc_servers, alices_rsa_key, startup_timeout=5, maximum_reconnections=2)
        h2 = Harem([the_room], bob_nick, list_of_all_irc_servers, bobs_rsa_key, startup_timeout=5, maximum_reconnections=2)
        while not (h1.ready and h2.ready):
            sleep(1)
        print("testFouritemsServerList is waiting for handshaking to complete")
        while len(h1.find_nickname_by_pubkey(bobs_rsa_key.public_key())) < noof_servers and len(h2.find_nickname_by_pubkey(alices_rsa_key.public_key())) < noof_servers:
            sleep(1)
        h1.quit()
        h2.quit()


if __name__ == "__main__":
    # import sys;sys.argv = ['', 'TestHaremTwo.testSimpleTest']
    unittest.main()

