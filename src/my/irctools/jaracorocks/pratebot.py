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


"""

import sys
from threading import Thread

# from my.classes.readwritelock import ReadWriteLock
from random import randint, shuffle, choice
from Crypto.PublicKey import RSA
from my.classes.exceptions import PublicKeyBadKeyError, IrcPrivateMessageTooLongError, PublicKeyUnknownError, \
                            IrcIAmNotInTheChannelError, IrcStillConnectingError, FernetKeyIsInvalidError, FernetKeyIsUnknownError

from my.irctools.jaracorocks.vanilla import VanillaBot
from time import sleep
from my.globals import MY_IP_ADDRESS, MAX_PRIVMSG_LENGTH, MAX_CRYPTO_MSG_LENGTH
from my.irctools.cryptoish import generate_fingerprint, squeeze_da_keez, rsa_encrypt, unsqueeze_da_keez, rsa_decrypt, bytes_64bit_cksum, receive_and_decrypt_message
from cryptography.fernet import Fernet
import base64
from my.classes.readwritelock import ReadWriteLock
from my.classes.homies import HomiesDct
from queue import Queue, Empty
# from my.globals import JOINING_IRC_SERVER_TIMEOUT, PARAGRAPH_OF_ALL_IRC_NETWORK_NAMES

_RQPK_ = "He"
_TXPK_ = "TK"
_RQFE_ = "RE"
_TXFE_ = "TE"
_RQIP_ = "RP"
_TXIP_ = "TP"
_TXTX_ = "XX"


class PrateBot(VanillaBot):

    def __init__(self, channels, nickname, irc_server, port, rsa_key,
                 startup_timeout=20, maximum_reconnections=2,
                 autoreconnect=True, strictly_nick=True):
        self.__strictly_nick = strictly_nick
        super().__init__(channels=channels, nickname=nickname, irc_server=irc_server,
                         port=port, startup_timeout=startup_timeout,
                         maximum_reconnections=maximum_reconnections,
                         autoreconnect=autoreconnect, strictly_nick=strictly_nick)
        if rsa_key is None or type(rsa_key) is not RSA.RsaKey:
            raise PublicKeyBadKeyError(str(rsa_key) + " is a goofy value for an RSA key. Fix it.")
        self.rsa_key = rsa_key
        self.__homies = HomiesDct()
        self.__homies_lock = ReadWriteLock()
        self.__crypto_rx_queue = Queue()
        self.paused = False
        assert(not hasattr(self, '__my_main_thread'))
        assert(not hasattr(self, '__my_main_loop'))
        self.__my_main_thread = Thread(target=self.__my_main_loop, daemon=True)
        self.__my_main_thread.start()

    @property
    def strictly_nick(self):
        return self.__strictly_nick

    @property
    def ready(self):
        try:
            return super().ready
        except AttributeError:
            return False

    def __my_main_loop(self):
        while not self.ready and not self.should_we_quit:
            sleep(.1)
        sleep(3)
        while self.paused:
            sleep(.1)

        if not self.should_we_quit:
            try:
                self.trigger_handshaking_with_the_other_users()
            except IrcIAmNotInTheChannelError:
                print("Warning -- %s cannot contact other users of %s in %s: I'm not even in there." % (self.nickname, self.channels, self.irc_server))

        while not self.should_we_quit:
            sleep(.1)
            if self.paused:
                pass
            else:
                try:
                    self.read_messages_from_users()
                except IrcStillConnectingError:  # print("We are in the middle of quitting. That's okay.")
                    pass
                except FernetKeyIsInvalidError:
                    print("Some kind of protocl error as %s in %s" % (self.nickname, self.irc_server))

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
                    if self.homies[sender].pubkey is None:  # print("I cannot send my fernet key to %s: I don't know his public key. That's OK! I'll ask for it again..." % sender)
                        self.put(sender, "%s%s" % (_RQPK_, squeeze_da_keez(self.rsa_key.public_key())))
                    else:
                        dc = rsa_decrypt(base64.b64decode(msg[len(_RQFE_):]), self.rsa_key)
                        if self.homies[sender].remotely_supplied_fernetkey != dc:
                            self.homies[sender].remotely_supplied_fernetkey = dc
                            print("Saving new fernet key for %s on %s" % (self.nickname, self.irc_server))
                        self.put(sender, "%s%s" % (_TXFE_, self.my_encrypted_fernetkey_for_this_user(sender)))
                elif msg.startswith(_TXFE_):
                    dc = rsa_decrypt(base64.b64decode(msg[len(_TXFE_):]), self.rsa_key)
                    if self.homies[sender].remotely_supplied_fernetkey != dc:
                        self.homies[sender].remotely_supplied_fernetkey = dc
                        print("Saving new fernet key for %s on %s" % (self.nickname, self.irc_server))
                    if self.homies[sender].fernetkey is not None:
                        self.put(sender, "%s%s" % (_RQIP_, self.my_encrypted_ipaddr(sender)))
                elif msg.startswith(_RQIP_):
                    cipher_suite = Fernet(self.homies[sender].fernetkey)
                    decoded_msg = cipher_suite.decrypt(msg[len(_RQIP_):])
                    new_ipaddr = decoded_msg.decode()
                    if self.homies[sender].ipaddr != new_ipaddr:
                        self.homies[sender].ipaddr = new_ipaddr
                    self.put(sender, "%s%s" % (_TXIP_, self.my_encrypted_ipaddr(sender)))
#                    print("I've sent %s my IP address." % sender)
                elif msg.startswith(_TXIP_):
                    cipher_suite = Fernet(self.homies[sender].fernetkey)
                    decoded_msg = cipher_suite.decrypt(msg[len(_TXIP_):])
                    new_ipaddr = decoded_msg.decode()
                    if self.homies[sender].ipaddr != new_ipaddr:
                        self.homies[sender].ipaddr = new_ipaddr
#                        print("%s IS PROBABLY KOSHER" % sender)
                elif msg.startswith(_TXTX_):
                    self.crypto_rx_queue.put((sender, receive_and_decrypt_message(msg[len(_TXTX_):], self.homies[sender].fernetkey)))
#                    print("TXTX'ing")
                else:
                    print("??? %s: %s" % (sender, msg))

    def trigger_handshaking_with_the_other_users(self):
        if not self.ready:
            print("I choose not to try to trigger handshaking with other users: I'm not even online/joinedroom yet.")
        else:
            for user in self.users:
                if user != self.nickname and self.whois(user) is not None and generate_fingerprint(user) == self.whois(user).split('* ', 1)[-1]:
                    if self.homies[user].pubkey is None:
                        print("I, %s, do not possess %s's public key. Therefore, I am triggering a handshake on %s" % (self.nickname, user, self.irc_server))
                        self.put(user, "%sllo, %s! I am %s. May I please have a copy of your public key?" % (_RQPK_, user, self.nickname))

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

    @property
    def crypto_rx_queue(self):
        return self.__crypto_rx_queue

    @property
    def crypto_not_empty(self):
        return self.crypto_rx_queue.not_empty

    def crypto_empty(self):
        return self.crypto_rx_queue.empty()

    def crypto_get(self, block=True, timeout=None):
        return self.crypto_rx_queue.get(block, timeout)

    def crypto_get_nowait(self):
        return self.crypto_rx_queue.get_nowait()

    def crypto_put(self, user, byteblock):
        """Write an encrypted message to this user via a private message on IRC."""
        if type(byteblock) is not bytes:
            raise ValueError("I cannot send a non-binary message to %s. The byteblock must be composed of bytes!" % user)
        elif self.homies[user].pubkey is None:
            raise PublicKeyUnknownError("I do not know %s's public key." % user)
        elif self.homies[user].fernetkey is None:
            raise FernetKeyIsUnknownError("I have not negotiated a fernet key with %s yet." % user)
        elif len(byteblock) > MAX_CRYPTO_MSG_LENGTH:
            raise IrcPrivateMessageTooLongError("The encrypted message will be too long")
        else:
            cipher_suite = Fernet(self.homies[user].fernetkey)
            cipher_text = cipher_suite.encrypt(byteblock)
            outgoing_str = "%s%s" % (_TXTX_, cipher_text.decode())
            if len(outgoing_str) > MAX_PRIVMSG_LENGTH - len(user):
                raise IrcPrivateMessageTooLongError("Cannot send %s to %s: message is too long" % (outgoing_str, user))
            self.put(user, outgoing_str)


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
    my_bot = PrateBot([my_channel], desired_nickname, my_irc_server, my_port, my_rsa_key)
    while not my_bot.ready:
        sleep(1)
    print("Hi there.")

