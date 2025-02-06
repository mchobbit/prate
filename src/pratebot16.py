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
from pratebot13 import *
desired_nickname = 'mac1'
my_irc_server = 'cinqcent.local'
my_channel = '#prate'
from pratebot13 import *
rx_q = queue.LifoQueue()
tx_q = queue.LifoQueue()
my_rsa_key = RSA.generate(2048)
svr = PrateBot(channel=my_channel, nickname=desired_nickname,rsa_key=my_rsa_key,
                is_pubkey_in_realname=False,
                irc_server=my_irc_server, port=6667,
                crypto_rx_queue=rx_q, crypto_tx_queue=tx_q)

"""

import sys
from time import sleep
from threading import Thread

from my.classes.readwritelock import ReadWriteLock
from _queue import Empty
from random import randint, choice
from my.classes.exceptions import MyIrcFingerprintMismatchCausedByServer
from Crypto.PublicKey import RSA
from my.irctools.jaracorocks import PersistentCryptoOrientedSingleServerIRCBotWithWhoisSupport
from queue import LifoQueue


class PrateBot:

    def __init__(self, channel, nickname, rsa_key, irc_server, port):
        self.c_rx_q = LifoQueue()
        self.c_tx_q = LifoQueue()
        self.channel = channel
        self.nickname = nickname
        self.rsa_key = rsa_key
        self.irc_server = irc_server
        self.port = port
        self.svr = None
        self.__time_to_quit = False
        self.__my_main_thread = Thread(target=self._start, daemon=True)
        self.__my_main_thread.start()

    def _start(self):
        old_nick = self.nickname
        while not self.__time_to_quit:
            sleep(.1)
            if self.svr is None:
                try:
                    print("*** CONNECTING AS %s ***" % self.nickname)
                    self.generate_new_svr()
                except MyIrcFingerprintMismatchCausedByServer:
                    print("svr changed my nickname, thus making my fingerprint out of date.")
            if self.svr is None or self.svr.fingerprint != self.svr.realname or self.svr.nickname != self.nickname:
                print("The svr changed my nickname and didn't tell me. I must disconnect and reconnect, so as to refresh my fingerprint.")
                if self.svr:
                    try:
                        self.svr.disconnect("Bye")
                    except Exception as e:
                        print("Exception occurred (which we shall ignore):", e)
                    self.svr.shut_down_threads()
                del self.svr  # Is this necessary?
                self.svr = None
                self.nickname = "%s%d" % (old_nick, randint(0, 9))
                old_nick = self.nickname
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
        self.__time_to_quit = True
        self.__my_main_thread.join()  # print("Joining server thread")

    def generate_new_svr(self):
        self.svr = PersistentCryptoOrientedSingleServerIRCBotWithWhoisSupport(
            channel=self.channel,
            nickname=self.nickname,
            rsa_key=self.rsa_key,
            is_pubkey_in_realname=False,
            irc_server=self.irc_server,
            port=self.port,
            crypto_rx_queue=self.c_rx_q, crypto_tx_queue=self.c_tx_q)

##########################################################################################################


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
    bot = PrateBot(my_channel, desired_nickname, my_rsa_key, my_irc_server, my_port)
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
                bot.c_tx_q.put((u, ('HELLO from %s to %s' % (bot.svr.nickname, u)).encode()))
            try:
                while True:
                    the_user, the_blk = bot.c_rx_q.get_nowait()
                    assert("HELLO from" in the_blk.decode())
                    print(the_user, "==>", the_blk)
            except Empty:
                pass
