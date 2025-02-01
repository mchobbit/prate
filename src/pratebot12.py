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

EXAMPLE

from random import randint
from pratebot11 import *
from my.irctools import *
from cryptography.fernet import Fernet, InvalidToken
import irc.bot
import types

desired_nickname = "clyde"  # nickname='mac' + str(randint(100,999)
rx_q = queue.LifoQueue()
tx_q = queue.LifoQueue()
svr = PrateBot(channel="#prate", nickname=desired_nickname, realname=squeeze_da_keez(MY_RSAKEY.public_key()),
                    irc_server='cinqcent.local', port=6667, crypto_rx_queue=rx_q, crypto_tx_queue=_tx_q)

while not svr.ready:
    sleep(1)

tx_q.put(('mac2', b'HELLO'))
incoming = crypto_rx_q.get()
print(incoming)

"""

import sys
import queue
from time import sleep
from threading import Thread

from cryptography.fernet import Fernet, InvalidToken
import base64
from my.globals import MY_IP_ADDRESS, MY_RSAKEY
from my.classes.readwritelock import ReadWriteLock
from my.irctools.cryptoish import rsa_decrypt, rsa_encrypt, unsqueeze_da_keez, squeeze_da_keez
from my.irctools.jaracorocks import SingleServerIRCBotWithWhoisSupport
from _queue import Empty
import datetime
from random import randint
from my.classes.homies import HomiesDct


class CryptoOrientedSingleServerIRCBotWithWhoisSupport(SingleServerIRCBotWithWhoisSupport):
    """Crypto-oriended single server IRC bot with Whois Support.

    This is a subclass of a subclass of Jaraco's amazing IRC server class.
    It joins the specified room, runs /whois to find the users whose public
    keys are in their realname fields, exchanges public keys, establishes
    a secure (symmetric) encoded channel, and exchanges IP addresses. Then,
    it presents an easy way for programmers to tell the two (or more) users
    to talk to one another programmatically and privately.

    Attributes:
        channel (str): IRC channel to be joined.
        nickname (str): Initial nickname. The real nickname will be changed
            if the IRC server reports a nickname collision.
        realname (str): The string that is stored in the realname field of /whois.
            This is usually our stringified public key.
        irc_server (str): The IRC server URL.
        port (int): The port number of the IRC server.
        crypto_rx_queue (LifoQueue): Decrypted user-and-msg stuff goes here.
        crypto_tx_queue (LifoQueue): User-and-msg stuff to be encrypted goes here.

    """

    def __init__(self, channel, nickname, realname, irc_server, port, crypto_rx_queue, crypto_tx_queue):
        super().__init__(channel=channel, nickname=nickname,
                         realname=realname, server=irc_server, port=port)
        self.__homies = HomiesDct()
        self.__homies_lock = ReadWriteLock()
        self.__crypto_rx_queue = crypto_rx_queue
        self.__crypto_tx_queue = crypto_tx_queue
        self.__scanusers_thread = Thread(target=self.__scanusers_worker_loop, daemon=True)
        self.__crypto_tx_thread = Thread(target=self.__crypto_tx_loop, daemon=True)
        self.__scanusers_thread.start()
        self.__crypto_tx_thread.start()

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
    def ready(self):
        """bool: Are we connected to the IRC server *and* have we joined the room that we want?"""
        return True if self.connected and self.joined else False

    def __scanusers_worker_loop(self):
        """Indefinitely scan the current channel for any users who have public keys in their realname fields."""
        while True:
            if not self.connected:
                sleep(.1)
            elif not self.joined:
                sleep(.1)
            else:
                self._scan_all_users_for_public_keys_etc()  # Scan the REALNAME (from /whois output) for public keys; then, exchange fernet keys & IP addresses
                sleep(randint(5, 10) / 10.)

    def __crypto_tx_loop(self):
        while True:
            sleep(.1)
            try:
                (user, byteblock) = self.__crypto_tx_queue.get_nowait()
                self.crypto_put(user, byteblock)
            except Empty:
                pass

    def _scan_all_users_for_public_keys_etc(self, channel=None):
        """Run a one-off scan the current channel for any users who have public keys in their realname fields."""
        if channel is None:
            channel = self.initial_channel
        try:
            all_users = list(self.channels[channel].users())
        except (KeyError, IndexError):
            print("I believe I am not in %s anymore. Therefore, I cannot scan its users' /whois outputs for public keys." % channel)
        else:
            for user in all_users:
                if user == self.nickname:
                    pass
                else:
                    self._scan_user_for_pubkey(user)
                    if self.homies[user].keyless is True:
                        pass  # print("Ignoring %s because he's keyless" % user)
                    elif self.homies[user].pubkey is None:
                        print("Ignoring %s because he doesn't have a public key yet" % user)
                    elif self.homies[user].fernetkey is None:
                        # print("%s has pub keys but no fernet key. I'll try to get one via RQFERN." % user)
                        self.privmsg(user, "RQFERN")
                    elif self.homies[user].ipaddr is None:
                        # print("%s has no IP address get. I'll try to get one via RQIPAD." % user)
                        self.privmsg(user, "RQIPAD")  # Request his IP address; in due course, he'll send it via TXIPAD.
                    else:
                        pass  # print("%s has EVERYTHING." % user)

    def _scan_user_for_pubkey(self, user):
        """Scan this user's realname field for a public key."""
        if self.homies[user].keyless is True:
            if 0 != randint(0, 1000):
                return
            else:
                self.homies[user].keyless = False  # else: print("Now and then, f*** it, let's ask the server /whois %s anyway." % user)
        try:
            whois_res = self.call_whois_and_wait_for_response(user)
            squozed_key = whois_res.split(' ', 4)[-1]
        except (AttributeError, ValueError, IndexError, TimeoutError):
            self.homies[user].pubkey = None
        else:
            try:
                self.homies[user].pubkey = unsqueeze_da_keez(squozed_key)
            except (AttributeError, ValueError, IndexError, TimeoutError):
                self.homies[user].keyless = True

    def privmsg(self, user, msg):
        """Send a private message on IRC. Then, pause; don't overload the server."""
        self.connection.privmsg(user, msg)
        sleep(randint(16, 20) / 10.)  # Do not send more than 20 messages in 30 seconds! => 30/(((20+16)/2)/10)=16.7 messages per 30 seconds.

    def whois(self, user):
        """Run /whois and get the result."""
        return self.call_whois_and_wait_for_response(user)

    def crypto_put(self, user, byteblock):
        """Write an encrypted message to this user via a private message on IRC."""
        if self.homies[user].keyless is False \
        and self.homies[user].pubkey is not None \
        and self.homies[user].fernetkey is not None:
            if type(byteblock) is not bytes:
                raise ValueError("I cannot send a non-binary message to %s. The byteblock must be composed of bytes!" % user)
            if self.homies[user].fernetkey is None:
                raise ValueError("I cannot encrypt a message with a null fernet key")
            cipher_suite = Fernet(self.homies[user].fernetkey)
            cipher_text = cipher_suite.encrypt(byteblock)
            self.privmsg(user, "TXTXTX%s" % cipher_text.decode())
        else:
            raise ValueError("pubkey and/or fernetkey missing")

    def show_users_dct_info(self):
        """Write the list of our users (and their crypto info) to screen."""
        outstr = ""
        for user in self.homies:
            if user == self.nickname:
                pass
            elif self.homies[user].keyless is True:
                outstr += "\n%-20s pubkey nope" % user
            elif self.homies[user].pubkey is None:
                outstr += "\n%-20s pubkey unk" % user
            elif self.homies[user].fernetkey is None:
                outstr += "\n%-20s pubkey OK; fernetkey unk" % user
            elif self.homies[user].ipaddr is None:
                outstr += "\n%-20s pubkey OK  fernetkey OK, IP nope" % user
            else:
                outstr += "\n%-20s pubkey OK, fernetkey OK, IP %s" % (user, self.homies[user].ipaddr)
        print(outstr)

    def my_encrypted_ipaddr(self, user):
        """Encrypt our IP address w/ the user's fernet key."""
        if self.homies[user].fernetkey is None:
            raise ValueError("Please download %s's fernet key before you try to encrypt." % user)
        cipher_suite = Fernet(self.homies[user].fernetkey)
        ipaddr_str = MY_IP_ADDRESS
        cipher_text = cipher_suite.encrypt(ipaddr_str.encode())
        return cipher_text.decode()

    def on_privmsg(self, c, e):  # @UnusedVariable
        """Process on_privmsg event from the bot's reactor IRC thread."""
        # self.reactor.process_once()
        if e is None:  # e is event
            raise AttributeError("act_on_msg_from_irc() has an e of None")
        if e.source:
            sender = e.source.split('@')[0].split('!')[0]
        else:
            sender = None
        txt = e.arguments[0]
        cmd = txt[:6]
        stem = txt[6:]
        if sender == self.nickname:
            raise ValueError("WHY AM I TALKING TO MYSELF?")
        if e.type == 'foo':
            print("e type is foo for %s; this is a foo-tile attempt at a test." % e.target)
        elif cmd == "RQFERN":  # you asked for a copy of my fernet key
            print("Sending my fernetkey to %s" % sender)
            if self.homies[sender].keyless is False and self.homies[sender].pubkey is not None:
                self.privmsg(sender, "TXFERN%s" % self.encrypt_fernetkey(sender, self.homies[sender].locally_generated_fernetkey))
        elif cmd == "TXFERN":
            self._txfern(c, e, sender, stem)
        elif cmd == "RQIPAD":
            if self.homies[sender].keyless is False \
            and self.homies[sender].pubkey is not None \
            and self.homies[sender].fernetkey is not None:
                self.privmsg(sender, "TXIPAD%s" % self.my_encrypted_ipaddr(sender))
            else:
                print("I don't have a pubkey and/or fernetkey. So, I can't send my IP address to %s." % sender)
        elif cmd == "TXIPAD":
            self._receiving_his_IP_address(sender, stem)
        elif cmd == 'TXTXTX':  # This means that some data was TX'd to us.
            print("TXTXTX incoming")
            try:
                cipher_suite = Fernet(self.homies[sender].fernetkey)
                decoded_msg = cipher_suite.decrypt(stem).decode()
            except InvalidToken:
                print("Warning - failed to decode %s's message (key bad? ciphertext bad?). " % sender)
            except KeyError:
                print("Warning - failed to decode %s's message (fernet key not found?)." % sender)
            else:
                print("From %s: %s" % (sender, str(decoded_msg)))
                self.__crypto_rx_queue.put([sender, decoded_msg.encode()])
        else:
            print("Probably a private message from %s: %s" % (sender, txt))
            print("What is private message %s for? " % cmd)

    def _txfern(self, c, e, user, stem):
        """If cmd==TXFERN is received, receive the user's fernet key & save it to our homie database."""
        del c, e
        try:
            decrypted_remote_fernetkey = rsa_decrypt(base64.b64decode(stem))
        except ValueError:
            print("Failed to decode the encrypted key in the stem")
        else:
            try:
                self.homies[user].remotely_supplied_fernetkey = decrypted_remote_fernetkey
            except AttributeError:
                print("I cannot update %s's remotely supplied fernetkey: I already have one." % user)
            else:
                if self.homies[user].fernetkey is not None:
                    print("YAY! I have %s's fernetkey!" % user)

    @property
    def crypto_empty(self):
        """Is the incoming crypto rx queue empty?"""
        return self.__crypto_rx_queue.empty()

    def crypto_get(self):
        """Get next record from crypto rx queue. Wait if necessary."""
        return self.__crypto_rx_queue.get()

    def crypto_get_nowait(self):
        """Get next record from crypto rx queue. Throw exception if queue is empty."""
        return self.__crypto_rx_queue.get_nowait()

    def _receiving_his_IP_address(self, user, stem):
        """Receive the user's IP address."""
        if self.homies[user].fernetkey is None:
            print("I do not possess %s's fernetkey. Please negotiate one" % user)
            return
        cipher_suite = Fernet(self.homies[user].fernetkey)
        try:
            decoded_msg = cipher_suite.decrypt(stem)
        except InvalidToken:
            return "Warning - failed to decode %s's message. " % user
        ipaddr = decoded_msg.decode()
        self.homies[user].ipaddr = ipaddr

    def encrypt_fernetkey(self, user, fernetkey):
        """Encrypt the user's fernet key with the user's public key."""
        if self.homies[user].keyless is False \
        and self.homies[user].pubkey is not None:
            encrypted_fernetkey = rsa_encrypt(message=fernetkey, public_key=self.homies[user].pubkey)
            b64_encrypted_fernetkey = base64.b64encode(encrypted_fernetkey).decode()
            return b64_encrypted_fernetkey
        else:
            raise ValueError("I can't the fernetkey unless I have a public key to do it with")


