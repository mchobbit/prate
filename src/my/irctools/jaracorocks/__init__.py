"""PrateBot class(es) for miniircd-ish... boring.

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

from my.irctools.cryptoish import sha1, squeeze_da_keez

import sys
import queue
from time import sleep
from threading import Thread, Lock

from cryptography.fernet import Fernet, InvalidToken
import base64
from my.globals import MY_IP_ADDRESS
from my.classes.readwritelock import ReadWriteLock
from my.irctools.cryptoish import rsa_decrypt, rsa_encrypt, unsqueeze_da_keez
from _queue import Empty
from random import randint, choice, shuffle
from my.classes.homies import HomiesDct
from my.classes.exceptions import MyIrcRealnameTruncationError, MyIrcConnectionError, MyIrcStillConnectingError
from my.irctools.jaracorocks.vanilla import SingleServerIRCBotWithWhoisSupport
import datetime
from my.classes import MyTTLCache
import time

_RQPK_ = "RQPK"
_TXPK_ = "TXPK"
_RQFE_ = "RQFE"
_TXFE_ = "TXFE"
_RQIP_ = "RQIP"
_TXIP_ = "TXIP"
_TXTX_ = "TXTX"


def groovylsttotxt(lst):
    return ('%3d users' % len(lst)) if len(lst) > 5 else ' '.join(lst)


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
        is_pubkey_in_realname (bool): If True, use realname to store the
            public key. If False, create a fingerprint w/ sha1 instead.
        rsa_key (RSA.RsaKey): Our rsa key.
        irc_server (str): The IRC server URL.
        port (int): The port number of the IRC server.
        crypto_rx_queue (LifoQueue): Decrypted user-and-msg stuff goes here.
        crypto_tx_queue (LifoQueue): User-and-msg stuff to be encrypted goes here.

    """

    def __init__(self, channel, nickname, rsa_key, is_pubkey_in_realname,
                 irc_server, port, crypto_rx_queue, crypto_tx_queue):
        self.__prev_showtxt_op = None
        self.__crypto_rx_queue = crypto_rx_queue
        self.__crypto_tx_queue = crypto_tx_queue
        self.__homies_lock = ReadWriteLock()
        self.__scan_a_user_mutex = Lock()
        self.__repop_mutex = Lock()
        self.__is_pubkey_in_realname = is_pubkey_in_realname
        self.__homies = HomiesDct()
        self.__rsa_key = rsa_key
        self.__stopstopstop = False
        super().__init__(channel, nickname, self.generate_fingerprint(nickname), irc_server, port)
        self.__scanusers_thread = Thread(target=self.__scanusers_worker_loop, daemon=True)
        self.__crypto_tx_thread = Thread(target=self.__crypto_tx_loop, daemon=True)
        self.__scanusers_thread.start()
        self.__crypto_tx_thread.start()

    def shutitdown(self):
        """Trigger the shutdown of all our processes."""
        self.__stopstopstop = True
        self.__scanusers_thread.join()
        self.__crypto_tx_thread.join()

    def generate_fingerprint(self, user=None):
        """Generate a fingerprint for the specified user."""
        if self.is_pubkey_in_realname:
            return squeeze_da_keez(self.rsa_key.public_key())
        else:
            if user is None:
                user = self.nickname
            return sha1(user)

    @property
    def fingerprint(self):
        """Returns the fingerprint for my current nickname."""
        return self.generate_fingerprint(self.nickname)

    @property
    def is_pubkey_in_realname(self):
        """Should users keep their public keys in their /whois realname fields?"""
        return self.__is_pubkey_in_realname

    @property
    def rsa_key(self):
        """Our public key."""
        return self.__rsa_key

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

    def __crypto_tx_loop(self):
        """Pull from the queue. Encrypt each item. Send it."""
        while not self.__stopstopstop:
            sleep(.1)
            try:
                (user, byteblock) = self.__crypto_tx_queue.get_nowait()
            except Empty:
                pass
            else:
                if self.homies[user].keyless:
                    print("I cannot crypto_put() to %s: he is keyless" % user)
                elif self.homies[user].pubkey is None:
                    print("I cannot crypto_put() to %s: idk his pubkey" % user)
                elif self.homies[user].fernetkey is None:
                    print("I cannot crypto_put() to %s: idk his fernetkey" % user)
                elif self.homies[user].ipaddr is None:
                    print("I cannot crypto_put() to %s: idk his ipaddr" % user)
                else:
                    self.crypto_put(user, byteblock)

    def __scanusers_worker_loop(self):
        """Indefinitely scan the current channel for any users who have public keys in their realname fields."""
        the_userlist = []
        irc_channel_members = None
        while not self.__stopstopstop:
            sleep(.1)
            if not self.ready:
                print("Waiting for the bot to be ready...")
                while not self.ready:
                    sleep(.1)
                print("Bot is ready now. Proceeding...")
            elif datetime.datetime.now().second % 15 == 0:
                irc_channel_members = list(self.channels[self.initial_channel].users())
            elif irc_channel_members is None:
                pass
            else:
                new_users = [str(u) for u in irc_channel_members if u not in the_userlist and str(u) != self.nickname]
                dead_users = [str(u) for u in the_userlist if u not in irc_channel_members and str(u) != self.nickname]
                for user in dead_users:
                    print("%-20s has died. Removing him from our list." % user)
                    self.load_homie_pubkey(user, None)
                    the_userlist.remove(user)
                for user in new_users:
                    the_userlist += [user]
                shuffle(new_users)
                the_users_we_care_about = [str(u) for u in the_userlist if str(u) != self.nickname]
                self.__scan_these_users_for_fingerprints_publickeys_etc(the_users_we_care_about)

    def __scan_these_users_for_fingerprints_publickeys_etc(self, the_users_we_care_about):
        for user in the_users_we_care_about:
            self.scan_a_user_for_fingerprints_publickeys_etc(user)

    def scan_a_user_for_fingerprints_publickeys_etc(self, user):
        """Scan this user for a fingerprint, a public key, fernet keys, etc."""
        with self.__scan_a_user_mutex:
            self.__scan_a_user_for_fingerprints_publickeys_etc(user)

    def __scan_a_user_for_fingerprints_publickeys_etc(self, user):
        if type(user) is not str:
            raise ValueError("Supplied parameter", user, "must be a string")
        if not self.homies[user].didwelook:
            self.load_homie_pubkey(user)  # via fingerprint & RXPK/TXPK if necessary
        elif self.homies[user].keyless:
            pass  # TODO: If datetime.datetime.now().second == 0, re-scan the 'keyless' to see if they're actually keyless
        elif self.homies[user].pubkey is None:
            print("%-20s has a null public key, but we looked. Perhaps we were offline at the time. I'll try again in a second or two." % user)
            sleep(randint(15, 40) / 10.)
        elif self.homies[user].fernetkey is None:
            self.initiate_fernet_key_negotiation(user)
        elif self.homies[user].ipaddr is None:
            self.privmsg(user, "%s%s" % (_RQIP_, squeeze_da_keez(self.rsa_key.public_key())))  # Request his IP address; in due course, he'll send it via TXIPAD.
        else:
            return user  # He's kosher

    def load_homie_pubkey(self, user, pubkey=None):
        """Obtain the specified user's public key, if there is one."""
        with self.__repop_mutex:
            self.__load_homie_pubkey(user, pubkey)

    def __load_homie_pubkey(self, user, pubkey=None):
        if pubkey is not None:
            self.__load_homie_pubkey_from_parameter(user, unsqueeze_da_keez(pubkey))
        if self.is_pubkey_in_realname:
            self.__load_homie_pubkey_from_whois_record(user)
        else:
            self.__load_homie_pubkey_from_negotiation_via_whois_fingerprint(user)

    def __load_homie_pubkey_from_parameter(self, user, pubkey):
        if type(user) is not str:
            raise ValueError(user, "should be type str")
        self.homies[user].didwelook = True
        self.homies[user].keyless = False  # He's GONE. He is neither keyful nor keyless. Keyless means "He's here & he has no key."
        self.homies[user].pubkey = pubkey

    def __load_homie_pubkey_from_whois_record(self, user):
        if type(user) is not str:
            raise ValueError(user, "should be type str")
        self.homies[user].didwelook = False
        self.homies[user].keyless = False
        old_pk = self.homies[user].pubkey
        new_pk = None
        try:
            whois_res = self.call_whois_and_wait_for_response(user)
            squozed_key = whois_res.split(' ', 4)[-1]
            unsqueezed_key = unsqueeze_da_keez(squozed_key)
        except (ValueError, AttributeError):
            self.homies[user].keyless = True  # It's not a key.
        except TimeoutError:
            pass
        else:
            new_pk = unsqueezed_key
            if old_pk is not None and old_pk != new_pk:
                print("HEY! HAS %s'S PUBLIC KEY CHANGED?!?!" % user)
            self.homies[user].pubkey = new_pk
        self.homies[user].didwelook = True

    def __load_homie_pubkey_from_negotiation_via_whois_fingerprint(self, user):
        try:
            his_fprint = self.call_whois_and_wait_for_response(user).split(' ', 4)[-1]
        except AttributeError:
            his_fprint = None
            print("Unable to load %s's /whois record. This means I don't know their fingerprint." % user)
            print("Let's try again later.")
            return
        shouldbe_fprint = self.generate_fingerprint(user)
        if his_fprint == shouldbe_fprint:
            self.wipe_our_copy_of_user_key_and_reinitiate_public_key_negotiation(user)
        else:
            pass  # print("%-20s is not a homie." % user)

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
            self.privmsg(user, "%s%s" % (_TXTX_, cipher_text.decode()))
        else:
            raise ValueError("pubkey and/or fernetkey missing")

    def show_users_dct_info(self, force=False):
        """Write the list of our users (and their crypto info) to screen."""
        kosher_homies = []
        nope = []
        unknown = []
        pubkey_only = []
        PK_plus_fern = []
        self.__homies_lock.acquire_read()
        outstr = "\n%-20s      %s" % (self.nickname, MY_IP_ADDRESS)
        for user in self.homies:
            if type(user) is not str:
                print("WARNING -- %s it not a string" % str(user))
            if user == self.nickname:
                pass  # print("WARNING - our nickname is on a list of homies")
            if self.homies[user].keyless is True:
                nope += [user]
            elif self.homies[user].pubkey is None:
                unknown += [user]
            elif self.homies[user].fernetkey is None:
                pubkey_only += [user]
            elif self.homies[user].ipaddr is None:
                PK_plus_fern += [user]
            else:
                kosher_homies += [user]
        outstr += """
Nope   :%s
Unknown:%s
PK only:%s
PK+Fern:%s
Kosher :%s
""" % (groovylsttotxt(nope), groovylsttotxt(unknown),
       groovylsttotxt(pubkey_only), groovylsttotxt(PK_plus_fern),
       groovylsttotxt(kosher_homies))
        if outstr != self.__prev_showtxt_op or force is True:
            self.__prev_showtxt_op = outstr
            print(outstr)
        self.__homies_lock.release_read()

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
                pass  # print("Saving %s's public key from incoming msg (not from whois)" % sender)
            else:
                print("Saving %s's new pubkey from incoming msg (not from whois)" % sender)
            self.homies[sender].ipaddr = None
            self.homies[sender].keyless = False
            self.homies[sender].didwelook = True
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
        cmd = txt[:4]
        stem = txt[4:]
        codes_and_calls = {_RQPK_: self._he_initiated_a_public_key_exchange,
                           _TXPK_: self._he_sent_me_his_public_key_in_response,
                           _RQFE_: self._he_initiated_a_fernet_key_negotiation,
                           _TXFE_: self._he_sent_me_a_fernet_key_accordingly,
                           _RQIP_: self._he_requested_my_ip_address_and_enclosed_his_own,
                           _TXIP_: self._he_sent_me_his_ip_address_because_i_asked,
                           _TXTX_: self._receive_and_decrypt_message}
        if sender == self.nickname:
            raise ValueError("WHY AM I TALKING TO MYSELF?")
        elif cmd in codes_and_calls:
            codes_and_calls[cmd](sender, stem)
        else:
            print("What does this mean? => >>>%s<<<" % txt)

    def _he_initiated_a_public_key_exchange(self, sender, stem):
        self.homies[sender].pubkey = unsqueeze_da_keez(stem)
        self.homies[sender].keyless = False
        self.homies[sender].didwelook = True
        self.homies[sender].ipaddr = None
        self.privmsg(sender, "%s%s" % (_TXPK_, squeeze_da_keez(self.rsa_key.public_key())))

    def _he_sent_me_his_public_key_in_response(self, sender, stem):
        self.homies[sender].pubkey = unsqueeze_da_keez(stem)
        self.homies[sender].keyless = False
        self.homies[sender].didwelook = True
        self.homies[sender].ipaddr = None

    def _he_initiated_a_fernet_key_negotiation(self, sender, stem):
        self.save_pubkey_from_stem(sender, stem)
        if self.homies[sender].keyless is True or self.homies[sender].pubkey is None:
            print("I can't send request a fernet key from %s: he's keyless" % sender)
        else:
            self.privmsg(sender, "%s%s" % (_TXFE_, self.encrypt_fernetkey_for_user(sender, self.homies[sender].locally_generated_fernetkey)))

    def _he_sent_me_a_fernet_key_accordingly(self, sender, stem):
        """If cmd==TXFERN is received, receive the sender's fernet key & save it to our homie database."""
        try:
            decrypted_remote_fernetkey = rsa_decrypt(base64.b64decode(stem), self.rsa_key)
        except ValueError:
            print("_txfern %s Failed to decode the encrypted fernet key in the stem. Is his copy of my public key out of date?" % sender)
            print("Requesting a public key from %s, to force a fresh negotiation of public keys between us." % sender)
            self.wipe_our_copy_of_user_key_and_reinitiate_public_key_negotiation(sender)
        else:
            try:
                self.homies[sender].remotely_supplied_fernetkey = decrypted_remote_fernetkey
            except AttributeError:
                print("I cannot update %s's remotely supplied fernetkey: I already have one." % sender)
            else:
                if self.homies[sender].fernetkey is None:
                    print("I'm still trying to pair up the fernet keys for talking with %s" % sender)
                # else:
                #     print("YAY! I have %s's fernetkey. We can talk to one another now." % sender)

    def _he_requested_my_ip_address_and_enclosed_his_own(self, sender, stem):
        self.save_pubkey_from_stem(sender, stem)  # He also sends us his public key, just in case our copy is outdated
        if self.homies[sender].keyless is True:
            print("%-20s requests my IP address, but he's keyless." % sender)
        elif self.homies[sender].pubkey is None:
            print("%-20s requests my IP address, but I don't have his public key. I'll ask for it." % sender)
            self.wipe_our_copy_of_user_key_and_reinitiate_public_key_negotiation(sender)
        elif self.homies[sender].fernetkey is None:
            print("%-20s requests my IP address, but we don't have a fernet key yet. I'll ask for his." % sender)
            self.initiate_fernet_key_negotiation(sender)
        else:
            print("%-20s requests my IP address, and I'm sending it." % sender)
            self.privmsg(sender, "%s%s" % (_TXIP_, self.my_encrypted_ipaddr(sender)))

    def _he_sent_me_his_ip_address_because_i_asked(self, sender, stem):
        try:
            self._receiving_his_IP_address(sender, stem)
            print("%-20s sent me his IP address. Yay." % sender)
        except InvalidToken:
            print("%-20s used the wrong fernet key to encrypt a message. To rectify, I'll initiate a new fernet key exchange." % sender)
            self.initiate_fernet_key_negotiation(sender)

    def _receive_and_decrypt_message(self, sender, stem):
        success = False
        if self.homies[sender].fernetkey is None:
            print("Cannot decipher message from %s: we have no fernet key." % sender)
            print("This might mean I'm using someone's ex-nickname & %s doesn't realize that." % sender)
            print("To calm him down a bit, I'm sending him a request for his public key.")
            if self.is_pubkey_in_realname:
                print("Granted, we store our public keys in our realnames, but my /whois entry might be out of date. Who knows? So, let's skip that & assume the worst.")
            print("Anyhow, let's request a new public key from him & go from there.")
        else:
            try:
                cipher_suite = Fernet(self.homies[sender].fernetkey)
                decoded_msg = cipher_suite.decrypt(stem).decode()
            except InvalidToken:
                print("Warning - txtxtx - failed to decode %s's message (key bad? ciphertext bad?)." % sender)
            except KeyError:
                print("Warning - txtxtx - failed to decode %s's message (fernet key not found?). Is his copy of my public key out of date?" % sender)
            else:
                self.__crypto_rx_queue.put([sender, decoded_msg.encode()])
                success = True
        # If you get here, it means we failed to decode the incoming data
        if not success:
            self.wipe_our_copy_of_user_key_and_reinitiate_public_key_negotiation(sender)

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

    def _receiving_his_IP_address(self, sender, stem):
        """Receive the sender's IP address."""
        if self.homies[sender].fernetkey is None:
            print("I do not possess %s's fernetkey. Please negotiate one" % sender)
            return
        cipher_suite = Fernet(self.homies[sender].fernetkey)
        decoded_msg = cipher_suite.decrypt(stem)
        ipaddr = decoded_msg.decode()
        self.homies[sender].ipaddr = ipaddr
        # EXCEPTION MIGHT BE THROWN. It would be InvalidKey.

    def wipe_our_copy_of_user_key_and_reinitiate_public_key_negotiation(self, user):
        self.homies[user].remotely_supplied_fernetkey = None
        self.homies[user].keyless = False
        self.homies[user].pubkey = None
        print("%-20s appears to be a homie. I am requesting his public key" % user)
        self.privmsg(user, "%s%s" % (_RQPK_, squeeze_da_keez(self.rsa_key.public_key())))

    def initiate_fernet_key_negotiation(self, user):
        self.homies[user].remotely_supplied_fernetkey = None
        self.privmsg(user, "%s%s" % (_RQFE_, squeeze_da_keez(self.rsa_key.public_key())))  # Request his fernet key

    def encrypt_fernetkey_for_user(self, user, fernetkey):
        """Encrypt the user's fernet key with the user's public key."""
        if self.homies[user].keyless is False \
        and self.homies[user].pubkey is not None:
            encrypted_fernetkey = rsa_encrypt(message=fernetkey, public_key=self.homies[user].pubkey)
            b64_encrypted_fernetkey = base64.b64encode(encrypted_fernetkey).decode()
            return b64_encrypted_fernetkey
        else:
            raise ValueError("I can't the fernetkey unless I have a public key to do it with")
