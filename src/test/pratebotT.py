'''
Created on Feb 9, 2025

@author: mchobbit





'''
import unittest
from my.irctools.jaracorocks.pratebot import PrateBot
from Crypto.PublicKey import RSA
from time import sleep
from my.stringtools import generate_irc_handle, get_word_salad
from my.globals import MAX_PRIVMSG_LENGTH, MAX_NICKNAME_LENGTH
from test.myttlcacheT import generate_random_alphanumeric_string
from random import randint
from _queue import Empty
import datetime
from my.classes.exceptions import MyIrcStillConnectingError


class TestGroupOne(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def testGoofyParams(self):
        my_rsa_key = RSA.generate(2048)
        self.assertRaises(ValueError, PrateBot, None, None, None, None, None)
        self.assertRaises(ValueError, PrateBot, None, 'mac1', 'cinqcent.local', 6667, my_rsa_key)
        self.assertRaises(ValueError, PrateBot, '', 'mac1', 'cinqcent.local', 6667, my_rsa_key)
        self.assertRaises(ValueError, PrateBot, 'missinghash', 'mac1', 'cinqcent.local', 6667, my_rsa_key)
        self.assertRaises(ValueError, PrateBot, '#', 'mac1', 'cinqcent.local', 6667, my_rsa_key)
        self.assertRaises(ValueError, PrateBot, '#roomname with a space in it', 'mac1', 'cinqcent.local', 6667, my_rsa_key)
        self.assertRaises(ValueError, PrateBot, '#impossiblylongimpossiblylongimpossiblylongimpossiblylongimpossiblylongimpossiblylongimpossiblylongimpossiblylongimpossiblylongimpossiblylong', 'mac1', 'cinqcent.local', 6667, my_rsa_key)
        self.assertRaises(ValueError, PrateBot, '#prate', None, 'cinqcent.local', 6667, my_rsa_key)
        self.assertRaises(ValueError, PrateBot, '#prate', '1', 'cinqcent.local', 6667, my_rsa_key)
        self.assertRaises(ValueError, PrateBot, '#prate', ' ', 'cinqcent.local', 6667, my_rsa_key)
        self.assertRaises(ValueError, PrateBot, '#prate', '#', 'cinqcent.local', 6667, my_rsa_key)
        self.assertRaises(ValueError, PrateBot, '#prate', '#a', 'cinqcent.local', 6667, my_rsa_key)
        self.assertRaises(ValueError, PrateBot, '#prate', ' hi', 'cinqcent.local', 6667, my_rsa_key)
        self.assertRaises(ValueError, PrateBot, '#prate', 'hi ', 'cinqcent.local', 6667, my_rsa_key)
        self.assertRaises(ValueError, PrateBot, '#prate', 'hi ', 'cinqcent.local', 6667, my_rsa_key)
        self.assertRaises(ValueError, PrateBot, '#prate', 'mac1', None, 6667, my_rsa_key)
        self.assertRaises(ValueError, PrateBot, '#prate', 'mac1', 'cinqcent dot local', 6667, my_rsa_key)
        self.assertRaises(ValueError, PrateBot, '#prate', 'mac1', 'cinqcent.local', None, my_rsa_key)
        self.assertRaises(ValueError, PrateBot, '#prate', 'mac1', 'cinqcent.local', 'Word up', my_rsa_key)
        self.assertRaises(ValueError, PrateBot, '#prate', 'mac1', 'cinqcent.local', 0, my_rsa_key)
        self.assertRaises(ValueError, PrateBot, '#prate', 'mac1', 'cinqcent.local', 6667, None)
        self.assertRaises(ValueError, PrateBot, '#prate', 'mac1', 'cinqcent.local', 6667, 'blah')
        self.assertRaises(ValueError, PrateBot, '#prate', 'mac1', 'cinqcent.local', 6667, my_rsa_key, startup_timeout=-1)
        self.assertRaises(ValueError, PrateBot, '#prate', 'mac1', 'cinqcent.local', 6667, my_rsa_key, startup_timeout=0)
        self.assertRaises(ValueError, PrateBot, '#prate', 'mac1', 'cinqcent.local', 6667, my_rsa_key, startup_timeout='Blah')

    def testSimpleLogin(self):
        my_rsa_key = RSA.generate(2048)
        bot = PrateBot('#prate', 'mac1', 'cinqcent.local', 6667, my_rsa_key)
        self.assertRaises(MyIrcStillConnectingError, bot.put, "mac1", "HI")
        sleep(2)
        self.assertTrue(bot.ready)
        bot.quit()

    def testReady(self):
        my_rsa_key = RSA.generate(2048)
        bot = PrateBot('#prate', 'mac1', 'cinqcent.local', 6667, my_rsa_key)
        self.assertRaises(MyIrcStillConnectingError, bot.put, "mac1", "HI")
        self.assertEqual(bot.ready, False)
        sleep(5)
        self.assertTrue(bot.ready)
        self.assertTrue(bot.client.ready)
        bot.quit()

    def testSimpleWhois(self):
        my_rsa_key = RSA.generate(2048)
        bot = PrateBot('#prate', 'mac1', 'cinqcent.local', 6667, my_rsa_key)
        self.assertRaises(MyIrcStillConnectingError, bot.put, "mac1", "HI")
        self.assertFalse(bot.ready)
        sleep(2)
        self.assertTrue(bot.ready)
        self.assertTrue(bot.client.ready)
        self.assertEqual(bot.whois('mac1').split('* ', 1)[-1], bot.client.realname)
        bot.quit()

    def testSimpleCallResponse(self):
        my_rsa_key = RSA.generate(2048)
        bot = PrateBot('#prate', 'mac1', 'cinqcent.local', 6667, my_rsa_key)
        sleep(2)
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
        my_room = '#' + generate_irc_handle(7, 9)
        bot1 = PrateBot(my_room, nick1, 'cinqcent.local', 6667, my_rsa_key1)
        bot2 = PrateBot(my_room, nick2, 'cinqcent.local', 6667, my_rsa_key2)
        while not (bot1.ready and bot2.ready):
            sleep(.1)
        shouldbe = [nick1, nick2]
        actuallyis = bot1.users
        shouldbe.sort()
        actuallyis.sort()
        self.assertEqual(shouldbe, actuallyis)

    def testTwoBots(self):
        my_room = '#' + generate_irc_handle(7, 9)
        nick1 = generate_irc_handle(4, MAX_NICKNAME_LENGTH)
        nick2 = generate_irc_handle(4, MAX_NICKNAME_LENGTH)
        self.assertNotEqual(nick1, nick2)
        my_rsa_key1 = RSA.generate(2048)
        my_rsa_key2 = RSA.generate(2048)
        bot1 = PrateBot(my_room, nick1, 'cinqcent.local', 6667, my_rsa_key1)
        bot2 = PrateBot(my_room, nick2, 'cinqcent.local', 6667, my_rsa_key2)
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
            my_room = '#' + generate_irc_handle(6, 9)
            if not nick1:
                nick1 = generate_irc_handle(4, MAX_NICKNAME_LENGTH)
            if not nick2:
                nick2 = generate_irc_handle(4, MAX_NICKNAME_LENGTH)
            self.assertNotEqual(nick1, nick2)
            my_rsa_key1 = RSA.generate(2048)
            my_rsa_key2 = RSA.generate(2048)
            bot1 = PrateBot(my_room, nick1, 'cinqcent.local', 6667, my_rsa_key1)
            bot2 = PrateBot(my_room, nick2, 'cinqcent.local', 6667, my_rsa_key2)
            sleep(3)
            self.assertTrue(bot1.ready)
            self.assertTrue(bot2.ready)
            assert(len(bot1.nickname) <= MAX_NICKNAME_LENGTH)
            assert(len(bot2.nickname) <= MAX_NICKNAME_LENGTH)
            bot1.put(bot1.nickname, msg)
            retvals = bot1.get(timeout=5)
            self.assertEqual(retvals, (bot1.nickname, msg))
            bot1.quit()
            bot2.quit()

        self.assertRaises(ValueError, send_test_msg, None)
        self.assertRaises(ValueError, send_test_msg, b'h9in0x')
        self.assertRaises(ValueError, send_test_msg, 3)
        self.assertRaises(ValueError, send_test_msg, '')
        self.assertRaises(ValueError, send_test_msg, generate_random_alphanumeric_string(MAX_PRIVMSG_LENGTH + 2))
        self.assertRaises(ValueError, send_test_msg, generate_random_alphanumeric_string(MAX_PRIVMSG_LENGTH + 1))
        for _ in range(0, 10):
            self.assertRaises(ValueError, send_test_msg, generate_random_alphanumeric_string(MAX_PRIVMSG_LENGTH))
        send_test_msg(generate_random_alphanumeric_string(MAX_PRIVMSG_LENGTH - 10), 'abcde%d' % randint(1000, 9999))

    def testSendGoofyValues(self):
        my_room = '#' + generate_irc_handle(7, 9)
        nick1 = generate_irc_handle(4, MAX_NICKNAME_LENGTH)
        nick2 = generate_irc_handle(4, MAX_NICKNAME_LENGTH)
        self.assertNotEqual(nick1, nick2)
        my_rsa_key1 = RSA.generate(2048)
        my_rsa_key2 = RSA.generate(2048)
        bot1 = PrateBot(my_room, nick1, 'cinqcent.local', 6667, my_rsa_key1)
        bot2 = PrateBot(my_room, nick2, 'cinqcent.local', 6667, my_rsa_key2)
        while not (bot1.ready and bot2.ready):
            sleep(.1)
        bot1.quit()
        bot2.quit()

    def testDifferentRooms(self):
        nick1 = generate_irc_handle(7, 9)
        nick2 = generate_irc_handle(7, 9)
        room1 = '#' + generate_irc_handle(4, MAX_NICKNAME_LENGTH)
        room2 = '#' + generate_irc_handle(4, MAX_NICKNAME_LENGTH)
        self.assertNotEqual(nick1, nick2)
        my_rsa_key1 = RSA.generate(2048)
        my_rsa_key2 = RSA.generate(2048)
        bot1 = PrateBot(room1, nick1, 'cinqcent.local', 6667, my_rsa_key1)
        bot2 = PrateBot(room2, nick2, 'cinqcent.local', 6667, my_rsa_key2)
        while not (bot1.ready and bot2.ready):
            sleep(.1)
        self.assertEqual(bot1.nickname, nick1)
        self.assertEqual(bot2.nickname, nick2)
        bot1.quit()
        bot2.quit()

    def testNicknameCollision(self):
        desired_nick = generate_irc_handle(4, MAX_NICKNAME_LENGTH)
        my_rsa_key = RSA.generate(2048)
        bot1 = PrateBot('#prate', desired_nick, 'cinqcent.local', 6667, my_rsa_key)
        sleep(1)
        bot2 = PrateBot('#prate', desired_nick, 'cinqcent.local', 6667, my_rsa_key)
        sleep(2)
        self.assertTrue(bot1.ready)
        self.assertTrue(bot2.ready)
        self.assertEqual(bot1.nickname, desired_nick)
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
        room1 = '#' + generate_irc_handle(5, 9)
        room2 = '#' + generate_irc_handle(5, 9)
        self.assertNotEqual(nick1, nick2)
        my_rsa_key1 = RSA.generate(2048)
        my_rsa_key2 = RSA.generate(2048)
        bot1 = PrateBot(room1, nick1, 'cinqcent.local', 6667, my_rsa_key1)
        bot2 = PrateBot(room2, nick2, 'cinqcent.local', 6667, my_rsa_key2)
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

    def testSendingSameMessageTwice_parttwo(self):
        nick1 = generate_irc_handle(4, MAX_NICKNAME_LENGTH)
        nick2 = generate_irc_handle(4, MAX_NICKNAME_LENGTH)
        room1 = '#' + generate_irc_handle(7, 9)
        room2 = '#' + generate_irc_handle(7, 9)
        self.assertNotEqual(nick1, nick2)
        my_rsa_key1 = RSA.generate(2048)
        my_rsa_key2 = RSA.generate(2048)
        bot1 = PrateBot(room1, nick1, 'cinqcent.local', 6667, my_rsa_key1)
        bot2 = PrateBot(room2, nick2, 'cinqcent.local', 6667, my_rsa_key2)
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
        bot1 = PrateBot('#prate', 'mac1', 'cinqcent.local', 6667, my_rsa_key1)
        bot2 = PrateBot('#prate', 'mac2', 'cinqcent.local', 6667, my_rsa_key2)
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
        noofbots = 5
        for botno in range(0, noofbots):
            nick = 'mac%d' % botno
            dct[nick] = {}
            dct[nick]['rsa key'] = RSA.generate(2048)
            dct[nick]['pratebot'] = PrateBot('#prate', nick, 'cinqcent.local', 6667, dct[nick]['rsa key'])
        while [dct[r]['pratebot'].ready for r in dct].count(False) > 0:
            sleep(1)
        all_found = False
        while not all_found:
            sleep(5)
            all_found = True
            for y in range(0, noofbots):
                for x in range(0, noofbots):
                    nickX = 'mac%d' % x
                    nickY = 'mac%d' % y
                    if nickX == nickY:
                        continue
                    if dct[nickX]['pratebot'].homies[nickY].ipaddr is None:
                        all_found = False
        print("Great. We have all the IP addresses.")
        for k in dct:
            dct[k]['pratebot'].quit()


if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
