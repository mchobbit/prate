# -*- coding: utf-8 -*-
"""
Created on Feb 9, 2025

@author: mchobbit


"""

import unittest
from Crypto.PublicKey import RSA
from time import sleep
from my.stringtools import generate_random_alphanumeric_string
from my.globals import ALL_SANDBOX_IRC_NETWORK_NAMES, MAX_NICKNAME_LENGTH, MAX_PRIVMSG_LENGTH, MAX_CRYPTO_MSG_LENGTH, ALL_REALWORLD_IRC_NETWORK_NAMES, RSA_KEY_SIZE
from random import randint
import datetime
import socket
from my.irctools.jaracorocks.pratebot import PrateBot
from my.classes.exceptions import PublicKeyBadKeyError, RookeryCorridorAlreadyClosedError
from my.irctools.jaracorocks.harem import Harem

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

'''
class TestHaremAndSimplePrateBot(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def testSimpleHaremAndBob(self):
        the_room = '#room' + generate_random_alphanumeric_string(5)
        noof_servers = 1
        list_of_all_irc_servers = ALL_SANDBOX_IRC_NETWORK_NAMES[-noof_servers:]
        alice_rsa_key = RSA.generate(RSA_KEY_SIZE)
        bob_rsa_key = RSA.generate(RSA_KEY_SIZE)
        alice_nick = 'alice%d' % randint(111, 999)
        bob_nick = 'bob%d' % randint(111, 999)
        bob_bot = PrateBot([the_room], bob_nick, list_of_all_irc_servers[0], 6667, bob_rsa_key, autohandshake=False)
        alice_harem = Harem([the_room], alice_nick, list_of_all_irc_servers, alice_rsa_key, autohandshake=False)
        while not (bob_bot.ready and alice_harem.ready):
            sleep(1)
        bob_bot.trigger_handshaking()
        sleep(30)
        self.assertEqual(alice_nick, alice_harem.desired_nickname)
        self.assertTrue(alice_nick in bob_bot.homies)
        self.assertEqual(bob_bot.rsa_key.public_key(), bob_rsa_key.public_key())
        self.assertEqual(bob_bot.homies[alice_nick].pubkey, alice_rsa_key.public_key())
        self.assertEqual(alice_harem.bots[list(alice_harem.bots)[0]].homies[bob_bot.nickname].pubkey, bob_rsa_key.public_key())
        alice_harem.quit()
        bob_bot.quit()


class TestHaremHandshook(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def testHaremUsersPubkeysAndtrue_homies(self):
        the_room = '#room' + generate_random_alphanumeric_string(5)
        list_of_all_irc_servers = ['rpi0irc1.local', 'rpi0irc2.local']
        alice_nick = 'alice%d' % randint(111, 999)
        bob_nick = 'bob%d' % randint(111, 999)
        h1 = Harem([the_room], alice_nick, list_of_all_irc_servers,
                              alices_rsa_key, startup_timeout=5, autohandshake=False)
        h2 = Harem([the_room], bob_nick, list_of_all_irc_servers,
                              bobs_rsa_key, startup_timeout=5, autohandshake=False)
        while not (h1.ready and h2.ready):
            sleep(1)
        h1.trigger_handshaking()
        h2.trigger_handshaking()
        noof_loops = 0
        while len(h1.true_homies) + len(h2.true_homies) < 2:
            sleep(1)
            noof_loops += 1
            if noof_loops > 180:
                raise TimeoutError("testHaremUsersPubkeysAndtrue_homies() ran out of time")
        print("Waiting for handshaking to complete")
        sleep(5)
        self.assertEqual(len(h1.users), 2)
        self.assertEqual(len(h2.users), 2)
        self.assertEqual(len(h1.pubkeys), 1)
        self.assertEqual(len(h2.pubkeys), 1)
        self.assertEqual(len(h1.true_homies), len(list_of_all_irc_servers))
        self.assertEqual(len(h2.true_homies), len(list_of_all_irc_servers))
        h2.quit()
        self.assertEqual(len(h1.users), 1)
        self.assertEqual(len(h1.pubkeys), 0)
        self.assertEqual(len(h1.true_homies), 0)
        h1.quit()

    def TestHaremHelloWordlSimple(self):
        my_nickname = socket.gethostname().replace('.', '_')[:MAX_NICKNAME_LENGTH]
        the_room = "#prattling"
        alice_rsa_key = RSA.generate(RSA_KEY_SIZE)
        bob_rsa_key = RSA.generate(RSA_KEY_SIZE)
        the_irc_server_URLs = ALL_SANDBOX_IRC_NETWORK_NAMES
        alice_harem = Harem([the_room], my_nickname, the_irc_server_URLs, alice_rsa_key)
        bob_harem = Harem([the_room], my_nickname, the_irc_server_URLs, bob_rsa_key)
        while not (alice_harem.ready and bob_harem.ready):
            sleep(1)
        print("Opening harems")
        while len(alice_harem.true_homies) + len(bob_harem.true_homies) < 2:
            sleep(1)

        for length in (10, 20, 50, 100, 200, 500, 1000, 2000, 5000, 10000):
            print("Sending a %d-char message" % length)
            outmsg = generate_random_alphanumeric_string(length).encode()
            alice_harem.put(bob_rsa_key.public_key(), outmsg)
            src, inmsg = bob_harem.get()
            self.assertEqual(src, alice_harem.desired_nickname)
            self.assertEqual(inmsg, outmsg)
        alice_harem.quit()
        bob_harem.quit()

    # def testHandshookGoofyParams
    #
    # def testHandshookPubKey
    #
    # def testHandshookIpaddr
    #
    # def testHandshookNickname

    # def testFullServerList(self):
    #     the_room = '#room' + generate_random_alphanumeric_string(5)
    #     noof_servers = 4
    #     print("testThreeandmoreitemsServerList with %d channels" % noof_servers)
    #     list_of_all_irc_servers = ALL_SANDBOX_IRC_NETWORK_NAMES[:noof_servers]
    #     alice_nick = 'alice%d' % randint(111, 999)
    #     bob_nick = 'bob%d' % randint(111, 999)
    #     h1 = Harem([the_room], alice_nick, list_of_all_irc_servers, alices_rsa_key, startup_timeout=5, maximum_reconnections=2)
    #     h2 = Harem([the_room], bob_nick, list_of_all_irc_servers, bobs_rsa_key, startup_timeout=5, maximum_reconnections=2)
    #     print("testFullServerList is waiting for handshaking to complete")
    #     while len(h1.find_nickname_by_pubkey(bobs_rsa_key.public_key())) < noof_servers and len(h2.find_nickname_by_pubkey(alices_rsa_key.public_key())) < noof_servers:
    #         sleep(1)
    #     h1.quit()
    #     h2.quit()


class TestSendFileBetweenTwoUserViaHarems(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        list_of_all_irc_servers = ALL_SANDBOX_IRC_NETWORK_NAMES
        alice_nick = 'alice%d' % randint(111, 999)
        bob_nick = 'bob%d' % randint(111, 999)
        cls.h1 = Harem(['#lokinbaa'], alice_nick, list_of_all_irc_servers, alices_rsa_key)
        cls.h2 = Harem(['#lokinbaa'], bob_nick, list_of_all_irc_servers, bobs_rsa_key)
        while not (cls.h1.ready and cls.h2.ready):
            sleep(1)
        print("TestSendFileBetweenTwoUserViaHarems() --- waiting for setup")
        noof_loops = 0
        while len(cls.h1.true_homies) + len(cls.h2.true_homies) < 2:
            sleep(1)
            noof_loops += 1
            if noof_loops > 180:
                raise TimeoutError("TestSendFileBetweenTwoUserViaHarems() ran out of time")

    @classmethod
    def tearDownClass(cls):
        cls.h1.quit()
        cls.h2.quit()

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def testFirstOfAll(self):
        plaintext = b""
        sleep(10)
        self.h1.put(bobs_rsa_key.public_key(), plaintext)
        pkey, xferred_data = self.h2.get()
        self.assertEqual((alices_rsa_key.public_key(), plaintext), (pkey, xferred_data))

        plaintext = b"WORD UP, HOMIE G."
        self.h1.put(bobs_rsa_key.public_key(), plaintext)
        pkey, xferred_data = self.h2.get()
        self.assertEqual((alices_rsa_key.public_key(), plaintext), (pkey, xferred_data))

    #     for length in (10, 20, 50, 100, 200, 500, 1000, 2000, 5000, 10000):
    #         plaintext = generate_random_alphanumeric_string(length).encode()
    #         self.h1.put(bobs_rsa_key.public_key(), plaintext)
    #         pkey, xferred_data = self.h2.get()
    #         self.assertEqual((alices_rsa_key.public_key(), plaintext), (pkey, xferred_data))
    #
    # def testTenLittleOnes(self):
    #     for _ in range(0, 10):
    #         plaintext = generate_random_alphanumeric_string(50).encode()
    #         self.h1.put(bobs_rsa_key.public_key(), plaintext)
    #         pk, msg = self.h2.get()
    #         self.assertEqual((pk, msg), (alices_rsa_key.public_key(), plaintext))

    # def testHomiesList(self):
    #     for homie in self.h1.homies:
    #         print(self.h1.homies)
    #         print(self.h2.homies)
    #         pass

    # .find_nickname_by_pubkey <== test

    # def testBigFile(self):
    #     with open("/Users/mchobbit/Downloads/pi_holder.stl", "rb") as f:
    #         self.h1.put(bobs_rsa_key.public_key(), f.read())
    #     pk, dat = self.h2.get()
    #     print("Yay.")


class TestSimpleOpenAndClose(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        list_of_all_irc_servers = ALL_SANDBOX_IRC_NETWORK_NAMES[:1]
        alice_nick = 'alice%d' % randint(111, 999)
        bob_nick = 'bob%d' % randint(111, 999)
        cls.h1 = Harem(['#lokinbee'], alice_nick, list_of_all_irc_servers, alices_rsa_key, autohandshake=False)
        cls.h2 = Harem(['#lokinbee'], bob_nick, list_of_all_irc_servers, bobs_rsa_key, autohandshake=False)
        print("TestSimpleOpenAndClose() --- waiting for setup")
        while not (cls.h1.ready and cls.h2.ready):
            sleep(1)
        [h.trigger_handshaking() for h in (cls.h1, cls.h2)]  # pylint: disable=expression-not-assigned
        noof_loops = 0
        while len(cls.h1.get_homies_list(True)) + len(cls.h2.get_homies_list(True)) < 2:
            sleep(1)
            noof_loops += 1
            if noof_loops > 180:
                raise TimeoutError("TestSimpleOpenAndClose() ran out of time")
        sleep(2)

    @classmethod
    def tearDownClass(cls):
        cls.h1.quit()
        cls.h2.quit()

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def testMakeAndCloseOneCorridor(self):
        self.assertEqual([], self.h1.corridors)
        f = self.h1.open(bobs_PK)
        self.assertEqual(1, len(self.h1.corridors))
        self.assertEqual([f], self.h1.corridors)
        f.close()
        self.assertEqual([], self.h1.corridors)

    def testMakeAndCloseANonexistentCorridor(self):
        self.assertRaises(ValueError, self.h1.open, 'This is not a public key, but it should be.')
        self.assertRaises(PublicKeyBadKeyError, self.h1.open, some_random_PK)
        self.assertEqual([], self.h1.corridors)

    def testMakeAndCloseTwoCorridorsBetweenTheSamePeople(self):
        self.assertEqual([], self.h1.corridors)
        f = self.h1.open(bobs_PK)
        self.assertEqual([f], self.h1.corridors)
        g = self.h1.open(bobs_PK)
        self.assertEqual(2, len(self.h1.corridors))
        self.assertNotEqual(f, g)
        self.assertNotEqual(f.uid, g.uid)
        self.assertTrue(f in self.h1.corridors)
        self.assertTrue(g in self.h1.corridors)
        f.close()
        self.assertEqual([g], self.h1.corridors)
        g.close()
        self.assertEqual([], self.h1.corridors)
        self.assertRaises(RookeryCorridorAlreadyClosedError, g.close)
        sleep(5)

    def testMakeTwocorridorsAndDeleteOne(self):
        sleep(5)
        self.assertEqual([], self.h1.corridors)
        f = self.h1.open(bobs_PK)
        self.assertTrue(f in self.h1.corridors)
        self.h1.corridors.remove(f)
        f.close()
        self.assertFalse(f in self.h1.corridors)


class TestSimpleWriteAndRead(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        list_of_all_irc_servers = ALL_SANDBOX_IRC_NETWORK_NAMES[:1]
        alice_nick = 'alice%d' % randint(111, 999)
        bob_nick = 'bob%d' % randint(111, 999)
        carol_nick = 'carol%d' % randint(111, 999)
        cls.h1 = Harem(['#lokinbee'], alice_nick, list_of_all_irc_servers, alices_rsa_key, autohandshake=False)
        cls.h2 = Harem(['#lokinbee'], bob_nick, list_of_all_irc_servers, bobs_rsa_key, autohandshake=False)
        cls.h3 = Harem(['#lokinbee'], carol_nick, list_of_all_irc_servers, carols_rsa_key, autohandshake=False)
        while not (cls.h1.ready and cls.h2.ready and cls.h3.ready):
            sleep(1)
        [h.trigger_handshaking() for h in (cls.h1, cls.h2, cls.h3)]  # pylint: disable=expression-not-assigned
        while len(cls.h1.get_homies_list(True)) + len(cls.h2.get_homies_list(True)) + len(cls.h3.get_homies_list(True)) < 6:
            sleep(5)

    @classmethod
    def tearDownClass(cls):
        cls.h1.quit()
        cls.h2.quit()
        cls.h3.quit()

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def testVisibilityOfTheCorridor(self):
        self.assertEqual([], self.h1.corridors)
        self.assertEqual([], self.h2.corridors)
        self.assertEqual([], self.h3.corridors)
        f = self.h1.open(bobs_PK)
        self.assertTrue(bobs_PK in [c.pubkey for c in self.h1.corridors])
        self.assertTrue(alices_PK in [c.pubkey for c in self.h2.corridors])
        g = self.h3.open(alices_PK)
        self.assertTrue(carols_PK in [c.pubkey for c in self.h1.corridors])
        self.assertTrue(alices_PK in [c.pubkey for c in self.h3.corridors])
        f.close()
        self.assertFalse(alices_PK in self.h2.corridors)
        self.assertFalse(bobs_PK in self.h1.corridors)
        self.assertTrue(carols_PK in [c.pubkey for c in self.h1.corridors])
        self.assertTrue(alices_PK in [c.pubkey for c in self.h3.corridors])
        g.close()
        self.assertEqual([], self.h1.corridors)
        self.assertEqual([], self.h2.corridors)
        self.assertEqual([], self.h3.corridors)
'''

if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
    pass

