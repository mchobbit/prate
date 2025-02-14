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

# class TestReliabilityOfEachPotentialIRCServer(unittest.TestCase):
#
#     def setUp(self):
#         pass
#
#     def tearDown(self):
#         pass
#
#     def testFirstOfAll(self):
#         Xbots = {}
#         Ybots = {}
#         Xmy_rsa_key = RSA.generate(2048)
#         Ymy_rsa_key = RSA.generate(2048)
#         my_channel = '#plate'
#         X_desired_nickname = 'x%sx' % generate_random_alphanumeric_string(7)
#         Y_desired_nickname = 'y%sy' % generate_random_alphanumeric_string(7)
#         my_port = 6667
#         for my_irc_server in ALL_IRC_NETWORK_NAMES:
#             Xbots[my_irc_server] = PrateBot([my_channel], X_desired_nickname, my_irc_server, my_port, Xmy_rsa_key)
#             Ybots[my_irc_server] = PrateBot([my_channel], Y_desired_nickname, my_irc_server, my_port, Ymy_rsa_key)
#         sleep(60)
#         for my_irc_server in ALL_IRC_NETWORK_NAMES:
#             Xbots[my_irc_server].crypto_put(Ymy_rsa_key.public_key(), b"HELLO WORLD")
#         sleep(5)
#         for my_irc_server in ALL_IRC_NETWORK_NAMES:
#             (pk, msg) = Ybots[my_irc_server].crypto_get_nowait()
#             if msg != b'HELLO WORLD':
#                 print("%s sucks" % my_irc_server)
#         print("OK.")


class TestHaremOne(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.my_rsa_key1 = RSA.generate(2048)
        cls.my_rsa_key2 = RSA.generate(2048)
        list_of_all_irc_servers = ALL_SANDBOX_IRC_NETWORK_NAMES
        alice_nick = 'alice%d' % randint(111, 999)
        bob_nick = 'bob%d' % randint(111, 999)
        cls.h1 = HaremOfPrateBots(['#locerno'], alice_nick, list_of_all_irc_servers, cls.my_rsa_key1, startup_timeout=5, maximum_reconnections=2)
        cls.h2 = HaremOfPrateBots(['#locerno'], bob_nick, list_of_all_irc_servers, cls.my_rsa_key2, startup_timeout=5, maximum_reconnections=2)
        while len(cls.h1.handshook(cls.my_rsa_key2.public_key())) < 3 and len(cls.h2.handshook(cls.my_rsa_key2.public_key())) < 3:
            sleep(.1)

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
        self.h1.put(self.my_rsa_key2.public_key(), plaintext)
        pkey, xferred_data = self.h2.get()
        self.assertEqual((self.my_rsa_key1.public_key(), plaintext), (pkey, xferred_data))

        plaintext = b"WORD UP, HOMIE G."
        self.h1.put(self.my_rsa_key2.public_key(), plaintext)
        pkey, xferred_data = self.h2.get()
        self.assertEqual((self.my_rsa_key1.public_key(), plaintext), (pkey, xferred_data))

        for length in (10, 20, 50, 100, 200, 500, 1000, 2000, 5000, 10000):
            plaintext = generate_random_alphanumeric_string(length).encode()
            self.h1.put(self.my_rsa_key2.public_key(), plaintext)
            pkey, xferred_data = self.h2.get()
            self.assertEqual((self.my_rsa_key1.public_key(), plaintext), (pkey, xferred_data))

    def testOneHundredLittleOnes(self):
        for _ in range(0, 100):
            plaintext = generate_random_alphanumeric_string(50).encode()
            self.h1.put(self.my_rsa_key2.public_key(), plaintext)
            pk, msg = self.h2.get()
            self.assertEqual((pk, msg), (self.my_rsa_key1.public_key(), plaintext))

    # .handshook <== test

    # def testBigFile(self):
    #     with open("/Users/mchobbit/Downloads/pi_holder.stl", "rb") as f:
    #         self.h1.put(self.my_rsa_key2.public_key(), f.read())
    #     pk, dat = self.h2.get()
    #     print("Yay.")


if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()

