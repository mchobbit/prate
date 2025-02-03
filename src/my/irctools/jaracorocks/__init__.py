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

_RQPK_ = "RQPK"
_TXPK_ = "TXPK"
_RQFE_ = "RQFE"
_TXFE_ = "TXFE"
_RQIP_ = "RQIP"
_TXIP_ = "TXIP"
_TXTX_ = "TXTX"


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
        self.paused = False

    def shutitdown(self):
        self.__stopstopstop = True
        self.__scanusers_thread.join()
        self.__crypto_tx_thread.join()

    def generate_fingerprint(self, user=None):
        if self.is_pubkey_in_realname:
            return squeeze_da_keez(self.rsa_key.public_key())
        else:
            if user is None:
                user = self.nickname
            return sha1(user)

    # @property
    # def fingerprint(self):
    #     if self.is_pubkey_in_realname:
    #         return self.generate_fingerprint()
    #     else:
    #         try:
    #             return self.generate_fingerprint(self.nickname)
    #         except (MyIrcStillConnectingError, AttributeError, ValueError):
    #             return None

    @property
    def is_pubkey_in_realname(self):
        return self.__is_pubkey_in_realname

    @property
    def rsa_key(self):
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
        while not self.__stopstopstop:
            if not self.ready:
                print("Waiting for the bot to be ready...")
                while not self.ready:
                    sleep(.1)
                print("Bot is ready now. Proceeding...")
            elif self.paused:
                sleep(.2)
            else:
                irc_channel_members = list(self.channels[self.initial_channel].users())
                new_users = [str(u) for u in irc_channel_members if u not in the_userlist and str(u) != self.nickname]
                dead_users = [str(u) for u in the_userlist if u not in irc_channel_members and str(u) != self.nickname]
                for user in dead_users:
                    print("%s has died. Removing him from our list." % user)
                    self.load_homie_pubkey(user, None)
                    the_userlist.remove(user)
                for user in new_users:
                    the_userlist += [user]
                    print("New user: %s" % user)
                shuffle(new_users)
                for user in [str(u) for u in the_userlist if str(u) != self.nickname]:
                    self.scan_a_user_for_fingerprints_publickeys_etc(user)
                for _ in range(randint(40, 60)):
                    sleep(.1)
                    if self.__stopstopstop:
                        break

    def scan_a_user_for_fingerprints_publickeys_etc(self, user):
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
            assert(self.homies[user].didwelook)
            assert(not self.homies[user].keyless)
            print("%s has a null public key, but we looked. Perhaps we were offline at the time. I'll try again in a second or two." % user)
        elif self.homies[user].fernetkey is None:
            assert(self.homies[user].didwelook)
            assert(not self.homies[user].keyless)
            assert(self.homies[user].pubkey is not None)
            print("Initiating fernet key exchange with %s" % user)
            self.privmsg(user, "%s%s" % (_RQFE_, squeeze_da_keez(self.rsa_key.public_key())))
        elif self.homies[user].ipaddr is None:
            assert(self.homies[user].didwelook)
            assert(not self.homies[user].keyless)
            assert(self.homies[user].pubkey is not None)
            assert(self.homies[user].fernetkey is not None)
            print("Initiating IP address exchange with %s" % user)
            self.privmsg(user, "%s%s" % (_RQIP_, squeeze_da_keez(self.rsa_key.public_key())))  # Request his IP address; in due course, he'll send it via TXIPAD.
        else:
            return user  # He's kosher

    def load_homie_pubkey(self, user, pubkey=None):
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

    @property
    def realname(self):
        return self.call_whois_and_wait_for_response(self.nickname).split(' ', 4)[-1]

    def __load_homie_pubkey_from_whois_record(self, user):
        if type(user) is not str:
            raise ValueError(user, "should be type str")
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
                        print("HEY! HAS %s'S PUBLIC KEY CHANGED?!?!" % user)  # print("New key:", new_pk)
                    self.homies[user].pubkey = new_pk
                    break  # ...from 'i'
            except TimeoutError:
                continue
        self.homies[user].didwelook = True

    def __load_homie_pubkey_from_negotiation_via_whois_fingerprint(self, user):
        try:
            his_fprint = self.call_whois_and_wait_for_response(user).split(' ', 4)[-1]
        except AttributeError:
            his_fprint = None
            print("Unable to load %s's /whois record. This means I don't know their fingerprint." % user)
            print("I am therefore assuming that %s is not a homie." % user)
            print("Let's try again later.")
            return
        shouldbe_fprint = self.generate_fingerprint(user)
