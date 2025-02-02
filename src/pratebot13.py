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

s = 'm&4c;;B32a?eKNjw~g*;$0{=kLOVcOcgu2HzbjBk98m2hvhGq~'
desired_nickname = 'mac1'
desired_fullname = squeeze_da_keez(MY_RSAKEY.public_key())
irc_server = 'cinqcent.local'
from pratebot13 import *
rx_q = queue.LifoQueue()
tx_q = queue.LifoQueue()
svr = PrateBot(channel='#prate', nickname=desired_nickname, realname=desired_fullname,
                irc_server=irc_server, port=6667, crypto_rx_queue=rx_q, crypto_tx_queue=tx_q)

assert(svr.nickname == desired_nickname)
assert(svr.fullname == desired_fullname)



TESTPORPOISES__MAXIMUM_REALNAME_LENGTH_SUPPORTED_BY_SERVER = 20
"""

import sys
import queue
from time import sleep
from threading import Thread, Lock

from cryptography.fernet import Fernet, InvalidToken
import base64
from my.globals import MY_IP_ADDRESS, MY_RSAKEY
from my.classes.readwritelock import ReadWriteLock
from my.irctools.cryptoish import rsa_decrypt, rsa_encrypt, unsqueeze_da_keez, squeeze_da_keez
from _queue import Empty
from random import randint, choice
from my.classes.homies import HomiesDct
from my.classes.exceptions import MyIrcRealnameTruncationError
from my.irctools.jaracorocks.miniircd import CryptoOrientedSingleServerIRCBotWithWhoisSupport


class PrateBot(CryptoOrientedSingleServerIRCBotWithWhoisSupport):
    """A background-threaded CryptoOrientedSingleServerIRCBotWithWhoisSupport.

    This is a subclass of CryptoOrientedSingleServerIRCBotWithWhoisSupport. Its
    primary purpose is to instantiate that class as a background thread. (Do I mean
    'instantiate'?)

    Attributes:
        channel (str): IRC channel to be joined.
        nickname (str): Initial nickname. The real nickname will be changed
            if the IRC server reports a nickname collision.
        irc_server (str): The IRC server URL.
        port (int): The port number of the IRC server.
        crypto_rx_queue (LifoQueue): Decrypted user-and-msg stuff goes here.
        crypto_tx_queue (LifoQueue): User-and-msg stuff to be encrypted goes here.

    """

    def __init__(self, channel, nickname, irc_server, port, crypto_rx_queue, crypto_tx_queue):
        super().__init__(channel, nickname, irc_server, port, crypto_rx_queue, crypto_tx_queue)
        self.__time_to_quit = False
        self.__time_to_quit_lock = ReadWriteLock()
        self.__bot_thread = Thread(target=self.__bot_worker_loop, daemon=True)
        self._start()

    def _start(self):
        self.__bot_thread.start()

    @property
    def time_to_quit(self):
        self.__time_to_quit_lock.acquire_read()
        try:
            retval = self.__time_to_quit
            return retval
        finally:
            self.__time_to_quit_lock.release_read()

    def quit(self):  # Do we need this?
        """Quit this bot."""
        self.__time_to_quit = True
        self.__bot_thread.join()  # print("Joining server thread")

    def __bot_worker_loop(self):
        """Start this bot."""
        print("Starting bot thread")
        self.start()
        print("You should not get here.")
        while not self.__time_to_quit:
            sleep(1)

##########################################################################################################


if __name__ == "__main__":
    if len(sys.argv) != 5:
        print("Usage: %s <URL> <port> <channel> <nickname>" % sys.argv[0])
        sys.exit(1)
    else:
        my_irc_server = sys.argv[1]
        my_port = int(sys.argv[2])
        my_channel = sys.argv[3]
        desired_nickname = sys.argv[4]

    rx_q = queue.LifoQueue()
    tx_q = queue.LifoQueue()
    svr = PrateBot(channel=my_channel, nickname=desired_nickname,
                                       irc_server=my_irc_server, port=my_port,
                                       crypto_rx_queue=rx_q, crypto_tx_queue=tx_q)

    while not svr.ready:
        sleep(.1)
    if svr.realname != svr.desired_realname:
        raise MyIrcRealnameTruncationError("Realname was truncated from %d chars to only %d chars by server." %
                                           (len(svr.desired_realname), len(svr.realname)))

    print("*** MY NICK SHOULD BE %s ***" % desired_nickname)
    old_nick = desired_nickname
    while True:
        sleep(randint(5, 10))
        if my_channel not in svr.channels:
            print("WARNING -- we dropped out of %s" % my_channel)
            svr.connection.join(my_channel)
        nick = svr.nickname
        if old_nick != nick:
            print("*** MY NICK CHANGED TO %s ***" % nick)
            old_nick = nick
        try:
            u = choice(list(svr.homies.keys()))
        except IndexError:
            pass
        else:
            svr.show_users_dct_info()
            if svr.homies[u].ipaddr is not None:
                tx_q.put((u, ('HELLO from %s to %s' % (svr.nickname, u)).encode()))
            try:
                while True:
                    the_user, the_blk = rx_q.get_nowait()
                    assert("HELLO from" in the_blk.decode())
                    print(the_user, "==>", the_blk)
            except Empty:
                continue

