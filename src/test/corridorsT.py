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
from my.globals.poetry import BORN_TO_DIE_IN_BYTES, CICERO
from threading import Thread
from my.classes.exceptions import RookeryCorridorAlreadyClosedError, RookeryCorridorTimeoutError
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
    alice_harem = Harem([the_room], alice_nick, my_list_of_all_irc_servers, alices_rsa_key)  # , autohandshake=False)
    bob_harem = Harem([the_room], bob_nick, my_list_of_all_irc_servers, bobs_rsa_key)
#    alice_harem.trigger_handshaking()
    sleep(20)
    return (alice_harem, bob_harem)


class TestTHISISBROKENWhyIsItWhyWhy(unittest.TestCase):

    def testThisOneIsNotBroken(self):
        alice_harem, bob_harem = setUpForNServers(1)
        alice_corridor = alice_harem.open(bobs_PK)
        self.assertTrue(alice_corridor.uid == alice_harem.corridors[0].uid == bob_harem.corridors[0].uid)
        alice_corridor.close(); self.assertTrue(alice_corridor.is_closed is True and alice_harem.corridors + bob_harem.corridors == [])
        [ h.quit() for h in (alice_harem, bob_harem)]  # pylint: disable=expression-not-assigned

    def testThisOneIsDefinitelyBroken(self):
        alice_harem, bob_harem = setUpForNServers(1)
        alice_corridor = alice_harem.open(bobs_PK)
        bob_corridor = bob_harem.open(alices_PK)
        self.assertTrue(bob_corridor.uid == alice_corridor.uid == alice_harem.corridors[0].uid == bob_harem.corridors[0].uid)
        alice_corridor.close()
        self.assertTrue(bob_corridor.is_closed)
        self.assertTrue(alice_corridor.is_closed)
        self.assertEqual(alice_harem.corridors, [])
        self.assertEqual(bob_harem.corridors, [])
        [ h.quit() for h in (alice_harem, bob_harem)]  # pylint: disable=expression-not-assigned

    def testThisOneIsAlsoNotBroken(self):
        alice_harem, bob_harem = setUpForNServers(1)
        alice_corridor = alice_harem.open(bobs_PK)
        bob_corridor = bob_harem.open(alices_PK); sleep(5)
        self.assertTrue(bob_corridor.uid == alice_corridor.uid == alice_harem.corridors[0].uid == bob_harem.corridors[0].uid)
        alice_corridor.close(); self.assertTrue(bob_corridor.is_closed is True and alice_corridor.is_closed is True and alice_harem.corridors + bob_harem.corridors == [])
        [ h.quit() for h in (alice_harem, bob_harem)]  # pylint: disable=expression-not-assigned

    def testThisOneIsNotBrokenToo(self):
        alice_harem, bob_harem = setUpForNServers(1)
        alice_corridor = alice_harem.open(bobs_PK); sleep(5)
        bob_corridor = bob_harem.open(alices_PK)
        self.assertTrue(bob_corridor.uid == alice_corridor.uid == alice_harem.corridors[0].uid == bob_harem.corridors[0].uid)
        alice_corridor.close(); self.assertTrue(bob_corridor.is_closed is True and alice_corridor.is_closed is True and alice_harem.corridors + bob_harem.corridors == [])
        [ h.quit() for h in (alice_harem, bob_harem)]  # pylint: disable=expression-not-assigned

    def testMakeSureSingletonsAreSingle(self):
        alice_harem, bob_harem = setUpForNServers(1)
        first_alice_corridor = alice_harem.open(bobs_PK)
        second_alice_corridor = alice_harem.open(bobs_PK)
        third_alice_corridor = alice_harem.open(bobs_PK)
        self.assertEqual(first_alice_corridor, second_alice_corridor)
        self.assertEqual(second_alice_corridor, third_alice_corridor)
        self.assertEqual(first_alice_corridor.uid, alice_harem.corridors[0].uid)
        self.assertEqual(second_alice_corridor.uid, alice_harem.corridors[0].uid)
        self.assertEqual(third_alice_corridor.uid, alice_harem.corridors[0].uid)
        first_alice_corridor.chewbacca = 1
        self.assertEqual(first_alice_corridor.chewbacca, alice_harem.corridors[0].chewbacca)
        first_alice_corridor.chewbacca += 1
        self.assertEqual(second_alice_corridor.chewbacca, alice_harem.corridors[0].chewbacca)
        self.assertEqual([first_alice_corridor], alice_harem.corridors)
        self.assertEqual([second_alice_corridor], alice_harem.corridors)
        self.assertEqual([third_alice_corridor], alice_harem.corridors)
        third_alice_corridor.close()
        self.assertTrue(first_alice_corridor.is_closed)
        self.assertTrue(second_alice_corridor.is_closed)
        self.assertTrue(third_alice_corridor.is_closed)
        self.assertEqual(alice_harem.corridors + bob_harem.corridors, [])
        [ h.quit() for h in (alice_harem, bob_harem)]  # pylint: disable=expression-not-assigned


