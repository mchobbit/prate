'''
Created on Jan 27, 2025

@author: mchobbit
'''
import unittest
from my.globals import get_my_public_ip_address


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
