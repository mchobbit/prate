# -*- coding: utf-8 -*-
"""
Created on Feb 9, 2025

@author: mchobbit

import unittest
from Crypto.PublicKey import RSA
from time import sleep
from my.irctools.jaracorocks.rookery import PrateRookery
from my.globals import ALL_IRC_NETWORK_NAMES
from my.stringtools import generate_random_alphanumeric_string
from my.irctools.jaracorocks.vanilla import BotForDualQueuedSingleServerIRCBotWithWhoisSupport
from my.irctools.jaracorocks.pratebot import PrateBot
from queue import Empty

"""
import unittest
from Crypto.PublicKey import RSA
from time import sleep
from my.stringtools import generate_random_alphanumeric_string
from my.globals import ALL_SANDBOX_IRC_NETWORK_NAMES, MAX_NICKNAME_LENGTH, MAX_CRYPTO_MSG_LENGTH, RSA_KEY_SIZE
from random import randint
import socket
from my.irctools.jaracorocks.pratebot import PrateBot
from my.irctools.jaracorocks.praterookery import PrateRookery

alices_rsa_key = RSA.generate(RSA_KEY_SIZE)
bobs_rsa_key = RSA.generate(RSA_KEY_SIZE)
carols_rsa_key = RSA.generate(RSA_KEY_SIZE)
alices_PK = alices_rsa_key.public_key()
bobs_PK = bobs_rsa_key.public_key()
carols_PK = carols_rsa_key.public_key()
some_random_rsa_key = RSA.generate(RSA_KEY_SIZE)
some_random_PK = some_random_rsa_key.public_key()

alice_rsa_key = RSA.generate(RSA_KEY_SIZE)
bob_rsa_key = RSA.generate(RSA_KEY_SIZE)


