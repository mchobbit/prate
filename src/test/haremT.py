'''
Created on Feb 9, 2025

@author: mchobbit

import unittest
from Crypto.PublicKey import RSA
from time import sleep
from my.irctools.jaracorocks.harem import HaremOfPrateBots
from my.globals import ALL_IRC_NETWORK_NAMES
from my.stringtools import generate_random_alphanumeric_string
from my.irctools.jaracorocks.vanilla import BotForDualQueuedSingleServerIRCBotWithWhoisSupport
from my.irctools.jaracorocks.pratebot import PrateBot
from queue import Empty






'''
import unittest
from Crypto.PublicKey import RSA
from time import sleep
from my.irctools.jaracorocks.harem import HaremOfPrateBots
from my.stringtools import generate_random_alphanumeric_string
from my.globals import ALL_SANDBOX_IRC_NETWORK_NAMES
from random import randint
import datetime

# class TestHaremZero(unittest.TestCase):
#
#     def setUp(self):
#         pass
#
#     def tearDown(self):
#         pass
#
#     def testOneitemServerList(self):
#         my_rsa_key1 = RSA.generate(2048)
#         my_rsa_key2 = RSA.generate(2048)
#         the_room = '#room' + generate_random_alphanumeric_string(5)
#         noof_channels = 1
#         list_of_all_irc_servers = ALL_SANDBOX_IRC_NETWORK_NAMES[:noof_channels]
#         alice_nick = 'alice%d' % randint(111, 999)
#         bob_nick = 'bob%d' % randint(111, 999)
#         h1 = HaremOfPrateBots([the_room], alice_nick, list_of_all_irc_servers, my_rsa_key1, startup_timeout=5, maximum_reconnections=2)
#         h2 = HaremOfPrateBots([the_room], bob_nick, list_of_all_irc_servers, my_rsa_key2, startup_timeout=5, maximum_reconnections=2)
#         print("testOneitemServerList is waiting for handshaking to complete")
#         while len(h1.find_nickname_by_pubkey(my_rsa_key2.public_key())) < noof_channels and len(h2.find_nickname_by_pubkey(my_rsa_key1.public_key())) < noof_channels:
#             sleep(1)
#         h1.quit()
#         h2.quit()
#
#     def testTwoitemsServerList(self):
#         my_rsa_key1 = RSA.generate(2048)
#         my_rsa_key2 = RSA.generate(2048)
#         the_room = '#room' + generate_random_alphanumeric_string(5)
#         noof_channels = 2
#         list_of_all_irc_servers = ALL_SANDBOX_IRC_NETWORK_NAMES[:noof_channels]
#         alice_nick = 'alice%d' % randint(111, 999)
#         bob_nick = 'bob%d' % randint(111, 999)
#         h1 = HaremOfPrateBots([the_room], alice_nick, list_of_all_irc_servers, my_rsa_key1, startup_timeout=5, maximum_reconnections=2)
#         h2 = HaremOfPrateBots([the_room], bob_nick, list_of_all_irc_servers, my_rsa_key2, startup_timeout=5, maximum_reconnections=2)
#         print("testTwoitemsServerList is waiting for handshaking to complete")
#         while len(h1.find_nickname_by_pubkey(my_rsa_key2.public_key())) < noof_channels and len(h2.find_nickname_by_pubkey(my_rsa_key1.public_key())) < noof_channels:
#             sleep(1)
#             if datetime.datetime.now().second == 0:
#                 h1.trigger_handshaking()
#                 h2.trigger_handshaking()
#         h1.quit()
#         h2.quit()
#
#     def testServerListOfOneGoodAndOneNonexistent(self):
#         my_rsa_key1 = RSA.generate(2048)
#         my_rsa_key2 = RSA.generate(2048)
#         the_room = '#room' + generate_random_alphanumeric_string(5)
#         list_of_all_irc_servers = ['cinqcent.local', 'rpi0irc99.local']
#         noof_channels = len(list_of_all_irc_servers)
#         alice_nick = 'alice%d' % randint(111, 999)
#         bob_nick = 'bob%d' % randint(111, 999)
#         h1 = HaremOfPrateBots([the_room], alice_nick, list_of_all_irc_servers, my_rsa_key1, startup_timeout=5, maximum_reconnections=2)
#         h2 = HaremOfPrateBots([the_room], bob_nick, list_of_all_irc_servers, my_rsa_key2, startup_timeout=5, maximum_reconnections=2)
#         print("testServerListOfOneGoodAndOneNonexistent is waiting for handshaking to complete")
#         while len(h1.find_nickname_by_pubkey(my_rsa_key2.public_key())) < noof_channels - 1 and len(h2.find_nickname_by_pubkey(my_rsa_key1.public_key())) < noof_channels - 1:
#             sleep(1)
#             if datetime.datetime.now().second == 0:
#                 h1.trigger_handshaking()
#                 h2.trigger_handshaking()
#         h1.quit()
#         h2.quit()
#
#     def testServerListOfOneNonexistentAndOneGood(self):
#         my_rsa_key1 = RSA.generate(2048)
#         my_rsa_key2 = RSA.generate(2048)
#         the_room = '#room' + generate_random_alphanumeric_string(5)
#         list_of_all_irc_servers = ['rpi0irc99.local', 'cinqcent.local']
#         noof_channels = len(list_of_all_irc_servers)
#         alice_nick = 'alice%d' % randint(111, 999)
#         bob_nick = 'bob%d' % randint(111, 999)
#         h1 = HaremOfPrateBots([the_room], alice_nick, list_of_all_irc_servers, my_rsa_key1, startup_timeout=5, maximum_reconnections=2)
#         h2 = HaremOfPrateBots([the_room], bob_nick, list_of_all_irc_servers, my_rsa_key2, startup_timeout=5, maximum_reconnections=2)
#         print("testServerListOfOneNonexistentAndOneGood is waiting for handshaking to complete")
#         while len(h1.find_nickname_by_pubkey(my_rsa_key2.public_key())) < noof_channels - 1 and len(h2.find_nickname_by_pubkey(my_rsa_key1.public_key())) < noof_channels - 1:
#             sleep(1)
#             if datetime.datetime.now().second == 0:
#                 h1.trigger_handshaking()
#                 h2.trigger_handshaking()
#         h1.quit()
#         h2.quit()
#
#     def testServerListOfTwoNonexistent(self):
#         my_rsa_key1 = RSA.generate(2048)
#         my_rsa_key2 = RSA.generate(2048)
#         the_room = '#room' + generate_random_alphanumeric_string(5)
#         list_of_all_irc_servers = ['rpi0irc98.local', 'rpi0irc99.local']
#         alice_nick = 'alice%d' % randint(111, 999)
#         bob_nick = 'bob%d' % randint(111, 999)
#         h1 = HaremOfPrateBots([the_room], alice_nick, list_of_all_irc_servers, my_rsa_key1, startup_timeout=5, maximum_reconnections=2)
#         h2 = HaremOfPrateBots([the_room], bob_nick, list_of_all_irc_servers, my_rsa_key2, startup_timeout=5, maximum_reconnections=2)
#         sleep(5)
#         self.assertEqual(0, len(h1.bots))
#         self.assertEqual(0, len(h2.bots))
#         h1.quit()
#         h2.quit()
#
#     def testFouritemsServerList(self):
#         my_rsa_key1 = RSA.generate(2048)
#         my_rsa_key2 = RSA.generate(2048)
#         the_room = '#room' + generate_random_alphanumeric_string(5)
#         noof_channels = 4
#         print("testThreeandmoreitemsServerList with %d channels" % noof_channels)
#         list_of_all_irc_servers = ALL_SANDBOX_IRC_NETWORK_NAMES[:noof_channels]
#         alice_nick = 'alice%d' % randint(111, 999)
#         bob_nick = 'bob%d' % randint(111, 999)
#         h1 = HaremOfPrateBots([the_room], alice_nick, list_of_all_irc_servers, my_rsa_key1, startup_timeout=5, maximum_reconnections=2)
#         h2 = HaremOfPrateBots([the_room], bob_nick, list_of_all_irc_servers, my_rsa_key2, startup_timeout=5, maximum_reconnections=2)
#         print("testFouritemsServerList is waiting for handshaking to complete")
#         while len(h1.find_nickname_by_pubkey(my_rsa_key2.public_key())) < noof_channels and len(h2.find_nickname_by_pubkey(my_rsa_key1.public_key())) < noof_channels:
#             sleep(1)
#             if datetime.datetime.now().second == 0:
#                 h1.trigger_handshaking()
#                 h2.trigger_handshaking()
#         h1.quit()
#         h2.quit()


