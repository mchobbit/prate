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

desired_nickname = "mac1"
from random import randint
from pratebot12 import *
from my.irctools import *
from cryptography.fernet import Fernet, InvalidToken
import irc.bot
import types
rx_q = queue.LifoQueue()
tx_q = queue.LifoQueue()
svr = PrateBot(channel="#prate", nickname=desired_nickname, realname=squeeze_da_keez(MY_RSAKEY.public_key()),
                    irc_server='cinqcent.local', port=6667, crypto_rx_queue=rx_q, crypto_tx_queue=tx_q)

svr.paused = True
while not svr.ready:
    sleep(1)

while 'mac1' not in svr.channels['#prate'].users() and 'mac2' not in svr.channels['#prate'].users():
    sleep(1)

svr.show_users_dct_info()
svr.scan_all_users_for_public_keys_etc()
svr.show_users_dct_info()



tx_q.put(('mac2', b'HELLO'))
incoming = crypto_rx_q.get()
print(incoming)

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
from my.irctools.jaracorocks import SingleServerIRCBotWithWhoisSupport
from _queue import Empty
import datetime
from random import randint
from my.classes.homies import HomiesDct, Homie
from my.stringtools import generate_irc_handle
from numpy import squeeze


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
        self.__repop_mutex = Lock()
        self.__scanusers_mutex = Lock()
        self.__scanusers_thread = Thread(target=self.__scanusers_worker_loop, daemon=True)
        self.__crypto_tx_thread = Thread(target=self.__crypto_tx_loop, daemon=True)
        self.__scanusers_thread.start()
        self.__crypto_tx_thread.start()
        self.paused = False

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
            if not self.ready or self.paused:
                sleep(.1)
            else:
                self.scan_all_users_for_public_keys_etc()  # Scan the REALNAME (from /whois output) for public keys; then, exchange fernet keys & IP addresses

    def __crypto_tx_loop(self):
        while True:
            sleep(.1)
            try:
                (user, byteblock) = self.__crypto_tx_queue.get_nowait()
                self.crypto_put(user, byteblock)
            except Empty:
                pass

    def scan_all_users_for_public_keys_etc(self, channel=None):
        with self.__scanusers_mutex:
            self.__scan_all_users_for_public_keys_etc(channel)

    def __scan_all_users_for_public_keys_etc(self, channel=None):
        """Run a one-off scan the current channel for any users who have public keys in their realname fields."""
        if channel is None:
            channel = self.initial_channel
        try:
            all_users = list(self.channels[channel].users())
        except (KeyError, IndexError):
            print("I believe I am not in %s anymore. Therefore, I cannot scan its users' /whois outputs for public keys." % channel)
        else:
            kosher_homies = []
            for user in all_users:
                if user == self.nickname:
                    continue
                else:
                    if self.__scan_a_user_for_public_keys_etc(user) is not None:
                        kosher_homies += [user]
            if kosher_homies != []:
                print("COMPLETE: %s" % ', '.join(kosher_homies))
            sleep(randint(50, 100) / 10.)

    def __scan_a_user_for_public_keys_etc(self, user):
        if self.homies[user].keyless and datetime.datetime.now().second % 30 == 0:
            print("Just for giggles, let's re-scan %s and see if the old user has gone, replaced with someone who has a public key." % user)
            self.load_homie_pubkey(user)
        if not self.homies[user].didwelook:
            self.load_homie_pubkey(user)
        if self.homies[user].keyless:
            return
        assert(self.homies[user].didwelook)
        assert(not self.homies[user].keyless)
        if self.homies[user].pubkey is None:
            print("%s has a null public key, but we looked. Perhaps we were offline at the time. Let's try rqfern." % user)
            self.privmsg(user, "RQFERN%s" % squeeze_da_keez(MY_RSAKEY))
            sleep(30)
            if not self.homies[user].didwelook:
                print("Seriously?! WE DIDN'T LOOK?!")
                self.load_homie_pubkey(user)
            return
        assert(self.homies[user].didwelook)
        assert(not self.homies[user].keyless)
        assert(self.homies[user].pubkey is not None)
        if self.homies[user].fernetkey is None:
            print("As part of a regular scan, I am asking %s for a fernet key exchange." % user)
            self.homies[user].remotely_supplied_fernetkey = None
            self.privmsg(user, "RQFERN%s" % squeeze_da_keez(MY_RSAKEY))
            return
        assert(self.homies[user].didwelook)
        assert(not self.homies[user].keyless)
        assert(self.homies[user].pubkey is not None)
        assert(self.homies[user].fernetkey is not None)
        if self.homies[user].ipaddr is None:
            print("As part of a regular scan, I am asking %s for his IP address." % user)
            self.privmsg(user, "RQIPAD%s" % squeeze_da_keez(MY_RSAKEY))  # Request his IP address; in due course, he'll send it via TXIPAD.
            return
        return user

    def load_homie_pubkey(self, user):
        with self.__repop_mutex:
            self.__load_homie_pubkey(user)

    def __load_homie_pubkey(self, user):
        self.homies[user].didwelook = False
        self.homies[user].keyless = False
        old_pk = self.homies[user].pubkey
        new_pk = None
        for i in range(0, 3):
            try:
                whois_res = self.call_whois_and_wait_for_response(user, timeout=3 + i)
                try:
                    squozed_key = whois_res.split(' ', 4)[-1]
                    unsqueezed_key = unsqueeze_da_keez(squozed_key)
                except (ValueError, AttributeError):
                    self.homies[user].keyless = True  # It's not a key.
                    break
                else:
                    new_pk = unsqueezed_key
                    if old_pk is not None and old_pk != new_pk:
                        print("HEY! %s'S PUBLIC KEY CHANGED!" % user)
                        print("New key:", new_pk)
                    else:
                        self.homies[user].pubkey = new_pk
                    break  # ...from 'i'
            except TimeoutError:
                continue
        self.homies[user].didwelook = True

    def privmsg(self, user, msg):
        """Send a private message on IRC. Then, pause; don't overload the server."""
        # if 0 == randint(0, 10):
        #     print("Repopulating my copy of %s's public key, just in case" % user)
        self.connection.privmsg(user, msg)
        sleep(randint(16, 20) / 10.)  # Do not send more than 20 messages in 30 seconds! => 30/(((20+16)/2)/10)=16.7 messages per 30 seconds.

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
        outstr = "\n%-20s pubkey %s                        (me)" % (self.nickname, squeeze_da_keez(MY_RSAKEY.publickey())[-12:-8])
        for user in self.homies:
            if user == self.nickname:
                print("WARNING - our nickname is on a list of homies")
            if self.homies[user].keyless is True:
                outstr += "\n%-20s pubkey nope" % user
            elif self.homies[user].pubkey is None:
                outstr += "\n%-20s pubkey unk" % user
            elif self.homies[user].fernetkey is None:
                outstr += "\n%-20s pubkey %s  fernetkey unk" % (user, squeeze_da_keez(self.homies[user].pubkey)[-12:-8])
            elif self.homies[user].ipaddr is None:
                outstr += "\n%-20s pubkey %s  fernetkey %s  IP nope" % (user, squeeze_da_keez(self.homies[user].pubkey)[-12:-8], self.homies[user].fernetkey.decode())
            else:
                outstr += "\n%-20s pubkey %s  fernetkey %s  IP %s" % (user, squeeze_da_keez(self.homies[user].pubkey)[-12:-8], self.homies[user].fernetkey.decode(), self.homies[user].ipaddr)
        print(outstr)

    def my_encrypted_ipaddr(self, user):
        """Encrypt our IP address w/ the user's fernet key."""
        if self.homies[user].fernetkey is None:
            raise ValueError("Please download %s's fernet key before you try to encrypt." % user)
        cipher_suite = Fernet(self.homies[user].fernetkey)
        ipaddr_str = MY_IP_ADDRESS
        cipher_text = cipher_suite.encrypt(ipaddr_str.encode())
        return cipher_text.decode()

    def save_pubkey_from_stem(self, sender, stem):
        stemkey = unsqueeze_da_keez(stem)
        self.homies[sender].keyless = False
        old_pubkey = self.homies[sender].pubkey
        if old_pubkey is None or old_pubkey == stemkey:
            pass  # print("%s's public key did not change. Good." % sender)
        if old_pubkey is None or old_pubkey != stemkey:
            if old_pubkey is None:
                print("Saving %s's public key from incoming msg (not from whois)" % sender)
            else:
                print("Saving %s's new pubkey from incoming msg (not from whois)" % sender)
            self.homies[sender].ipaddr = None