# TestAliceBobClosingRaceCondition WORKS 100% as of 2025/03/23 @ 22:05
class TestAliceBobClosingRaceCondition(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.alice_harem, cls.bob_harem = setUpForNServers(1)  # opens alice and bob harems

    @classmethod
    def tearDownClass(cls):
        cls.alice_harem.quit()
        cls.bob_harem.quit()

    def setUp(self):
        self.assertTrue(self.alice_harem.connected_and_joined, "Alice should have connected and joined by now.")
        self.assertTrue(self.bob_harem.connected_and_joined, "Bob should have connected and joined by now.")
        sleep(20 if len(self.alice_harem.true_homies) < 1 or len(self.bob_harem.true_homies) < 1 else 0)
        self.assertGreaterEqual(len(self.alice_harem.homies_pubkeys), 1, "By now, Alice's harem of bots should have gathered at least one public key from another potential homie.")
        self.assertGreaterEqual(len(self.bob_harem.homies_pubkeys), 1, "By now, Bob's harem of bots should have gathered at least one public key from another potential homie.")
        self.assertGreaterEqual(len(self.alice_harem.true_homies), 1, "By now, Alice should have found at least one true homie: Bob.")
        self.assertGreaterEqual(len(self.bob_harem.true_homies), 1, "By now, Bob should have found at least one true homie: Alice.")
        self.assertEqual(self.alice_harem.corridors, [], "Previous test left Alice with open corridor(s)")
        self.assertEqual(self.bob_harem.corridors, [], "Previous test left Bob with open corridor(s)")
        print("╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍")

    def tearDown(self):
        print("====================================================================================================")
        self.assertTrue(self.alice_harem.connected_and_joined, "Alice should have connected and joined by now.")
        self.assertTrue(self.bob_harem.connected_and_joined, "Bob should have connected and joined by now.")
        self.assertGreaterEqual(len(self.alice_harem.homies_pubkeys), 1, "By now, Alice's harem of bots should have gathered at least one public key from another potential homie.")
        self.assertGreaterEqual(len(self.bob_harem.homies_pubkeys), 1, "By now, Bob's harem of bots should have gathered at least one public key from another potential homie.")
        self.assertGreaterEqual(len(self.alice_harem.true_homies), 1, "By now, Alice should have found at least one true homie: Bob.")
        self.assertGreaterEqual(len(self.bob_harem.true_homies), 1, "By now, Bob should have found at least one true homie: Alice.")
        self.assertEqual(self.alice_harem.corridors, [], "Alice should have closed all corridors by now")
        self.assertEqual(self.bob_harem.corridors, [], "Bob should have closed all corridors by now")

    def testAAAAliceOnly(self):  # GUARANTEED TO WORK. LAST MODIFIED 2025/03/23 @ 18:42
        alice_corridor = self.alice_harem.open(bobs_PK)
        bob_corridor = self.bob_harem.open(alices_PK)
        sleep(2)
        alice_corridor.close()
        self.assertTrue(alice_corridor.is_closed)
        self.assertTrue(bob_corridor.is_closed)

    def testBBBAliceOnly(self):  # GUARANTEED TO WORK. LAST MODIFIED 2025/03/23 @ 18:42
        alice_corridor = self.alice_harem.open(bobs_PK)
        bob_corridor = self.bob_harem.open(alices_PK)
        sleep(2)
        alice_corridor.close()
        self.assertTrue(alice_corridor.is_closed)
        self.assertTrue(bob_corridor.is_closed)

    def testCCCBobOnly(self):  # GUARANTEED TO WORK. LAST MODIFIED 2025/03/23 @ 18:42
        alice_corridor = self.alice_harem.open(bobs_PK)
        bob_corridor = self.bob_harem.open(alices_PK)
        sleep(2)
        bob_corridor.close()
        self.assertTrue(alice_corridor.is_closed)
        self.assertTrue(bob_corridor.is_closed)

    def testDDDBobOnly(self):  # GUARANTEED TO WORK. LAST MODIFIED 2025/03/23 @ 18:42
        alice_corridor = self.alice_harem.open(bobs_PK)
        bob_corridor = self.bob_harem.open(alices_PK)
        sleep(2)
        bob_corridor.close()
        self.assertTrue(alice_corridor.is_closed)
        self.assertTrue(bob_corridor.is_closed)

    def testEEEAliceAndBob(self):  # GUARANTEED TO WORK. LAST MODIFIED 2025/03/23 @ 18:42
        alice_corridor = self.alice_harem.open(bobs_PK)
        bob_corridor = self.bob_harem.open(alices_PK)
        sleep(2)
        alice_corridor.close()
        bob_corridor.close()
        self.assertTrue(alice_corridor.is_closed)
        self.assertTrue(bob_corridor.is_closed)

    def testFFFAliceAndBob(self):  # GUARANTEED TO WORK. LAST MODIFIED 2025/03/23 @ 18:42
        alice_corridor = self.alice_harem.open(bobs_PK)
        bob_corridor = self.bob_harem.open(alices_PK)
        sleep(2)
        alice_corridor.close()
        bob_corridor.close()
        self.assertTrue(alice_corridor.is_closed)
        self.assertTrue(bob_corridor.is_closed)

    def testZZZAliceOnly(self):  # GUARANTEED TO WORK. LAST MODIFIED 2025/03/23 @ 18:42
        alice_corridor = self.alice_harem.open(bobs_PK)
        bob_corridor = self.bob_harem.open(alices_PK)
        sleep(5)
        alice_corridor.close()
        self.assertTrue(alice_corridor.is_closed)
        self.assertTrue(bob_corridor.is_closed)

    def testBANJAX123(self):  # GUARANTEED TO WORK. LAST MODIFIED 2025/03/23 @ 16:20
        alice_corridor = self.alice_harem.open(bobs_PK)
        out_data = b"HELLO THERE. HOW ARE YOU?"
        alice_corridor.put(out_data)
        alice_corridor.close()
        self.assertTrue(alice_corridor.is_closed)
        sleep(5)
        self.assertEqual(len(self.alice_harem.corridors), 0)
        self.assertEqual(len(self.bob_harem.corridors), 0)

    def testSimplest7sPause(self):  # GUARANTEED TO WORK. LAST MODIFIED 2025/03/23 @ 21:53
        alice_corridor = self.alice_harem.open(bobs_PK)
        bob_corridor = self.bob_harem.open(alices_PK)
        sleep(7)
        alice_corridor.close()
        bob_corridor.close()
        self.assertTrue(alice_corridor.is_closed)
        self.assertTrue(bob_corridor.is_closed)
        self.assertEqual([], self.alice_harem.corridors)
        self.assertEqual([], self.bob_harem.corridors)

    def testAliceAndBobSimultaneousOpenAndClose(self):
#        for _ in range(0,10):
        al_thread = Thread(target=self.alice_harem.open, args=[bobs_PK], daemon=True)
        bb_thread = Thread(target=self.bob_harem.open, args=[alices_PK], daemon=True)
        al_thread.start()
        bb_thread.start()
        while self.alice_harem.corridors == [] and self.bob_harem.corridors == []:
            print("Waiting for corridors to open (simultaneously)")
            sleep(5)
        print("Joining the threads")
        al_thread.join()
        bb_thread.join()
        self.assertEqual(len(self.alice_harem.corridors), 1)
        self.assertEqual(len(self.bob_harem.corridors), 1)
        alice_corridor = self.alice_harem.corridors[0]
        bob_corridor = self.bob_harem.corridors[0]
        self.assertEqual(alice_corridor.uid, bob_corridor.uid)
        self.assertNotEqual(alice_corridor.our_uid, bob_corridor.our_uid)
        self.assertNotEqual(alice_corridor.his_uid, bob_corridor.his_uid)
        self.assertEqual(alice_corridor.his_uid, bob_corridor.our_uid)
        self.assertEqual(alice_corridor.our_uid, bob_corridor.his_uid)
        self.assertFalse(alice_corridor.is_closed)
        self.assertFalse(bob_corridor.is_closed)

        bob_corridor.close()
        sleep(5)
        self.assertTrue(bob_corridor.is_closed)
        self.assertTrue(alice_corridor.is_closed, "Closing Bob should also close Alice")
        self.assertEqual([], self.alice_harem.corridors)
        self.assertEqual([], self.bob_harem.corridors)

    def testSimplestOpenAndClosePartTwo(self):
        for pausdur in (10, 5, 3, 2, 1, .1):
            print("Sleeping for 10 seconds, as a precaution..... (cough) Race conditions (cough)")
            sleep(10)
            alice_corridor = self.alice_harem.open(bobs_PK)
            if len(self.bob_harem.corridors) == 0:
                sleep(10)
                self.assertEqual(self.bob_harem.corridors[0].destination_pk, alices_PK)
                self.assertEqual(self.bob_harem.corridors[0].uid, alice_corridor.uid)
            alice_corridor.close(timeout=300)
            self.assertEqual(self.alice_harem.corridors, [])
            self.assertEqual([], self.alice_harem.corridors)
            self.assertEqual([], self.alice_harem.corridors)
            sleep(pausdur)
            self.assertTrue(alice_corridor.is_closed)
            sleep(5 if [] != self.alice_harem.corridors else 0)
            sleep(5 if [] != self.bob_harem.corridors else 0)
            self.assertEqual([], self.bob_harem.corridors)
            self.assertEqual([], self.bob_harem.corridors)
            sleep(2)

    def testSimplest0sPause(self):  # PASESES! DO NOT CHANGE. LAST MODIFIED 2025/03/23 @ 22:23
        alice_corridor = self.alice_harem.open(bobs_PK)
        bob_corridor = self.bob_harem.open(alices_PK)
        self.assertFalse(alice_corridor.is_closed)
        self.assertFalse(bob_corridor.is_closed)
        alice_corridor.close(timeout=9999)
        bob_corridor.close(timeout=9999)
        self.assertTrue(alice_corridor.is_closed)
        self.assertTrue(bob_corridor.is_closed)
        sleep(5 if [] != self.alice_harem.corridors else 0)
        sleep(5 if [] != self.bob_harem.corridors else 0)
        self.assertEqual(len(self.alice_harem.corridors), 0)
        self.assertEqual(len(self.bob_harem.corridors), 0)

    def testSimplest1sPause(self):  # PASESES! DO NOT CHANGE. LAST MODIFIED 2025/03/23 @ 22:23
        print("THIS ONE TENDS TO BREAK. Why?")
        alice_corridor = self.alice_harem.open(bobs_PK)
        bob_corridor = self.bob_harem.open(alices_PK)
        sleep(1)
        print("OK so far.")
        alice_corridor.close()
        bob_corridor.close()
        print("Well, we JUUUUUST opened a corridor (the same one twice) and then we closed them both again.")
        self.assertTrue(alice_corridor.is_closed)
        self.assertTrue(bob_corridor.is_closed)
        self.assertEqual([], self.alice_harem.corridors)
        self.assertEqual([], self.bob_harem.corridors)

    def testSimplest5sPause(self):  # PASESES! DO NOT CHANGE. LAST MODIFIED 2025/03/23 @ 22:23
        alice_corridor = self.alice_harem.open(bobs_PK)
        bob_corridor = self.bob_harem.open(alices_PK)
        self.assertFalse(alice_corridor.is_closed)
        self.assertFalse(bob_corridor.is_closed)
        sleep(5)
        alice_corridor.close()
        bob_corridor.close()
        self.assertTrue(alice_corridor.is_closed)
        self.assertTrue(bob_corridor.is_closed)
        sleep(5 if [] != self.alice_harem.corridors else 0)
        sleep(5 if [] != self.bob_harem.corridors else 0)
        self.assertEqual(len(self.alice_harem.corridors), 0)
        self.assertEqual(len(self.bob_harem.corridors), 0)


# TestcorridorsOpeningAndClosing WORKS 100% as of 2025/03/23 @ 22:05
class TestcorridorsOpeningAndClosing(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.alice_harem, cls.bob_harem = setUpForNServers(1)  # opens alice and bob harems

    @classmethod
    def tearDownClass(cls):
        cls.alice_harem.quit()
        cls.bob_harem.quit()

    def setUp(self):
        self.assertTrue(self.alice_harem.connected_and_joined, "Alice should have connected and joined by now.")
        self.assertTrue(self.bob_harem.connected_and_joined, "Bob should have connected and joined by now.")
        sleep(20 if len(self.alice_harem.true_homies) < 1 or len(self.bob_harem.true_homies) < 1 else 0)
        self.assertGreaterEqual(len(self.alice_harem.homies_pubkeys), 1, "By now, Alice's harem of bots should have gathered at least one public key from another potential homie.")
        self.assertGreaterEqual(len(self.bob_harem.homies_pubkeys), 1, "By now, Bob's harem of bots should have gathered at least one public key from another potential homie.")
        self.assertGreaterEqual(len(self.alice_harem.true_homies), 1, "By now, Alice should have found at least one true homie: Bob.")
        self.assertGreaterEqual(len(self.bob_harem.true_homies), 1, "By now, Bob should have found at least one true homie: Alice.")
        self.assertEqual(self.alice_harem.corridors, [], "Previous test left Alice with open corridor(s)")
        self.assertEqual(self.bob_harem.corridors, [], "Previous test left Bob with open corridor(s)")
        print("╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍")

    def tearDown(self):
        print("====================================================================================================")
        self.assertTrue(self.alice_harem.connected_and_joined, "Alice should have connected and joined by now.")
        self.assertTrue(self.bob_harem.connected_and_joined, "Bob should have connected and joined by now.")
        self.assertGreaterEqual(len(self.alice_harem.homies_pubkeys), 1, "By now, Alice's harem of bots should have gathered at least one public key from another potential homie.")
        self.assertGreaterEqual(len(self.bob_harem.homies_pubkeys), 1, "By now, Bob's harem of bots should have gathered at least one public key from another potential homie.")
        self.assertGreaterEqual(len(self.alice_harem.true_homies), 1, "By now, Alice should have found at least one true homie: Bob.")
        self.assertGreaterEqual(len(self.bob_harem.true_homies), 1, "By now, Bob should have found at least one true homie: Alice.")
        self.assertEqual(self.alice_harem.corridors, [], "Alice should have closed all corridors by now")
        self.assertEqual(self.bob_harem.corridors, [], "Bob should have closed all corridors by now")

    def testASequentialAAAOpenAndClose(self):  # GUARANTEED TO WORK. LAST MODIFIED 2025/03/23 @ 15:35
        alice_corridor = self.alice_harem.open(bobs_PK)
        self.assertFalse(alice_corridor.is_closed)
        self.assertEqual([alice_corridor], [r for r in self.alice_harem.corridors if r.uid == alice_corridor.uid])
        self.assertEqual(alice_corridor.destination_pk, bobs_PK)
        alice_corridor.close()

    def testASequentialZZZOpenAndClose(self):  # GUARANTEED TO WORK. LAST MODIFIED 2025/03/23 @ 15:35
        alice_corridor = self.alice_harem.open(bobs_PK)
        self.assertFalse(alice_corridor.is_closed)
        self.assertEqual([alice_corridor], [r for r in self.alice_harem.corridors if r.uid == alice_corridor.uid])
        self.assertEqual(alice_corridor.destination_pk, bobs_PK)
        alice_corridor.close()

    def testOpenOnlyOnecorridor(self):  # GUARANTEED TO WORK. LAST MODIFIED 2025/03/23 @ 15:35
        self.assertEqual(len(self.alice_harem.corridors), 0)
        self.assertEqual(len(self.bob_harem.corridors), 0)
        alice_corridor = self.alice_harem.open(bobs_PK)
        alice_corridor.close()
        self.assertTrue(alice_corridor.is_closed)
        self.assertEqual(len(self.alice_harem.corridors), 0)
        self.assertEqual(len(self.bob_harem.corridors), 0)
        bob_corridor = self.bob_harem.open(alices_PK)
        self.assertFalse(bob_corridor.is_closed)
        self.assertEqual([bob_corridor], [r for r in self.bob_harem.corridors if r.uid in (alice_corridor.uid, bob_corridor.uid)])
        self.assertEqual(bob_corridor.destination_pk, alices_PK)
        sleep(10)
        alice_corridor.close()
        self.assertTrue(alice_corridor.is_closed)
        sleep(5)
        self.assertTrue(bob_corridor.is_closed, "Closing alice should also close bob")
        self.assertEqual([], self.bob_harem.corridors)
        self.assertEqual([], self.alice_harem.corridors)

    def testSimplestVARIETYPause(self):  # GUARANTEED TO WORK. LAST MODIFIED 2025/03/23 @ 20:00
        for pauselen in (10, 8, 7, 6, 5, 4, 3, 2, 1):
            print("TRYING W/ PAUSELEN=%d" % pauselen)
            self.assertEqual([], self.alice_harem.corridors, "testSimplestVARIETYPause: pauselen=%d; alice harem has corridors, left over from the previous iteration" % pauselen)
            self.assertEqual([], self.bob_harem.corridors, "testSimplestVARIETYPause: pauselen=%d; bob harem has corridors, left over from the previous iteration" % pauselen)
            alice_corridor = self.alice_harem.open(bobs_PK)
            bob_corridor = self.bob_harem.open(alices_PK)
            sleep(pauselen)
            alice_corridor.close()
            bob_corridor.close()
            self.assertTrue(alice_corridor.is_closed, "testSimplestVARIETYPause: pauselen=%d; failed to close alice harem's corridor" % pauselen)
            self.assertTrue(bob_corridor.is_closed, "testSimplestVARIETYPause: pauselen=%d; failed to close alice harem's corridor" % pauselen)
            self.assertEqual([], self.alice_harem.corridors, "testSimplestVARIETYPause: pauselen=%d; alice harem has corridors, despite my successful attempt to close the only corridor there was" % pauselen)
            self.assertEqual([], self.bob_harem.corridors, "testSimplestVARIETYPause: pauselen=%d; bob harem has corridors, despite my successful attempt to close the only corridor there was" % pauselen)

    def testSimplest15sPause(self):  # GUARANTEED TO WORK. LAST MODIFIED 2025/03/23 @ 19:23
        alice_corridor = self.alice_harem.open(bobs_PK)
        bob_corridor = self.bob_harem.open(alices_PK)
        self.assertFalse(alice_corridor.is_closed)
        self.assertFalse(bob_corridor.is_closed)
        self.assertEqual(bob_corridor.uid, alice_corridor.uid)
        self.assertEqual(bob_corridor.uid, self.alice_harem.corridors[0].uid)
        self.assertEqual(alice_corridor.uid, self.bob_harem.corridors[0].uid)
        sleep(15)
#        bob_corridor.close()
        alice_corridor.close()
        self.assertTrue(alice_corridor.is_closed)
        self.assertTrue(bob_corridor.is_closed)
        sleep(5 if [] != self.alice_harem.corridors else 0)
        sleep(5 if [] != self.bob_harem.corridors else 0)
        self.assertEqual(len(self.alice_harem.corridors), 0)
        self.assertEqual(len(self.bob_harem.corridors), 0)

    def testBANJAX567(self):  # GUARANTEED TO WORK. LAST MODIFIED 2025/03/23 @ 16:44
        """Open corridor. Send message. Close corridor. THEN, on recipient, try to read incoming data."""
        alice_corridor = self.alice_harem.open(bobs_PK)
        out_data = b"WORD UP. WHAT'S THE HAPS?"
        alice_corridor.put(out_data)
        bob_corridor = self.bob_harem.corridors[0]
        alice_corridor.close()
        self.assertTrue(alice_corridor.is_closed)
        self.assertRaises(RookeryCorridorAlreadyClosedError, alice_corridor.put, "THIS SHOULD NOT WORK")
        self.assertEqual(self.alice_harem.corridors, [])
        self.assertEqual(self.bob_harem.corridors, [])
        del alice_corridor
        self.assertRaises(RookeryCorridorAlreadyClosedError, bob_corridor.get_nowait)
        bob_corridor.close()
        self.assertTrue(bob_corridor.is_closed)
        self.assertRaises(RookeryCorridorAlreadyClosedError, bob_corridor.put, "THIS SHOULD NOT WORK")
        sleep(5)
        self.assertEqual(len(self.alice_harem.corridors), 0)
        self.assertEqual(len(self.bob_harem.corridors), 0)

    def testSimplestOpenAndClosePartOne(self):  # GUARANTEED TO WORK. LAST MODIFIED 2025/03/23 @ 15:35
        self.assertEqual(self.alice_harem.corridors, [])
        self.assertEqual(self.bob_harem.corridors, [])
        alice_corridor = self.alice_harem.open(bobs_PK)
        sleep(10)
        self.assertFalse(alice_corridor.is_closed)
        self.assertEqual([alice_corridor], [r for r in self.alice_harem.corridors if r.uid == alice_corridor.uid])
        self.assertEqual(alice_corridor.destination_pk, bobs_PK)
        self.assertEqual(self.bob_harem.corridors[0].destination_pk, alices_PK)
        self.assertEqual(self.bob_harem.corridors[0].uid, alice_corridor.uid)
        sleep(10)
        alice_corridor.close(timeout=300)
        self.assertEqual(self.alice_harem.corridors, [])
        self.assertEqual(self.bob_harem.corridors, [])
        self.assertTrue(alice_corridor.is_closed)
        self.assertEqual([], self.alice_harem.corridors)
        self.assertEqual([], self.bob_harem.corridors)
        sleep(10)
        self.assertEqual([], self.alice_harem.corridors)
        self.assertEqual([], self.bob_harem.corridors)


class TestThisOneFingTurd(unittest.TestCase):

    def this_test_shortcut(self, sleepdur):
        print("vvv BEGINNING TEST w/ %f SLEEPDUR vvv" % sleepdur)
        alice_harem, bob_harem = setUpForNServers(1)
        alice_corridor = alice_harem.open(bobs_PK, timeout=60)
        self.assertTrue(bob_harem.corridors != [] and bob_harem.corridors[0].uid == alice_corridor.uid and alice_corridor.uid == bob_harem.corridors[0].uid and len(bob_harem.corridors) == 1)
        bob_corridor = bob_harem.open(alices_PK, timeout=300)
        sleep(sleepdur)
        self.assertTrue(bob_corridor.uid == alice_corridor.uid == alice_harem.corridors[0].uid == bob_harem.corridors[0].uid)
        alice_corridor.close(timeout=300)
        self.assertTrue(alice_corridor.is_closed is True and bob_corridor.is_closed is True and alice_harem.corridors + bob_harem.corridors == [])
        [ h.quit() for h in (alice_harem, bob_harem)]  # pylint: disable=expression-not-assigned
        print("^^^ ENDING TEST w/ %f SLEEPDUR ^^^" % sleepdur)
        print("====================================")

    def testAAThisOneFingTurdFIVE(self):
        self.this_test_shortcut(5)
        self.this_test_shortcut(0)

    def testBBThisOneFingTurdZeroish(self):
        alice_harem, bob_harem = setUpForNServers(1)

        alice_corridor, bob_corridor = (alice_harem.open(bobs_PK), bob_harem.open(alices_PK))
        sleep(5); self.assertTrue(bob_corridor.uid == alice_corridor.uid == alice_harem.corridors[0].uid == bob_harem.corridors[0].uid)
        alice_corridor.close(); self.assertTrue(bob_corridor.is_closed is True and alice_corridor.is_closed is True and alice_harem.corridors + bob_harem.corridors == [])
        alice_corridor, bob_corridor = (alice_harem.open(bobs_PK), bob_harem.open(alices_PK))
        sleep(4); self.assertTrue(bob_corridor.uid == alice_corridor.uid == alice_harem.corridors[0].uid == bob_harem.corridors[0].uid)
        alice_corridor.close(); self.assertTrue(bob_corridor.is_closed is True and alice_corridor.is_closed is True and alice_harem.corridors + bob_harem.corridors == [])

        alice_corridor, bob_corridor = (alice_harem.open(bobs_PK), bob_harem.open(alices_PK))
        sleep(3); self.assertTrue(bob_corridor.uid == alice_corridor.uid == alice_harem.corridors[0].uid == bob_harem.corridors[0].uid)
        alice_corridor.close(); self.assertTrue(bob_corridor.is_closed is True and alice_corridor.is_closed is True and alice_harem.corridors + bob_harem.corridors == [])

        alice_corridor, bob_corridor = (alice_harem.open(bobs_PK), bob_harem.open(alices_PK))
        sleep(2); self.assertTrue(bob_corridor.uid == alice_corridor.uid == alice_harem.corridors[0].uid == bob_harem.corridors[0].uid)
        alice_corridor.close(); self.assertTrue(bob_corridor.is_closed is True and alice_corridor.is_closed is True and alice_harem.corridors + bob_harem.corridors == [])

        alice_corridor, bob_corridor = (alice_harem.open(bobs_PK), bob_harem.open(alices_PK))
        sleep(1); self.assertTrue(bob_corridor.uid == alice_corridor.uid == alice_harem.corridors[0].uid == bob_harem.corridors[0].uid)
        alice_corridor.close(); self.assertTrue(bob_corridor.is_closed is True and alice_corridor.is_closed is True and alice_harem.corridors + bob_harem.corridors == [])

        alice_corridor, bob_corridor = (alice_harem.open(bobs_PK), bob_harem.open(alices_PK))
        sleep(0); self.assertTrue(bob_corridor.uid == alice_corridor.uid == alice_harem.corridors[0].uid == bob_harem.corridors[0].uid)
        alice_corridor.close(); self.assertTrue(bob_corridor.is_closed is True and alice_corridor.is_closed is True and alice_harem.corridors + bob_harem.corridors == [])

        [ h.quit() for h in (alice_harem, bob_harem)]  # pylint: disable=expression-not-assigned

    def testRRThisOneFingTurdZERO(self):
        alice_harem, bob_harem = setUpForNServers(1)
        alice_corridor = alice_harem.open(bobs_PK, timeout=60)
        self.assertNotEqual(bob_harem.corridors, [])
        self.assertEqual(bob_harem.corridors[0].uid, alice_corridor.uid)
        self.assertTrue(alice_corridor.uid == bob_harem.corridors[0].uid)
        self.assertEqual(len(bob_harem.corridors), 1)
        bob_corridor = bob_harem.open(alices_PK, timeout=300)  # This should REUSE a corridor that ALICE caused Bob to open.
        self.assertTrue(bob_corridor.uid == \
                        alice_corridor.uid == \
                        alice_harem.corridors[0].uid == \
                        bob_harem.corridors[0].uid)
        alice_corridor.close(timeout=300)
        self.assertTrue(alice_corridor.is_closed and bob_corridor.is_closed)
        self.assertEqual(alice_harem.corridors + bob_harem.corridors, [])
        alice_harem.quit()
        bob_harem.quit()


class TestTurnDownForWhatDJSnake(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.alice_harem, cls.bob_harem = setUpForNServers(1)  # opens alice and bob harems

    @classmethod
    def tearDownClass(cls):
        cls.alice_harem.quit()
        cls.bob_harem.quit()

    def setUp(self):
        self.assertTrue(self.alice_harem.connected_and_joined, "Alice should have connected and joined by now.")
        self.assertTrue(self.bob_harem.connected_and_joined, "Bob should have connected and joined by now.")
        sleep(20 if len(self.alice_harem.true_homies) < 1 or len(self.bob_harem.true_homies) < 1 else 0)
        self.assertGreaterEqual(len(self.alice_harem.homies_pubkeys), 1, "By now, Alice's harem of bots should have gathered at least one public key from another potential homie.")
        self.assertGreaterEqual(len(self.bob_harem.homies_pubkeys), 1, "By now, Bob's harem of bots should have gathered at least one public key from another potential homie.")
        self.assertGreaterEqual(len(self.alice_harem.true_homies), 1, "By now, Alice should have found at least one true homie: Bob.")
        self.assertGreaterEqual(len(self.bob_harem.true_homies), 1, "By now, Bob should have found at least one true homie: Alice.")
        self.assertEqual(self.alice_harem.corridors, [], "Previous test left Alice with open corridor(s)")
        self.assertEqual(self.bob_harem.corridors, [], "Previous test left Bob with open corridor(s)")
        print("╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍")

    def tearDown(self):
        for c in self.alice_harem.corridors:
            c.close()
        for c in self.bob_harem.corridors:
            c.close()
        print("====================================================================================================")
        self.assertEqual(self.alice_harem.corridors, [], "Alice should have closed all corridors by now")
        self.assertEqual(self.bob_harem.corridors, [], "Bob should have closed all corridors by now")

    def run_test_SOaCn_slim(self, t):
        sleep(10)
        alice_corridor = self.alice_harem.open(bobs_PK, timeout=60)
        sleep(10)
        self.assertNotEqual(self.bob_harem.corridors, [])
        self.assertTrue(self.bob_harem.corridors[0].uid, alice_corridor.uid)
        self.assertTrue(self.alice_harem.corridors[0].uid, alice_corridor.uid)
        self.assertEqual(len(self.bob_harem.corridors), 1)
        bob_corridor = self.bob_harem.open(alices_PK, timeout=300)  # This should REUSE a corridor that ALICE caused Bob to open.
        sleep(t)
        self.assertTrue(bob_corridor.uid == \
                        alice_corridor.uid == \
                        self.alice_harem.corridors[0].uid == \
                        self.bob_harem.corridors[0].uid)
        alice_corridor.close(timeout=300)
        self.assertTrue(alice_corridor.is_closed and bob_corridor.is_closed)
        self.assertEqual(self.alice_harem.corridors + self.bob_harem.corridors, [])

    def run_test_SOaCn_beefier(self, t):
        sleep(10)
        self.assertEqual(self.alice_harem.corridors, [])
        self.assertEqual(self.bob_harem.corridors, [])
        sleep(10)
        alice_corridor = self.alice_harem.open(bobs_PK, timeout=60)
        self.assertFalse(alice_corridor.is_closed)
        self.assertEqual([alice_corridor], self.alice_harem.corridors)
        self.assertEqual(alice_corridor.destination_pk, bobs_PK)
        try:
            self.assertEqual(self.bob_harem.corridors[0].uid, alice_corridor.uid)
        except IndexError:
            sleep(5)
            self.assertNotEqual(self.bob_harem.corridors, [])
        bob_corridor = self.bob_harem.open(alices_PK, timeout=300)  # This should REUSE a corridor that ALICE caused Bob to open.
        sleep(t)
        self.assertEqual([bob_corridor], self.bob_harem.corridors)
        self.assertEqual(bob_corridor.uid, alice_corridor.uid)
        self.assertEqual(len(self.alice_harem.corridors), 1)
        self.assertEqual(len(self.bob_harem.corridors), 1)
        alice_corridor.close(timeout=300)
        self.assertTrue(alice_corridor.is_closed)
        self.assertTrue(bob_corridor.is_closed)
        self.assertEqual(self.alice_harem.corridors, [])
        self.assertEqual(self.bob_harem.corridors, [])

    def testSimplestAA(self):  # QQQ Does this one pass? Is it causing problems?
        self.run_test_SOaCn_slim(5)
        self.run_test_SOaCn_beefier(5)

    def testSimplestBB(self):  # QQQ Does this one pass? Is it causing problems?
        self.run_test_SOaCn_slim(4)
        self.run_test_SOaCn_beefier(4)

    def testSimplestCC(self):  # QQQ Does this one pass? Is it causing problems?
        self.run_test_SOaCn_slim(3)
        self.run_test_SOaCn_beefier(3)

    def testSimplestDD(self):  # QQQ Does this one pass? Is it causing problems?
        self.run_test_SOaCn_slim(2)
        self.run_test_SOaCn_beefier(2)

    def testSimplestEE(self):  # QQQ Does this one pass? Is it causing problems?
        self.run_test_SOaCn_slim(1)
        self.run_test_SOaCn_beefier(1)
        self.run_test_SOaCn_slim(1)
        self.run_test_SOaCn_beefier(1)

    def testSimplestFF(self):  # QQQ Does this one pass? Is it causing problems?
        self.run_test_SOaCn_slim(0)

    def testSimplestQQ(self):  # QQQ Does this one pass? Is it causing problems?
        self.run_test_SOaCn_slim(0)
        self.run_test_SOaCn_beefier(3)

    def testSimplestRR(self):  # QQQ Does this one pass? Is it causing problems?
        self.run_test_SOaCn_slim(0)
        self.run_test_SOaCn_beefier(0)

    def testSimplestSS(self):  # QQQ Does this one pass? Is it causing problems?
        self.run_test_SOaCn_slim(3)
        self.run_test_SOaCn_beefier(3)

    def testSimplestZZ(self):  # QQQ Does this one pass? Is it causing problems?
        self.run_test_SOaCn_slim(5)
        self.run_test_SOaCn_beefier(5)

    def testKeepCrashingUTIIUDWhwatever(self):
        alice_corridor = self.alice_harem.open(bobs_PK)
        sleep(5)
        out_data = b"HELLO THERE. HOW ARE YOU?"
        alice_corridor.put(out_data)
        sleep(5)
        alice_corridor.close()
        self.assertRaises(RookeryCorridorAlreadyClosedError, alice_corridor.put, b"THIS SHOULD NOT WORK")
        sleep(10)
        bob_corridor = self.bob_harem.open(alices_PK)
        self.assertRaises(Empty, bob_corridor.get, timeout=10)
        bob_corridor.close()
        self.assertTrue(alice_corridor.is_closed)
        self.assertTrue(bob_corridor.is_closed)
        self.assertRaises(RookeryCorridorAlreadyClosedError, bob_corridor.put, b"THIS SHOULD NOT WORK")
        self.assertEqual(len(self.alice_harem.corridors), 0)
        self.assertEqual(len(self.bob_harem.corridors), 0)

    def testFasterKeepCrashingKillKillKill(self):
        self.assertEqual(len(self.alice_harem.corridors), 0)
        self.assertEqual(len(self.bob_harem.corridors), 0)
        alice_corridor = self.alice_harem.open(bobs_PK)
        out_data = b"HELLO THERE. HOW ARE YOU?"
        alice_corridor.put(out_data)
        alice_corridor.close()
        self.assertRaises(RookeryCorridorAlreadyClosedError, alice_corridor.put, b"THIS SHOULD NOT WORK")
        bob_corridor = self.bob_harem.open(alices_PK)
        try:
            bob_corridor.get(timeout=5)
        except Empty:
            pass
        bob_corridor.close()
        self.assertTrue(alice_corridor.is_closed)
        self.assertTrue(bob_corridor.is_closed)
        self.assertRaises(RookeryCorridorAlreadyClosedError, bob_corridor.put, b"THIS SHOULD NOT WORK")
        self.assertEqual(len(self.alice_harem.corridors), 0)
        self.assertEqual(len(self.bob_harem.corridors), 0)
        self.assertEqual(len(self.alice_harem.corridors), 0)
        self.assertEqual(len(self.bob_harem.corridors), 0)

    def testOpenOnlyOneCrdrAndSayHelloThenOpenOtherCrdr(self):
        alice_corridor = self.alice_harem.open(bobs_PK)
        out_data = b"HELLO THERE. HOW ARE Y'All?"
        alice_corridor.put(out_data)
        alice_corridor.close()
        self.assertRaises(RookeryCorridorAlreadyClosedError, alice_corridor.put, b"THIS SHOULD NOT WORK")
        bob_corridor = self.bob_harem.open(alices_PK)
        self.assertRaises(Empty, bob_corridor.get, timeout=10)
        bob_corridor.close()
        self.assertTrue(alice_corridor.is_closed)
        self.assertTrue(bob_corridor.is_closed)
        self.assertRaises(RookeryCorridorAlreadyClosedError, bob_corridor.put, b"THIS SHOULD NOT WORK")
        sleep(5)
        self.assertEqual(len(self.alice_harem.corridors), 0)
        self.assertEqual(len(self.bob_harem.corridors), 0)


class TestcorridorsZero(unittest.TestCase):

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

    def run_test_with_N_servers_and_dupes(self, noof_servers, dupes, framesize_lst, timeout=600):
        for frame_size in framesize_lst:
            self.__run_super_duper_simple_test(noof_servers=noof_servers, dupes=dupes,
                                               frame_size=frame_size, datalen_lst=(
                           frame_size // 2, frame_size - 1, frame_size, frame_size + 1,
                           frame_size * 2 - 1, frame_size * 2, frame_size * 2 + 1,
                           frame_size * 3 - 1, frame_size * 3, frame_size * 3 + 1,
                           frame_size * 9 - 1, frame_size * 9, frame_size * 9 + 1), timeout=timeout)

    def testBasicOne(self):
        alice_harem, bob_harem = setUpForNServers(noof_servers=1)
        alice_corridor = alice_harem.open(bobs_PK)
        bob_corridor = bob_harem.open(alices_PK)
        sleep(5)
        all_data = generate_random_alphanumeric_string(500).encode()
        alice_corridor.put(all_data)
        sleep(5)
        rxd_data = bob_corridor.get(timeout=1200)
        if all_data != rxd_data:
            self.assertEqual(all_data, rxd_data)
        self.assertRaises(Empty, bob_corridor.get_nowait)
        alice_corridor.close()
        bob_corridor.close()
        alice_harem.quit()
        bob_harem.quit()

    def testSDSOwithTimeout10(self):
        self.assertRaises(RookeryCorridorTimeoutError, self.__run_super_duper_simple_test, 1, 0, 32, (8, 16, 31, 32, 256, 512), 10)  # 10 is timeout value

    def testSlightlyOddValues(self):
        self.__run_super_duper_simple_test(noof_servers=5, dupes=5, frame_size=256, datalen_lst=(0, 0, 1, 1, 0, 1))

    def testSDSOwithTimeout180(self):
        self.__run_super_duper_simple_test(noof_servers=5, dupes=1, frame_size=32, datalen_lst=(8, 16, 31, 32, 33), timeout=180)

    def testSDSOwithTimeoutDefault(self):
        self.__run_super_duper_simple_test(noof_servers=5, dupes=1, frame_size=32, datalen_lst=(8, 16, 31, 32, 33))

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
        self.run_test_with_N_servers_and_dupes(noof_servers=8, dupes=0, framesize_lst=(128, 256), timeout=120)

    # def testSuperDuperSimpleVarietyAAA(self):
    #     self.run_test_with_N_servers_and_dupes(noof_servers=1, dupes=4, framesize_lst=(64, 128, 256), timeout=120)

    # def testSuperDuperSimpleVarietyBBB(self):
    #     self.run_test_with_N_servers_and_dupes(noof_servers=2, dupes=3, framesize_lst=(64, 128, 256), timeout=120)

    # def testSuperDuperSimpleVarietyCCC(self):
    #     self.run_test_with_N_servers_and_dupes(noof_servers=3, dupes=2, framesize_lst=(64, 128, 256), timeout=120)

    def testSuperDuperSimpleVarietyDDD(self):
        self.run_test_with_N_servers_and_dupes(noof_servers=4, dupes=1, framesize_lst=(64, 128, 256), timeout=120)

    # def testSuperDuperSimpleVarietyEEE(self):
    #     self.run_test_with_N_servers_and_dupes(noof_servers=5, dupes=0, framesize_lst=(64, 128, 256), timeout=120)


class TestcorridorsOne(unittest.TestCase):

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
            if alice_corridor.is_closed is True:
                print("WTF? Why is this CLOSED? Okay, fine. I'll count to 5 and try again.")
                sleep(5)
            self.assertEqual(alice_corridor.is_closed, False)
            alice_corrid_2 = alice_harem.open(bobs_PK)
            self.assertEqual(alice_corridor.is_closed, False)
            self.assertEqual(alice_corrid_2.is_closed, False)
            sleep(2)
            bob_corridor = bob_harem.open(alices_PK)
            self.assertEqual(bob_corridor.is_closed, False)
            bob_corrid_2 = bob_harem.open(alices_PK)
            self.assertEqual(bob_corridor.is_closed, False)
            self.assertEqual(bob_corrid_2.is_closed, False)
            assert(bob_corridor == bob_corrid_2)
            assert(alice_corridor == alice_corrid_2)
            assert(bob_corridor != alice_corridor)
            sleep(2)
            if bob_corridor.is_closed:
                self.assertEqual(bob_corridor.is_closed, False)
            bob_corridor.close()
            self.assertTrue(bob_corridor.is_closed)
            self.assertTrue(bob_corrid_2.is_closed)
            bob_corrid_2.close()
            alice_corridor.close()
            self.assertTrue(alice_corridor.is_closed)
            alice_corrid_2.close()
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
            self.assertEqual(bob_corridor.get(timeout=9999999), b"MARCO?")
            sleep(2)
            bob_corridor.put(b"POLO!")
            sleep(2)
            self.assertEqual(alice_corridor.get(timeout=30), b"POLO!")
            sleep(2)
            self.assertEqual(alice_corridor.irc_servers, list(alice_harem.bots.keys()))
            self.assertEqual(bob_corridor.irc_servers, list(bob_harem.bots.keys()))
            alice_corridor.close()
            bob_corridor.close()
            alice_harem.quit()
            bob_harem.quit()

    def testMarcoPoloWithoutPauses(self):
        for noof_servers in range(1, 5):
            alice_harem, bob_harem = setUpForNServers(noof_servers)
            self.assertEqual(alice_harem.corridors, [])
            self.assertEqual(bob_harem.corridors, [])
            alice_corridor = alice_harem.open(bobs_PK)
            bob_corridor = bob_harem.open(alices_PK)
            sleep(30)
            alice_corridor.put(b"MARCO?")
            self.assertEqual(bob_corridor.get(timeout=30), b"MARCO?")
            bob_corridor.put(b"POLO!")
            self.assertEqual(alice_corridor.get(timeout=30), b"POLO!")
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
            received_data = bob_corridor.get(timeout=30)
            self.assertEqual(received_data, BORN_TO_DIE_IN_BYTES)
            bob_corridor.put(CICERO.encode())
            sleep(20)
            received_data = alice_corridor.get(timeout=30)
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
            sleep(10)
            alice_corridor = alice_harem.open(bobs_PK)
            alice_corridor.put(BORN_TO_DIE_IN_BYTES)
            sleep(20)
            bob_corridor = bob_harem.open(alices_PK)
            received_data = bob_corridor.get(timeout=300)
            self.assertEqual(received_data, BORN_TO_DIE_IN_BYTES)
            bob_corridor.put(CICERO.encode())
            sleep(20)
            received_data = alice_corridor.get(timeout=300)
            self.assertEqual(received_data, CICERO.encode())
            self.assertEqual(alice_corridor.irc_servers, list(alice_harem.bots.keys()))
            self.assertEqual(bob_corridor.irc_servers, list(bob_harem.bots.keys()))
            alice_corridor.close()
            bob_corridor.close()
            alice_harem.quit()
            bob_harem.quit()


class TestcorridorsBigFiles(unittest.TestCase):

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
        received_data = bob_corridor.get(timeout=600)
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

    # def testCushionStl(self):
    #     self.runABigBadThoroughTestOnThisFile("/Users/mchobbit/Downloads/cushion.stl")

    # def testPrinterFilesCfgTarGz(self):
    #     self.runABigBadThoroughTestOnThisFile("/Users/mchobbit/Downloads/t1-printer-files.cfg.tar.gz")

    # def testSideCushnStl(self):
    #     self.runABigBadThoroughTestOnThisFile("/Users/mchobbit/Downloads/side_cushion.stl")

    # def testPiHolderStl(self):
    #     self.runABigBadThoroughTestOnThisFile("/Users/mchobbit/Downloads/pi_holder.stl")


class TestFailToCloseCorridor(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        pass

    @classmethod
    def tearDownClass(cls):
        pass

    def testThisOneFailToClose(self):
        alice_harem, bob_harem = setUpForNServers(1)
        alice_corridor = alice_harem.open(bobs_PK)
        self.assertTrue(alice_corridor.uid == alice_harem.corridors[0].uid == bob_harem.corridors[0].uid)
        [ h.quit() for h in (alice_harem, bob_harem)]  # pylint: disable=expression-not-assigned


class TestStreamingAbility(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        pass

    @classmethod
    def tearDownClass(cls):
        pass

    def testThisOneIsNotBroken(self):
        alice_harem, bob_harem = setUpForNServers(1)
        alice_corridor = alice_harem.open(bobs_PK)
        self.assertTrue(alice_corridor.uid == alice_harem.corridors[0].uid == bob_harem.corridors[0].uid)
        alice_corridor.close(); self.assertTrue(alice_corridor.is_closed is True and alice_harem.corridors + bob_harem.corridors == [])
        [ h.quit() for h in (alice_harem, bob_harem)]  # pylint: disable=expression-not-assigned


if __name__ == "__main__":
#    import sys;sys.argv = ['TestTurnDownForWhatDJSnake.testSimplestAA']
    unittest.main()