class TestHaremHandshook(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def testHaremUsersPubkeysAndIpaddrs(self):
        my_rsa_key1 = RSA.generate(2048)
        my_rsa_key2 = RSA.generate(2048)
        the_room = '#room' + generate_random_alphanumeric_string(5)
        list_of_all_irc_servers = ['rpi0irc1.local', 'rpi0irc2.local']
        alice_nick = 'alice%d' % randint(111, 999)
        bob_nick = 'bob%d' % randint(111, 999)
        h1 = HaremOfPrateBots([the_room], alice_nick, list_of_all_irc_servers, my_rsa_key1, startup_timeout=5, maximum_reconnections=2)
        h2 = HaremOfPrateBots([the_room], bob_nick, list_of_all_irc_servers, my_rsa_key2, startup_timeout=5, maximum_reconnections=2)
        h1.trigger_handshaking()
        h2.trigger_handshaking()

        for _ in range(0, 60):
            sleep(1)
            if len(h1.ipaddrs) == 2 and len(h2.ipaddrs) == 2:
                break

        print("Waiting for handshaking to complete")
        self.assertEqual(len(h1.users), 2)
        self.assertEqual(len(h2.users), 2)
        self.assertEqual(len(h1.pubkeys), 1)
        self.assertEqual(len(h2.pubkeys), 1)
        self.assertEqual(len(h1.ipaddrs), 1)
        self.assertEqual(len(h2.ipaddrs), 1)
        h2.quit()
        self.assertEqual(len(h1.users), 1)
        self.assertEqual(len(h1.pubkeys), 0)
        self.assertEqual(len(h1.ipaddrs), 0)
        h1.quit()

    # def testHandshookGoofyParams
    #
    # def testHandshookPubKey
    #
    # def testHandshookIpaddr
    #
    # def testHandshookNickname

    # def testFullServerList(self):
    #     my_rsa_key1 = RSA.generate(2048)
    #     my_rsa_key2 = RSA.generate(2048)
    #     the_room = '#room' + generate_random_alphanumeric_string(5)
    #     noof_channels = 4
    #     print("testThreeandmoreitemsServerList with %d channels" % noof_channels)
    #     list_of_all_irc_servers = ALL_SANDBOX_IRC_NETWORK_NAMES[:noof_channels]
    #     alice_nick = 'alice%d' % randint(111, 999)
    #     bob_nick = 'bob%d' % randint(111, 999)
    #     h1 = HaremOfPrateBots([the_room], alice_nick, list_of_all_irc_servers, my_rsa_key1, startup_timeout=5, maximum_reconnections=2)
    #     h2 = HaremOfPrateBots([the_room], bob_nick, list_of_all_irc_servers, my_rsa_key2, startup_timeout=5, maximum_reconnections=2)
    #     print("testFullServerList is waiting for handshaking to complete")
    #     while len(h1.find_nickname_by_pubkey(my_rsa_key2.public_key())) < noof_channels and len(h2.find_nickname_by_pubkey(my_rsa_key1.public_key())) < noof_channels:
    #         sleep(1)
    #     h1.quit()
    #     h2.quit()

# class TestSendFileBetweenTwoUserViaHarems(unittest.TestCase):
#
#     @classmethod
#     def setUpClass(cls):
#         cls.my_rsa_key1 = RSA.generate(2048)
#         cls.my_rsa_key2 = RSA.generate(2048)
#         list_of_all_irc_servers = ALL_SANDBOX_IRC_NETWORK_NAMES[:4]
#         alice_nick = 'alice%d' % randint(111, 999)
#         bob_nick = 'bob%d' % randint(111, 999)
#         cls.h1 = HaremOfPrateBots(['#locerno'], alice_nick, list_of_all_irc_servers, cls.my_rsa_key1, startup_timeout=5, maximum_reconnections=2)
#         cls.h2 = HaremOfPrateBots(['#locerno'], bob_nick, list_of_all_irc_servers, cls.my_rsa_key2, startup_timeout=5, maximum_reconnections=2)
#         while len(cls.h1.find_nickname_by_pubkey(cls.my_rsa_key2.public_key())) < 3 and len(cls.h2.find_nickname_by_pubkey(cls.my_rsa_key1.public_key())) < 3:
#             sleep(.1)
#
#     @classmethod
#     def tearDownClass(cls):
#         cls.h1.quit()
#         cls.h2.quit()
#
#     def setUp(self):
#         pass
#
#     def tearDown(self):
#         pass
#
#     def testFirstOfAll(self):
#
#         plaintext = b""
#         self.h1.put(self.my_rsa_key2.public_key(), plaintext)
#         pkey, xferred_data = self.h2.get()
#         self.assertEqual((self.my_rsa_key1.public_key(), plaintext), (pkey, xferred_data))
#
#         plaintext = b"WORD UP, HOMIE G."
#         self.h1.put(self.my_rsa_key2.public_key(), plaintext)
#         pkey, xferred_data = self.h2.get()
#         self.assertEqual((self.my_rsa_key1.public_key(), plaintext), (pkey, xferred_data))
#
#         for length in (10, 20, 50, 100, 200, 500, 1000, 2000, 5000, 10000):
#             plaintext = generate_random_alphanumeric_string(length).encode()
#             self.h1.put(self.my_rsa_key2.public_key(), plaintext)
#             pkey, xferred_data = self.h2.get()
#             self.assertEqual((self.my_rsa_key1.public_key(), plaintext), (pkey, xferred_data))
#
#     def testOneHundredLittleOnes(self):
#         for _ in range(0, 100):
#             plaintext = generate_random_alphanumeric_string(50).encode()
#             self.h1.put(self.my_rsa_key2.public_key(), plaintext)
#             pk, msg = self.h2.get()
#            self.assertEqual((pk, msg), (self.my_rsa_key1.public_key(), plaintext))

    # .find_nickname_by_pubkey <== test

    # def testBigFile(self):
    #     with open("/Users/mchobbit/Downloads/pi_holder.stl", "rb") as f:
    #         self.h1.put(self.my_rsa_key2.public_key(), f.read())
    #     pk, dat = self.h2.get()
    #     print("Yay.")


if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
    pass