#            self.homies[sender].remotely_supplied_fernetkey = None
            self.homies[sender].keyless = False
            self.homies[sender].yesilooked = True
            self.homies[sender].pubkey = stemkey

    def on_privmsg(self, c, e):  # @UnusedVariable
        """Process on_privmsg event from the bot's reactor IRC thread."""
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
        elif cmd == "RQFERN":  # Sender requested a copy of my fernet key
            if stem != '':
                self.save_pubkey_from_stem(sender, stem)
            if self.homies[sender].keyless is True or self.homies[sender].pubkey is None:
                print("I can't send RQFERN to %s: he's keyless" % sender)
            else:
                self.privmsg(sender, "TXFERN%s" % self.encrypt_fernetkey(sender, self.homies[sender].locally_generated_fernetkey))
        elif cmd == "TXFERN":
            self._txfern(sender, stem)
#            self.privmsg(sender, "RQIPAD")
        elif cmd == "RQIPAD":
            self._rqipad(sender, stem)
        elif cmd == "TXIPAD":
            try:
                self._receiving_his_IP_address(sender, stem)
            except InvalidToken:
                print("Bad %s fernet key. We'll need to call RQFERN to regenerate it." % sender)
                self.homies[sender].remotely_supplied_fernetkey = None
                self.homies[sender].pubkey = None
                self.privmsg(sender, "RQFERN%s" % squeeze_da_keez(MY_RSAKEY))
        elif cmd == 'TXTXTX':  # This means that some data was TX'd to us.
            self._txtxtx(sender, stem)
        else:
            print("Probably a private message from %s: %s" % (sender, txt))
            print("What is private message %s for? " % cmd)

    def _txfern(self, user, stem):
        """If cmd==TXFERN is received, receive the user's fernet key & save it to our homie database."""
        try:
            decrypted_remote_fernetkey = rsa_decrypt(base64.b64decode(stem))
        except ValueError:
            print("_txfern %s Failed to decode the encrypted fernet key in the stem. Is his copy of my public key out of date?" % user)
            print("Requesting a public key from %s" % user)
            self.homies[user].remotely_supplied_fernetkey = None
            self.privmsg(user, "RQFERN%s" % squeeze_da_keez(MY_RSAKEY))
        else:
            try:
                self.homies[user].remotely_supplied_fernetkey = decrypted_remote_fernetkey
            except AttributeError:
                print("I cannot update %s's remotely supplied fernetkey: I already have one." % user)
            else:
                if self.homies[user].fernetkey is not None:
                    pass

