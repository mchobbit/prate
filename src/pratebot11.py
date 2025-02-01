# -*- coding: utf-8 -*-
"""

TO DO

Detect if users' nicknames change
Make the users' dictionary threadsafe
Make the entire class threadsafe
Use the public keys' fingerprints, not the users' nicknames, as the key for the dictionary
Turn the users' dictionary into a class
Auto-check the nicknames whenever using a dictionary entry

WRITE UNIT TESTS!

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

    def __init__(self, channel, nickname, realname, irc_server, port, crypto_rx_queue):
        super().__init__(channel=channel, nickname=nickname,
                         realname=realname, server=irc_server, port=port)
        self.__paused = False
        self.__paused_lock = ReadWriteLock()
        self.__homies = HomiesDct()
        self.__homies_lock = ReadWriteLock()
        self.crypto_rx_queue = crypto_rx_queue
        self.__scanusers_thread = Thread(target=self.__scanusers_worker_loop, daemon=True)
        self.__scanusers_thread.start()

    @property
    def homies(self):
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
        return True if self.connected and self.joined else False

    @property
    def paused(self):
        self.__paused_lock.acquire_read()
        try:
            retval = self.__paused
            return retval
        finally:
            self.__paused_lock.release_read()

    @paused.setter
    def paused(self, value):
        self.__paused_lock.acquire_write()
        try:
            self.__paused = value
        finally:
            self.__paused_lock.release_write()

    def __scanusers_worker_loop(self):
        while True:
            if not self.connected:
                sleep(.1)
            elif not self.joined:
                sleep(.1)
            else:
                if self.__paused:
                    continue
                self._scan_all_users_for_public_keys_etc()  # Scan the REALNAME (from /whois output) for public keys; then, exchange fernet keys & IP addresses
                sleep(randint(5, 10) / 10.)

    def _scan_all_users_for_public_keys_etc(self, channel=None):
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
                        print("%s has pub keys but no fernet key. I'll try to get one via RQFERN." % user)
                        self.privmsg(user, "RQFERN")
                    elif self.homies[user].ipaddr is None:
                        print("%s has no IP address get. I'll try to get one via RQIPAD." % user)
                        self.privmsg(user, "RQIPAD")  # Request his IP address; in due course, he'll send it via TXIPAD.
                    else:
                        pass  # print("%s has EVERYTHING." % user)

    def _scan_user_for_pubkey(self, user):
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
        self.connection.privmsg(user, msg)
        sleep(randint(16, 20) / 10.)  # Do not send more than 20 messages in 30 seconds! => 30/(((20+16)/2)/10)=16.7 messages per 30 seconds.

    def whois(self, user):
        return self.call_whois_and_wait_for_response(user)

    def crypto_put(self, user, byteblock):
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
        outstr = ""
        for user in self.homies:
            if self.homies[user].keyless is True:
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

    def my_encrypted_ipaddr(self, sender):
        if self.homies[sender].fernetkey is None:
            raise ValueError("Please download %s's fernet key before you try to encrypt." % sender)
        cipher_suite = Fernet(self.homies[sender].fernetkey)
        ipaddr_str = MY_IP_ADDRESS
        cipher_text = cipher_suite.encrypt(ipaddr_str.encode())
        return cipher_text.decode()

    def on_privmsg(self, c, e):  # @UnusedVariable
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
                self.crypto_rx_queue.put([sender, decoded_msg])
        else:
            print("Probably a private message from %s: %s" % (sender, txt))
            print("What is private message %s for? " % cmd)

    def _txfern(self, c, e, sender, stem):
        del c, e
        try:
            decrypted_remote_fernkey = rsa_decrypt(base64.b64decode(stem))
        except ValueError:
            print("Failed to decode the encrypted key in the stem")
        else:
            try:
                self.homies[sender].remotely_supplied_fernetkey = decrypted_remote_fernkey
            except AttributeError:
                print("I cannot update %s's remotely supplied fernetkey: I already have one." % sender)
            else:
                if self.homies[sender].fernetkey is not None:
                    print("YAY! I have %s's fernetkey!" % sender)

    @property
    def crypto_empty(self):
        return self.crypto_rx_queue.empty()

    def crypto_get(self):
        return self.crypto_rx_queue.get()

    def crypto_get_nowait(self):
        return self.crypto_rx_queue.get_nowait()

    def _receiving_his_IP_address(self, sender, stem):
        if self.homies[sender].fernetkey is None:
            print("I do not possess %s's fernetkey. Please negotiate one" % sender)
            return
        cipher_suite = Fernet(self.homies[sender].fernetkey)
        try:
            decoded_msg = cipher_suite.decrypt(stem)
        except InvalidToken:
            return "Warning - failed to decode %s's message. " % sender
        ipaddr = decoded_msg.decode()
        self.homies[sender].ipaddr = ipaddr

    def encrypt_fernetkey(self, user, fernetkey):
        if self.homies[user].keyless is False \
        and self.homies[user].pubkey is not None:
            encrypted_fernetkey = rsa_encrypt(message=fernetkey, public_key=self.homies[user].pubkey)
            b64_encrypted_fernetkey = base64.b64encode(encrypted_fernetkey).decode()
            return b64_encrypted_fernetkey
        else:
            raise ValueError("I can't the fernetkey unless I have a public key to do it with")


class PrateBot:

    def __init__(self, channel, nickname, realname, irc_server, port, crypto_rx_queue):
        self.__time_to_quit = False
        self.__time_to_quit_lock = ReadWriteLock()
        self.__ready_lock = ReadWriteLock()
        self.rx_queue = crypto_rx_queue
        self.bot = CryptoOrientedSingleServerIRCBotWithWhoisSupport(channel, nickname, realname, irc_server, port, crypto_rx_queue)
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
from random import randint
from pratebot11 import *
from my.irctools import *
from cryptography.fernet import Fernet, InvalidToken
import irc.bot
import types

desired_nickname = "clyde"  # nickname='mac' + str(randint(100,999)
crypto_rx_q = queue.LifoQueue()
svr = PrateBot(channel="#prate", nickname=desired_nickname, realname=squeeze_da_keez(MY_RSAKEY.public_key()),
                    irc_server='cinqcent.local', port=6667, crypto_rx_queue=crypto_rx_q)

while not svr.ready:
    sleep(1)




svr.bot.crypto_put('mac2', b'HELLO')
incoming = crypto_rx_q.get()
print(incoming)

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
    crypto_rx_q = queue.LifoQueue()
    svr = PrateBot(channel=my_channel, nickname=desired_nickname,
                                       realname=squeeze_da_keez(MY_RSAKEY.public_key()),
                                       irc_server=my_irc_server, port=my_port,
                                       crypto_rx_queue=crypto_rx_q)

    while not svr.ready:
        sleep(1)

    while True:
        sleep(.1)
        if datetime.datetime.now().second % 3 == 0:
            svr.bot.show_users_dct_info()
#            svr.bot.introduce_myself_to_everyone()  # ...if they have pub keys in their realname fields
            sleep(1)
        try:
            the_user, the_blk = crypto_rx_q.get_nowait()
            print(the_user, "=>", the_blk)
        except Empty:
            pass