class PrateBot:

    def __init__(self, channel, nickname, realname, irc_server, port, crypto_rx_queue, crypto_tx_queue):
        self.__time_to_quit = False
        self.__time_to_quit_lock = ReadWriteLock()
        self.__ready_lock = ReadWriteLock()
        self.bot = CryptoOrientedSingleServerIRCBotWithWhoisSupport(channel, nickname,
                                                            realname, irc_server, port,
                                                            crypto_rx_queue, crypto_tx_queue)
        self.__bot_thread = Thread(target=self.__bot_worker_loop, daemon=True)
        self._start()

    def _start(self):
        self.__bot_thread.start()

    @property
    def ready(self):
        self.__ready_lock.acquire_read()
        try:
            return self.bot.ready
        finally:
            self.__ready_lock.release_read()

    @property
    def time_to_quit(self):
        self.__time_to_quit_lock.acquire_read()
        try:
            retval = self.__time_to_quit
            return retval
        finally:
            self.__time_to_quit_lock.release_read()

    def quit(self):  # Do we need this?
        self.__time_to_quit = True
        self.__bot_thread.join()  # print("Joining server thread")

    def __bot_worker_loop(self):
        print("Starting bot thread")
        self.bot.start()
        print("You should not get here.")
        while not self.__time_to_quit:
            sleep(1)