#                    print("YAY! I have %s's fernetkey!" % user)
    def _rqipad(self, sender, stem):
        if stem != '':
            self.save_pubkey_from_stem(sender, stem)
#            self.homies[sender].remotely_supplied_fernetkey = None
        if self.homies[sender].keyless is True:
            print("%s sent me an RQIPAD, a request for my IP address. I can't help him: he's keyless." % sender)
        elif self.homies[sender].pubkey is None:
            print("%s sent me an RQIPAD, a request for my IP address. I can't help him: I don't have his public key." % sender)
        elif self.homies[sender].fernetkey is None:
            print("%s sent me an RQIPAD, a request for my IP address. I can't help him: we don't have a fernet key yet." % sender)
        else:
            print("%s's RQIPAD received, understood, and handled. I'm replying with a TXIPAD containing my IP address" % sender)
            self.privmsg(sender, "TXIPAD%s" % self.my_encrypted_ipaddr(sender))

    def _txtxtx(self, sender, stem):
#            print("TXTXTX incoming")
        if self.homies[sender].fernetkey is None:
            print("Cannot decipher message from %s: we have no fernet key." % sender)
            print("This might mean I'm using someone's ex-nickname & %s doesn't realize that." % sender)
            # # print("I'll initiate a new fernet key exchange. This will cause the other side to double-check my public key.")
            # print("Asking %s to send me his IP address, via RQIPAD." % sender)
            # self.privmsg(sender, "RQIPAD%s" % squeeze_da_keez(MY_RSAKEY))  # Request his IP address; in due course, he'll send it via TXIPAD.
        else:
            try:
                cipher_suite = Fernet(self.homies[sender].fernetkey)
                decoded_msg = cipher_suite.decrypt(stem).decode()
            except InvalidToken:
                print("Warning - txtxtx - failed to decode %s's message (key bad? ciphertext bad?)." % sender)
