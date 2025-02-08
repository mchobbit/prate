# -*- coding: utf-8 -*-
"""Example Google style docstrings.

Created on Jan 30, 2025

@author: mchobbit

This module contains classes for creating a Prate class that monitors the IRC
server and sets up secure comms between users.

Todo:
    * Better docs
    * Detect if users' nicknames change
    * Make the users' dictionary threadsafe
    * Make the entire class threadsafe
    * Use the public keys' fingerprints, not the users' nicknames, as the key for the dictionary
    * Turn the users' dictionary into a class
    * Auto-check the nicknames whenever using a dictionary entry

.. _Google Python Style Guide:
   http://google.github.io/styleguide/pyguide.html

.. _Napoleon Style Guide:
   https://sphinxcontrib-napoleon.readthedocs.io/en/latest/example_google.html

Example:

from Crypto.PublicKey import RSA
from pratebot16 import *
import queue
desired_nickname = 'mac1'
my_irc_server = 'cinqcent.local'
my_channel = '#prate'
rx_q = queue.LifoQueue()
tx_q = queue.LifoQueue()
my_rsa_key = RSA.generate(2048)
bot = PrateBot(channel=my_channel, nickname=desired_nickname,
                rsa_key=my_rsa_key,
                irc_server=my_irc_server,
                port=6667,
                startup_timeout=30)

"""

import sys
from time import sleep
from threading import Thread

from my.classes.readwritelock import ReadWriteLock
from _queue import Empty
from random import randint, choice, shuffle
from Crypto.PublicKey import RSA
from my.irctools.jaracorocks import PersistentCryptoOrientedSingleServerIRCBotWithWhoisSupport
from queue import LifoQueue
from my.stringtools import generate_irc_handle
from my.classes.exceptions import MyIrcFingerprintMismatchCausedByServer, MyIrcInitialConnectionTimeoutError
from my.globals import JOINING_IRC_SERVER_TIMEOUT
# from my.globals import JOINING_IRC_SERVER_TIMEOUT, PARAGRAPH_OF_ALL_IRC_NETWORK_NAMES


class PrateBot:

    def __init__(self, channel, nickname, rsa_key, irc_server, port, startup_timeout,
                 maximum_reconnections=None):
        self.__startup_timeout = startup_timeout
        self.__crypto_rx_queue = LifoQueue()
        self.__crypto_tx_queue = LifoQueue()
        self.channel = channel
        self.nickname = nickname
        self.rsa_key = rsa_key
        self.irc_server = irc_server
        self.port = port
        self.svr = None  # Set by self.maintain_server_connection()
        self.__maximum_reconnections = maximum_reconnections
        self.__time_to_quit = False
        self.__autoreconnect = True  # Set to False to suspend autoreconnection. Set to True to resume autoreconnecting.
        self.noof_reconnections = 0  # FIXME: not threadsafe
        self.__my_main_thread = Thread(target=self._start, daemon=True)
        self.__my_main_thread.start()

    @property
    def startup_timeout(self):
        return self.__startup_timeout

    @property
    def crypto_rx_queue(self):
        return self.__crypto_rx_queue

    @property
    def crypto_tx_queue(self):
        return self.__crypto_tx_queue

    def _start(self):
        while not self.time_to_quit and (self.maximum_reconnections is None or self.noof_reconnections < self.maximum_reconnections):
            sleep(1)
            if self.svr is None and self.autoreconnect:
                self.reconnect_server_connection()  # If its fingerprint is wonky, quit&reconnect.
#           self.process_data_input_and_output()  # if self.svr and self.svr.ready [not written yet] :)
        if self.maximum_reconnections is not None and self.noof_reconnections >= self.maximum_reconnections:
            print("We've reconnected %d times. That's enough. It's over. This connection has died and I'll not resurrect it. Instead, I'll wait until this bot is told to quit; then, I'll exit/join/whatever.")
        while not self.time_to_quit:
            sleep(1)
        print("Quitting. Huzzah.")

    @property
    def autoreconnect(self):
        return self.__autoreconnect

    @autoreconnect.setter
    def autoreconnect(self, value):  # FIXME: not threadsafe
        self.__autoreconnect = value

    @property
    def time_to_quit(self):
        return self.__time_to_quit

    @time_to_quit.setter
    def time_to_quit(self, value):  # FIXME: not threadsafe
        self.__time_to_quit = value

    @property
    def maximum_reconnections(self):
        return self.__maximum_reconnections

    def reconnect_server_connection(self):
        while self.svr is None and self.autoreconnect:
            try:
                print("*** CONNECTING TO %s AS %s ***" % (self.irc_server, self.nickname))
                self.generate_new_svr()
            except MyIrcFingerprintMismatchCausedByServer:
                print("svr changed my nickname, thus making my fingerprint out of date.")
            except MyIrcInitialConnectionTimeoutError:
                print("Timed out while trying to connect to server.")
            if self.svr is None or self.svr.fingerprint != self.svr.realname or self.svr.nickname != self.nickname:
                if self.svr is None:
                    print("%s timed out." % self.irc_server)
                else:
                    print("%s changed my nickname and didn't tell me. I must disconnect and reconnect, so as to refresh my fingerprint." % self.irc_server)
                    try:
                        self.svr.disconnect("Bye")
                    except Exception as e:
                        print("Exception occurred (which we shall ignore):", e)
                    self.svr.shut_down_threads()
