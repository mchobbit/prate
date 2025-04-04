# -*- coding: utf-8 -*-
"""
Created on Feb 9, 2025

@author: mchobbit


"""
import unittest
from Crypto.PublicKey import RSA
from time import sleep
from my.stringtools import generate_irc_handle, get_word_salad, s_now
from my.globals import MAX_PRIVMSG_LENGTH, MAX_NICKNAME_LENGTH, MAX_CHANNEL_LENGTH, MAX_CRYPTO_MSG_LENGTH, RSA_KEY_SIZE
from test.myttlcacheT import generate_random_alphanumeric_string
from queue import Empty
from my.irctools.jaracorocks.pratebot import PrateBot, _TRANSMIT_PLAINTEXT_
from my.classes.exceptions import PublicKeyBadKeyError, IrcPrivateMessageContainsBadCharsError, IrcBadNicknameError, IrcChannelNameTooLongError, IrcBadChannelNameError, \
    IrcNicknameTooLongError, IrcBadServerPortError, IrcBadServerNameError
from random import randint
from my.stringtools import flatten
from my.irctools.cryptoish import squeeze_da_keez
import datetime
import base64

my_rsa_key = RSA.generate(RSA_KEY_SIZE)
my_rsa_key1 = RSA.generate(RSA_KEY_SIZE)
my_rsa_key2 = RSA.generate(RSA_KEY_SIZE)