#        print("%s has a fingerprint of %s; if he's a homie, it would be %s" % (user, his_fprint, shouldbe_fprint))
        if his_fprint == shouldbe_fprint:
#            print("I do believe that %s is a homie" % user)
#            print("I'll initiate a public key exchange now.")
            print("I am requesting %s's public key" % user)
            self.privmsg(user, "%s%s" % (_RQPK_, squeeze_da_keez(self.rsa_key.public_key())))
        else:
#            print("%s is not a homie." % user)
            pass

    def privmsg(self, user, msg):
        """Send a private message on IRC. Then, pause; don't overload the server."""
        self.connection.privmsg(user, msg)
        sleep(randint(16, 20) / 10.)  # 20 per 30s... or 2/3 per 1s... or 1s per 3/2... or 1.5 per second.

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

    def show_users_dct_info(self):
        """Write the list of our users (and their crypto info) to screen."""
        self.__homies_lock.acquire_read()
        outstr = "\n%-30s  %s   <==pubkey     vv---fernet key---vv     IP==>   %s" % (self.nickname, squeeze_da_keez(self.rsa_key.public_key())[-12:-8], MY_IP_ADDRESS)
        for user in self.homies:
            if type(user) is not str:
                print("WARNING -- %s it not a string" % str(user))
            if user == self.nickname:
                pass  # print("WARNING - our nickname is on a list of homies")
            if self.homies[user].keyless is True:
                outstr += "\n%-30s  nope" % user
            elif self.homies[user].pubkey is None:
                outstr += "\n%-30s  unk" % user
            elif self.homies[user].fernetkey is None:
                outstr += "\n%-30s  %s   unk" % (user, squeeze_da_keez(self.homies[user].pubkey)[-12:-8])
            elif self.homies[user].ipaddr is None:
                outstr += "\n%-30s  %s   %s   nope" % (user, squeeze_da_keez(self.homies[user].pubkey)[-12:-8], self.homies[user].fernetkey.decode())
            else:
                outstr += "\n%-30s  %s   %s   %s" % (user, squeeze_da_keez(self.homies[user].pubkey)[-12:-8], self.homies[user].fernetkey.decode(), self.homies[user].ipaddr)
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
        if sender == self.nickname:
            raise ValueError("WHY AM I TALKING TO MYSELF?")
        elif cmd == _RQPK_:
            if stem != '':
                print("We received %s's public key and a request for a copy of ours." % sender)
                self.homies[sender].pubkey = unsqueeze_da_keez(stem)  # self.load_homie_pubhey etc.
                self.homies[sender].keyless = False
                self.homies[sender].didwelook = True
                self.homies[sender].ipaddr = None
            print("We are sending %s a copy of our public key." % sender)
            self.privmsg(sender, "%s%s" % (_TXPK_, squeeze_da_keez(self.rsa_key.public_key())))
        elif cmd == _TXPK_:
            print("We received a public key from %s" % sender)
            self.homies[sender].pubkey = unsqueeze_da_keez(stem)
            self.homies[sender].keyless = False
            self.homies[sender].didwelook = True
            self.homies[sender].ipaddr = None
        elif cmd == _RQFE_:  # Sender requested a copy of my fernet key
            self._request_fernet_key_exchange(sender, stem)
