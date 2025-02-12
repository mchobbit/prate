'''
Created on Feb 9, 2025

@author: mchobbit





'''
import unittest
from Crypto.PublicKey import RSA
from time import sleep
from my.irctools.jaracorocks.harem import HaremOfPrateBots
from my.globals import PARAGRAPH_OF_ALL_IRC_NETWORK_NAMES
from my.stringtools import generate_random_alphanumeric_string


class TestHaremOne(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.my_rsa_key1 = RSA.generate(2048)
        cls.my_rsa_key2 = RSA.generate(2048)
        list_of_all_irc_servers = PARAGRAPH_OF_ALL_IRC_NETWORK_NAMES.split(' ')
        cls.h1 = HaremOfPrateBots(['#prate', '#etarp'], list_of_all_irc_servers, cls.my_rsa_key1)
        cls.h2 = HaremOfPrateBots(['#prate', '#etarp'], list_of_all_irc_servers, cls.my_rsa_key2)
        cls.h1.log_into_all_functional_IRC_servers()
        cls.h2.log_into_all_functional_IRC_servers()
        while len(cls.h1.ready_bots(cls.my_rsa_key2.public_key())) < 3 and len(cls.h2.ready_bots(cls.my_rsa_key2.public_key())) < 3:
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

        print("Yay.")


if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()