##########################################################################################################

'''


'''

if __name__ == "__main__":
    if len(sys.argv) != 3:
#        print("Usage: %s <channel> <nickname>" % sys.argv[0])
#        sys.exit(1)
        my_channel = "#prate"
        desired_nickname = "macgyver"  # generate_irc_handle()
        my_realname = "iammcgyv"
        print("Assuming my_channel is", my_channel, "and nickname is", desired_nickname)
    else:
        my_channel = sys.argv[1]
        desired_nickname = sys.argv[2]
        my_realname = desired_nickname[::-1] * 3

    my_irc_server = 'cinqcent.local'
    my_port = 6667
    rx_q = queue.LifoQueue()
    tx_q = queue.LifoQueue()
    svr = PrateBot(channel=my_channel, nickname=desired_nickname,
                                       realname=squeeze_da_keez(MY_RSAKEY.public_key()),
                                       irc_server=my_irc_server, port=my_port,
                                       crypto_rx_queue=rx_q, crypto_tx_queue=tx_q)
    while not svr.ready:
        sleep(1)

    while True:
        sleep(.1)
        for u in list(svr.bot.channels[my_channel].users()):
            if svr.bot.homies[u].ipaddr is not None:
                tx_q.put((u, ('HELLO from %s' % svr.bot.nickname).encode()))
        if datetime.datetime.now().second % 30 == 0:
            svr.bot.show_users_dct_info()
            sleep(1)
        try:
            while True:
                the_user, the_blk = rx_q.get_nowait()
                print(the_user, "=>", the_blk)
        except Empty:
            pass