#                    self.load_homie_pubkey(sender)  # ...which will also force the renegotiation of the fernet key
            except KeyError:
                print("Warning - txtxtx - failed to decode %s's message (fernet key not found?). Is his copy of my public key out of date?" % sender)
                self.homies[sender].remotely_supplied_fernetkey = None
                self.privmsg(sender, "RQFERN%s" % squeeze_da_keez(MY_RSAKEY))
            else:
                print("From %s: %s" % (sender, str(decoded_msg)))
                self.__crypto_rx_queue.put([sender, decoded_msg.encode()])

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
        '''exceptions
        InvalidToken - bad key
        '''
        if self.homies[user].fernetkey is None:
            print("I do not possess %s's fernetkey. Please negotiate one" % user)
            return
        cipher_suite = Fernet(self.homies[user].fernetkey)
        decoded_msg = cipher_suite.decrypt(stem)
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


class PrateBot(CryptoOrientedSingleServerIRCBotWithWhoisSupport):

    def __init__(self, channel, nickname, realname, irc_server, port, crypto_rx_queue, crypto_tx_queue):
        super().__init__(channel, nickname, realname, irc_server, port, crypto_rx_queue, crypto_tx_queue)
        self.__time_to_quit = False
        self.__time_to_quit_lock = ReadWriteLock()
        self.__ready_lock = ReadWriteLock()
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
        self.__time_to_quit = True
        self.__bot_thread.join()  # print("Joining server thread")

    def __bot_worker_loop(self):
        print("Starting bot thread")
        self.start()
        print("You should not get here.")
        while not self.__time_to_quit:
            sleep(1)

##########################################################################################################


if __name__ == "__main__":
    if len(sys.argv) != 3:
#        print("Usage: %s <channel> <nickname>" % sys.argv[0])
#        sys.exit(1)
        my_channel = "#prate"
        desired_nickname = "mac1"  # macgyver"  # % (generate_irc_handle(), randint(11,99)) # ""
        print("Assuming my_channel is", my_channel, "and nickname is", desired_nickname)
    else:
        my_channel = sys.argv[1]
        desired_nickname = sys.argv[2]

    my_irc_server = 'cinqcent.local'
    my_port = 6667
    rx_q = queue.LifoQueue()
    tx_q = queue.LifoQueue()
    svr = PrateBot(channel=my_channel, nickname=desired_nickname,
                                       realname=squeeze_da_keez(MY_RSAKEY.public_key()),
                                       irc_server=my_irc_server, port=my_port,
                                       crypto_rx_queue=rx_q, crypto_tx_queue=tx_q)

    print("*** MY NICK IS %s ***" % svr.nickname)
    while not svr.ready:
        sleep(1)

    sleep(30)
#    svr.paused = True

    shouldbe_nickname = desired_nickname
    while True:
        if my_channel not in svr.channels:
            print("WARNING -- we dropped out of %s" % my_channel)
            svr.connection.join(my_channel)
        if datetime.datetime.now().second % 30 == 0:
            svr.show_users_dct_info()
            sleep(1)
            if shouldbe_nickname != svr.nickname:
                shouldbe_nickname = svr.nickname
                renegotiate_keys = True
            try:
                my_whois_pubkey = unsqueeze_da_keez(svr.call_whois_and_wait_for_response(shouldbe_nickname).split(' ', 4)[-1])
                my_real_pubkey = MY_RSAKEY.publickey()
                renegotiate_keys = True if my_whois_pubkey != my_real_pubkey else False
            except TimeoutError:
                renegotiate_keys = False
            for u in list(svr.channels[my_channel].users()):
                if u != svr.nickname and svr.homies[u].ipaddr is not None:
                    if renegotiate_keys:
                        print("Renegotiating keys w/ %s" % u)
                        svr.privmsg(u, "RQFERN%s" % squeeze_da_keez(MY_RSAKEY))
                    else:
                        tx_q.put((u, ('HELLO from %s to %s' % (svr.nickname, u)).encode()))
            try:
                while True:
                    the_user, the_blk = rx_q.get_nowait()
                    assert("HELLO from" in the_blk.decode())
                    print(the_user, "=>", the_blk)
            except Empty:
                continue

