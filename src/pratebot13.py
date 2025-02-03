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
s = 'm&4c;;B32a?eKNjw~g*;$0{=kLOVcOcgu2HzbjBk98m2hvhGq~'
desired_nickname = 'mac1'
my_irc_server = 'cinqcent.local'
my_channel = '#prate'
from pratebot13 import *
rx_q = queue.LifoQueue()
tx_q = queue.LifoQueue()
my_rsa_key = RSA.generate(1024)  # TODO: Change to 2048 on 3/1/2025
svr = PrateBot(channel=my_channel, nickname=desired_nickname,rsa_key=my_rsa_key,
                is_pubkey_in_realname=True,
                irc_server=my_irc_server, port=6667,
                crypto_rx_queue=rx_q, crypto_tx_queue=tx_q)

svr.paused = True
user = 'mac2'
svr.homies[user].keyless = False
svr.homies[user].didwelook = False
svr.scan_a_user_for_fingerprints_publickeys_etc('mac2')
"""

import sys
import queue
from time import sleep
from threading import Thread

from my.classes.readwritelock import ReadWriteLock
from _queue import Empty
from random import randint, choice
from my.classes.exceptions import MyIrcRealnameTruncationError, MyIrcFingerprintMismatchCausedByServer, MyIrcNicknameChangedByServer
from Crypto.PublicKey import RSA
from my.irctools.jaracorocks import CryptoOrientedSingleServerIRCBotWithWhoisSupport


class PrateBot(CryptoOrientedSingleServerIRCBotWithWhoisSupport):
    """A background-threaded RealnameTruncatingCryptoOrientedSingleServerIRCBotWithWhoisSupport.

    This is a subclass of RealnameTruncatingCryptoOrientedSingleServerIRCBotWithWhoisSupport.
    Its primary purpose is to instantiate that class as a background thread. (Do I mean
    'instantiate'?)

    FYI, RealnameTruncatingCryptoOrientedSingleServerIRCBotWithWhoisSupport is unlike
    CryptoOrientedSingleServerIRCBotWithWhoisSupport in one major aspect: the latter
    sets each user's realname to the user's RSA public key. What does the former use?
    I haven't decided yet.

    Attributes:
        channel (str): IRC channel to be joined.
        nickname (str): Initial nickname. The real nickname will be changed
            if the IRC server reports a nickname collision.
        rsa_key (RSA.RsaKey): RSA key.
        irc_server (str): The IRC server URL.
        port (int): The port number of the IRC server.
        crypto_rx_queue (LifoQueue): Decrypted user-and-msg stuff goes here.
        crypto_tx_queue (LifoQueue): User-and-msg stuff to be encrypted goes here.

    """

    def __init__(self, channel, nickname, rsa_key, is_pubkey_in_realname,
                 irc_server, port, crypto_rx_queue, crypto_tx_queue):
        super().__init__(channel,
                         nickname,
                         rsa_key,
                         is_pubkey_in_realname,
                         irc_server,
                         port,
                         crypto_rx_queue,
                         crypto_tx_queue)
        self.__time_to_quit = False
        self.__time_to_quit_lock = ReadWriteLock()
        self.__intended_fingerprint = self._generate_fingerprint(self.initial_nickname)
        self.__bot_thread = Thread(target=self.__bot_worker_loop, daemon=True)
        self._start()
        sleep(1)

    def _start(self):
        self.__bot_thread.start()
        while not self.ready:
            sleep(.1)
        current_fprint = self.fingerprint
        shouldbe_fprint = self.__intended_fingerprint
        if len(current_fprint) < len(shouldbe_fprint):
            raise MyIrcRealnameTruncationError("""
Realname was truncated from %d chars to only %d chars by server. This means
the server likes to trancate realnames. This, in turn, means you're better off
switching from PubkeyInFullnameCryptoOrientedSingleServerIRCBotWithWhoisSupport to
FingerprintInFullnameTruncatingCryptoOrientedSingleServerIRCBotWithWhoisSupport as
the class that PrateBot uses.""" % (len(shouldbe_fprint), len(current_fprint)))
        if current_fprint != shouldbe_fprint:
            print("Current fingerprint:", current_fprint)
            print("Should be:          ", shouldbe_fprint)
            if self.is_pubkey_in_realname is True:
                raise MyIrcFingerprintMismatchCausedByServer("There's a mismatch between my intended public key and my intended public key. THAT MAKES NO SENSE.")
            else:
                raise MyIrcNicknameChangedByServer("There's a mismatch between my intended public key and my intended public key. THAT MAKES NO SENSE.")

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

    my_rsa_key = RSA.generate(1024)  # TODO: Change to 2048 on 3/1/2025
    rx_q = queue.LifoQueue()
    tx_q = queue.LifoQueue()
    is_server_stingy_with_realname_maxlen = True
    svr = PrateBot(channel=my_channel, nickname=desired_nickname,
                                        rsa_key=my_rsa_key,
                                        is_pubkey_in_realname=not is_server_stingy_with_realname_maxlen,
                                        irc_server=my_irc_server, port=my_port,
                                        crypto_rx_queue=rx_q, crypto_tx_queue=tx_q)

    sleep(5)  # Why?
    old_nick = desired_nickname
    while True:
        if not svr.connected:
            print("Waiting for server to be ready")
            sleep(1)
            continue
        if my_channel not in svr.channels:
            print("WARNING -- we dropped out of %s" % my_channel)
            svr.connection.join(my_channel)
            continue
        nick = svr.nickname
        if old_nick != nick:
            print("*** MY NICK CHANGED FROM %s TO %s ***" % (old_nick, nick))
            old_nick = nick
            if svr.fingerprint != svr._generate_fingerprint(nick):
                raise ValueError("FINGERPRINT SNAFU")
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
                pass
        sleep(randint(5, 10))
