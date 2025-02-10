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


from my.irctools.jaracorocks.pratebot import PrateBot
from Crypto.PublicKey import RSA
from my.irctools.cryptoish import *
from time import sleep
my_rsa_key1 = RSA.generate(2048)
my_rsa_key2 = RSA.generate(2048)
bot1 = PrateBot('#prate', 'mac1', 'cinqcent.local', 6667, my_rsa_key1)
bot2 = PrateBot('#prate', 'mac2', 'cinqcent.local', 6667, my_rsa_key2)
#bot1.paused = True
#bot2.paused = True
while not (bot1.ready and bot2.ready):
    sleep(.1)


"""

import sys
from threading import Thread, Lock

# from my.classes.readwritelock import ReadWriteLock
from random import randint, shuffle
from Crypto.PublicKey import RSA
from my.stringtools import generate_irc_handle, chop_up_string_into_substrings_of_N_characters
from my.classes.exceptions import IrcFingerprintMismatchCausedByServer, IrcInitialConnectionTimeoutError, \
                                FernetKeyIsInvalidError, FernetKeyIsUnknownError, IrcStillConnectingError, \
                                FernetKeyIsUnknownError, IrcPrivateMessageContainsBadCharsError, PublicKeyBadKeyError, PublicKeyUnknownError, IrcPrivateMessageTooLongError
from my.irctools.jaracorocks.vanilla import BotForDualQueuedSingleServerIRCBotWithWhoisSupport
from time import sleep
from my.globals import MY_IP_ADDRESS, MAX_NICKNAME_LENGTH, MAX_PRIVMSG_LENGTH
from my.irctools.cryptoish import generate_fingerprint, squeeze_da_keez, rsa_encrypt, unsqueeze_da_keez, rsa_decrypt
from cryptography.fernet import Fernet, InvalidToken
import base64
from my.classes.readwritelock import ReadWriteLock
from _queue import Empty
from my.classes.homies import HomiesDct
import datetime
# from my.globals import JOINING_IRC_SERVER_TIMEOUT, PARAGRAPH_OF_ALL_IRC_NETWORK_NAMES

_RQPK_ = "Hell"
_TXPK_ = "TXPK"
_RQFE_ = "RQFE"
_TXFE_ = "TXFE"
_RQIP_ = "RQIP"
_TXIP_ = "TXIP"
_TXTX_ = "TXTX"


def groovylsttotxt(lst):
    return ('%3d users' % len(lst)) if len(lst) > 5 else ' '.join(lst)


class PrateBot(BotForDualQueuedSingleServerIRCBotWithWhoisSupport):

    def __init__(self, channel, nickname, irc_server, port, rsa_key,
                 startup_timeout=40, maximum_reconnections=None):
        super().__init__(channel, nickname, irc_server, port, startup_timeout, maximum_reconnections)
        if rsa_key is None or type(rsa_key) is not RSA.RsaKey:
            raise PublicKeyBadKeyError(str(rsa_key) + " is a goofy value for an RSA key. Fix it.")
        self.rsa_key = rsa_key
        assert(not hasattr(self, '_bot_start'))
        assert(not hasattr(self, '__my_main_thread'))
        self.__homies = HomiesDct()
        self.__homies_lock = ReadWriteLock()
        self.paused = False
        self.__my_main_thread = Thread(target=self._bot_loop, daemon=True)
        self.__my_main_thread.start()

    @property
    def ready(self):
        try:
            return super().ready
        except AttributeError:
            return False

    def _bot_loop(self):
        print("Waiting for the bot to be ready to connect to %s..." % self.irc_server)
        while not self.ready and not self.should_we_quit:
            sleep(.1)
        print("Connected. Looping...")
        sleep(3)
        while self.paused:
            sleep(.1)
        self.trigger_handshaking_with_the_other_users()
        while not self.should_we_quit:
            sleep(.1)
            if self.paused:
                pass
            elif datetime.datetime.now().second % 60 == 0:
                self.trigger_handshaking_with_the_other_users()
                sleep(1)
            else:
                self.read_messages_from_users()
        print("Quitting. Huzzah.")

    def read_messages_from_users(self):
        while True:
            try:
                (sender, msg) = self.get_nowait()  # t(timeout=1)
            except Empty:
                return
            else:
                if msg.startswith(_RQPK_):
                    self.put(sender, "%s%s" % (_TXPK_, squeeze_da_keez(self.rsa_key.public_key())))
                elif msg.startswith(_TXPK_):
                    self.homies[sender].pubkey = unsqueeze_da_keez(msg[len(_TXPK_):])
                    self.put(sender, "%s%s" % (_RQFE_, self.my_encrypted_fernetkey_for_this_user(sender)))
                elif msg.startswith(_RQFE_):
                    if self.homies[sender].pubkey is None:
                        print("I cannot send my fernet key to %s: I don't know his public key. That's OK! I'll ask for it again..." % sender)
                        self.put(sender, "%s%s" % (_RQPK_, squeeze_da_keez(self.rsa_key.public_key())))
                    else:
                        self.homies[sender].remotely_supplied_fernetkey = rsa_decrypt(base64.b64decode(msg[len(_RQFE_):]), self.rsa_key)
                        self.put(sender, "%s%s" % (_TXFE_, self.my_encrypted_fernetkey_for_this_user(sender)))
                elif msg.startswith(_TXFE_):
                    self.homies[sender].remotely_supplied_fernetkey = \
                                        rsa_decrypt(base64.b64decode(msg[len(_TXFE_):]), self.rsa_key)
                    if self.homies[sender].fernetkey is not None:
                        self.put(sender, "%s%s" % (_RQIP_, self.my_encrypted_ipaddr(sender)))
                elif msg.startswith(_RQIP_):
                    cipher_suite = Fernet(self.homies[sender].fernetkey)
                    decoded_msg = cipher_suite.decrypt(msg[len(_RQIP_):])
                    self.homies[sender].ipaddr = decoded_msg.decode()
                    self.put(sender, "%s%s" % (_TXIP_, self.my_encrypted_ipaddr(sender)))
                    print("I've sent %s my IP address." % sender)
                elif msg.startswith(_TXIP_):
                    cipher_suite = Fernet(self.homies[sender].fernetkey)
                    decoded_msg = cipher_suite.decrypt(msg[len(_TXIP_):])
                    self.homies[sender].ipaddr = decoded_msg.decode()
                    print("%s IS PROBABLY KOSHER" % sender)
                else:
                    print("??? %s: %s" % (sender, msg))

    def trigger_handshaking_with_the_other_users(self):
        for user in self.users:
            if user != self.nickname and self.whois(user) is not None and generate_fingerprint(user) == self.whois(user).split('* ', 1)[-1]:
                if self.homies[user].pubkey is None:
                    print("I, %s, am triggering a handshake with %s" % (self.nickname, user))
                    self.put(user, "%so, %s! I am %s. May I please have a copy of your public key?" % (_RQPK_, user, self.nickname))

    def my_encrypted_ipaddr(self, user):
        """Encrypt our IP address w/ the user's fernet key."""
        if self.homies[user].fernetkey is None:
            raise FernetKeyIsUnknownError("Please download %s's fernet key before you try to encrypt." % user)
        cipher_suite = Fernet(self.homies[user].fernetkey)
        ipaddr_str = MY_IP_ADDRESS
        cipher_text = cipher_suite.encrypt(ipaddr_str.encode())
        return cipher_text.decode()

    def my_encrypted_fernetkey_for_this_user(self, user):
        """Encrypt the user's fernet key with the user's public key."""
        encrypted_fernetkey = rsa_encrypt(message=self.homies[user].locally_generated_fernetkey, public_key=self.homies[user].pubkey)
        b64_encrypted_fernetkey = base64.b64encode(encrypted_fernetkey).decode()
        return b64_encrypted_fernetkey

    @property
    def homies(self):
        """Dictionary of relevant IRC users."""
        self.__homies_lock.acquire_read()
        try:
            retval = self.__homies
            return retval
        finally:
            self.__homies_lock.release_read()

    @homies.setter
    def homies(self, value):
        self.__homies_lock.acquire_write()
        try:
            self.__homies = value
        finally:
            self.__homies_lock.release_write()


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
        except (IrcInitialConnectionTimeoutError, IrcFingerprintMismatchCausedByServer):
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
    print("Hi there.")