#            self.reactor.process_once()  # Is this necessary?
        elif cmd == _TXFE_:
            self._transmit_my_fernet_key(sender, stem)
        elif cmd == _RQIP_:
            self._request_his_ip_address(sender, stem)
        elif cmd == _TXIP_:
            self._transmit_my_ip_address(sender, stem)
        elif cmd == _TXTX_:  # This means that some data was TX'd to us.
            self._receive_and_decrypt_message(sender, stem)
        else:
            print("Probably a private message from %s: %s" % (sender, txt))
            print("What is private message %s for? " % cmd)

    def _request_fernet_key_exchange(self, sender, stem):
        if stem != '':
            self.save_pubkey_from_stem(sender, stem)
        if self.homies[sender].keyless is True or self.homies[sender].pubkey is None:
            print("I can't send %s to %s: he's keyless" % (_RQFE_, sender))
        else:
            print("%s has initiated fernet key exchange." % sender)
            self.privmsg(sender, "%s%s" % (_TXFE_, self.encrypt_fernetkey(sender, self.homies[sender].locally_generated_fernetkey)))

    def _transmit_my_fernet_key(self, user, stem):
        """If cmd==TXFERN is received, receive the user's fernet key & save it to our homie database."""
        try:
            decrypted_remote_fernetkey = rsa_decrypt(base64.b64decode(stem), self.rsa_key)
        except ValueError:
            print("_txfern %s Failed to decode the encrypted fernet key in the stem. Is his copy of my public key out of date?" % user)
            print("Requesting a public key from %s" % user)
            self.homies[user].remotely_supplied_fernetkey = None
            self.privmsg(user, "%s%s" % (_RQPK_, squeeze_da_keez(self.rsa_key.public_key())))
        else:
            try:
                self.homies[user].remotely_supplied_fernetkey = decrypted_remote_fernetkey
            except AttributeError:
                print("I cannot update %s's remotely supplied fernetkey: I already have one." % user)
            else:
                if self.homies[user].fernetkey is not None:
                    pass  # print("YAY! I have %s's fernetkey!" % user)

    def _request_his_ip_address(self, sender, stem):
        if stem != '':
            self.save_pubkey_from_stem(sender, stem)
        if self.homies[sender].keyless is True:
            print("%s requests my IP address, but he's keyless." % sender)
        elif self.homies[sender].pubkey is None:
            print("%s requests my IP address, but I don't have his public key." % sender)
        elif self.homies[sender].fernetkey is None:
            print("%s requests my IP address, but we don't have a fernet key yet." % sender)
        else:
            print("%s requests my IP address, and I'm sending it." % sender)
            self.privmsg(sender, "%s%s" % (_TXIP_, self.my_encrypted_ipaddr(sender)))

    def _transmit_my_ip_address(self, sender, stem):
        try:
            self._receiving_his_IP_address(sender, stem)
            print("%s sent me his IP address. Yay." % sender)
        except InvalidToken:
            print("%s used the wrong fernet key to encrypt a message. To rectify, I'll initiate a new fernet key exchange." % sender)
            self.homies[sender].remotely_supplied_fernetkey = None
            self.homies[sender].pubkey = None
            self.privmsg(sender, "%s%s" % (_RQFE_, squeeze_da_keez(self.rsa_key.public_key())))

    def _receive_and_decrypt_message(self, sender, stem):
        if self.homies[sender].fernetkey is None:
            print("Cannot decipher message from %s: we have no fernet key." % sender)
            print("This might mean I'm using someone's ex-nickname & %s doesn't realize that." % sender)
        else:
            try:
                cipher_suite = Fernet(self.homies[sender].fernetkey)
                decoded_msg = cipher_suite.decrypt(stem).decode()
            except InvalidToken:
                print("Warning - txtxtx - failed to decode %s's message (key bad? ciphertext bad?)." % sender)
            except KeyError:
                print("Warning - txtxtx - failed to decode %s's message (fernet key not found?). Is his copy of my public key out of date?" % sender)
                self.privmsg(sender, "%s%s" % (_RQFE_, squeeze_da_keez(self.rsa_key.public_key())))
            else:
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
        if self.homies[user].fernetkey is None:
            print("I do not possess %s's fernetkey. Please negotiate one" % user)
            return
        cipher_suite = Fernet(self.homies[user].fernetkey)
        decoded_msg = cipher_suite.decrypt(stem)
        ipaddr = decoded_msg.decode()
        self.homies[user].ipaddr = ipaddr
        # EXCEPTION MIGHT BE THROWN. It would be InvalidKey.

    def encrypt_fernetkey(self, user, fernetkey):
        """Encrypt the user's fernet key with the user's public key."""
        if self.homies[user].keyless is False \
        and self.homies[user].pubkey is not None:
            encrypted_fernetkey = rsa_encrypt(message=fernetkey, public_key=self.homies[user].pubkey)
            b64_encrypted_fernetkey = base64.b64encode(encrypted_fernetkey).decode()
            return b64_encrypted_fernetkey
        else:
            raise ValueError("I can't the fernetkey unless I have a public key to do it with")
