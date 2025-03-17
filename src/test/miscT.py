# -*- coding: utf-8 -*-
"""
Created on Jan 27, 2025

@author: mchobbit
"""

import unittest
from my.globals import get_my_public_ip_address, RSA_KEY_SIZE
from Crypto.PublicKey import RSA

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
        _ = get_my_public_ip_address()
        # for i in range(0,100):
        #
        # pass


if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()