#                del self.svr  # Is this necessary?
                    self.svr = None
                    self.nickname = "%s%d" % (generate_irc_handle(), randint(1000, 9999))
            elif not self.svr.ready:
                print("Waiting for svr to be ready")
                sleep(1)
            elif self.channel not in self.svr.channels:
                print("WARNING -- we dropped out of %s" % self.channel)
                self.svr.connection.join(self.channel)
            else:
                pass

    def quit(self):  # Do we need this?
        """Quit this bot."""
        self.autoreconnect = False
        self.time_to_quit = True
        if self.svr:
            self.svr.shut_down_threads()
        self.__my_main_thread.join()  # print("Joining server thread")

    def generate_new_svr(self):
        self.noof_reconnections += 1
        self.svr = PersistentCryptoOrientedSingleServerIRCBotWithWhoisSupport(
            channel=self.channel,
            nickname=self.nickname,
            rsa_key=self.rsa_key,
            is_pubkey_in_realname=False,
            irc_server=self.irc_server,
            port=self.port,
            crypto_rx_queue=self.crypto_rx_queue,
            crypto_tx_queue=self.crypto_tx_queue,
            startup_timeout=self.startup_timeout)


class HaremOfBots:
# Eventually, make it threaded!

    def __init__(self, channel, list_of_all_irc_servers, rsa_key, harem_rx_queue, harem_tx_queue):
        max_nickname_length = 9
        self.__harem_rx_queue = harem_rx_queue
        self.__harem_tx_queue = harem_tx_queue
        self.__channel = channel
        self.__rsa_key = rsa_key
        self.__list_of_all_irc_servers = list_of_all_irc_servers
        self.__desired_nickname = "%s%d" % (generate_irc_handle(max_nickname_length - 3, max_nickname_length - 3), randint(111, 999))
        self.port = 6667
        self.bots = {}

    @property
    def list_of_all_irc_servers(self):
        return self.__list_of_all_irc_servers

    @property
    def channel(self):
        return self.__channel

    @property
    def rsa_key(self):
        return self.__rsa_key

    @property
    def desired_nickname(self):
        return self.__desired_nickname

    @property
    def harem_rx_queue(self):
        return self.__harem_rx_queue

    @property
    def harem_tx_queue(self):
        return self.__harem_tx_queue

    def log_into_all_functional_IRC_servers(self):
        shuffle(self.list_of_all_irc_servers)
        print("Trying all IRC servers")
        for k in self.list_of_all_irc_servers:
            print("Trying", k)
            self.try_to_log_into_this_IRC_server(k)
        failures = lambda: [k for k in self.bots if self.bots[k].noof_reconnections >= 3 and not self.bots[k].svr]
        successes = lambda: [k for k in self.bots if self.bots[k].svr and self.bots[k].svr.joined]
        while len(failures()) + len(successes()) < len(self.bots):
            sleep(1)
        for k in list(failures()):
            print("Deleting", k)
            self.bots[k].autoreconnect = False
            self.bots[k].quit()
            del self.bots[k]
        print("Huzzah. We are logged into %d functional IRC servers." % len(self.bots))

    def try_to_log_into_this_IRC_server(self, k):
        try:
            self.bots[k] = PrateBot(channel=self.channel,
                                   nickname=self.desired_nickname,
                                   rsa_key=self.rsa_key,
                                   irc_server=k,
                                   port=self.port,
                                   startup_timeout=JOINING_IRC_SERVER_TIMEOUT)
        except (MyIrcInitialConnectionTimeoutError, MyIrcFingerprintMismatchCausedByServer):
            self.bots[k] = None


if __name__ == "__main__":
    if len(sys.argv) != 5:
#        print("Usage: %s <URL> <port> <channel> <nickname>" % sys.argv[0])
#        sys.exit(1)
        my_irc_server = 'cinqcent.local'
        my_port = 6667
        my_channel = '#prate'
        desired_nickname = 'mac1'
    else:
        my_irc_server = sys.argv[1]
        my_port = int(sys.argv[2])
        my_channel = sys.argv[3]
        desired_nickname = sys.argv[4]

    my_crypto_rx_queue = LifoQueue()
    my_crypto_tx_queue = LifoQueue()
    my_rsa_key = RSA.generate(2048)
    bot = PrateBot(my_channel, desired_nickname, my_rsa_key,
                   my_irc_server, my_port,
                   startup_timeout=JOINING_IRC_SERVER_TIMEOUT)
    while True:
        sleep(1)
        if bot.svr is None:
            continue
        bot.svr.show_users_dct_info(True if randint(0, 10) == 0 else False)
        try:
            u = choice(list(bot.svr.homies.keys()))
        except IndexError:
            pass
        else:
            if bot.svr.homies[u].ipaddr is not None and randint(0, 10) == 0:
                bot.crypto_tx_queue.put((u, ('HELLO from %s to %s' % (bot.svr.nickname, u)).encode()))
            try:
                while True:
                    the_user, the_blk = bot.crypto_rx_queue.get_nowait()
                    assert("HELLO from" in the_blk.decode())
                    print(the_user, "==>", the_blk)
            except Empty:
                pass