class TestRookeryZero(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def testOneitemServerList(self):
        """Log two rookeries into one room on one IRC server. Shake hands. Then, quit."""
        the_room = '#room' + generate_random_alphanumeric_string(5)
        noof_servers = 1
        list_of_all_irc_servers = ALL_SANDBOX_IRC_NETWORK_NAMES[:noof_servers]
        alice_nick = 'alice%d' % randint(111, 999)
        bob_nick = 'bob%d' % randint(111, 999)
        h1 = PrateRookery([the_room], alice_nick, list_of_all_irc_servers, alices_rsa_key, startup_timeout=5, maximum_reconnections=2)
        h2 = PrateRookery([the_room], bob_nick, list_of_all_irc_servers, bobs_rsa_key, startup_timeout=5, maximum_reconnections=2)
        while not (h1.connected_and_joined and h2.connected_and_joined):
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
        """Just like testOneitemServerList().. but with 2 rooms instead of just 1."""
        the_room = '#room' + generate_random_alphanumeric_string(5)
        noof_servers = 2
        list_of_all_irc_servers = ALL_SANDBOX_IRC_NETWORK_NAMES[:noof_servers]
        alice_nick = 'alice%d' % randint(111, 999)
        bob_nick = 'bob%d' % randint(111, 999)
        h1 = PrateRookery([the_room], alice_nick, list_of_all_irc_servers, alices_rsa_key, startup_timeout=5, maximum_reconnections=2)
        h2 = PrateRookery([the_room], bob_nick, list_of_all_irc_servers, bobs_rsa_key, startup_timeout=5, maximum_reconnections=2)
        while not (h1.connected_and_joined and h2.connected_and_joined):
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
        """Create two rookeries. Then, for no good reason, initiate handshaking for a second time."""
        the_room = '#room' + generate_random_alphanumeric_string(5)
        noof_servers = 2
        list_of_all_irc_servers = ALL_SANDBOX_IRC_NETWORK_NAMES[:noof_servers]
        alice_nick = 'alice%d' % randint(111, 999)
        bob_nick = 'bob%d' % randint(111, 999)
        h1 = PrateRookery([the_room], alice_nick, list_of_all_irc_servers, alices_rsa_key, startup_timeout=5, maximum_reconnections=2)
        h2 = PrateRookery([the_room], bob_nick, list_of_all_irc_servers, bobs_rsa_key, startup_timeout=5, maximum_reconnections=2)
        while not (h1.connected_and_joined and h2.connected_and_joined):
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

    def testServerListOfOneGoodAndOneNonexistent(self):
        """Initiate two rookeries, with one invalid IRC server and one valid IRC server."""
        the_room = '#room' + generate_random_alphanumeric_string(5)
        list_of_all_irc_servers = ['cinqcent.local', 'rpi0irc99.local']
        noof_servers = len(list_of_all_irc_servers)
        alice_nick = 'alice%d' % randint(111, 999)
        bob_nick = 'bob%d' % randint(111, 999)
        h1 = PrateRookery([the_room], alice_nick, list_of_all_irc_servers, alices_rsa_key, startup_timeout=5, maximum_reconnections=2)
        h2 = PrateRookery([the_room], bob_nick, list_of_all_irc_servers, bobs_rsa_key, startup_timeout=5, maximum_reconnections=2)
        while not (h1.connected_and_joined and h2.connected_and_joined):
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
        """Initiate two rookeries, using two totally invalid IRC servers."""
        the_room = '#room' + generate_random_alphanumeric_string(5)
        list_of_all_irc_servers = ['rpi0irc98.local', 'rpi0irc99.local']
        alice_nick = 'alice%d' % randint(111, 999)
        bob_nick = 'bob%d' % randint(111, 999)
        h1 = PrateRookery([the_room], alice_nick, list_of_all_irc_servers, alices_rsa_key, startup_timeout=5, maximum_reconnections=2)
        h2 = PrateRookery([the_room], bob_nick, list_of_all_irc_servers, bobs_rsa_key, startup_timeout=5, maximum_reconnections=2)
        while not (h1.connected_and_joined and h2.connected_and_joined):
            sleep(1)
        sleep(5)
        self.assertEqual(0, len(h1.bots))
        self.assertEqual(0, len(h2.bots))
        h1.quit()
        h2.quit()

    def testFouritemsServerList(self):
        """FOUR IRC SERVERS. Oh, my."""
        the_room = '#room' + generate_random_alphanumeric_string(5)
        noof_servers = 4
        print("testFouritemsServerList with %d channels" % noof_servers)
        list_of_all_irc_servers = ALL_SANDBOX_IRC_NETWORK_NAMES[:noof_servers]
        alice_nick = 'alice%d' % randint(111, 999)
        bob_nick = 'bob%d' % randint(111, 999)
        h1 = PrateRookery([the_room], alice_nick, list_of_all_irc_servers, alices_rsa_key, startup_timeout=5, maximum_reconnections=2)
        h2 = PrateRookery([the_room], bob_nick, list_of_all_irc_servers, bobs_rsa_key, startup_timeout=5, maximum_reconnections=2)
        while not (h1.connected_and_joined and h2.connected_and_joined):
            sleep(1)
        print("testFouritemsServerList is waiting for handshaking to complete")
        while len(h1.find_nickname_by_pubkey(bobs_rsa_key.public_key())) < noof_servers and len(h2.find_nickname_by_pubkey(alices_rsa_key.public_key())) < noof_servers:
            sleep(1)
        h1.quit()
        h2.quit()


class TestRookeryAndSimplePrateBot(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def testSimpleRookeryAndBob(self):
        """Create two PrateBots. Make them shake hands. That's it. (Why is this here?)"""
        the_room = '#room' + generate_random_alphanumeric_string(5)
        noof_servers = 1
        list_of_all_irc_servers = ALL_SANDBOX_IRC_NETWORK_NAMES[-noof_servers:]
        alice_nick = 'alice%d' % randint(111, 999)
        bob_nick = 'bob%d' % randint(111, 999)
        bob_bot = PrateBot([the_room], bob_nick, list_of_all_irc_servers[0], 6667, bob_rsa_key, autohandshake=False)
        alice_rookery = PrateRookery([the_room], alice_nick, list_of_all_irc_servers, alice_rsa_key, autohandshake=False)
        while not (bob_bot.connected_and_joined and alice_rookery.connected_and_joined):
            sleep(1)
        bob_bot.trigger_handshaking()
        sleep(30)
        self.assertEqual(alice_nick, alice_rookery.desired_nickname)
        self.assertTrue(alice_nick in bob_bot.homies)
        self.assertEqual(bob_bot._my_rsa_key.public_key(), bob_rsa_key.public_key())  # pylint: disable=protected-access
        self.assertEqual(bob_bot._my_rsa_key.public_key(), bob_bot.my_pubkey)  # pylint: disable=protected-access
        self.assertEqual(bob_bot.homies[alice_nick].pubkey, alice_rsa_key.public_key())
        self.assertEqual(alice_rookery.bots[list(alice_rookery.bots)[0]].homies[bob_bot.nickname].pubkey, bob_rsa_key.public_key())
        alice_rookery.quit()
        bob_bot.quit()


class TestRookeryHandshook(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def testRookeryUsersPubkeysAndTrueHomies(self):
        """Do the two rookeries shake hands properly? When one leaves, does the other notice?"""
        the_room = '#room' + generate_random_alphanumeric_string(5)
        list_of_all_irc_servers = ['rpi0irc1.local', 'rpi0irc2.local']
        alice_nick = 'alice%d' % randint(111, 999)
        bob_nick = 'bob%d' % randint(111, 999)
        h1 = PrateRookery([the_room], alice_nick, list_of_all_irc_servers,
                              alices_rsa_key, startup_timeout=5, autohandshake=False)
        h2 = PrateRookery([the_room], bob_nick, list_of_all_irc_servers,
                              bobs_rsa_key, startup_timeout=5, autohandshake=False)
        while not (h1.connected_and_joined and h2.connected_and_joined):
            sleep(1)
        h1.trigger_handshaking()
        h2.trigger_handshaking()
        noof_loops = 0
        while len(h1.true_homies) + len(h2.true_homies) < 2:
            sleep(1)
            noof_loops += 1
            if noof_loops > 180:
                raise TimeoutError("testRookeryUsersPubkeysAndIpaddrs() ran out of time")
        sleep(10)
        self.assertEqual(len(h1.users), 2)
        self.assertEqual(len(h2.users), 2)
        self.assertEqual(len(h1.homies_pubkeys), 1)
        self.assertEqual(len(h2.homies_pubkeys), 1)
        self.assertEqual(len(h1.true_homies), len(list_of_all_irc_servers))
        self.assertEqual(len(h2.true_homies), len(list_of_all_irc_servers))
        h2.quit()
        sleep(5)
        self.assertEqual(len(h1.users), 1)
        self.assertEqual(len(h1.homies_pubkeys), 0)
        self.assertEqual(len(h1.true_homies), 0)
        h1.quit()

    def TestRookeryHelloWorldSimple(self):
        """Launch two rookies. Send some short messages between them."""
        my_nickname = socket.gethostname().replace('.', '_')[:MAX_NICKNAME_LENGTH]
        the_room = "#prattling"

        the_irc_server_URLs = ALL_SANDBOX_IRC_NETWORK_NAMES
        alice_rookery = PrateRookery([the_room], my_nickname, the_irc_server_URLs, alice_rsa_key)
        bob_rookery = PrateRookery([the_room], my_nickname, the_irc_server_URLs, bob_rsa_key)
        while not (alice_rookery.connected_and_joined and bob_rookery.connected_and_joined):
            sleep(1)
        print("Opening rookeries")
        while len(alice_rookery.true_homies) + len(bob_rookery.true_homies) < 2:
            sleep(1)

        for length in (10, 20, 50, 100, 200, 500, 1000, 2000, 5000, 10000):
            print("Sending a %d-char message" % length)
            outmsg = generate_random_alphanumeric_string(length).encode()
            alice_rookery.put(bob_rsa_key.public_key(), outmsg)
            src, inmsg = bob_rookery.get()
            self.assertEqual(src, alice_rookery.desired_nickname)
            self.assertEqual(inmsg, outmsg)

        for length in (10, 20, 50, 100, 200, 500, 1000, 2000, 5000, 10000):
            print("Sending a %d-char message" % length)
            outmsg = generate_random_alphanumeric_string(length).encode()
            bob_rookery.put(alice_rsa_key.public_key(), outmsg)
            src, inmsg = alice_rookery.get()
            self.assertEqual(src, bob_rookery.desired_nickname)
            self.assertEqual(inmsg, outmsg)

        alice_rookery.quit()
        bob_rookery.quit()


class TestSendFileBetweenTwoUserViaRookeries(unittest.TestCase):
    """Run some major tests... but USE THE SAME ROOKERIES THROUGHOUT!"""

    @classmethod
    def setUpClass(cls):
        list_of_all_irc_servers = ALL_SANDBOX_IRC_NETWORK_NAMES
        alice_nick = 'alice%d' % randint(111, 999)
        bob_nick = 'bob%d' % randint(111, 999)
        cls.h1 = PrateRookery(['#lokinbaa'], alice_nick, list_of_all_irc_servers, alices_rsa_key)
        cls.h2 = PrateRookery(['#lokinbaa'], bob_nick, list_of_all_irc_servers, bobs_rsa_key)
        while not (cls.h1.connected_and_joined and cls.h2.connected_and_joined):
            sleep(1)
        print("TestSendFileBetweenTwoUserViaRookeries() --- waiting for setup")
        noof_loops = 0
        while len(cls.h1.true_homies) + len(cls.h2.true_homies) < 2:
            sleep(1)
            noof_loops += 1
            if noof_loops > 180:
                raise TimeoutError("TestSendFileBetweenTwoUserViaRookeries() ran out of time")

    @classmethod
    def tearDownClass(cls):
        cls.h1.quit()
        cls.h2.quit()

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def testFirstOfAll(self):
        """Do some very simple message-sending."""
        plaintext = b""
        sleep(10)
        self.h1.put(bobs_rsa_key.public_key(), plaintext)
        pkey, xferred_data = self.h2.get()
        self.assertEqual((alices_rsa_key.public_key(), plaintext), (pkey, xferred_data))

        plaintext = b"WORD UP, HOMIE G."
        self.h1.put(bobs_rsa_key.public_key(), plaintext)
        pkey, xferred_data = self.h2.get()
        self.assertEqual((alices_rsa_key.public_key(), plaintext), (pkey, xferred_data))

        for length in (10, 20, 50, 100, 200, MAX_CRYPTO_MSG_LENGTH):
            plaintext = generate_random_alphanumeric_string(length).encode()
            self.h1.put(bobs_rsa_key.public_key(), plaintext)
            pkey, xferred_data = self.h2.get()
            self.assertEqual((alices_rsa_key.public_key(), plaintext), (pkey, xferred_data))

    def testTenLittleOnes(self):
        for _ in range(0, 10):
            plaintext = generate_random_alphanumeric_string(50).encode()
            self.h1.put(bobs_rsa_key.public_key(), plaintext)
            pk, msg = self.h2.get()
            self.assertEqual((pk, msg), (alices_rsa_key.public_key(), plaintext))


class TestBrokenRookeryStuff(unittest.TestCase):  # This belongs in praterookeryT.py

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def testFullServerList(self):
        the_room = '#room' + generate_random_alphanumeric_string(5)
        noof_servers = 4
        print("testThreeandmoreitemsServerList with %d channels" % noof_servers)
        list_of_all_irc_servers = ALL_SANDBOX_IRC_NETWORK_NAMES[:noof_servers]
        alice_nick = 'alice%d' % randint(111, 999)
        bob_nick = 'bob%d' % randint(111, 999)
        h1 = PrateRookery([the_room], alice_nick, list_of_all_irc_servers, alices_rsa_key, startup_timeout=5, maximum_reconnections=2)
        h2 = PrateRookery([the_room], bob_nick, list_of_all_irc_servers, bobs_rsa_key, startup_timeout=5, maximum_reconnections=2)
        print("testFullServerList is waiting for handshaking to complete")
        while len(h1.homies_pubkeys) < 1 or len(h2.homies_pubkeys) < 1:
            sleep(1)
        while h2.my_pubkey not in h1.homies_pubkeys or h1.my_pubkey not in h2.homies_pubkeys:
            sleep(1)
        h1.quit()
        h2.quit()


if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()

