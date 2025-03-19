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
from my.globals import ALL_SANDBOX_IRC_NETWORK_NAMES, RSA_KEY_SIZE
from random import randint
from my.classes.exceptions import RookerySimpipeTimeoutError, RookerySimpipeAlreadyClosedError
from my.globals.poetry import BORN_TO_DIE_IN_BYTES, CICERO
from my.irctools.jaracorocks.harem import Harem

alices_rsa_key = RSA.generate(RSA_KEY_SIZE)
bobs_rsa_key = RSA.generate(RSA_KEY_SIZE)
carols_rsa_key = RSA.generate(RSA_KEY_SIZE)
alices_PK = alices_rsa_key.public_key()
bobs_PK = bobs_rsa_key.public_key()
carols_PK = carols_rsa_key.public_key()
some_random_rsa_key = RSA.generate(RSA_KEY_SIZE)
some_random_PK = some_random_rsa_key.public_key()


def setUpForNServers(noof_servers):
    if noof_servers < 1:
        raise ValueError("noof_servers must be >=1")
    my_list_of_all_irc_servers = ALL_SANDBOX_IRC_NETWORK_NAMES[:noof_servers]  # ALL_REALWORLD_IRC_NETWORK_NAMES
    alice_nick = 'alice%d' % randint(111, 999)
    bob_nick = 'bob%d' % randint(111, 999)
    the_room = '#room' + generate_random_alphanumeric_string(5)
    alice_harem = Harem([the_room], alice_nick, my_list_of_all_irc_servers, alices_rsa_key)
    bob_harem = Harem([the_room], bob_nick, my_list_of_all_irc_servers, bobs_rsa_key)
    sleep(20)
    return (alice_harem, bob_harem)


