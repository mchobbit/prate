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
from my.globals import ALL_SANDBOX_IRC_NETWORK_NAMES, RSA_KEY_SIZE, STARTUP_TIMEOUT
from random import randint
from my.classes.exceptions import RookeryCorridorAlreadyClosedError, RookeryCorridorNoTrueHomiesError, RookeryCorridorTimeoutError
from my.globals.poetry import HAMLET, BORN_TO_DIE_IN_BYTES, CICERO
from my.irctools.jaracorocks.harem import Harem

alices_rsa_key = RSA.generate(RSA_KEY_SIZE)
bobs_rsa_key = RSA.generate(RSA_KEY_SIZE)
carols_rsa_key = RSA.generate(RSA_KEY_SIZE)
alices_PK = alices_rsa_key.public_key()
bobs_PK = bobs_rsa_key.public_key()
carols_PK = carols_rsa_key.public_key()
some_random_rsa_key = RSA.generate(RSA_KEY_SIZE)
some_random_PK = some_random_rsa_key.public_key()


def setUpForNServers(noof_servers, strict=True):
    if noof_servers < 1:
        raise ValueError("noof_servers must be >=1")
    my_list_of_all_irc_servers = ALL_SANDBOX_IRC_NETWORK_NAMES[:noof_servers]  # ALL_REALWORLD_IRC_NETWORK_NAMES
    alice_nick = 'alice%d' % randint(111, 999)
    bob_nick = 'bob%d' % randint(111, 999)
    the_room = '#room' + generate_random_alphanumeric_string(5)
    alice_harem = Harem([the_room], alice_nick, my_list_of_all_irc_servers, alices_rsa_key, autohandshake=False)
    bob_harem = Harem([the_room], bob_nick, my_list_of_all_irc_servers, bobs_rsa_key, autohandshake=False)
    while not (alice_harem.connected_and_joined and bob_harem.connected_and_joined):
        sleep(1)
    alice_harem.trigger_handshaking()
    bob_harem.trigger_handshaking()
    the_noof_homies = -1
    while the_noof_homies != len(alice_harem.get_homies_list(True)):
        the_noof_homies = len(alice_harem.get_homies_list(True))
        sleep(STARTUP_TIMEOUT // 2 + 1)
    if len(alice_harem.bots) < noof_servers or len(bob_harem.bots) < noof_servers:
        s = "WARNING -- only %d of %d servers were available" % (min(len(alice_harem.bots), len(bob_harem.bots)), noof_servers)
        if strict:
            raise RookeryCorridorNoTrueHomiesError(s)
        else:
            print(s)
    if min(len(alice_harem.bots), len(bob_harem.bots)) == 0:
        raise RookeryCorridorNoTrueHomiesError("Unable to find any harems in %s" % ','.join(my_list_of_all_irc_servers))
    return (alice_harem, bob_harem)


class TestCorridorsZero(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        pass

    @classmethod
    def tearDownClass(cls):
        pass

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def __run_super_duper_simple_test(self, noof_servers, dupes, frame_size, datalen_lst, timeout=1800):
        alice_harem, bob_harem = setUpForNServers(noof_servers=noof_servers)
        alice_corridor = alice_harem.open(bobs_PK)
        bob_corridor = bob_harem.open(alices_PK)
        sleep(5)
        alice_corridor.dupes = dupes
        alice_corridor.frame_size = frame_size
        if type(datalen_lst) is int:
            datalen_lst = (datalen_lst,)
        for datalen in datalen_lst:
            print("%s servers=%d; dupes=%d; frame_size=%d; datalen=%d" % ('-' * 33, noof_servers, alice_corridor.dupes, alice_corridor.frame_size, datalen))
            all_data = generate_random_alphanumeric_string(datalen).encode()
            alice_corridor.put(all_data)
            try:
                rxd_data = bob_corridor.get(timeout=timeout)
            except Empty as e:
                raise RookeryCorridorTimeoutError("Transfer took too long! --- %s servers=%d; dupes=%d; frame_size=%d; datalen=%d; FAILED" % ('-' * 33, noof_servers, alice_corridor.dupes, alice_corridor.frame_size, datalen)) from e
            if all_data != rxd_data:
                print("%s servers=%d; dupes=%d; frame_size=%d; datalen=%d; FAILED" % ('-' * 33, noof_servers, alice_corridor.dupes, alice_corridor.frame_size, datalen))
                self.assertEqual(all_data, rxd_data)
            self.assertRaises(Empty, bob_corridor.get_nowait)
        alice_corridor.close()
        bob_corridor.close()
        alice_harem.quit()
        bob_harem.quit()

    def run_test_with_N_servers_and_dupes(self, noof_servers, dupes, framesize_lst, timeout=1800):
        for frame_size in framesize_lst:
            self.__run_super_duper_simple_test(noof_servers=noof_servers, dupes=dupes,
                                               frame_size=frame_size, datalen_lst=(
                           frame_size // 2, frame_size - 1, frame_size, frame_size + 1,
                           frame_size * 2 - 1, frame_size * 2, frame_size * 2 + 1,
                           frame_size * 3 - 1, frame_size * 3, frame_size * 3 + 1,
                           frame_size * 9 - 1, frame_size * 9, frame_size * 9 + 1), timeout=timeout)

    # def testBasicOne(self):
    #     alice_harem, bob_harem = setUpForNServers(noof_servers=10, strict=False)
    #     alice_corridor = alice_harem.open(bobs_PK)
    #     bob_corridor = bob_harem.open(alices_PK)
    #     sleep(5)
    #     all_data = generate_random_alphanumeric_string(500).encode()
    #     alice_corridor.put(all_data)
    #     sleep(5)
    #     rxd_data = bob_corridor.get(timeout=3600)
    #     if all_data != rxd_data:
    #         self.assertEqual(all_data, rxd_data)
    #     self.assertRaises(Empty, bob_corridor.get_nowait)
    #     alice_corridor.close()
    #     bob_corridor.close()
    #     alice_harem.quit()
    #     bob_harem.quit()
    #
    # def testSDSOwithTimeout10(self):
    #     self.assertRaises(RookeryCorridorTimeoutError, self.__run_super_duper_simple_test, 1, 0, 32, (8, 16, 31, 32, 256, 512), 10)  # 10 is timeout value

    def testSlightlyOddValues(self):
        self.__run_super_duper_simple_test(noof_servers=5, dupes=5, frame_size=256, datalen_lst=(0, 0, 1, 1, 0, 1))

'''

    def testSDSOwithTimeout180(self):
        self.__run_super_duper_simple_test(noof_servers=5, dupes=0, frame_size=32, datalen_lst=(8, 16, 31, 32, 33), timeout=180)

    #
    def testSDSOwithTimeoutDefault(self):
        self.__run_super_duper_simple_test(noof_servers=5, dupes=0, frame_size=32, datalen_lst=(8, 16, 31, 32, 33))

    def testD4SimpleFileTransmission(self):
        self.run_test_with_N_servers_and_dupes(noof_servers=3, dupes=4, framesize_lst=(32,))

    def testD3SimpleFileTransmission(self):
        self.run_test_with_N_servers_and_dupes(noof_servers=3, dupes=3, framesize_lst=(32,))

    def testD2SimpleFileTransmission(self):
        self.run_test_with_N_servers_and_dupes(noof_servers=8, dupes=2, framesize_lst=(32,))

    def testD1SimpleFileTransmission(self):
        self.run_test_with_N_servers_and_dupes(noof_servers=8, dupes=1, framesize_lst=(32,))

    def testD0SimpleFileTransmission(self):
        self.run_test_with_N_servers_and_dupes(noof_servers=8, dupes=0, framesize_lst=(32,))

    def testD4BigFileTransmission(self):
        self.run_test_with_N_servers_and_dupes(noof_servers=8, dupes=4, framesize_lst=(128, 256))

    def testD3BigFileTransmission(self):
        self.run_test_with_N_servers_and_dupes(noof_servers=8, dupes=3, framesize_lst=(128, 256))

    def testD2BigFileTransmission(self):
        self.run_test_with_N_servers_and_dupes(noof_servers=8, dupes=2, framesize_lst=(128, 256))

    def testD1BigFileTransmission(self):
        self.run_test_with_N_servers_and_dupes(noof_servers=8, dupes=1, framesize_lst=(128, 256))

    def testD0BigFileTransmission(self):
        self.run_test_with_N_servers_and_dupes(noof_servers=8, dupes=0, framesize_lst=(128, 256))

    def testSuperDuperSimpleVariety(self):
        noof_servers = 1
        timeout = 30
        for dupes in (4, 3, 2, 1, 0):
            self.run_test_with_N_servers_and_dupes(noof_servers=noof_servers, dupes=dupes, framesize_lst=(64, 128, 256), timeout=timeout)


class TestCorridorsOne(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        pass

    @classmethod
    def tearDownClass(cls):
        pass

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def testSimpleCreateAndDestroyTest(self):
        for noof_servers in range(1, 5):
            alice_harem, bob_harem = setUpForNServers(noof_servers)
            self.assertEqual(alice_harem.corridors, [])
            self.assertEqual(bob_harem.corridors, [])
            alice_corridor = alice_harem.open(bobs_PK)
            self.assertEqual(alice_corridor.closed, False)
            alice_corrid_2 = alice_harem.open(bobs_PK)
            self.assertEqual(alice_corridor.closed, False)
            self.assertEqual(alice_corrid_2.closed, False)
            sleep(2)
            bob_corridor = bob_harem.open(alices_PK)
            self.assertEqual(bob_corridor.closed, False)
            bob_corrid_2 = bob_harem.open(alices_PK)
            self.assertEqual(bob_corridor.closed, False)
            self.assertEqual(bob_corrid_2.closed, False)
            assert(bob_corridor == bob_corrid_2)
            assert(alice_corridor == alice_corrid_2)
            assert(bob_corridor != alice_corridor)
            sleep(2)
            if bob_corridor.closed:
                self.assertEqual(bob_corridor.closed, False)
            bob_corridor.close()
            self.assertRaises(RookeryCorridorAlreadyClosedError, bob_corrid_2.close)
            alice_corridor.close()
            self.assertRaises(RookeryCorridorAlreadyClosedError, alice_corrid_2.close)
            sleep(2)
            self.assertEqual(alice_harem.corridors, [])
            self.assertEqual(bob_harem.corridors, [])
            alice_harem.quit()
            bob_harem.quit()

    def testMarcoPolo(self):
        for noof_servers in range(1, 5):
            alice_harem, bob_harem = setUpForNServers(noof_servers)
            self.assertEqual(alice_harem.corridors, [])
            self.assertEqual(bob_harem.corridors, [])
            alice_corridor = alice_harem.open(bobs_PK)
            bob_corridor = bob_harem.open(alices_PK)
            alice_corridor.put(b"MARCO?")
            sleep(2)
            self.assertEqual(bob_corridor.get(), b"MARCO?")
            sleep(2)
            bob_corridor.put(b"POLO!")
            sleep(2)
            self.assertEqual(alice_corridor.get(), b"POLO!")
            sleep(2)
            self.assertEqual(alice_corridor.irc_servers, list(alice_harem.bots.keys()))
            self.assertEqual(bob_corridor.irc_servers, list(bob_harem.bots.keys()))
            alice_corridor.close()
            bob_corridor.close()
            alice_harem.quit()
            bob_harem.quit()

    def testMarcoPoloWithoutPausesthe(self):
        for noof_servers in range(1, 5):
            alice_harem, bob_harem = setUpForNServers(noof_servers)
            self.assertEqual(alice_harem.corridors, [])
            self.assertEqual(bob_harem.corridors, [])
            alice_corridor = alice_harem.open(bobs_PK)
            bob_corridor = bob_harem.open(alices_PK)
            alice_corridor.put(b"MARCO?")
            self.assertEqual(bob_corridor.get(), b"MARCO?")
            bob_corridor.put(b"POLO!")
            self.assertEqual(alice_corridor.get(), b"POLO!")
            self.assertEqual(alice_corridor.irc_servers, list(alice_harem.bots.keys()))
            self.assertEqual(bob_corridor.irc_servers, list(bob_harem.bots.keys()))
            alice_corridor.close()
            bob_corridor.close()
            alice_harem.quit()
            bob_harem.quit()

    def testMarcoPoloOfBorntodieANDcicero(self):
        for noof_servers in range(1, 5):
            alice_harem, bob_harem = setUpForNServers(noof_servers)
            self.assertEqual(alice_harem.corridors, [])
            self.assertEqual(bob_harem.corridors, [])
            alice_corridor = alice_harem.open(bobs_PK)
            bob_corridor = bob_harem.open(alices_PK)
            alice_corridor.put(BORN_TO_DIE_IN_BYTES)
            sleep(20)
            received_data = bob_corridor.get(timeout=20)
            self.assertEqual(received_data, BORN_TO_DIE_IN_BYTES)
            bob_corridor.put(CICERO.encode())
            sleep(20)
            received_data = alice_corridor.get(timeout=20)
            self.assertEqual(received_data, CICERO.encode())
            self.assertEqual(alice_corridor.irc_servers, list(alice_harem.bots.keys()))
            self.assertEqual(bob_corridor.irc_servers, list(bob_harem.bots.keys()))
            alice_corridor.close()
            bob_corridor.close()
            alice_harem.quit()
            bob_harem.quit()

    def testMarcoPoloOfDELAYEDBOBCORRIDORborntodieANDcicero(self):
        for noof_servers in range(1, 5):
            alice_harem, bob_harem = setUpForNServers(noof_servers)
            self.assertEqual(alice_harem.corridors, [])
            self.assertEqual(bob_harem.corridors, [])
            alice_corridor = alice_harem.open(bobs_PK)
            alice_corridor.put(BORN_TO_DIE_IN_BYTES)
            sleep(20)
            bob_corridor = bob_harem.open(alices_PK)
            received_data = bob_corridor.get(timeout=20)
            self.assertEqual(received_data, BORN_TO_DIE_IN_BYTES)
            bob_corridor.put(CICERO.encode())
            sleep(20)
            received_data = alice_corridor.get(timeout=20)
            self.assertEqual(received_data, CICERO.encode())
            self.assertEqual(alice_corridor.irc_servers, list(alice_harem.bots.keys()))
            self.assertEqual(bob_corridor.irc_servers, list(bob_harem.bots.keys()))
            alice_corridor.close()
            bob_corridor.close()
            alice_harem.quit()
            bob_harem.quit()


class TestCorridorsBigFiles(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        pass

    @classmethod
    def tearDownClass(cls):
        pass

    def runATestOnThisFile(self, fname, alice_corridor, bob_corridor, dupes, frame_size):
        alice_corridor.dupes = dupes
        alice_corridor.frame_size = frame_size
        bob_corridor.dupes = dupes
        bob_corridor.frame_size = frame_size
        with open(fname, "rb") as f:
            data_to_send = bytes(f.read())
        alice_corridor.put(data_to_send)
        sleep(10)
        received_data = bob_corridor.get(timeout=10)
        i = 0
        while i < min(len(received_data), len(data_to_send)) and received_data[i] == data_to_send[i]:
            i += 1
        if i < min(len(received_data), len(data_to_send)):
            print("WARNING -- mismatch @ #%d" % i)
            print("The final %d chars do not match" % max(len(received_data), len(data_to_send)) - i)
        self.assertEqual(received_data, data_to_send)

    def runABigBadThoroughTestOnThisFile(self, fname):
        for noof_servers in (1, 5, 10):
            alice_harem, bob_harem = setUpForNServers(noof_servers)
            self.assertEqual(alice_harem.corridors, [])
            self.assertEqual(bob_harem.corridors, [])
            alice_corridor = alice_harem.open(bobs_PK)
            bob_corridor = bob_harem.open(alices_PK)
            for dupes in (0, 1, 2):
                for frame_size in (16, 32, 64, 128, 256):
                    self.runATestOnThisFile(fname, alice_corridor, bob_corridor, dupes, frame_size)
            alice_corridor.close()
            bob_corridor.close()
            alice_harem.quit()
            bob_harem.quit()
        self.assertEqual(alice_corridor.irc_servers, list(alice_harem.bots.keys()))
        self.assertEqual(bob_corridor.irc_servers, list(bob_harem.bots.keys()))

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def testCushionStl(self):
        self.runABigBadThoroughTestOnThisFile("/Users/mchobbit/Downloads/cushion.stl")

    def testPrinterFilesCfgTarGz(self):
        self.runABigBadThoroughTestOnThisFile("/Users/mchobbit/Downloads/t1-printer-files.cfg.tar.gz")

    def testSideCushnStl(self):
        self.runABigBadThoroughTestOnThisFile("/Users/mchobbit/Downloads/side_cushion.stl")

    def testPiHolderStl(self):
        self.runABigBadThoroughTestOnThisFile("/Users/mchobbit/Downloads/pi_holder.stl")
'''

if __name__ == "__main__":
    # import sys;sys.argv = ['', 'TestHaremTwo.testSimpleTest']
    unittest.main()

