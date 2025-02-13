'''
Created on Feb 9, 2025

@author: mchobbit





'''
import unittest
from Crypto.PublicKey import RSA
from time import sleep
from my.irctools.jaracorocks.vanilla import VanillaBot
from my.stringtools import generate_random_alphanumeric_string
from queue import Empty
from my.globals import ALL_SANDOX_IRC_NETWORK_NAMES
from random import randint
from my.classes.exceptions import IrcDuplicateNicknameError, IrcInitialConnectionTimeoutError


class TestVanillaBot(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def testSimpleCreationAndDeletion(self):
        alice_nick = 'alice%d' % randint(111, 999)
        bob_nick = 'bob%d' % randint(111, 999)
        first_room = '#room' + generate_random_alphanumeric_string(5)
        alice_bot = VanillaBot(channels=[first_room],
                         nickname=alice_nick,
                         irc_server=ALL_SANDOX_IRC_NETWORK_NAMES[-1],
                         port=6667,
                         startup_timeout=30,
                         maximum_reconnections=3,
                         strictly_nick=True,
                         autoreconnect=True)
        bob_bot = VanillaBot(channels=[first_room],
                         nickname=bob_nick,
                         irc_server=ALL_SANDOX_IRC_NETWORK_NAMES[-1],
                         port=6667,
                         startup_timeout=30,
                         maximum_reconnections=3,
                         strictly_nick=True,
                         autoreconnect=True)
        self.assertTrue(alice_bot.ready)
        self.assertTrue(bob_bot.ready)
        alice_bot.quit()
        self.assertTrue(alice_nick not in bob_bot.users)
        bob_bot.quit()

    def testMultipleChannelsUserlist(self):
        alice_nick = 'alice%d' % randint(111, 999)
        bob_nick = 'bob%d' % randint(111, 999)
        charlie_nick = 'charl%d' % randint(111, 999)
        first_room = '#room' + generate_random_alphanumeric_string(5)
        second_room = '#boom' + generate_random_alphanumeric_string(5)
        alice_bot = VanillaBot(channels=[first_room],
                         nickname=alice_nick,
                         irc_server=ALL_SANDOX_IRC_NETWORK_NAMES[-1],
                         port=6667,
                         startup_timeout=30,
                         maximum_reconnections=3,
                         strictly_nick=True,
                         autoreconnect=True)
        bob_bot = VanillaBot(channels=[second_room],
                         nickname=bob_nick,
                         irc_server=ALL_SANDOX_IRC_NETWORK_NAMES[-1],
                         port=6667,
                         startup_timeout=30,
                         maximum_reconnections=3,
                         strictly_nick=True,
                         autoreconnect=True)
        charlie_bot = VanillaBot(channels=[first_room, second_room],
                         nickname=charlie_nick,
                         irc_server=ALL_SANDOX_IRC_NETWORK_NAMES[-1],
                         port=6667,
                         startup_timeout=30,
                         maximum_reconnections=3,
                         strictly_nick=True,
                         autoreconnect=True)
        self.assertTrue(alice_bot.ready)
        self.assertTrue(bob_bot.ready)
        self.assertTrue(charlie_bot.ready)
        self.assertEqual(2, len(alice_bot.users))
        self.assertEqual(2, len(bob_bot.users))
        self.assertEqual(3, len(charlie_bot.users))
        self.assertEqual(1, charlie_bot.users.count(alice_nick))
        self.assertTrue(alice_nick in charlie_bot.users)
        self.assertTrue(bob_nick in charlie_bot.users)
        self.assertTrue(charlie_nick in bob_bot.users)
        self.assertTrue(charlie_nick in alice_bot.users)
        self.assertFalse(alice_nick in bob_bot.users)
        self.assertFalse(bob_nick in alice_bot.users)
        alice_bot.quit()
        self.assertFalse(alice_nick in bob_bot.users)
        self.assertFalse(alice_nick in charlie_bot.users)
        bob_bot.quit()
        self.assertFalse(bob_nick in charlie_bot.users)
        self.assertEqual(charlie_bot.users, [charlie_nick])
        charlie_bot.quit()

    def testEnterAndLeaveRooms(self):
        alice_nick = 'alice%d' % randint(111, 999)
        bob_nick = 'bob%d' % randint(111, 999)
        first_room = '#room' + generate_random_alphanumeric_string(5)
        second_room = '#boom' + generate_random_alphanumeric_string(5)
        alice_bot = VanillaBot(channels=[first_room],
                         nickname=alice_nick,
                         irc_server=ALL_SANDOX_IRC_NETWORK_NAMES[-1],
                         port=6667,
                         startup_timeout=30,
                         maximum_reconnections=3,
                         strictly_nick=True,
                         autoreconnect=True)
        bob_bot = VanillaBot(channels=[second_room],
                         nickname=bob_nick,
                         irc_server=ALL_SANDOX_IRC_NETWORK_NAMES[-1],
                         port=6667,
                         startup_timeout=30,
                         maximum_reconnections=3,
                         strictly_nick=True,
                         autoreconnect=True)
        self.assertTrue(alice_bot.ready)
        self.assertTrue(bob_bot.ready)
        self.assertEqual(1, len(alice_bot.users))
        self.assertEqual(1, len(alice_bot.channels))
        self.assertEqual(1, len(bob_bot.users))
        self.assertEqual(1, len(bob_bot.channels))
        bob_bot.join(first_room)
        self.assertEqual(2, len(bob_bot.channels))
        self.assertEqual(2, len(bob_bot.users))
        self.assertEqual(2, len(alice_bot.users))
        alice_bot.quit()
        self.assertEqual(1, len(bob_bot.users))
        bob_bot.quit()

    def testDisconnectAndReconnect(self):
        alice_nick = 'alice%d' % randint(111, 999)
        bob_nick = 'bob%d' % randint(111, 999)
        first_room = '#room' + generate_random_alphanumeric_string(5)
        second_room = '#boom' + generate_random_alphanumeric_string(5)

        alice_bot = VanillaBot(channels=[first_room],
                         nickname=alice_nick,
                         irc_server=ALL_SANDOX_IRC_NETWORK_NAMES[-1],
                         port=6667,
                         startup_timeout=30,
                         maximum_reconnections=3,
                         strictly_nick=True,
                         autoreconnect=True)
        bob_bot = VanillaBot(channels=[second_room],
                         nickname=bob_nick,
                         irc_server=ALL_SANDOX_IRC_NETWORK_NAMES[-1],
                         port=6667,
                         startup_timeout=30,
                         maximum_reconnections=3,
                         strictly_nick=True,
                         autoreconnect=True)
        self.assertTrue(alice_bot.ready)
        self.assertTrue(bob_bot.ready)
        self.assertEqual(1, len(alice_bot.users))
        self.assertEqual(1, len(alice_bot.channels))
        self.assertEqual([first_room], list(alice_bot.channels.keys()))

        alice_bot.join(second_room)
        self.assertEqual([first_room, second_room], list(alice_bot.channels.keys()))
        self.assertEqual(2, len(bob_bot.users))
        self.assertEqual(1, len(bob_bot.channels))
        self.assertEqual(2, len(alice_bot.channels))
        alice_bot.quit()
        bob_bot.quit()

    def testDupeNicks(self):
        alice_nick = 'alice%d' % randint(111, 999)
        bob_nick = 'bob%d' % randint(111, 999)
        dupe_nick = alice_nick
        the_room = '#room' + generate_random_alphanumeric_string(5)
        alice_bot = VanillaBot(channels=[the_room],
                         nickname=alice_nick,
                         irc_server=ALL_SANDOX_IRC_NETWORK_NAMES[-1],
                         port=6667,
                         startup_timeout=30,
                         maximum_reconnections=3,
                         strictly_nick=True,
                         autoreconnect=True)
        bob_bot = VanillaBot(channels=[the_room],
                         nickname=bob_nick,
                         irc_server=ALL_SANDOX_IRC_NETWORK_NAMES[-1],
                         port=6667,
                         startup_timeout=30,
                         maximum_reconnections=3,
                         strictly_nick=True,
                         autoreconnect=True)
        self.assertTrue(alice_bot.ready)
        self.assertTrue(bob_bot.ready)
        self.assertRaises(IrcDuplicateNicknameError, VanillaBot, [the_room],
                         dupe_nick, ALL_SANDOX_IRC_NETWORK_NAMES[-1], 6667, 30, 3, True, True)
        alice_bot.quit()
        bob_bot.quit()

    def testFingerprintSettingAndRecognizing(self):
        alice_nick = 'alice%d' % randint(111, 999)
        bob_nick = 'bob%d' % randint(111, 999)
        the_room = '#room' + generate_random_alphanumeric_string(5)
        alice_bot = VanillaBot(channels=[the_room],
                         nickname=alice_nick,
                         irc_server=ALL_SANDOX_IRC_NETWORK_NAMES[-1],
                         port=6667,
                         startup_timeout=30,
                         maximum_reconnections=3,
                         strictly_nick=True,
                         autoreconnect=True)
        bob_bot = VanillaBot(channels=[the_room],
                         nickname=bob_nick,
                         irc_server=ALL_SANDOX_IRC_NETWORK_NAMES[-1],
                         port=6667,
                         startup_timeout=30,
                         maximum_reconnections=3,
                         strictly_nick=True,
                         autoreconnect=True)
        self.assertTrue(alice_bot.ready)
        self.assertTrue(bob_bot.ready)
        self.assertEqual(alice_bot.fingerprint, alice_bot.whois(alice_nick).split('* ', 1)[-1])
        self.assertEqual(alice_bot.fingerprint, bob_bot.whois(alice_nick).split('* ', 1)[-1])
        self.assertEqual(bob_bot.fingerprint, alice_bot.whois(bob_nick).split('* ', 1)[-1])
        self.assertEqual(bob_bot.fingerprint, bob_bot.whois(bob_nick).split('* ', 1)[-1])
        alice_bot.quit()
        bob_bot.quit()

    def testNickCollisionAndAuthorizedReconnect(self):
        alice_nick = 'alice%d' % randint(111, 999)
        bob_nick = 'bob%d' % randint(111, 999)
        dupe_nick = alice_nick
        the_room = '#room' + generate_random_alphanumeric_string(5)
        alice_bot = VanillaBot(channels=[the_room],
                         nickname=alice_nick,
                         irc_server=ALL_SANDOX_IRC_NETWORK_NAMES[-1],
                         port=6667,
                         startup_timeout=30,
                         maximum_reconnections=3,
                         strictly_nick=True,
                         autoreconnect=True)
        bob_bot = VanillaBot(channels=[the_room],
                         nickname=bob_nick,
                         irc_server=ALL_SANDOX_IRC_NETWORK_NAMES[-1],
                         port=6667,
                         startup_timeout=30,
                         maximum_reconnections=3,
                         strictly_nick=True,
                         autoreconnect=True)
        dupe_bot = VanillaBot(channels=[the_room],
                         nickname=bob_nick,
                         irc_server=ALL_SANDOX_IRC_NETWORK_NAMES[-1],
                         port=6667,
                         startup_timeout=30,
                         maximum_reconnections=3,
                         strictly_nick=False,
                         autoreconnect=True)
        self.assertTrue(alice_bot.ready)
        self.assertTrue(bob_bot.ready)
        self.assertTrue(dupe_bot.ready)
        self.assertNotEqual(dupe_nick, dupe_bot.nickname)
        alice_bot.quit()
        bob_bot.quit()
        dupe_bot.quit()

    def testNickCollisionWithNoRetry(self):
        alice_nick = 'alice%d' % randint(111, 999)
        bob_nick = 'bob%d' % randint(111, 999)
        dupe_nick = alice_nick
        the_room = '#room' + generate_random_alphanumeric_string(5)
        alice_bot = VanillaBot(channels=[the_room],
                         nickname=alice_nick,
                         irc_server=ALL_SANDOX_IRC_NETWORK_NAMES[-1],
                         port=6667,
                         startup_timeout=30,
                         maximum_reconnections=3,
                         strictly_nick=True,
                         autoreconnect=True)
        bob_bot = VanillaBot(channels=[the_room],
                         nickname=bob_nick,
                         irc_server=ALL_SANDOX_IRC_NETWORK_NAMES[-1],
                         port=6667,
                         startup_timeout=30,
                         maximum_reconnections=3,
                         strictly_nick=True,
                         autoreconnect=True)
        self.assertTrue(alice_bot.ready)
        self.assertTrue(bob_bot.ready)
        self.assertRaises(IrcInitialConnectionTimeoutError, VanillaBot, [the_room],
                         dupe_nick, ALL_SANDOX_IRC_NETWORK_NAMES[-1], 6667, 30, 0, False, True)
        dupe_bot = VanillaBot(channels=[the_room],
                         nickname=dupe_nick,
                         irc_server=ALL_SANDOX_IRC_NETWORK_NAMES[-1],
                         port=6667,
                         startup_timeout=30,
                         maximum_reconnections=1,
                         strictly_nick=False,
                         autoreconnect=True)
        self.assertNotEqual(dupe_bot.nickname, dupe_nick)
        alice_bot.quit()
        bob_bot.quit()
        dupe_bot.quit()

    def testNonexistentServerConnect(self):
        alice_nick = 'alice%d' % randint(111, 999)
        the_room = '#room' + generate_random_alphanumeric_string(5)
        self.assertRaises(IrcInitialConnectionTimeoutError, VanillaBot, [the_room],
                         alice_nick, 'irc.nonexistent.server', 6667, 4, 2, True, True)

    def testTalkToEachOther(self):
        alice_nick = 'alice%d' % randint(111, 999)
        bob_nick = 'bob%d' % randint(111, 999)
        dupe_nick = alice_nick
        the_room = '#room' + generate_random_alphanumeric_string(5)
        alice_bot = VanillaBot(channels=[the_room],
                         nickname=alice_nick,
                         irc_server=ALL_SANDOX_IRC_NETWORK_NAMES[-1],
                         port=6667,
                         startup_timeout=30,
                         maximum_reconnections=3,
                         strictly_nick=True,
                         autoreconnect=True)
        bob_bot = VanillaBot(channels=[the_room],
                         nickname=bob_nick,
                         irc_server=ALL_SANDOX_IRC_NETWORK_NAMES[-1],
                         port=6667,
                         startup_timeout=30,
                         maximum_reconnections=3,
                         strictly_nick=True,
                         autoreconnect=True)
        dupe_bot = VanillaBot(channels=[the_room],
                         nickname=bob_nick,
                         irc_server=ALL_SANDOX_IRC_NETWORK_NAMES[-1],
                         port=6667,
                         startup_timeout=30,
                         maximum_reconnections=3,
                         strictly_nick=False,
                         autoreconnect=True)
        alice_bot.put(bob_bot.nickname, "HELLO BOB")
        bob_bot.put(dupe_bot.nickname, "HELLO DUPE")
        dupe_bot.put(alice_bot.nickname, "HELLO ALICE")
        self.assertEqual(alice_bot.get(), (dupe_bot.nickname, "HELLO ALICE"))
        self.assertEqual(bob_bot.get(), (alice_bot.nickname, "HELLO BOB"))
        self.assertEqual(dupe_bot.get(), (bob_bot.nickname, "HELLO DUPE"))
        self.assertRaises(Empty, alice_bot.get_nowait)
        self.assertRaises(Empty, bob_bot.get_nowait)
        self.assertRaises(Empty, dupe_bot.get_nowait)
        alice_bot.put(bob_bot.nickname, "HELLO bob")
        alice_bot.put(bob_bot.nickname, "HELLO bob")  # Cached
        alice_bot.put(bob_bot.nickname, "HELLO bob")  # Cached
        bob_bot.put(dupe_bot.nickname, "HELLO dupe")
        bob_bot.put(dupe_bot.nickname, "HELLO dupe")  # Cached
        bob_bot.put(dupe_bot.nickname, "HELLO dupe")  # Cached
        dupe_bot.put(alice_bot.nickname, "HELLO alice")
        dupe_bot.put(alice_bot.nickname, "HELLO alice")  # Cached
        dupe_bot.put(alice_bot.nickname, "HELLO alice")  # Cached
        self.assertEqual(alice_bot.get(), (dupe_bot.nickname, "HELLO alice"))
        self.assertEqual(bob_bot.get(), (alice_bot.nickname, "HELLO bob"))
        self.assertEqual(dupe_bot.get(), (bob_bot.nickname, "HELLO dupe"))
        self.assertRaises(Empty, alice_bot.get, timeout=2)
        self.assertRaises(Empty, bob_bot.get, timeout=2)
        self.assertRaises(Empty, dupe_bot.get, timeout=2)
        alice_bot.quit()
        bob_bot.quit()
        dupe_bot.quit()

#         Xbots = {}
#         Ybots = {}
#         my_channel = '#platit'
#         X_desired_nickname = 'x%sx' % generate_random_alphanumeric_string(7)
#         Y_desired_nickname = 'y%sy' % generate_random_alphanumeric_string(7)
#
#         my_port = 6667
#         for my_irc_server in ALL_SANDOX_IRC_NETWORK_NAMES:
#             Xbots[my_irc_server] = VanillaBot([my_channel], X_desired_nickname, my_irc_server, my_port)
#             Ybots[my_irc_server] = VanillaBot([my_channel], Y_desired_nickname, my_irc_server, my_port)
#
# elf, channels:list, nickname:str, irc_server:str, port:int,
#                  startup_timeout:int, maximum_reconnections:int, strictly_nick:bool, autoreconnect:bool
#
#
#         successes_thus_far = -1
#         while successes_thus_far < len([k for k in ALL_SANDOX_IRC_NETWORK_NAMES if Xbots[k].ready and Ybots[k].ready]):
#             successes_thus_far = len([k for k in ALL_SANDOX_IRC_NETWORK_NAMES if Xbots[k].ready and Ybots[k].ready])
#             sleep(10)
#         readyKs = [k for k in ALL_SANDOX_IRC_NETWORK_NAMES if Xbots[k].ready and Ybots[k].ready]
#         for k in readyKs:
#             for xy in (Xbots, Ybots):
#                 try:
#                     while True:
#                         _ = xy[k].get_nowait()
#                 except Empty:
#                     break
#         for k in readyKs:
#             print("Trying %s" % k)
#             if Xbots[k].ready and Ybots[k].ready:
#                 p = "Hello there from %s" % k
#                 Xbots[k].put(Y_desired_nickname, p)
#
#         defective_items = []
#         for k in readyKs:
#             p = "WORD UP FROM %s" % k
#             (src, msg) = Ybots[k].get()
#             if p != msg:
#                 print("%s is defective" % k)
#                 defective_items += [k]
#
#         for k in defective_items:
#             readyKs.remove(k)
#
#         for my_irc_server in ALL_SANDOX_IRC_NETWORK_NAMES:
#             Xbots[my_irc_server].quit()
#             Ybots[my_irc_server].quit()


if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()

