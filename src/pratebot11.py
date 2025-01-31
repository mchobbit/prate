#!/usr/bin/env python3

"""

TO DO

Detect if users' nicknames change
Make the users' dictionary threadsafe
Make the entire class threadsafe
Use the public keys' fingerprints, not the users' nicknames, as the key for the dictionary
Turn the users' dictionary into a class
Auto-check the nicknames whenever using a dictionary entry

WRITE UNIT TESTS!

'''

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
from my.irctools.homies import Homie
from my.irctools.jaracorocks import SingleServerIRCBotWithWhoisSupport
from _queue import Empty
import datetime
from random import randint


class CryptoOrientedSingleServerIRCBotWithWhoisSupport(SingleServerIRCBotWithWhoisSupport):

    def __init__(self, channel, nickname, realname, irc_server, port, crypto_rx_queue):
        super().__init__(channel=channel, nickname=nickname,
                         realname=realname, server=irc_server, port=port)
        self.homies = {}
        self.crypto_rx_queue = crypto_rx_queue
#        self.__bot_thread = Thread(target=self._bot_thread_worker, daemon=True)
        self.__last_printed_status_output_str = None  # For when I print my status onscreen w/ show_users_dct_info()
#        self.__bot_thread.start()

#    def _bot_thread_worker(self):
#        self.start()

    def whois(self, user):
        return self.call_whois_and_wait_for_response(user)

    def crypto_put(self, user, byteblock):
        if user not in self.homies:
            raise ValueError("I cannot send a message to a user whose info I don't possess")
        if type(byteblock) is not bytes:
            raise ValueError("I cannot send a non-binary message to %s. The byteblock must be composed of bytes!" % user)
        if self.homies[user].fernetkey is None:
            raise ValueError("I cannot encrypt a message with a null fernet key")
        cipher_suite = Fernet(self.homies[user].fernetkey)
        cipher_text = cipher_suite.encrypt(byteblock)
        self.connection.privmsg(user, "TXTXTX%s" % cipher_text.decode())
        sleep(randint(16, 20) // 10.)  # Do not send more than 20 messages in 30 seconds! => 30/(((20+16)/2)/10)=16.7 messages per 30 seconds.

    def show_users_dct_info(self, force=True):
        outstr = ""
        for user in self.homies:
            if user == self.nickname or user not in self.homies:
                pass
            elif self.homies[user].pubkey is None:
                outstr += "\n%-20s pubkey nope" % user
            elif self.homies[user].fernetkey is None:
                outstr += "\n%-20s pubkey OK; fernetkey nope" % user
            elif self.homies[user].ipaddr is None:
                outstr += "\n%-20s pubkey OK  fernetkey OK; IP nope" % user
            else:
                outstr += "\n%-20s pubkey OK, fernetkey OK, IP %s" % (user, self.homies[user].ipaddr)
                if self.homies[user].pubkey is None \
                                        or self.homies[user].fernetkey is None \
                                        or self.homies[user].ipaddr is None:
                    print("WHAAAAAA?")
        if force or self.__last_printed_status_output_str != outstr:
            self.__last_printed_status_output_str = outstr
            print(outstr)

    def my_encrypted_ipaddr(self, sender):
        if sender not in self.homies or self.homies[sender].fernetkey is None:
            raise ValueError("Please download %s's fernet key before you try to encrypt." % sender)
        cipher_suite = Fernet(self.homies[sender].fernetkey)
        ipaddr_str = MY_IP_ADDRESS
        cipher_text = cipher_suite.encrypt(ipaddr_str.encode())
        return cipher_text.decode()

    def on_privmsg(self, c, e):
        _connection = c
        if e is None:  # e is event
            raise AttributeError("act_on_msg_from_irc() has an e of None")
        if e.source:
            sender = e.source.split('@')[0].split('!')[0]
        else:
            sender = None
        txt = e.arguments[0]
        cmd = txt[:6]
        stem = txt[6:]
        print("Private message from", sender, ":", txt)
        if sender == self.nickname:
            raise ValueError("WHY AM I TALKING TO MYSELF?")
        if sender not in self.homies:  # or self.homies[user].pubkey is None:
            self.homies[sender] = Homie(nickname=sender)
        if e.type == 'foo':
            print("e type is foo for %s; this is a foo-tile attempt at a test." % e.target)
        elif cmd == "RQFERN":  # you asked for a copy of my fernet key
            if self.homies[sender].pubkey is None:
                print("I can't transmit my fernet key: I don't know %s's public key!" % sender)
            else:
                self.connection.privmsg(sender, "TXFERN%s" % self.encrypt_fernetkey(sender, self.homies[sender].my_locally_generate_fernet_key))
        elif cmd == "TXFERN":
            self.homies[sender].he_sent_me_this_fernetkey = rsa_decrypt(base64.b64decode(stem))
        elif cmd == "RQIPAD":
            if sender not in self.homies or self.homies[sender].fernetkey is None:
                print("I cannot send my IP address out: I don't know %s's fernet key!" % sender)
            else:
                self.connection.privmsg(sender, "TXIPAD%s" % self.my_encrypted_ipaddr(sender))
        elif cmd == "TXIPAD":
            self._receiving_his_IP_address(sender, stem)
        elif cmd == 'TXTXTX':  # This means that some data was TX'd to us.
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

    @property
    def crypto_empty(self):
        return self.crypto_rx_queue.empty()

    def crypto_get(self):
        return self.crypto_rx_queue.get()

    def crypto_get_nowait(self):
        return self.crypto_rx_queue.get_nowait()

    def _receiving_his_IP_address(self, sender, stem):
        if self.homies[sender].fernetkey is None:
            raise ValueError("I do not possess %s's fernetkey. Please negotiate one" % sender)
        cipher_suite = Fernet(self.homies[sender].fernetkey)
        try:
            decoded_msg = cipher_suite.decrypt(stem)
        except InvalidToken:
            return "Warning - failed to decode %s's message. " % sender
        ipaddr = decoded_msg.decode()
        self.homies[sender].ipaddr = ipaddr

    def get_pubkey_from_whois(self, user):
        try:
            whois_res = self.call_whois_and_wait_for_response(user)
            squozed_key = whois_res.split(' ', 3)[-1]
            return unsqueeze_da_keez(squozed_key)
        except (AttributeError, ValueError, IndexError, TimeoutError):
            return None

    def encrypt_fernetkey(self, user, fernetkey):
        if user not in self.homies or fernetkey is None:
            raise ValueError("Do not try to encrypt the fernetkey until you've CREATED a fernetkey.")
        encrypted_fernetkey = rsa_encrypt(message=fernetkey, public_key=self.homies[user].pubkey)
        b64_encrypted_fernetkey = base64.b64encode(encrypted_fernetkey).decode()
        return b64_encrypted_fernetkey

    def introduce_myself_to_everyone(self, channel=None):
        if channel is None:
            channel = self.initial_channel
        all_users = None
        try:
            all_users = list(self.channels[channel].users())
        except (KeyError, IndexError):
            print("WARNING - I am not in %s anymore" % channel)
        else:
            for user in all_users:
                self.introduce_myself_to_user(user)

    def introduce_myself_to_user(self, user):
        # RQFERN TXFERN RQIPAD TXIPAD
        if user == self.nickname:
#            print("Skipping %s because he's me" % user)
            return
        if user not in self.homies:  # or self.homies[user].pubkey is None:
            self.homies[user] = Homie(nickname=user)
        if self.homies[user].pubkey is None:
            self.homies[user].pubkey = self.get_pubkey_from_whois(user)
            return  # Can't get pubkey for this user
        if self.homies[user].fernetkey is None and self.homies[user].he_sent_me_this_fernetkey is None:
            self.connection.privmsg(user, "RQFERN")  # Request his fernet key
            return
        if self.homies[user].fernetkey is None and self.homies[user].he_sent_me_this_fernetkey is not None:
            print("our two fernet keys are", self.homies[user].he_sent_me_this_fernetkey, "and", self.homies[user].my_locally_generate_fernet_key)
            self.homies[user].fernetkey = self.homies[user].he_sent_me_this_fernetkey if self.homies[user].he_sent_me_this_fernetkey > self.homies[user].my_locally_generate_fernet_key else self.homies[user].my_locally_generate_fernet_key
            print("We choose", self.homies[user].fernetkey, "as our fernet key.")
            return
        if self.homies[user].ipaddr is None:
            self.connection.privmsg(user, "RQIPAD")  # Request his IP address


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
            return True if self.bot.connected and self.bot.joined else False
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
            pass

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

svr.crypto_put('mac2', 'HELLO')
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

    svr.bot.whois('clyde')
    svr.bot.whois('mchobbit')
#    svr.bot.crypto_put('mac2', 'HELLO')

#    incoming = crypto_rx_q.get()
#    print(incoming)
    svr.bot.introduce_myself_to_everyone()

    while True:
        sleep(.1)
        if datetime.datetime.now().second % 30 == 0:
            svr.bot.show_users_dct_info()
            svr.bot.introduce_myself_to_everyone()  # ...if they have pub keys in their realname fields
            sleep(1)
        try:
            user, blk = crypto_rx_q.get()
            print(user, "=>", blk)
        except Empty:
            pass