class TestSimpipesOpeningAndClosing(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.alice_harem, cls.bob_harem = setUpForNServers(1)  # opens alice and bob harems

    @classmethod
    def tearDownClass(cls):
        cls.alice_harem.quit()
        cls.bob_harem.quit()

    def setUp(self):
        print("----------------------------------------------------------------------------------------------------")
        self.assertTrue(self.alice_harem.connected_and_joined, "Alice should have connected and joined by now.")
        self.assertTrue(self.bob_harem.connected_and_joined, "Bob should have connected and joined by now.")
        sleep(20 if len(self.alice_harem.true_homies) < 1 or len(self.bob_harem.true_homies) < 1 else 0)
        self.assertGreaterEqual(len(self.alice_harem.homies_pubkeys), 1, "By now, Alice's harem of bots should have gathered at least one public key from another potential homie.")
        self.assertGreaterEqual(len(self.bob_harem.homies_pubkeys), 1, "By now, Bob's harem of bots should have gathered at least one public key from another potential homie.")
        self.assertGreaterEqual(len(self.alice_harem.true_homies), 1, "By now, Alice should have found at least one true homie: Bob.")
        self.assertGreaterEqual(len(self.bob_harem.true_homies), 1, "By now, Bob should have tound at least one true homie: Alice.")

    def tearDown(self):
        self.assertTrue(self.alice_harem.connected_and_joined, "Alice should have connected and joined by now.")
        self.assertTrue(self.bob_harem.connected_and_joined, "Bob should have connected and joined by now.")
        self.assertGreaterEqual(len(self.alice_harem.homies_pubkeys), 1, "By now, Alice's harem of bots should have gathered at least one public key from another potential homie.")
        self.assertGreaterEqual(len(self.bob_harem.homies_pubkeys), 1, "By now, Bob's harem of bots should have gathered at least one public key from another potential homie.")
        self.assertGreaterEqual(len(self.alice_harem.true_homies), 1, "By now, Alice should have found at least one true homie: Bob.")
        self.assertGreaterEqual(len(self.bob_harem.true_homies), 1, "By now, Bob should have tound at least one true homie: Alice.")

    def close_any_lingering_simpipes(self):
        for h in (self.alice_harem, self.bob_harem):
            [s.close() for s in h.simpipes]
            self.assertEqual(h.simpipes, [])

    def testSimplest5sPause(self):
        self.close_any_lingering_simpipes()
        alice_simpipe = self.alice_harem.open(bobs_PK)
        bob_simpipe = self.bob_harem.open(alices_PK)
        self.assertFalse(alice_simpipe.is_closed)
        self.assertFalse(bob_simpipe.is_closed)
        sleep(5)
        alice_simpipe.close()
        bob_simpipe.close()
        self.assertTrue(alice_simpipe.is_closed)
        self.assertTrue(bob_simpipe.is_closed)
        self.assertEqual(len(self.alice_harem.simpipes), 0)
        self.assertEqual(len(self.bob_harem.simpipes), 0)

        self.close_any_lingering_simpipes()

    def testSimplest1sPause(self):
        self.close_any_lingering_simpipes()
        alice_simpipe = self.alice_harem.open(bobs_PK)
        bob_simpipe = self.bob_harem.open(alices_PK)
        self.assertFalse(alice_simpipe.is_closed)
        self.assertFalse(bob_simpipe.is_closed)
        sleep(1)
        alice_simpipe.close()
        bob_simpipe.close()
        self.assertTrue(alice_simpipe.is_closed)
        self.assertTrue(bob_simpipe.is_closed)
        self.assertEqual(len(self.alice_harem.simpipes), 0)
        self.assertEqual(len(self.bob_harem.simpipes), 0)

    def testSimplest0sPause(self):
        self.close_any_lingering_simpipes()
        alice_simpipe = self.alice_harem.open(bobs_PK)
        bob_simpipe = self.bob_harem.open(alices_PK)
        self.assertFalse(alice_simpipe.is_closed)
        self.assertFalse(bob_simpipe.is_closed)
        alice_simpipe.close()
        bob_simpipe.close()
        self.assertTrue(alice_simpipe.is_closed)
        self.assertTrue(bob_simpipe.is_closed)
        self.assertEqual(len(self.alice_harem.simpipes), 0)
        self.assertEqual(len(self.bob_harem.simpipes), 0)

    def testOpenOnlyOneSimpipe(self):
        self.close_any_lingering_simpipes()
        alice_simpipe = self.alice_harem.open(bobs_PK)
        alice_simpipe.close()
        self.assertTrue(alice_simpipe.is_closed)
        self.assertEqual(len(self.alice_harem.simpipes), 0)
        self.assertEqual(len(self.bob_harem.simpipes), 0)

    def testKeepCrashingUTIIUDWhwatever(self):
        self.close_any_lingering_simpipes()
        alice_simpipe = self.alice_harem.open(bobs_PK)
        sleep(5)
        out_data = b"HELLO THERE. HOW ARE YOU?"
        alice_simpipe.put(out_data)
        sleep(5)
        alice_simpipe.close()
        self.assertRaises(RookerySimpipeAlreadyClosedError, alice_simpipe.put, b"THIS SHOULD NOT WORK")
        bob_simpipe = self.bob_harem.open(alices_PK)
        rxd_data = bob_simpipe.get(timeout=300)  # timeout=10
        self.assertEqual(out_data, rxd_data)
        bob_simpipe.close()
        self.assertTrue(alice_simpipe.is_closed)
        self.assertTrue(bob_simpipe.is_closed)
        self.assertRaises(RookerySimpipeAlreadyClosedError, bob_simpipe.put, b"THIS SHOULD NOT WORK")
        self.assertEqual(len(self.alice_harem.simpipes), 0)
        self.assertEqual(len(self.bob_harem.simpipes), 0)

    def testFasterKeepCrashingKillKillKill(self):
        self.close_any_lingering_simpipes()
        self.assertEqual(len(self.alice_harem.simpipes), 0)
        self.assertEqual(len(self.bob_harem.simpipes), 0)
        alice_simpipe = self.alice_harem.open(bobs_PK)
        out_data = b"HELLO THERE. HOW ARE YOU?"
        alice_simpipe.put(out_data)
        alice_simpipe.close()
        self.assertRaises(RookerySimpipeAlreadyClosedError, alice_simpipe.put, b"THIS SHOULD NOT WORK")
        bob_simpipe = self.bob_harem.open(alices_PK)
        try:
            bob_simpipe.get(timeout=5)
        except Empty:
            pass
        bob_simpipe.close()
        self.assertTrue(alice_simpipe.is_closed)
        self.assertTrue(bob_simpipe.is_closed)
        self.assertRaises(RookerySimpipeAlreadyClosedError, bob_simpipe.put, b"THIS SHOULD NOT WORK")
        self.assertEqual(len(self.alice_harem.simpipes), 0)
        self.assertEqual(len(self.bob_harem.simpipes), 0)
        self.assertEqual(len(self.alice_harem.simpipes), 0)
        self.assertEqual(len(self.bob_harem.simpipes), 0)

    def testOpenOnlyOneCrdrAndSayHelloThenOpenOtherCrdr(self):
        self.close_any_lingering_simpipes()
        alice_simpipe = self.alice_harem.open(bobs_PK)
        out_data = b"HELLO THERE. HOW ARE YOU?"
        alice_simpipe.put(out_data)
        alice_simpipe.close()
        self.assertRaises(RookerySimpipeAlreadyClosedError, alice_simpipe.put, b"THIS SHOULD NOT WORK")
        bob_simpipe = self.bob_harem.open(alices_PK)
        rxd_data = bob_simpipe.get(timeout=300)  # timeout=10
        self.assertEqual(out_data, rxd_data)
        bob_simpipe.close()
        self.assertTrue(alice_simpipe.is_closed)
        self.assertTrue(bob_simpipe.is_closed)
        self.assertRaises(RookerySimpipeAlreadyClosedError, bob_simpipe.put, b"THIS SHOULD NOT WORK")
        sleep(5)
        self.assertEqual(len(self.alice_harem.simpipes), 0)
        self.assertEqual(len(self.bob_harem.simpipes), 0)

    def testBANJAX567(self):
        """Open corridor. Send message. Close corridor. THEN, on recipient, try to read incoming data."""
        self.close_any_lingering_simpipes()
        alice_simpipe = self.alice_harem.open(bobs_PK)
        out_data = b"HELLO THERE. HOW ARE YOU?"
        alice_simpipe.put(out_data)
        alice_simpipe.close()
        self.assertTrue(alice_simpipe.is_closed)
        print("Daring...")
        self.assertRaises(RookerySimpipeAlreadyClosedError, alice_simpipe.put, b"THIS SHOULD NOT WORK")
        bob_simpipe = self.bob_harem.open(alices_PK)
        rxd_data = bob_simpipe.get(timeout=1000)  # timeout=10
        self.assertEqual(out_data, rxd_data)
        bob_simpipe.close()
        self.assertTrue(bob_simpipe.is_closed)
        self.assertRaises(RookerySimpipeAlreadyClosedError, bob_simpipe.put, b"THIS SHOULD NOT WORK")
        sleep(5)
        self.assertEqual(len(self.alice_harem.simpipes), 0)
        self.assertEqual(len(self.bob_harem.simpipes), 0)

    def testScreamIntoTheVoid(self):
        self.close_any_lingering_simpipes()
        out_data = b"ANOTHER FABULOUS TEST! HUZZAH%d..." % randint(1, 100000)
        self.assertEqual(self.alice_harem.simpipes, [], "There should be no simpipes at Alice")
        self.assertEqual(self.bob_harem.simpipes, [], "There should be no simpipes at Bob")
        alice_simpipe = self.alice_harem.open(bobs_PK)
        self.assertEqual(len(self.alice_harem.simpipes), 1)
        self.assertEqual(self.bob_harem.simpipes, [])
        alice_simpipe.put(out_data)
        self.assertEqual(len(self.alice_harem.simpipes), 1)
        sleep(10 if self.bob_harem.simpipes == [] else 0)
        self.assertEqual(len(self.bob_harem.simpipes), 1)
        the_bob_simpipe_that_alice_made_bob_create = self.bob_harem.simpipes[0]
        self.assertEqual(alice_simpipe.uid, the_bob_simpipe_that_alice_made_bob_create.uid)
        self.assertTrue(self.alice_harem.is_handshook_with(bobs_PK))
        self.assertTrue(self.bob_harem.is_handshook_with(alices_PK))
        another_bobC = self.bob_harem.open(alices_PK)
        self.assertEqual(another_bobC.uid, the_bob_simpipe_that_alice_made_bob_create.uid)
        alice_simpipe.close()
        self.assertEqual(len(self.bob_harem.simpipes), 1)
        self.assertTrue(self.bob_harem.is_handshook_with(alices_PK))
        the_simpipe_that_BOB_had_to_open_for_Alice = self.bob_harem.simpipes[0]
        self.assertEqual(alice_simpipe.uid, the_simpipe_that_BOB_had_to_open_for_Alice.uid)
        alice_simpipe.close()
#        self.assertRaises(RookerySimpipeAlreadyClosedError, alice_simpipe.close)
        bob_simpipe = self.bob_harem.open(alices_PK)
        self.assertEqual(bob_simpipe.uid, the_simpipe_that_BOB_had_to_open_for_Alice.uid)
        rxd_data = bob_simpipe.get(timeout=10)
        self.assertEqual(out_data, rxd_data)
        bob_simpipe.close()
        self.assertTrue(bob_simpipe.is_closed, "I just closed this simpipe. Why is it open?")
        self.assertRaises(RookerySimpipeAlreadyClosedError, bob_simpipe.put, b"THIS SHOULD NOT WORK")
        self.assertEqual(self.alice_harem.simpipes, [], "Alice should have no simpipes left.")
        bob_simpipe.close()
        self.assertEqual(self.bob_harem.simpipes, [])
        self.assertTrue(another_bobC.is_closed, "I closed bob_simpipe; that should have closed another_bobC, too.")
        self.assertTrue(the_bob_simpipe_that_alice_made_bob_create.is_closed, "I closed bob_simpipe; that should have closed the_bob_simpipe_that_alice_made_bob_create, too.")
        self.assertEqual(self.bob_harem.simpipes, [])
        self.assertTrue(another_bobC.is_closed)
        self.assertTrue(the_bob_simpipe_that_alice_made_bob_create.is_closed)
        sleep(5)
        self.assertEqual(len(self.alice_harem.simpipes), 0)
        self.assertEqual(len(self.bob_harem.simpipes), 0)


class TestSimpipesZero(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def __run_super_duper_simple_test(self, noof_servers, dupes, frame_size, datalen_lst, timeout=1800):
        alice_harem, bob_harem = setUpForNServers(noof_servers=noof_servers)
        alice_simpipe = alice_harem.open(bobs_PK)
        bob_simpipe = bob_harem.open(alices_PK)
        sleep(5)
        alice_simpipe.dupes = dupes
        alice_simpipe.frame_size = frame_size
        if type(datalen_lst) is int:
            datalen_lst = (datalen_lst,)
        for datalen in datalen_lst:
            print("%s servers=%d; dupes=%d; frame_size=%d; datalen=%d" % ('-' * 33, noof_servers, alice_simpipe.dupes, alice_simpipe.frame_size, datalen))
            all_data = generate_random_alphanumeric_string(datalen).encode()
            alice_simpipe.put(all_data)
            try:
                rxd_data = bob_simpipe.get(timeout=timeout)
            except Empty as e:
                raise RookerySimpipeTimeoutError("Transfer took too long! --- %s servers=%d; dupes=%d; frame_size=%d; datalen=%d; FAILED" % ('-' * 33, noof_servers, alice_simpipe.dupes, alice_simpipe.frame_size, datalen)) from e
            if all_data != rxd_data:
                print("%s servers=%d; dupes=%d; frame_size=%d; datalen=%d; FAILED" % ('-' * 33, noof_servers, alice_simpipe.dupes, alice_simpipe.frame_size, datalen))
                self.assertEqual(all_data, rxd_data)
            self.assertRaises(Empty, bob_simpipe.get_nowait)
        alice_simpipe.close()
        bob_simpipe.close()
        alice_harem.quit()
        bob_harem.quit()

    def run_test_with_N_servers_and_dupes(self, noof_servers, dupes, framesize_lst, timeout=600):
        for frame_size in framesize_lst:
            self.__run_super_duper_simple_test(noof_servers=noof_servers, dupes=dupes,
                                               frame_size=frame_size, datalen_lst=(
                           frame_size // 2, frame_size - 1, frame_size, frame_size + 1,
                           frame_size * 2 - 1, frame_size * 2, frame_size * 2 + 1,
                           frame_size * 3 - 1, frame_size * 3, frame_size * 3 + 1,
                           frame_size * 9 - 1, frame_size * 9, frame_size * 9 + 1), timeout=timeout)

    # def testBasicOne(self):
    #     alice_harem, bob_harem = setUpForNServers(noof_servers=1)
    #     alice_simpipe = alice_harem.open(bobs_PK)
    #     bob_simpipe = bob_harem.open(alices_PK)
    #     sleep(5)
    #     all_data = generate_random_alphanumeric_string(500).encode()
    #     alice_simpipe.put(all_data)
    #     sleep(5)
    #     rxd_data = bob_simpipe.get(timeout=1200)
    #     if all_data != rxd_data:
    #         self.assertEqual(all_data, rxd_data)
    #     self.assertRaises(Empty, bob_simpipe.get_nowait)
    #     alice_simpipe.close()
    #     bob_simpipe.close()
    #     alice_harem.quit()
    #     bob_harem.quit()
    # #
    # def testSDSOwithTimeout10(self):
    #     self.assertRaises(RookerySimpipeTimeoutError, self.__run_super_duper_simple_test, 1, 0, 32, (8, 16, 31, 32, 256, 512), 10)  # 10 is timeout value

    def testSlightlyOddValues(self):
        self.__run_super_duper_simple_test(noof_servers=5, dupes=5, frame_size=256, datalen_lst=(0, 0, 1, 1, 0, 1))

    def testSDSOwithTimeout180(self):
        self.__run_super_duper_simple_test(noof_servers=5, dupes=0, frame_size=32, datalen_lst=(8, 16, 31, 32, 33), timeout=180)

    #
    def testSDSOwithTimeoutDefault(self):
        self.__run_super_duper_simple_test(noof_servers=5, dupes=0, frame_size=32, datalen_lst=(8, 16, 31, 32, 33))

    # def testD4SimpleFileTransmission(self):
    #     self.run_test_with_N_servers_and_dupes(noof_servers=3, dupes=4, framesize_lst=(32,))
    #
    # def testD3SimpleFileTransmission(self):
    #     self.run_test_with_N_servers_and_dupes(noof_servers=3, dupes=3, framesize_lst=(32,))
    #
    # def testD2SimpleFileTransmission(self):
    #     self.run_test_with_N_servers_and_dupes(noof_servers=8, dupes=2, framesize_lst=(32,))
    #
    # def testD1SimpleFileTransmission(self):
    #     self.run_test_with_N_servers_and_dupes(noof_servers=8, dupes=1, framesize_lst=(32,))
    #
    # def testD0SimpleFileTransmission(self):
    #     self.run_test_with_N_servers_and_dupes(noof_servers=8, dupes=0, framesize_lst=(32,))
    #
    # def testD4BigFileTransmission(self):
    #     self.run_test_with_N_servers_and_dupes(noof_servers=8, dupes=4, framesize_lst=(128, 256))
    #
    # def testD3BigFileTransmission(self):
    #     self.run_test_with_N_servers_and_dupes(noof_servers=8, dupes=3, framesize_lst=(128, 256))
    #
    # def testD2BigFileTransmission(self):
    #     self.run_test_with_N_servers_and_dupes(noof_servers=8, dupes=2, framesize_lst=(128, 256))
    #
    # def testD1BigFileTransmission(self):
    #     self.run_test_with_N_servers_and_dupes(noof_servers=8, dupes=1, framesize_lst=(128, 256))
    #
    # def testD0BigFileTransmission(self):
    #     self.run_test_with_N_servers_and_dupes(noof_servers=8, dupes=0, framesize_lst=(128, 256), timeout=120)

    def testSuperDuperSimpleVariety(self):
        noof_servers = 1
        timeout = 30
        for dupes in (4, 3, 2, 1, 0):
            self.run_test_with_N_servers_and_dupes(noof_servers=noof_servers, dupes=dupes, framesize_lst=(64, 128, 256), timeout=timeout)

'''
class TestSimpipesOne(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def testSimpleCreateAndDestroyTest(self):
        for noof_servers in range(1, 5):
            alice_harem, bob_harem = setUpForNServers(noof_servers)
            self.assertEqual(alice_harem.simpipes, [])
            self.assertEqual(bob_harem.simpipes, [])
            alice_simpipe = alice_harem.open(bobs_PK)
            if alice_simpipe.closed is True:
                print("WTF? Why is this CLOSED? Okay, fine. I'll count to 5 and try again.")
                sleep(5)
            self.assertEqual(alice_simpipe.closed, False)
            alice_corrid_2 = alice_harem.open(bobs_PK)
            self.assertEqual(alice_simpipe.closed, False)
            self.assertEqual(alice_corrid_2.closed, False)
            sleep(2)
            bob_simpipe = bob_harem.open(alices_PK)
            self.assertEqual(bob_simpipe.closed, False)
            bob_corrid_2 = bob_harem.open(alices_PK)
            self.assertEqual(bob_simpipe.closed, False)
            self.assertEqual(bob_corrid_2.closed, False)
            assert(bob_simpipe == bob_corrid_2)
            assert(alice_simpipe == alice_corrid_2)
            assert(bob_simpipe != alice_simpipe)
            sleep(2)
            if bob_simpipe.closed:
                self.assertEqual(bob_simpipe.closed, False)
            bob_simpipe.close()
            self.assertRaises(RookerySimpipeAlreadyClosedError, bob_corrid_2.close)
            alice_simpipe.close()
            self.assertRaises(RookerySimpipeAlreadyClosedError, alice_corrid_2.close)
            sleep(2)
            self.assertEqual(alice_harem.simpipes, [])
            self.assertEqual(bob_harem.simpipes, [])
            alice_harem.quit()
            bob_harem.quit()

    def testMarcoPolo(self):
        for noof_servers in range(1, 5):
            alice_harem, bob_harem = setUpForNServers(noof_servers)
            self.assertEqual(alice_harem.simpipes, [])
            self.assertEqual(bob_harem.simpipes, [])
            alice_simpipe = alice_harem.open(bobs_PK)
            bob_simpipe = bob_harem.open(alices_PK)
            alice_simpipe.put(b"MARCO?")
            sleep(2)
            self.assertEqual(bob_simpipe.get(timeout=30), b"MARCO?")
            sleep(2)
            bob_simpipe.put(b"POLO!")
            sleep(2)
            self.assertEqual(alice_simpipe.get(timeout=30), b"POLO!")
            sleep(2)
            self.assertEqual(alice_simpipe.irc_servers, list(alice_harem.bots.keys()))
            self.assertEqual(bob_simpipe.irc_servers, list(bob_harem.bots.keys()))
            alice_simpipe.close()
            bob_simpipe.close()
            alice_harem.quit()
            bob_harem.quit()

    def testMarcoPoloWithoutPausesthe(self):
        for noof_servers in range(1, 5):
            alice_harem, bob_harem = setUpForNServers(noof_servers)
            self.assertEqual(alice_harem.simpipes, [])
            self.assertEqual(bob_harem.simpipes, [])
            alice_simpipe = alice_harem.open(bobs_PK)
            bob_simpipe = bob_harem.open(alices_PK)
            alice_simpipe.put(b"MARCO?")
            self.assertEqual(bob_simpipe.get(timeout=30), b"MARCO?")
            bob_simpipe.put(b"POLO!")
            self.assertEqual(alice_simpipe.get(timeout=30), b"POLO!")
            self.assertEqual(alice_simpipe.irc_servers, list(alice_harem.bots.keys()))
            self.assertEqual(bob_simpipe.irc_servers, list(bob_harem.bots.keys()))
            alice_simpipe.close()
            bob_simpipe.close()
            alice_harem.quit()
            bob_harem.quit()

    def testMarcoPoloOfBorntodieANDcicero(self):
        for noof_servers in range(1, 5):
            alice_harem, bob_harem = setUpForNServers(noof_servers)
            self.assertEqual(alice_harem.simpipes, [])
            self.assertEqual(bob_harem.simpipes, [])
            alice_simpipe = alice_harem.open(bobs_PK)
            bob_simpipe = bob_harem.open(alices_PK)
            alice_simpipe.put(BORN_TO_DIE_IN_BYTES)
            sleep(20)
            received_data = bob_simpipe.get(timeout=30)
            self.assertEqual(received_data, BORN_TO_DIE_IN_BYTES)
            bob_simpipe.put(CICERO.encode())
            sleep(20)
            received_data = alice_simpipe.get(timeout=30)
            self.assertEqual(received_data, CICERO.encode())
            self.assertEqual(alice_simpipe.irc_servers, list(alice_harem.bots.keys()))
            self.assertEqual(bob_simpipe.irc_servers, list(bob_harem.bots.keys()))
            alice_simpipe.close()
            bob_simpipe.close()
            alice_harem.quit()
            bob_harem.quit()

    def testMarcoPoloOfDELAYEDBOBCORRIDORborntodieANDcicero(self):
        for noof_servers in range(1, 5):
            alice_harem, bob_harem = setUpForNServers(noof_servers)
            self.assertEqual(alice_harem.simpipes, [])
            self.assertEqual(bob_harem.simpipes, [])
            alice_simpipe = alice_harem.open(bobs_PK)
            alice_simpipe.put(BORN_TO_DIE_IN_BYTES)
            sleep(20)
            bob_simpipe = bob_harem.open(alices_PK)
            received_data = bob_simpipe.get(timeout=30)
            self.assertEqual(received_data, BORN_TO_DIE_IN_BYTES)
            bob_simpipe.put(CICERO.encode())
            sleep(20)
            received_data = alice_simpipe.get(timeout=30)
            self.assertEqual(received_data, CICERO.encode())
            self.assertEqual(alice_simpipe.irc_servers, list(alice_harem.bots.keys()))
            self.assertEqual(bob_simpipe.irc_servers, list(bob_harem.bots.keys()))
            alice_simpipe.close()
            bob_simpipe.close()
            alice_harem.quit()
            bob_harem.quit()


class TestSimpipesBigFiles(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        pass

    @classmethod
    def tearDownClass(cls):
        pass

    def runATestOnThisFile(self, fname, alice_simpipe, bob_simpipe, dupes, frame_size):
        alice_simpipe.dupes = dupes
        alice_simpipe.frame_size = frame_size
        bob_simpipe.dupes = dupes
        bob_simpipe.frame_size = frame_size
        with open(fname, "rb") as f:
            data_to_send = bytes(f.read())
        alice_simpipe.put(data_to_send)
        sleep(10)
        received_data = bob_simpipe.get(timeout=30)
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
            self.assertEqual(alice_harem.simpipes, [])
            self.assertEqual(bob_harem.simpipes, [])
            alice_simpipe = alice_harem.open(bobs_PK)
            bob_simpipe = bob_harem.open(alices_PK)
            for dupes in (0, 1, 2):
                for frame_size in (16, 32, 64, 128, 256):
                    self.runATestOnThisFile(fname, alice_simpipe, bob_simpipe, dupes, frame_size)
            alice_simpipe.close()
            bob_simpipe.close()
            alice_harem.quit()
            bob_harem.quit()
        self.assertEqual(alice_simpipe.irc_servers, list(alice_harem.bots.keys()))
        self.assertEqual(bob_simpipe.irc_servers, list(bob_harem.bots.keys()))

    def setUp(self):
        pass

    def tearDown(self):
        pass

    # def testCushionStl(self):
    #     self.runABigBadThoroughTestOnThisFile("/Users/mchobbit/Downloads/cushion.stl")
    #
    # def testPrinterFilesCfgTarGz(self):
    #     self.runABigBadThoroughTestOnThisFile("/Users/mchobbit/Downloads/t1-printer-files.cfg.tar.gz")
    #
    # def testSideCushnStl(self):
    #     self.runABigBadThoroughTestOnThisFile("/Users/mchobbit/Downloads/side_cushion.stl")
    #
    # def testPiHolderStl(self):
    #     self.runABigBadThoroughTestOnThisFile("/Users/mchobbit/Downloads/pi_holder.stl")
'''

if __name__ == "__main__":
    # import sys;sys.argv = ['', 'TestHaremTwo.testSimpleTest']
    unittest.main()

