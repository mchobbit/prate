'''
Created on Feb 9, 2025

@author: mchobbit





'''
import unittest
from Crypto.PublicKey import RSA
from time import sleep
from my.stringtools import generate_irc_handle, get_word_salad
from my.globals import MAX_PRIVMSG_LENGTH, MAX_NICKNAME_LENGTH, MAX_CHANNEL_LENGTH
from test.myttlcacheT import generate_random_alphanumeric_string
from _queue import Empty
from my.irctools.jaracorocks.pratebot import PrateBot
from my.classes.exceptions import IrcBadChannelNameError, IrcBadServerNameError, IrcBadNicknameError, IrcChannelNameTooLongError, IrcNicknameTooLongError, IrcBadServerPortError, \
    PublicKeyBadKeyError, IrcPrivateMessageContainsBadCharsError, IrcStillConnectingError
from my.irctools.jaracorocks.vanilla import BotForDualQueuedFingerprintedSingleServerIRCBotWithWhoisSupport


class TestGroupOne(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def testGoofyParams(self):
        my_rsa_key = RSA.generate(2048)
        self.assertRaises(IrcBadChannelNameError, PrateBot, None, 'mac1', 'cinqcent.local', 6667, my_rsa_key)
        self.assertRaises(IrcBadChannelNameError, PrateBot, [''], 'mac1', 'cinqcent.local', 6667, my_rsa_key)
        self.assertRaises(IrcBadChannelNameError, PrateBot, ['missinghash'], 'mac1', 'cinqcent.local', 6667, my_rsa_key)
        self.assertRaises(IrcBadChannelNameError, PrateBot, ['#'], 'mac1', 'cinqcent.local', 6667, my_rsa_key)
        self.assertRaises(IrcBadChannelNameError, PrateBot, ['#roomname with a space in it'], 'mac1', 'cinqcent.local', 6667, my_rsa_key)
        self.assertRaises(IrcChannelNameTooLongError, PrateBot, ['#impossiblylongimpossiblylongimpossiblylongimpossiblylongimpossiblylongimpossiblylongimpossiblylongimpossiblylongimpossiblylongimpossiblylong'], 'mac1', 'cinqcent.local', 6667, my_rsa_key)
        self.assertRaises(IrcBadNicknameError, PrateBot, ['#prate'], None, 'cinqcent.local', 6667, my_rsa_key)
        self.assertRaises(IrcBadNicknameError, PrateBot, ['#prate'], '1', 'cinqcent.local', 6667, my_rsa_key)
        self.assertRaises(IrcBadNicknameError, PrateBot, ['#prate'], ' ', 'cinqcent.local', 6667, my_rsa_key)
        self.assertRaises(IrcBadNicknameError, PrateBot, ['#prate'], '#', 'cinqcent.local', 6667, my_rsa_key)
        self.assertRaises(IrcBadNicknameError, PrateBot, ['#prate'], '#a', 'cinqcent.local', 6667, my_rsa_key)
        self.assertRaises(IrcBadNicknameError, PrateBot, ['#prate'], ' hi', 'cinqcent.local', 6667, my_rsa_key)
        self.assertRaises(IrcBadNicknameError, PrateBot, ['#prate'], 'hi ', 'cinqcent.local', 6667, my_rsa_key)
        self.assertRaises(IrcBadNicknameError, PrateBot, ['#prate'], 'hi ', 'cinqcent.local', 6667, my_rsa_key)
        self.assertRaises(IrcNicknameTooLongError, PrateBot, ['#prate'], 'hitherefolksomgthisiswaytoolong', 'cinqcent.local', 6667, my_rsa_key)
        self.assertRaises(IrcBadServerNameError, PrateBot, ['#prate'], 'mac1', None, 6667, my_rsa_key)
        self.assertRaises(IrcBadServerNameError, PrateBot, ['#prate'], 'mac1', 'cinqcent dot local', 6667, my_rsa_key)
        self.assertRaises(IrcBadServerPortError, PrateBot, ['#prate'], 'mac1', 'cinqcent.local', None, my_rsa_key)
        self.assertRaises(IrcBadServerPortError, PrateBot, ['#prate'], 'mac1', 'cinqcent.local', 'Word up', my_rsa_key)
        self.assertRaises(IrcBadServerPortError, PrateBot, ['#prate'], 'mac1', 'cinqcent.local', 0, my_rsa_key)
        self.assertRaises(PublicKeyBadKeyError, PrateBot, ['#prate'], 'mac1', 'cinqcent.local', 6667, None)
        self.assertRaises(PublicKeyBadKeyError, PrateBot, ['#prate'], 'mac1', 'cinqcent.local', 6667, 'blah')
        self.assertRaises(ValueError, PrateBot, ['#prate'], 'mac1', 'cinqcent.local', 6667, my_rsa_key, startup_timeout=-1)
        self.assertRaises(ValueError, PrateBot, ['#prate'], 'mac1', 'cinqcent.local', 6667, my_rsa_key, startup_timeout=0)
        self.assertRaises(ValueError, PrateBot, ['#prate'], 'mac1', 'cinqcent.local', 6667, my_rsa_key, startup_timeout='Blah')

    def testSimpleLogin(self):
        my_rsa_key = RSA.generate(2048)
        bot = PrateBot(['#prate'], 'mac1', 'cinqcent.local', 6667, my_rsa_key)
        self.assertRaises(IrcStillConnectingError, bot.put, "mac1", "HI")
        while not bot.ready:
            print("Waiting for bot to be ready")
            sleep(1)
        self.assertTrue(bot.ready)
        bot.quit()

    def testReady(self):
        my_rsa_key = RSA.generate(2048)
        bot = PrateBot(['#prate'], 'mac1', 'cinqcent.local', 6667, my_rsa_key)
        self.assertRaises(IrcStillConnectingError, bot.put, "mac1", "HI")
        self.assertEqual(bot.ready, False)
        while not bot.ready:
            print("Waiting for bot to be ready")
            sleep(1)
        self.assertTrue(bot.ready)
        self.assertTrue(bot.client.ready)
        bot.quit()

    def testSimpleWhois(self):
        my_rsa_key = RSA.generate(2048)
        bot = PrateBot(['#prate'], 'mac1', 'cinqcent.local', 6667, my_rsa_key)
        self.assertRaises(IrcStillConnectingError, bot.put, "mac1", "HI")
        self.assertFalse(bot.ready)
        while not bot.ready:
            print("Waiting for bot to be ready")
            sleep(1)
        self.assertTrue(bot.ready)
        self.assertTrue(bot.client.ready)
        self.assertEqual(bot.whois('mac1').split('* ', 1)[-1], bot.client.realname)
        bot.quit()

    def testSimpleCallResponse(self):
        my_rsa_key = RSA.generate(2048)
        bot = PrateBot(['#prate'], 'mac1', 'cinqcent.local', 6667, my_rsa_key)
        while not bot.ready:
            print("Waiting for bot to be ready")
            sleep(1)
        self.assertTrue(bot.ready)
        self.assertTrue(bot.client.ready)
        bot.put(bot.nickname, "HELLO")
        sleep(1)
        self.assertEqual(bot.get_nowait(), (bot.nickname, 'HELLO'))


class TestGroupTwo(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def testRoomMembership(self):
        nick1 = generate_irc_handle(4, MAX_NICKNAME_LENGTH)
        nick2 = generate_irc_handle(4, MAX_NICKNAME_LENGTH)
        self.assertNotEqual(nick1, nick2)
        my_rsa_key1 = RSA.generate(2048)
        my_rsa_key2 = RSA.generate(2048)
        my_room = '#T' + generate_random_alphanumeric_string(MAX_CHANNEL_LENGTH - 2)
        bot1 = PrateBot([my_room], nick1, 'cinqcent.local', 6667, my_rsa_key1)
        bot2 = PrateBot([my_room], nick2, 'cinqcent.local', 6667, my_rsa_key2)
        while not (bot1.ready and bot2.ready):
            sleep(.1)
        sleep(5)
        shouldbe = [nick1, nick2]
        actuallyis = bot1.users
        shouldbe.sort()
        actuallyis.sort()
        self.assertEqual(shouldbe, actuallyis)
        bot1.quit()
        bot2.quit()

    def testTwoBots(self):
        my_room = '#prate'  # + generate_irc_handle(7, 9)
        nick1 = generate_irc_handle(4, MAX_NICKNAME_LENGTH)
        nick2 = generate_irc_handle(4, MAX_NICKNAME_LENGTH)
        self.assertNotEqual(nick1, nick2)
        my_rsa_key1 = RSA.generate(2048)
        my_rsa_key2 = RSA.generate(2048)
        bot1 = PrateBot([my_room], nick1, 'cinqcent.local', 6667, my_rsa_key1)
        bot2 = PrateBot([my_room], nick2, 'cinqcent.local', 6667, my_rsa_key2)
        while not (bot1.ready and bot2.ready):
            sleep(.1)
        the_message = get_word_salad()[:400]
        bot1.put(bot1.nickname, the_message)
        sleep(1)
        self.assertEqual(bot1.get_nowait(), (bot1.nickname, the_message))
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
            my_rsa_key1 = RSA.generate(2048)
            my_rsa_key2 = RSA.generate(2048)
            try:
                bot1 = PrateBot([my_room], nick1, 'cinqcent.local', 6667, my_rsa_key1)
                bot1.paused = True
                bot2 = PrateBot([my_room], nick2, 'cinqcent.local', 6667, my_rsa_key2)
                bot2.paused = True
                sleep(3)
                self.assertTrue(bot1.ready)
                self.assertTrue(bot2.ready)
                assert(len(bot1.nickname) <= MAX_NICKNAME_LENGTH)
                assert(len(bot2.nickname) <= MAX_NICKNAME_LENGTH)
                bot1.put(bot1.nickname, msg)
                retvals = bot1.get(timeout=5)
                self.assertEqual(retvals, (bot1.nickname, msg))
            finally:
                bot1.quit()
                bot2.quit()

        self.assertRaises(IrcPrivateMessageContainsBadCharsError, send_test_msg, b'h9in0x')
        self.assertRaises(IrcPrivateMessageContainsBadCharsError, send_test_msg, None)
        self.assertRaises(IrcPrivateMessageContainsBadCharsError, send_test_msg, 3)
        self.assertRaises(IrcPrivateMessageContainsBadCharsError, send_test_msg, '')
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
        my_rsa_key1 = RSA.generate(2048)
        my_rsa_key2 = RSA.generate(2048)
        bot1 = PrateBot([my_room], nick1, 'cinqcent.local', 6667, my_rsa_key1)
        bot2 = PrateBot([my_room], nick2, 'cinqcent.local', 6667, my_rsa_key2)
        bot1.paused = True
        bot2.paused = True
        while not (bot1.ready and bot2.ready):
            sleep(.1)
        bot1.quit()
        bot2.quit()

    def testDifferentRooms(self):
        nick1 = generate_irc_handle(7, 9)
        nick2 = generate_irc_handle(7, 9)
        room1 = '#T' + generate_random_alphanumeric_string(MAX_CHANNEL_LENGTH - 2)
        room2 = '#T' + generate_random_alphanumeric_string(MAX_CHANNEL_LENGTH - 2)
        self.assertNotEqual(nick1, nick2)
        my_rsa_key1 = RSA.generate(2048)
        my_rsa_key2 = RSA.generate(2048)
        bot1 = PrateBot([room1], nick1, 'cinqcent.local', 6667, my_rsa_key1)
        bot2 = PrateBot([room2], nick2, 'cinqcent.local', 6667, my_rsa_key2)
        bot1.paused = True
        bot2.paused = True
        while not (bot1.ready and bot2.ready):
            sleep(.1)
        self.assertEqual(bot1.nickname, nick1)
        self.assertEqual(bot2.nickname, nick2)
        bot1.quit()
        bot2.quit()

    def testNicknameCollision(self):
        desired_nick = 'A' + generate_random_alphanumeric_string(MAX_NICKNAME_LENGTH - 1)
        my_rsa_key = RSA.generate(2048)
        bot1 = PrateBot(['#prate'], desired_nick, 'cinqcent.local', 6667, my_rsa_key)
        bot1.paused = True
        while not bot1.ready:
            sleep(.1)
        self.assertTrue(bot1.ready)
        self.assertEqual(bot1.nickname, desired_nick)
        bot2 = PrateBot(['#prate'], desired_nick, 'cinqcent.local', 6667, my_rsa_key)
        bot2.paused = True
        while not bot2.ready:
            sleep(.1)
        self.assertTrue(bot2.ready)
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
        msg = generate_random_alphanumeric_string(MAX_PRIVMSG_LENGTH - len(bot2.nickname))
        bot1.put(bot2.nickname, msg)
        self.assertEqual(bot2.get(timeout=5), (bot1.nickname, msg))
        msg = generate_random_alphanumeric_string(MAX_PRIVMSG_LENGTH - len(bot1.nickname))
        bot2.put(bot1.nickname, msg)
        self.assertEqual(bot1.get(timeout=5), (bot2.nickname, msg))
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
        my_rsa_key1 = RSA.generate(2048)
        my_rsa_key2 = RSA.generate(2048)
        bot1 = PrateBot([room1], nick1, 'cinqcent.local', 6667, my_rsa_key1)
        bot2 = PrateBot([room2], nick2, 'cinqcent.local', 6667, my_rsa_key2)
        bot1.paused = True
        bot2.paused = True
        while not (bot1.ready and bot2.ready):
            sleep(.1)
        msg = generate_random_alphanumeric_string(MAX_PRIVMSG_LENGTH - len(nick2))
        bot1.put(bot2.nickname, msg)
        bot1.put(bot2.nickname, "Hello, world.")
        bot1.put(bot2.nickname, msg)
        self.assertEqual(bot2.get(timeout=5), (bot1.nickname, msg))
        self.assertEqual(bot2.get(timeout=5), (bot1.nickname, "Hello, world."))
        sleep(2)
        self.assertRaises(Empty, bot2.get_nowait)
        bot1.quit()
        bot2.quit()

#
    def testSendingSameMessageTwice_parttwo(self):
        nick1 = generate_irc_handle(4, MAX_NICKNAME_LENGTH)
        nick2 = generate_irc_handle(4, MAX_NICKNAME_LENGTH)
        room1 = '#prate'  # + generate_irc_handle(7, 9)
        room2 = '#prate'  # + generate_irc_handle(7, 9)
        self.assertNotEqual(nick1, nick2)
        my_rsa_key1 = RSA.generate(2048)
        my_rsa_key2 = RSA.generate(2048)
        bot1 = PrateBot([room1], nick1, 'cinqcent.local', 6667, my_rsa_key1)
        bot2 = PrateBot([room2], nick2, 'cinqcent.local', 6667, my_rsa_key2)
        bot1.paused = True
        bot2.paused = True
        while not (bot1.ready and bot2.ready):
            sleep(.1)
        msg = generate_random_alphanumeric_string(MAX_PRIVMSG_LENGTH - len(nick2))
        bot1.put(bot2.nickname, msg)
        bot1.put(bot2.nickname, msg)
        bot1.put(bot2.nickname, "Hello, world.")
        sleep(2)
        self.assertEqual(bot2.get(timeout=5), (bot1.nickname, msg))
        self.assertEqual(bot2.get(timeout=5), (bot1.nickname, "Hello, world."))
        sleep(2)
        if bot2.empty():
            pass  # print("Good.")
        else:
            self.assertRaises(Empty, bot2.get_nowait)
        bot1.quit()
        bot2.quit()


class TestKeyExchangingAndHandshaking(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def testOne(self):
        my_rsa_key1 = RSA.generate(2048)
        my_rsa_key2 = RSA.generate(2048)
        bot1 = PrateBot(['#prate'], 'mac1', 'cinqcent.local', 6667, my_rsa_key1)
        bot2 = PrateBot(['#prate'], 'mac2', 'cinqcent.local', 6667, my_rsa_key2)
        while not (bot1.ready and bot2.ready):
            sleep(.1)
        while bot1.homies[bot2.nickname].ipaddr is None and bot2.homies[bot1.nickname].ipaddr is None:
            sleep(.1)
        print("%s: %s" % (bot1.nickname, bot1.homies[bot2.nickname].ipaddr))
        print("%s: %s" % (bot2.nickname, bot1.homies[bot1.nickname].ipaddr))
        bot1.quit()
        bot2.quit()

    def testTwo(self):
        dct = {}
        noofbots = 4
        for _ in range(0, noofbots):
            nick = generate_irc_handle()
            dct[nick] = {}
            dct[nick]['rsa key'] = RSA.generate(2048)
            dct[nick]['pratebot'] = PrateBot(['#prate'], nick, 'cinqcent.local', 6667, dct[nick]['rsa key'])
        while [dct[r]['pratebot'].ready for r in dct].count(False) > 0:
            sleep(1)
        all_found = False
        while not all_found:
            sleep(5)
            all_found = True
            for nickY in dct:
                for nickX in dct:
                    if nickX == nickY:
                        continue
                    if dct[nickX]['pratebot'].homies[nickY].ipaddr is None:
#                        print("%s doesn't know %s's IP address" % (nickX, nickY))
                        all_found = False
        print("Great. We have all the IP addresses.")
        for k in dct:
            dct[k]['pratebot'].quit()


class TestKeyCryptoPutAndCryptoGet(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def testSimpleEncryptedTransferOf100Bytes(self):
        my_rsa_key1 = RSA.generate(2048)
        my_rsa_key2 = RSA.generate(2048)
        bot1 = PrateBot(['#prate'], 'mac1', 'cinqcent.local', 6667, my_rsa_key1)
        bot2 = PrateBot(['#prate'], 'mac2', 'cinqcent.local', 6667, my_rsa_key2)
        while not (bot1.ready and bot2.ready):
            sleep(.1)
        while bot1.homies[bot2.nickname].ipaddr is None or bot2.homies[bot1.nickname].ipaddr is None:
            sleep(.1)
        self.assertTrue(bot1.empty())
        for i in range(0, 10):
#            print("loop", i)
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
        '''
        from Crypto.PublicKey import RSA
        from time import sleep
        from my.stringtools import *
        from random import randint
        from my.irctools.jaracorocks.pratebot import PrateBot
        from my.globals import *
        from my.classes.exceptions import *
        '''
        my_rsa_key1 = RSA.generate(2048)
        my_rsa_key2 = RSA.generate(2048)
        bot1 = PrateBot(['#prate'], 'mac1', 'cinqcent.local', 6667, my_rsa_key1)
        while not bot1.ready:
            sleep(.1)
        lou1 = bot1.users
        lou1.sort()
        bot2 = PrateBot(['#prate'], 'mac2', 'cinqcent.local', 6667, my_rsa_key2)
        while not bot2.ready:
            sleep(.1)
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
        '''
        from Crypto.PublicKey import RSA
        from time import sleep
        from my.stringtools import *
        from random import randint
        from my.irctools.jaracorocks.pratebot import PrateBot
        from my.globals import *
        from my.classes.exceptions import *
        '''
        my_rsa_key1 = RSA.generate(2048)
        my_rsa_key2 = RSA.generate(2048)
        bot1 = PrateBot(['#prate'], 'mac1', 'cinqcent.local', 6667, my_rsa_key1)
        while not bot1.ready:
            sleep(.1)
        lou1 = bot1.users
        sleep(3)
        bot2 = PrateBot(['#prate'], 'mac2', 'cinqcent.local', 6667, my_rsa_key2)
        while not bot2.ready:
            sleep(.1)
#        lou2 = bot2.users
        b1nick = bot1.nickname
        b2nick = bot2.nickname
        sleep(3)
        self.assertTrue(b2nick not in lou1)
        self.assertTrue(b2nick in bot1.users)
        self.assertTrue(b1nick in bot2.users)
        bot1.quit()
        sleep(.5)
        self.assertTrue(b1nick not in bot2.users)
        bot2.quit()

    def testJoiningAndLeavingSeveralDifferentChannels(self):
        my_rsa_key1 = RSA.generate(2048)
        my_rsa_key2 = RSA.generate(2048)
        bot1 = PrateBot(['#prate'], 'mac1', 'cinqcent.local', 6667, my_rsa_key1)
        bot2 = PrateBot(['#prate'], 'mac2', 'cinqcent.local', 6667, my_rsa_key2)
        while not (bot2.ready and bot1.ready):
            sleep(.1)
        bot1.quit()
        bot2.quit()


if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()

