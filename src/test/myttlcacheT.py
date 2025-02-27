# -*- coding: utf-8 -*-
"""
Created on Feb 4, 2025

@author: mchobbit

Test MyTTLCache
"""

import unittest
from my.classes import MyTTLCache
from time import sleep
from random import randint, choice
import string
from my.stringtools import generate_random_alphanumeric_string


class Test(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def testGoofyParams(self):
        self.assertRaises(TypeError, MyTTLCache)
        self.assertRaises(ValueError, MyTTLCache, None)
        self.assertRaises(ValueError, MyTTLCache, -1)
        self.assertRaises(ValueError, MyTTLCache, 0)
        self.assertRaises(ValueError, MyTTLCache, 0.1)
        self.assertRaises(ValueError, MyTTLCache, 'Hello')

    def testDataEnduresForNSeconds(self):
        for attempts in range(0, 2):
            for timedelay in (1, 2, 3, 1):
                cache = MyTTLCache(timedelay)
                dct = {}
                noof_items = randint(1, 100)
                for itemno in range(0, noof_items):
                    if 0 == randint(0, 1):
                        key = randint(-1000, 1000)
                    else:
                        key = generate_random_alphanumeric_string(randint(1, 64))
                    if 0 == randint(0, 1):
                        value = randint(-1000, 1000)
                    else:
                        value = generate_random_alphanumeric_string(randint(1, 64))
                    dct[key] = value
                    cache.set(key, value)
                    self.assertEqual(dct[key], cache.get(key))
                    self.assertEqual(value, dct[key])
                    self.assertEqual(value, cache.get(key))
                sleep(.5)
                for key in dct:
                    self.assertEqual(dct[key], cache.get(key))
                sleep(timedelay)
                for key in dct:
                    self.assertEqual(cache.get(key), None)


if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
