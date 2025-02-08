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
from my.irctools.jaracorocks.vanilla import BotForDualQueuedSingleServerIRCBotWithWhoisSupport
desired_nickname = 'mac2'
my_irc_server = 'cinqcent.local'
my_channel = '#prate'
my_port = 6667
bot = BotForDualQueuedSingleServerIRCBotWithWhoisSupport(my_channel, desired_nickname, my_irc_server, my_port)
while not bot.ready:
    sleep(1)

bot.put("mac1", "WORD")
bot.get()

"""

import sys
from threading import Thread

# from my.classes.readwritelock import ReadWriteLock
from random import randint, shuffle
from Crypto.PublicKey import RSA
from my.stringtools import generate_irc_handle
from my.classes.exceptions import MyIrcFingerprintMismatchCausedByServer, MyIrcInitialConnectionTimeoutError
from my.irctools.jaracorocks.vanilla import BotForDualQueuedSingleServerIRCBotWithWhoisSupport
from time import sleep
# from my.globals import JOINING_IRC_SERVER_TIMEOUT, PARAGRAPH_OF_ALL_IRC_NETWORK_NAMES


class PrateBot(BotForDualQueuedSingleServerIRCBotWithWhoisSupport):

    def __init__(self, channel, nickname, irc_server, port, rsa_key,
                 startup_timeout=40, maximum_reconnections=None):
        super().__init__(channel, nickname, irc_server, port, startup_timeout, maximum_reconnections)
        self.rsa_key = rsa_key
        assert(not hasattr(self, '_bot_start'))
        assert(not hasattr(self, '__my_main_thread'))
        self.__my_main_thread = Thread(target=self._bot_loop, daemon=True)
        self.__my_main_thread.start()

    def _bot_loop(self):
        print("_start() --- started")
        while not self.should_we_quit:
            sleep(.1)
            # Process incoming/outgoing messages, for interfacing with our homies
        print("Quitting. Huzzah.")
        # self.join() # TODO: Do I need this?


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
        failures = lambda: [k for k in self.bots if self.bots[k].noof_reconnections >= 3 and not self.bots[k].client]
        successes = lambda: [k for k in self.bots if self.bots[k].client and self.bots[k].client.joined]
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
                                   irc_server=k,
                                   port=self.port,
                                   rsa_key=self.rsa_key)
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

    my_rsa_key = RSA.generate(2048)
    bot = PrateBot(my_channel, desired_nickname, my_irc_server, my_port, my_rsa_key)
    while not bot.ready:
        sleep(1)

