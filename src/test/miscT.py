# -*- coding: utf-8 -*-
"""
Created on Jan 27, 2025

@author: mchobbit
"""

import unittest
from my.globals import get_my_public_ip_address, ALL_SANDBOX_IRC_NETWORK_NAMES, RSA_KEY_SIZE
from my.stringtools import generate_random_alphanumeric_string, generate_irc_handle, s_now
from random import randint
from my.irctools.jaracorocks.praterookery import PrateRookery
from time import sleep
from Crypto.PublicKey import RSA
from my.irctools.jaracorocks.pratebot import PrateBot
from my.irctools.cryptoish import squeeze_da_keez

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


class Test(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def testGetMyPublicIpAddress(self):
        s = get_my_public_ip_address()
        # for _ in range(0,100):
        #
        # pass


if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()