class TestGroupOne(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def testGoofyParams(self):

        alice_nick = 'alice%d' % randint(111, 999)
        self.assertRaises(IrcBadChannelNameError, PrateBot, None, alice_nick, 'cinqcent.local', 6667, my_rsa_key)
        self.assertRaises(IrcBadChannelNameError, PrateBot, [''], alice_nick, 'cinqcent.local', 6667, my_rsa_key)
        self.assertRaises(IrcBadChannelNameError, PrateBot, ['missinghash'], alice_nick, 'cinqcent.local', 6667, my_rsa_key)
        self.assertRaises(IrcBadChannelNameError, PrateBot, ['#'], alice_nick, 'cinqcent.local', 6667, my_rsa_key)
        self.assertRaises(IrcBadChannelNameError, PrateBot, ['#roomname with a space in it'], alice_nick, 'cinqcent.local', 6667, my_rsa_key)
        self.assertRaises(IrcChannelNameTooLongError, PrateBot, ['#impossiblylongimpossiblylongimpossiblylongimpossiblylongimpossiblylongimpossiblylongimpossiblylongimpossiblylongimpossiblylongimpossiblylong'], alice_nick, 'cinqcent.local', 6667, my_rsa_key)
        self.assertRaises(IrcBadNicknameError, PrateBot, ['#prate'], None, 'cinqcent.local', 6667, my_rsa_key)
        self.assertRaises(IrcBadNicknameError, PrateBot, ['#prate'], '1', 'cinqcent.local', 6667, my_rsa_key)
        self.assertRaises(IrcBadNicknameError, PrateBot, ['#prate'], ' ', 'cinqcent.local', 6667, my_rsa_key)
        self.assertRaises(IrcBadNicknameError, PrateBot, ['#prate'], '#', 'cinqcent.local', 6667, my_rsa_key)
        self.assertRaises(IrcBadNicknameError, PrateBot, ['#prate'], '#a', 'cinqcent.local', 6667, my_rsa_key)
        self.assertRaises(IrcBadNicknameError, PrateBot, ['#prate'], ' hi', 'cinqcent.local', 6667, my_rsa_key)
        self.assertRaises(IrcBadNicknameError, PrateBot, ['#prate'], 'hi ', 'cinqcent.local', 6667, my_rsa_key)
        self.assertRaises(IrcBadNicknameError, PrateBot, ['#prate'], 'hi ', 'cinqcent.local', 6667, my_rsa_key)
        self.assertRaises(IrcNicknameTooLongError, PrateBot, ['#prate'], 'hitherefolksomgthisiswaytoolong', 'cinqcent.local', 6667, my_rsa_key)
        self.assertRaises(IrcBadServerNameError, PrateBot, ['#prate'], alice_nick, None, 6667, my_rsa_key)
        self.assertRaises(IrcBadServerNameError, PrateBot, ['#prate'], alice_nick, 'cinqcent dot local', 6667, my_rsa_key)
        self.assertRaises(IrcBadServerPortError, PrateBot, ['#prate'], alice_nick, 'cinqcent.local', None, my_rsa_key)
        self.assertRaises(IrcBadServerPortError, PrateBot, ['#prate'], alice_nick, 'cinqcent.local', 'Word up', my_rsa_key)
        self.assertRaises(IrcBadServerPortError, PrateBot, ['#prate'], alice_nick, 'cinqcent.local', 0, my_rsa_key)
        self.assertRaises(ValueError, PrateBot, ['#prate'], alice_nick, 'cinqcent.local', 6667, None)
        self.assertRaises(ValueError, PrateBot, ['#prate'], alice_nick, 'cinqcent.local', 6667, my_rsa_key, startup_timeout=-1)
        self.assertRaises(ValueError, PrateBot, ['#prate'], alice_nick, 'cinqcent.local', 6667, my_rsa_key, startup_timeout=0)
        self.assertRaises(ValueError, PrateBot, ['#prate'], alice_nick, 'cinqcent.local', 6667, my_rsa_key, startup_timeout='Blah')
        self.assertRaises(ValueError, PrateBot, ['#prate'], alice_nick, 'cinqcent.local', 6667, 'blah')

    def testSimpleLogin(self):
        alice_nick = 'alice%d' % randint(111, 999)
        bot = PrateBot(['#prate'], alice_nick, 'cinqcent.local', 6667, my_rsa_key)
        self.assertTrue(bot.connected_and_joined)
        bot.quit()

#
    def testReady(self):
        alice_nick = 'alice%d' % randint(111, 999)
        bot = PrateBot(['#prate'], alice_nick, 'cinqcent.local', 6667, my_rsa_key)
        self.assertTrue(bot.connected_and_joined)
        self.assertTrue(bot._client.connected_and_joined)  # Should be the same as bot.connected_and_joined pylint: disable=protected-access
        bot.quit()

    def testSimpleWhois(self):
        alice_nick = 'alice%d' % randint(111, 999)
        bot = PrateBot(['#prate'], alice_nick, 'cinqcent.local', 6667, my_rsa_key)
        self.assertTrue(bot.connected_and_joined)
        self.assertEqual(bot.whois(alice_nick).split('* ', 1)[-1], bot.fingerprint)
        bot.quit()

    def testSimpleCallResponse(self):
        alice_nick = 'alice%d' % randint(111, 999)
        bot = PrateBot(['#prate'], alice_nick, 'cinqcent.local', 6667, my_rsa_key)
        self.assertTrue(bot.connected_and_joined)
        bot.put(bot.nickname, "HELLO")
        self.assertEqual(bot.get(timeout=10), (bot.nickname, 'HELLO'))
        bot.quit()

    def testHomiesShouldNotIncludeMe(self):
        alice_nick = 'alice%d' % randint(111, 999)
        bob_nick = 'bob%d' % randint(111, 999)
        alice_bot = PrateBot(['#prate'], alice_nick, 'cinqcent.local', 6667, my_rsa_key)
        bob_bot = PrateBot(['#prate'], bob_nick, 'cinqcent.local', 6667, my_rsa_key)
        self.assertTrue(alice_bot.connected_and_joined)
        self.assertTrue(bob_bot.connected_and_joined)
        if not (alice_bot.is_handshook_with(bob_bot.my_pubkey) and bob_bot.is_handshook_with(alice_bot.my_pubkey)):
            sleep(10)
        self.assertTrue(alice_bot.is_handshook_with(bob_bot.my_pubkey))
        self.assertTrue(bob_bot.is_handshook_with(alice_bot.my_pubkey))
        self.assertFalse(alice_nick in alice_bot.homies)
        self.assertFalse(bob_nick in bob_bot.homies)
        self.assertTrue(alice_nick in bob_bot.homies)
        self.assertTrue(bob_nick in alice_bot.homies)
        alice_bot.quit()
        bob_bot.quit()


class TestGroupTwo(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def testRoomMembership(self):
        nick1 = generate_irc_handle(4, MAX_NICKNAME_LENGTH)
        nick2 = generate_irc_handle(4, MAX_NICKNAME_LENGTH)
        self.assertNotEqual(nick1, nick2)
        my_room = '#T' + generate_random_alphanumeric_string(MAX_CHANNEL_LENGTH - 2)
        bot1 = PrateBot([my_room], nick1, 'cinqcent.local', 6667, my_rsa_key1)
        bot2 = PrateBot([my_room], nick2, 'cinqcent.local', 6667, my_rsa_key2)
        if not (bot1.is_handshook_with(bot2.my_pubkey) and bot2.is_handshook_with(bot1.my_pubkey)):
            sleep(10)
        self.assertTrue(bot1.is_handshook_with(bot2.my_pubkey))
        self.assertTrue(bot2.is_handshook_with(bot1.my_pubkey))
        shouldbe = [nick1, nick2]
        actuallyis = bot1.users
        shouldbe.sort()
        actuallyis.sort()
        self.assertEqual(shouldbe, actuallyis)
        bot1.quit()
        bot2.quit()

    def testTwoBots(self):
        my_room = '#pratjbqy'  # + generate_irc_handle(7, 9)
        nick1 = generate_irc_handle(4, MAX_NICKNAME_LENGTH)
        nick2 = generate_irc_handle(4, MAX_NICKNAME_LENGTH)
        self.assertNotEqual(nick1, nick2)
        bot1 = PrateBot([my_room], nick1, 'cinqcent.local', 6667, my_rsa_key1)
        bot2 = PrateBot([my_room], nick2, 'cinqcent.local', 6667, my_rsa_key2)
        if not (bot1.is_handshook_with(bot2.my_pubkey) and bot2.is_handshook_with(bot1.my_pubkey)):
            sleep(10)
        self.assertTrue(bot1.is_handshook_with(bot2.my_pubkey))
        self.assertTrue(bot2.is_handshook_with(bot1.my_pubkey))
        self.assertEqual([my_rsa_key1.public_key()], bot2.homies_pubkeys)
        self.assertEqual([my_rsa_key2.public_key()], bot1.homies_pubkeys)
        the_message = get_word_salad()[:MAX_CRYPTO_MSG_LENGTH].encode()
        while bot1.homies[bot2.nickname].ipaddr is None or bot2.homies[bot1.nickname].ipaddr is None:
            print("Waiting for %s and %s to negotiate a connection" % (bot1.nickname, bot2.nickname))
            sleep(2)
        bot1.crypto_put(bot2.nickname, the_message)
        sleep(2)
        incoming_sender, incoming_message = bot2.crypto_get()
        self.assertEqual((incoming_sender, incoming_message), (bot1.nickname, the_message))
        bot1.quit()
        bot2.quit()

    def testBadMessageLengthAndType(self):

        def send_test_msg(msg, nick1=None, nick2=None):
            my_room = '#prate'  #  + generate_irc_handle(6, 9)
            if not nick1:
                nick1 = generate_irc_handle(4, MAX_NICKNAME_LENGTH)
            if not nick2:
                nick2 = generate_irc_handle(4, MAX_NICKNAME_LENGTH)
            self.assertNotEqual(nick1, nick2)
            try:
                bot1 = PrateBot([my_room], nick1, 'cinqcent.local', 6667, my_rsa_key1)
                bot2 = PrateBot([my_room], nick2, 'cinqcent.local', 6667, my_rsa_key2)
                self.assertTrue(bot1.connected_and_joined)
                self.assertTrue(bot2.connected_and_joined)
                if not (bot1.is_handshook_with(bot2.my_pubkey) and bot2.is_handshook_with(bot1.my_pubkey)):
                    sleep(10)
                self.assertTrue(bot1.is_handshook_with(bot2.my_pubkey))
                self.assertTrue(bot2.is_handshook_with(bot1.my_pubkey))
                assert(len(bot1.nickname) <= MAX_NICKNAME_LENGTH)
                assert(len(bot2.nickname) <= MAX_NICKNAME_LENGTH)
                bot1.put(bot1.nickname, msg)
                retvals = bot1.get(timeout=8)
                self.assertEqual(retvals, (bot1.nickname, msg))
                self.assertRaises(IrcPrivateMessageContainsBadCharsError, send_test_msg, b'h9in0x')
                self.assertRaises(IrcPrivateMessageContainsBadCharsError, send_test_msg, None)
                self.assertRaises(IrcPrivateMessageContainsBadCharsError, send_test_msg, 3)
                self.assertRaises(IrcPrivateMessageContainsBadCharsError, send_test_msg, '')
            finally:
                bot1.quit()
                bot2.quit()

        # self.assertRaises(IrcPrivateMessageTooLongError, send_test_msg, generate_random_alphanumeric_string(MAX_PRIVMSG_LENGTH + 2))
        # self.assertRaises(IrcPrivateMessageTooLongError, send_test_msg, generate_random_alphanumeric_string(MAX_PRIVMSG_LENGTH + 1))
        # for _ in range(0, 5):
        #     self.assertRaises(IrcPrivateMessageTooLongError, send_test_msg, generate_random_alphanumeric_string(MAX_PRIVMSG_LENGTH))
        # send_test_msg(generate_random_alphanumeric_string(MAX_PRIVMSG_LENGTH - 10), 'abcde%d' % randint(1000, 9999))

    def testSendGoofyValues(self):
        my_room = '#prate'  # + generate_irc_handle(7, 9)
        nick1 = generate_irc_handle(4, MAX_NICKNAME_LENGTH)
        nick2 = generate_irc_handle(4, MAX_NICKNAME_LENGTH)
        self.assertNotEqual(nick1, nick2)
        sleep(5)
        print("AAAAaa")
        bot1 = PrateBot([my_room], nick1, 'cinqcent.local', 6667, my_rsa_key1)
        print("BBBBbb")
        bot2 = PrateBot([my_room], nick2, 'cinqcent.local', 6667, my_rsa_key2)
        print("CCCCcc")
        bot1.quit()
        print("DDDDdd")
        bot2.quit()
        print("EEEEee")
        sleep(5)

    def testSendGoofyValuesWithoutSleeping(self):
        my_room = '#prate'  # + generate_irc_handle(7, 9)
        nick1 = generate_irc_handle(4, MAX_NICKNAME_LENGTH)
        nick2 = generate_irc_handle(4, MAX_NICKNAME_LENGTH)
        self.assertNotEqual(nick1, nick2)
        bot1 = PrateBot([my_room], nick1, 'cinqcent.local', 6667, my_rsa_key1)
        bot2 = PrateBot([my_room], nick2, 'cinqcent.local', 6667, my_rsa_key2)
        bot1.quit()
        bot2.quit()

    def testDifferentRooms(self):
        nick1 = generate_irc_handle(7, 9)
        nick2 = generate_irc_handle(7, 9)
        room1 = '#T' + generate_random_alphanumeric_string(MAX_CHANNEL_LENGTH - 2)
        room2 = '#T' + generate_random_alphanumeric_string(MAX_CHANNEL_LENGTH - 2)
        self.assertNotEqual(nick1, nick2)
        bot1 = PrateBot([room1], nick1, 'cinqcent.local', 6667, my_rsa_key1)
        bot2 = PrateBot([room2], nick2, 'cinqcent.local', 6667, my_rsa_key2)
        self.assertEqual(bot1.nickname, nick1)
        self.assertEqual(bot2.nickname, nick2)
        bot1.quit()
        bot2.quit()

    def testNicknameCollision(self):
        desired_nick = 'A' + generate_random_alphanumeric_string(MAX_NICKNAME_LENGTH - 1)
        bot1 = PrateBot(['#prate'], desired_nick, 'cinqcent.local', 6667, my_rsa_key)
        self.assertTrue(bot1.connected_and_joined)
        self.assertEqual(bot1.nickname, desired_nick)
        bot2 = PrateBot(['#prate'], desired_nick, 'cinqcent.local', 6667, my_rsa_key, strictly_nick=False)  # To allow the automatic renaming of the nickname
        self.assertTrue(bot2.connected_and_joined)
        try:
            while True:
                _ = bot1.get_nowait()
        except Empty:
            pass
        try:
            while True:
                _ = bot2.get_nowait()
        except Empty:
            pass
        self.assertNotEqual(bot2.nickname, desired_nick)
        self.assertNotEqual(bot2.nickname, bot1.nickname)
        msg = generate_random_alphanumeric_string(MAX_PRIVMSG_LENGTH - len(bot2.nickname) - len(_TRANSMIT_PLAINTEXT_))
        bot1.put(bot2.nickname, msg)
        self.assertEqual(bot2.get(timeout=180), (bot1.nickname, msg))
        msg = generate_random_alphanumeric_string(MAX_PRIVMSG_LENGTH - len(bot1.nickname) - len(_TRANSMIT_PLAINTEXT_))
        bot2.put(bot1.nickname, msg)
        self.assertEqual(bot1.get(timeout=180), (bot2.nickname, msg))
        bot1.quit()
        bot2.quit()


class TestGroupThree(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def testSendingSameMessageTwice_partone(self):
        nick1 = generate_irc_handle()
        nick2 = generate_irc_handle()
        room1 = '#T' + generate_random_alphanumeric_string(MAX_CHANNEL_LENGTH - 2)
        room2 = '#T' + generate_random_alphanumeric_string(MAX_CHANNEL_LENGTH - 2)
        self.assertNotEqual(nick1, nick2)
        bot1 = PrateBot([room1, room2], nick1, 'cinqcent.local', 6667, my_rsa_key1)
        bot2 = PrateBot([room1, room2], nick2, 'cinqcent.local', 6667, my_rsa_key2)
        if not (bot1.is_handshook_with(bot2.my_pubkey) and bot2.is_handshook_with(bot1.my_pubkey)):
            sleep(10)
        self.assertTrue(bot1.is_handshook_with(bot2.my_pubkey))
        self.assertTrue(bot2.is_handshook_with(bot1.my_pubkey))
        msg = generate_random_alphanumeric_string(MAX_PRIVMSG_LENGTH - len(bot2.nickname) - len(_TRANSMIT_PLAINTEXT_))
        bot1.put(bot2.nickname, msg)
        bot1.put(bot2.nickname, "Hello, world.")
        bot1.put(bot2.nickname, msg)
        self.assertEqual(bot2.get(timeout=8), (bot1.nickname, msg))
        self.assertEqual(bot2.get(timeout=8), (bot1.nickname, "Hello, world."))
        sleep(2)
        self.assertRaises(Empty, bot2.get_nowait)
        bot1.quit()
        bot2.quit()

    def testSendingSameMessageTwice_parttwo(self):
        nick1 = generate_irc_handle(4, MAX_NICKNAME_LENGTH)
        nick2 = generate_irc_handle(4, MAX_NICKNAME_LENGTH)
        room1 = '#prate'  # + generate_irc_handle(7, 9)
        room2 = '#prate'  # + generate_irc_handle(7, 9)
        self.assertNotEqual(nick1, nick2)
        bot1 = PrateBot([room1], nick1, 'cinqcent.local', 6667, my_rsa_key1)
        bot2 = PrateBot([room2], nick2, 'cinqcent.local', 6667, my_rsa_key2)
        if not (bot1.is_handshook_with(bot2.my_pubkey) and bot2.is_handshook_with(bot1.my_pubkey)):
            sleep(10)
        self.assertTrue(bot1.is_handshook_with(bot2.my_pubkey))
        self.assertTrue(bot2.is_handshook_with(bot1.my_pubkey))
        msg = generate_random_alphanumeric_string(MAX_PRIVMSG_LENGTH - len(nick2) - len(_TRANSMIT_PLAINTEXT_))
        bot1.put(bot2.nickname, msg)
        bot1.put(bot2.nickname, msg)
        bot1.put(bot2.nickname, "Hello, world.")
        sleep(2)
        self.assertEqual(bot2.get(timeout=8), (bot1.nickname, msg))
        self.assertEqual(bot2.get(timeout=8), (bot1.nickname, "Hello, world."))
        sleep(2)
        if bot2.empty():
            pass  # print("Good.")
        else:
            self.assertRaises(Empty, bot2.get_nowait)
        bot1.quit()
        bot2.quit()


class TestKeyCryptoPutAndCryptoGet(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def testSimpleEncryptedTransferOf100Bytes(self):
        alice_nick = 'alice%d' % randint(111, 999)
        bob_nick = 'alice%d' % randint(111, 999)
        bot1 = PrateBot(['#prate'], alice_nick, 'cinqcent.local', 6667, my_rsa_key1, autohandshake=True)
        bot2 = PrateBot(['#prate'], bob_nick, 'cinqcent.local', 6667, my_rsa_key2, autohandshake=True)
        if not (bot1.is_handshook_with(bot2.my_pubkey) and bot2.is_handshook_with(bot1.my_pubkey)):
            sleep(10)
        self.assertTrue(bot1.is_handshook_with(bot2.my_pubkey))  # ...which implies bot1.connected_and_joined is True
        self.assertTrue(bot2.is_handshook_with(bot1.my_pubkey))  # ...which implies bot2.connected_and_joined is True
        self.assertTrue(bot1.empty())
        self.assertTrue(bot2.empty())
        for i in range(0, 10):
            print("loop", i)
            plaintext = generate_random_alphanumeric_string(MAX_PRIVMSG_LENGTH // 2).encode()
            bot1.crypto_put(bot2.nickname, plaintext)
            while bot2.crypto_empty():
                sleep(.1)
            (from_user, received_msg) = bot2.crypto_get()
            self.assertEqual(from_user, bot1.nickname)
            self.assertEqual(plaintext, received_msg)
        bot1.quit()
        bot2.quit()

    def testDoesChannelUserlistUpdateAutomatically(self):
        alice_nick = 'alice%d' % randint(111, 999)
        bob_nick = 'alice%d' % randint(111, 999)
        bot1 = PrateBot(['#prattq'], alice_nick, 'cinqcent.local', 6667, my_rsa_key1)
        sleep(5)
        lou1 = bot1.users
        lou1.sort()
        bot2 = PrateBot(['#prattq'], bob_nick, 'cinqcent.local', 6667, my_rsa_key2)
        sleep(5)
        lou2 = bot2.users
        lou2.sort()
        self.assertTrue(bot2.nickname not in lou1)
        self.assertTrue(bot2.nickname in bot1.users)
        self.assertTrue(bot1.nickname in bot2.users)
        b1nick = bot1.nickname
        bot1.quit()
        sleep(.5)
        self.assertTrue(b1nick not in bot2.users)
        bot2.quit()

    def testSlowlyJoinAndLeave(self):
        alice_nick = 'alice%d' % randint(111, 999)
        bob_nick = 'alice%d' % randint(111, 999)
        bot1 = PrateBot(['#prat45'], alice_nick, 'cinqcent.local', 6667, my_rsa_key1)
        sleep(5)
        lou1 = bot1.users
        bot2 = PrateBot(['#prat45'], bob_nick, 'cinqcent.local', 6667, my_rsa_key2)
        sleep(5)
        b1nick = bot1.nickname
        b2nick = bot2.nickname
        self.assertTrue(b2nick not in lou1)
        self.assertTrue(b2nick in bot1.users)
        self.assertTrue(b1nick in bot2.users)
        sleep(2)
        bot1.quit()
        sleep(.5)
        self.assertTrue(b1nick not in bot2.users)
        bot2.quit()

    def testJoiningAndLeavingSeveralDifferentChannels(self):
        alice_nick = 'alice%d' % randint(111, 999)
        bob_nick = 'alice%d' % randint(111, 999)
        the_room = '#room' + generate_random_alphanumeric_string(5)
        bot1 = PrateBot([the_room], alice_nick, 'cinqcent.local', 6667, my_rsa_key1)
        bot2 = PrateBot(['#prate234'], bob_nick, 'cinqcent.local', 6667, my_rsa_key2)
        self.assertFalse(bot1.nickname in bot2.users)
        self.assertFalse(bot2.nickname in bot1.users)
        self.assertEqual(1, len(bot1.channels))
        self.assertEqual(1, len(bot2.channels))
        bot2.join(the_room)
        self.assertTrue(bot1.nickname in bot2.users)
        self.assertTrue(bot2.nickname in bot1.users)
        self.assertEqual(2, len(bot1.users))
        self.assertEqual(2, len(bot2.users))
        self.assertEqual(1, len(bot1.channels))
        self.assertEqual(2, len(bot2.channels))
        bot1.join("#prate234")
        self.assertTrue(bot1.nickname in bot2.users)
        self.assertTrue(bot2.nickname in bot1.users)
        self.assertEqual(2, len(bot1.users))
        self.assertEqual(2, len(bot2.users))
        self.assertEqual(2, len(bot1.channels))
        self.assertEqual(2, len(bot2.channels))
        bot1.join("#prate456")
        self.assertTrue(bot1.nickname in bot2.users)
        self.assertTrue(bot2.nickname in bot1.users)
        self.assertEqual(2, len(bot1.users))
        self.assertEqual(2, len(bot2.users))
        self.assertEqual(3, len(bot1.channels))
        self.assertEqual(2, len(bot2.channels))
        bot1.part(the_room)
        bot1.part("#prate234")
        sleep(5)
        self.assertFalse(bot1.nickname in bot2.users)
        self.assertFalse(bot2.nickname in bot1.users)
        self.assertEqual(1, len(bot1.users))
        self.assertEqual(1, len(bot2.users))
        self.assertEqual(1, len(bot1.channels))
        self.assertEqual(2, len(bot2.channels))
        bot1.part("#prate456")
        sleep(5)
        self.assertEqual(0, len(bot1.channels))
        self.assertEqual(2, len(bot2.channels))
        bot1.quit()
        bot2.quit()


class TestFernetKeyMismatches(unittest.TestCase):

    def testSimpleFernetKeyMismatch(self):
        my_room = '#pratexx'  # + generate_irc_handle(7, 9)
        nick1 = generate_irc_handle(4, MAX_NICKNAME_LENGTH)
        nick2 = generate_irc_handle(4, MAX_NICKNAME_LENGTH)
        self.assertNotEqual(nick1, nick2)
        bot1 = PrateBot([my_room], nick1, 'cinqcent.local', 6667, my_rsa_key1)
        bot2 = PrateBot([my_room], nick2, 'cinqcent.local', 6667, my_rsa_key2)
        while not (bot1.connected_and_joined and bot2.connected_and_joined):
            sleep(1)
        sleep(10)
        self.assertTrue(bot1.is_handshook_with(bot2.my_pubkey))
        self.assertTrue(bot2.is_handshook_with(bot1.my_pubkey))
        the_message = get_word_salad()[:MAX_CRYPTO_MSG_LENGTH]
        bot1.put(bot1.nickname, the_message)
        self.assertEqual(bot1.get(timeout=30), (bot1.nickname, the_message))
        self.assertEqual(bot1.homies[nick2].fernetkey, bot2.homies[nick1].fernetkey)
        self.assertEqual(bot2.homies[nick1].fernetkey, bot1.homies[nick2].fernetkey)
        bot1.quit()
        bot2.quit()


class TestPlaintextStuff(unittest.TestCase):

    def testSimpleSendAndReceivePlaintext(self):
        my_room = '#pratelick'
        nick1 = generate_irc_handle(4, MAX_NICKNAME_LENGTH)
        nick2 = generate_irc_handle(4, MAX_NICKNAME_LENGTH)
        self.assertNotEqual(nick1, nick2)
        bot1 = PrateBot([my_room], nick1, 'cinqcent.local', 6667, my_rsa_key1)
        bot2 = PrateBot([my_room], nick2, 'cinqcent.local', 6667, my_rsa_key2)
        if not (bot1.is_handshook_with(bot2.my_pubkey) and bot2.is_handshook_with(bot1.my_pubkey)):
            sleep(10)
        self.assertTrue(bot1.is_handshook_with(bot2.my_pubkey))  # ...which implies bot1.connected_and_joined is True
        self.assertTrue(bot2.is_handshook_with(bot1.my_pubkey))  # ...which implies bot2.connected_and_joined is True
        self.assertTrue(bot1.empty())
        self.assertTrue(bot2.empty())
        for i in range(0, 10):
            print("Loop %d" % i)
            t = datetime.datetime.now()
            msg_to_send = "HELLO " + generate_random_alphanumeric_string(10)
            bot1.put(nick2, msg_to_send)
            u = datetime.datetime.now()
            print("It took %1.4f seconds to send block" % float((u - t).microseconds / 1000000))
            sender, sentmsg = bot2.get()
            v = datetime.datetime.now()
            print("It took %1.4f seconds to recv block" % float((v - u).microseconds / 1000000))
            self.assertEqual(sender, nick1)
            self.assertEqual(sentmsg, msg_to_send)
        bot1.quit()
        bot2.quit()

    def testSimpleSendAndReceiveCiphertext(self):
        my_room = '#pratelwqj'
        nick1 = generate_irc_handle(4, MAX_NICKNAME_LENGTH)
        nick2 = generate_irc_handle(4, MAX_NICKNAME_LENGTH)
        self.assertNotEqual(nick1, nick2)
        bot1 = PrateBot([my_room], nick1, 'cinqcent.local', 6667, my_rsa_key1)
        bot2 = PrateBot([my_room], nick2, 'cinqcent.local', 6667, my_rsa_key2)
        if not (bot1.is_handshook_with(bot2.my_pubkey) and bot2.is_handshook_with(bot1.my_pubkey)):
            sleep(10)
        self.assertTrue(bot1.is_handshook_with(bot2.my_pubkey))
        self.assertTrue(bot2.is_handshook_with(bot1.my_pubkey))
        for i in range(0, 10):
            print("Loop %d" % i)
            t = datetime.datetime.now()
            msg_to_send = "HELLO " + generate_random_alphanumeric_string(10)
            byteblock_to_send = base64.b85encode(msg_to_send.encode())
            bot1.crypto_put(nick2, byteblock_to_send)
            u = datetime.datetime.now()
            print("It took %1.4f seconds to send block" % float((u - t).microseconds / 1000000))
            sender, sent_bb = bot2.crypto_get()
            v = datetime.datetime.now()
            print("It took %1.4f seconds to recv block" % float((v - u).microseconds / 1000000))
            self.assertEqual(sender, nick1)
            self.assertEqual(sent_bb, byteblock_to_send)
            self.assertEqual(base64.b85decode(sent_bb).decode(), msg_to_send)
        bot1.quit()
        bot2.quit()


class TestNewHandshakingAndTimeoutStuff(unittest.TestCase):

    def testCreateHaremsAndLeaveHaremsWITHHandshaking(self):
        my_room = '#tchalhwh'
        nick1 = generate_irc_handle(MAX_NICKNAME_LENGTH, MAX_NICKNAME_LENGTH)
        nick2 = generate_irc_handle(MAX_NICKNAME_LENGTH, MAX_NICKNAME_LENGTH)
        self.assertNotEqual(nick1, nick2)
        bot1 = PrateBot([my_room], nick1, 'cinqcent.local', 6667, my_rsa_key1)  # auto-handshake is True by default
        bot2 = PrateBot([my_room], nick2, 'cinqcent.local', 6667, my_rsa_key2)
        self.assertEqual(bot1.connected_and_joined, True)
        self.assertEqual(bot2.connected_and_joined, True)
        bot1.quit()
        bot2.quit()
        # self.assertTrue([self.bots[k] for k in self.bots if None in [self.bots[k].homies[h].ipaddr for h in self.bots[k].homies]] is not [])
        # self.assertEqual(bot1.handshook, True)

    def testSimpleSendAndReceiveCiphertext(self):
        my_room = '#pratelwqj'
        nick1 = generate_irc_handle(4, MAX_NICKNAME_LENGTH)
        nick2 = generate_irc_handle(4, MAX_NICKNAME_LENGTH)
        self.assertNotEqual(nick1, nick2)
        bot1 = PrateBot([my_room], nick1, 'cinqcent.local', 6667, my_rsa_key1)
        bot2 = PrateBot([my_room], nick2, 'cinqcent.local', 6667, my_rsa_key2)
        while not (bot1.connected_and_joined and bot2.connected_and_joined):
            sleep(1)
        bot1.quit()
        bot2.quit()
        self.assertFalse(bot1.connected)
        self.assertFalse(bot1.joined)
        self.assertFalse(bot2.connected)
        self.assertFalse(bot2.joined)


class TestNewBoringPrateBotLaunchAndQuit(unittest.TestCase):

    def testMakeAndUnmakeTwoPrateBotsMANUALLY(self):
        alices_rsa_key = my_rsa_key1
        bobs_rsa_key = my_rsa_key2
        bot1 = PrateBot(channels=['#prate'], nickname='mac1', irc_server='cinqcent.local', port=6667, rsa_key=alices_rsa_key, startup_timeout=30, maximum_reconnections=2, strictly_nick=True, autoreconnect=True,
                        autohandshake=False)
        self.assertEqual(bot1.connected, True)
        self.assertEqual(bot1.joined, True)
        self.assertEqual(bot1.connected_and_joined, True)
        bot2 = PrateBot(channels=['#prate'], nickname='mac2', irc_server='cinqcent.local', port=6667, rsa_key=bobs_rsa_key, startup_timeout=30, maximum_reconnections=2, strictly_nick=True, autoreconnect=True,
                        autohandshake=False)
        self.assertEqual(bot1.connected, True)
        self.assertEqual(bot1.joined, True)
        self.assertEqual(bot1.connected_and_joined, True)
        self.assertEqual(bot2.connected, True)
        self.assertEqual(bot2.joined, True)
        self.assertEqual(bot2.connected_and_joined, True)
        bot1.trigger_handshaking()
        if not (bot1.is_handshook_with(bot2.my_pubkey) and bot2.is_handshook_with(bot1.my_pubkey)):
            sleep(10)
        self.assertTrue(bot1.is_handshook_with(bot2.my_pubkey))
        self.assertTrue(bot2.is_handshook_with(bot1.my_pubkey))
        bot1.quit()
        bot2.quit()

    def testMakeAndUnmakeTwoPrateBotsAUTOMATICALLY(self):
        alices_rsa_key = my_rsa_key1
        bobs_rsa_key = my_rsa_key2
        bot1 = PrateBot(channels=['#prate'], nickname='mac1', irc_server='cinqcent.local', port=6667, rsa_key=alices_rsa_key, startup_timeout=30, maximum_reconnections=2, strictly_nick=True, autoreconnect=True,
                        autohandshake=True)
        self.assertEqual(bot1.connected, True)
        self.assertEqual(bot1.joined, True)
        self.assertEqual(bot1.connected_and_joined, True)
        bot2 = PrateBot(channels=['#prate'], nickname='mac2', irc_server='cinqcent.local', port=6667, rsa_key=bobs_rsa_key, startup_timeout=30, maximum_reconnections=2, strictly_nick=True, autoreconnect=True,
                        autohandshake=True)
        self.assertEqual(bot1.connected, True)
        self.assertEqual(bot1.joined, True)
        self.assertEqual(bot1.connected_and_joined, True)
        self.assertEqual(bot2.connected, True)
        self.assertEqual(bot2.joined, True)
        self.assertEqual(bot2.connected_and_joined, True)
        if not (bot1.is_handshook_with(bot2.my_pubkey) and bot2.is_handshook_with(bot1.my_pubkey)):
            sleep(10)
        self.assertTrue(bot1.is_handshook_with(bot2.my_pubkey))
        self.assertTrue(bot2.is_handshook_with(bot1.my_pubkey))
        bot1.quit()
        bot2.quit()

    def testMakeAndUnmakeTwoPrateBotsONEMANUALHANDSHAKE(self):
        alices_rsa_key = my_rsa_key1
        bobs_rsa_key = my_rsa_key2
        bot1 = PrateBot(channels=['#prate'], nickname='mac1', irc_server='cinqcent.local', port=6667, rsa_key=alices_rsa_key, startup_timeout=30, maximum_reconnections=2, strictly_nick=True, autoreconnect=True,
                        autohandshake=False)
        self.assertEqual(bot1.connected, True)
        self.assertEqual(bot1.joined, True)
        self.assertEqual(bot1.connected_and_joined, True)
        bot2 = PrateBot(channels=['#prate'], nickname='mac2', irc_server='cinqcent.local', port=6667, rsa_key=bobs_rsa_key, startup_timeout=30, maximum_reconnections=2, strictly_nick=True, autoreconnect=True,
                        autohandshake=False)
        self.assertEqual(bot1.connected, True)
        self.assertEqual(bot1.joined, True)
        self.assertEqual(bot1.connected_and_joined, True)
        self.assertEqual(bot2.connected, True)
        self.assertEqual(bot2.joined, True)
        self.assertEqual(bot2.connected_and_joined, True)
        bot1.trigger_handshaking(bot2.nickname)
        if not (bot1.is_handshook_with(bot2.my_pubkey) and bot2.is_handshook_with(bot1.my_pubkey)):
            sleep(10)
        self.assertTrue(bot1.is_handshook_with(bot2.my_pubkey))
        self.assertTrue(bot2.is_handshook_with(bot1.my_pubkey))
        bot1.quit()
        bot2.quit()

    def testMakeAndUnmakeTwoPrateBotsOTHERMANUALHANDSHAKE(self):
        alices_rsa_key = my_rsa_key1
        bobs_rsa_key = my_rsa_key2
        bot1 = PrateBot(channels=['#prate'], nickname='mac1', irc_server='cinqcent.local', port=6667, rsa_key=alices_rsa_key, startup_timeout=30, maximum_reconnections=2, strictly_nick=True, autoreconnect=True,
                        autohandshake=False)
        self.assertEqual(bot1.connected, True)
        self.assertEqual(bot1.joined, True)
        self.assertEqual(bot1.connected_and_joined, True)
        bot2 = PrateBot(channels=['#prate'], nickname='mac2', irc_server='cinqcent.local', port=6667, rsa_key=bobs_rsa_key, startup_timeout=30, maximum_reconnections=2, strictly_nick=True, autoreconnect=True,
                        autohandshake=False)
        self.assertEqual(bot1.connected, True)
        self.assertEqual(bot1.joined, True)
        self.assertEqual(bot1.connected_and_joined, True)
        self.assertEqual(bot2.connected, True)
        self.assertEqual(bot2.joined, True)
        self.assertEqual(bot2.connected_and_joined, True)
        bot2.trigger_handshaking(bot1.nickname)
        if not (bot1.is_handshook_with(bot2.my_pubkey) and bot2.is_handshook_with(bot1.my_pubkey)):
            sleep(10)
        self.assertTrue(bot1.is_handshook_with(bot2.my_pubkey))
        self.assertTrue(bot2.is_handshook_with(bot1.my_pubkey))
        bot1.quit()
        bot2.quit()

    def testMakeAndUnmakeTwoPrateBotsBOTHMANUALHANDSHAKE(self):
        alices_rsa_key = my_rsa_key1
        bobs_rsa_key = my_rsa_key2
        bot1 = PrateBot(channels=['#prate'], nickname='mac1', irc_server='cinqcent.local', port=6667, rsa_key=alices_rsa_key, startup_timeout=30, maximum_reconnections=2, strictly_nick=True, autoreconnect=True,
                        autohandshake=False)
        self.assertEqual(bot1.connected, True)
        self.assertEqual(bot1.joined, True)
        self.assertEqual(bot1.connected_and_joined, True)
        bot2 = PrateBot(channels=['#prate'], nickname='mac2', irc_server='cinqcent.local', port=6667, rsa_key=bobs_rsa_key, startup_timeout=30, maximum_reconnections=2, strictly_nick=True, autoreconnect=True,
                        autohandshake=False)
        self.assertEqual(bot1.connected, True)
        self.assertEqual(bot1.joined, True)
        self.assertEqual(bot1.connected_and_joined, True)
        self.assertEqual(bot2.connected, True)
        self.assertEqual(bot2.joined, True)
        self.assertEqual(bot2.connected_and_joined, True)
        bot1.trigger_handshaking(bot2.nickname)
        bot2.trigger_handshaking(bot1.nickname)
        if not (bot1.is_handshook_with(bot2.my_pubkey) and bot2.is_handshook_with(bot1.my_pubkey)):
            sleep(10)
        self.assertTrue(bot1.is_handshook_with(bot2.my_pubkey))
        self.assertTrue(bot2.is_handshook_with(bot1.my_pubkey))
        bot1.quit()
        bot2.quit()


if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()

