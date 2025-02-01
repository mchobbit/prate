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
from random import randint
from testbot9 import *
from my.irctools import *
from cryptography.fernet import Fernet, InvalidToken
import irc.bot
import types

desired_nickname = "clyde"  # nickname='mac' + str(randint(100,999)
svr = MyWrapperForTheGroovyTestBot(channel="#prate", desired_nickname=desired_nickname, rsa_key=MY_RSAKEY.public_key(),
                    irc_server='cinqcent.local', port=6667)

rejig_ircbot(svr.ircbot)
while not svr.ready:
    sleep(1)

svr.ircbot.connection.whois('mchobbit')
pass
'''

"""
import sys
import queue
import datetime
from time import sleep
from threading import Thread
from _queue import Empty

from cryptography.fernet import Fernet, InvalidToken
import base64
from my.globals import MY_IP_ADDRESS, MY_RSAKEY, get_my_public_ip_address
from my.stringtools import generate_irc_handle
from my.classes.readwritelock import ReadWriteLock
from Crypto.PublicKey import RSA
import irc.bot
from my.irctools.cryptoish import pubkey_to_b85, b85_to_pubkey, rsa_decrypt, rsa_encrypt
from my.irctools import LifoQueuedSimpleIRCBot
from my.irctools.homies import Homie

# Generate RSA keys

# pip3 install pycryptodome

# https://medium.com/@info_82002/a-beginners-guide-to-encryption-and-decryption-in-python-12d81f6a9eac


def squeeze_da_keez(i):
#    return skinny_key(i)
    return pubkey_to_b85(i)


def unsqueeze_da_keez(i):
#    return unskin_key(i)
    return b85_to_pubkey(i)


class MyObject(object):
    pass


class MyWrapperForTheGroovyTestBot:

    def __init__(self, channel, desired_nickname, rsa_key, irc_server, port):
        self.homies = {}
        self.__channel = channel
        self.__desired_nickname = desired_nickname
        self.__rsa_key = rsa_key
        self.__server_url = irc_server
        self.__port = port
        self.__channel = channel
        self.__channel_lock = ReadWriteLock()
        self.__nickname_lock = ReadWriteLock()
        self.__desired_nickname_lock = ReadWriteLock()
        self.__rsa_key_lock = ReadWriteLock()
        self.__server_url_lock = ReadWriteLock()
        self.__port_lock = ReadWriteLock()
        self.rx_queue = queue.LifoQueue()
        self.tx_queue = queue.LifoQueue()
        self.ircbot = LifoQueuedSimpleIRCBot(channel=self.channel, nickname=self.desired_nickname,
                                      realname=squeeze_da_keez(self.rsa_key), server=self.server_url, port=self.port)
        self.input_queue = queue.LifoQueue()
        self.output_queue = queue.LifoQueue()
        self.__time_to_quit = False
        self.__my_worker_thread = Thread(target=self._worker_loop, daemon=True)
        self.__the_previous_time_i_said_what_was_going_on = None
        self.__ready = False
        self._start()

    @property
    def desired_nickname(self):
        self.__desired_nickname_lock.acquire_read()
        try:
            retval = self.__desired_nickname
            return retval
        finally:
            self.__desired_nickname_lock.release_read()

    @desired_nickname.setter
    def desired_nickname(self, value):
        raise ValueError("Do not try to set a readonly item")

    @property
    def channel(self):
        self.__channel_lock.acquire_read()
        try:
            retval = self.__channel
            return retval
        finally:
            self.__channel_lock.release_read()

    @channel.setter
    def channel(self, value):
        raise ValueError("Do not try to set a readonly item")

    @property
    def nickname(self):
        self.__nickname_lock.acquire_read()
        try:
            retval = self.ircbot.connection.get_nickname()
            return retval
        finally:
            self.__nickname_lock.release_read()

    @nickname.setter
    def nickname(self, value):
        raise ValueError("Do not try to set a readonly item")

    @property
    def rsa_key(self):
        self.__rsa_key_lock.acquire_read()
        try:
            retval = self.__rsa_key
            return retval
        finally:
            self.__rsa_key_lock.release_read()

    @rsa_key.setter
    def rsa_key(self, value):
        # RSA.RsaKey
        raise ValueError("Do not try to set a readonly item")

    @property
    def server_url(self):
        self.__server_url_lock.acquire_read()
        try:
            retval = self.__server_url
            return retval
        finally:
            self.__server_url_lock.release_read()

    @server_url.setter
    def server_url(self, value):
        raise ValueError("Do not try to set a readonly item")

    @property
    def port(self):
        self.__port_lock.acquire_read()
        try:
            retval = self.__port
            return retval
        finally:
            self.__port_lock.release_read()

    @port.setter
    def port(self, value):
        raise ValueError("Do not try to set a readonly item")

    @property
    def ready(self):
        return self.__ready

    def _start(self):
        self.__my_worker_thread.start()

    def quit(self):
        self.__time_to_quit = True
        self.__my_worker_thread.join()  # print("Joining server thread")
#        self.ircbot.quit()

    def _worker_loop(self):
        print("Waiting for connection")
        while not self.ircbot.connected:
            sleep(.1)
        print("Connected. Waiting to join channel")
        while self.channel not in self.ircbot.channels:
            sleep(.1)
        print("*** MY NAME IS %s ***" % self.ircbot.connection.get_nickname())
        print("Joined. Introducing myself to everyone")
        self.introduce_myself_to_everyone()
        print("Waiting for their responses & other incoming messages")
        self.__ready = True
        while not self.__time_to_quit:
            try:
                (a_user, msg_txt) = self.tx_queue.get_nowait()
                print("Send to %s (encrypted): %s" % (a_user, msg_txt))
            except Empty:
                pass
            self.process_incoming_message()

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
        if force or self.__the_previous_time_i_said_what_was_going_on != outstr:
            self.__the_previous_time_i_said_what_was_going_on = outstr
            print(outstr)

    def process_incoming_message(self, wait=True):
        (connection, event) = self.get_from_irc(wait)
#        try:
        return self.act_on_msg_from_irc(connection, event)
        # except Exception as e:
        #     print("act_on_msg_from_irc() generated an exception:", e)
        #     return None

    def my_encrypted_ipaddr(self, sender):
        if sender not in self.homies or self.homies[sender].fernetkey is None:
            raise ValueError("Please download %s's fernet key before you try to encrypt." % sender)
        cipher_suite = Fernet(self.homies[sender].fernetkey)
        ipaddr_str = MY_IP_ADDRESS
        cipher_text = cipher_suite.encrypt(ipaddr_str.encode())
        return cipher_text.decode()

    def get_from_irc(self, wait=True):
        return self.ircbot.get() if wait else self.ircbot.get_nowait()

    def act_on_msg_from_irc(self, connection, event):
        if event is None:
            raise AttributeError("act_on_msg_from_irc() has an event of None")
        if event.source:
            sender = event.source.split('@')[0].split('!')[0]
        else:
            sender = None
        txt = event.arguments[0]
        cmd = txt[:6]
        stem = txt[6:]
        if sender == self.ircbot.nickname:
            raise ValueError("WHY AM I TALKING TO MYSELF?")
        retval_dct = {'event':event, 'sender':sender, 'cmd':cmd, 'stem':stem}
        if sender not in self.homies:  # or self.homies[user].pubkey is None:
            self.homies[sender] = Homie(nickname=sender)
        if event.type == 'foo':
            print("event type is foo for %s; this is a foo-tile attempt at a test." % event.target)
        elif cmd == "RQFERN":  # you asked for a copy of my fernet key
            if self.homies[sender].pubkey is None:
                print("I can't transmit my fernet key: I don't know %s's public key!" % sender)
            else:
                self.ircbot.put(sender, "TXFERN%s" % self.encrypt_fernetkey(sender, self.homies[sender].my_locally_generated_fernetkey))
        elif cmd == "TXFERN":
            self.homies[sender]._his_fernet = rsa_decrypt(base64.b64decode(stem))
        elif cmd == "RQIPAD":
            if sender not in self.homies or self.homies[sender].fernetkey is None:
                print("I cannot send my IP address out: I don't know %s's fernet key!" % sender)
            else:
                self.ircbot.put(sender, "TXIPAD%s" % self.my_encrypted_ipaddr(sender))
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
#                 with self.rx_queue.mutex:
                self.rx_queue.put([sender, decoded_msg])
                retval_dct['decoded'] = decoded_msg
        else:
            print("Probably a private message from %s: %s" % (sender, txt))
            print("What is private message %s for? " % cmd)
        return retval_dct

    @property
    def crypto_empty(self):
#        with self.rx_queue.mutex:
        return self.rx_queue.empty()

    def crypto_get(self):
#        with self.rx_queue.mutex:
        return self.rx_queue.get()

    def crypto_get_nowait(self):
#        with self.rx_queue.mutex:
        return self.rx_queue.get_nowait()

    def crypto_put(self, user, byteblock):
        if user not in self.homies:
            raise ValueError("I cannot send a message to a user whose info I don't possess")
        if type(byteblock) is not bytes:
            raise ValueError("I cannot send a non-binary message to %s. The byteblock must be composed of bytes!" % user)
        if self.homies[user].fernetkey is None:
            raise ValueError("I cannot encrypt a message with a null fernet key")
        cipher_suite = Fernet(self.homies[user].fernetkey)
        cipher_text = cipher_suite.encrypt(byteblock)
        self.ircbot.put(user, "TXTXTX%s" % cipher_text.decode())

    def _receiving_his_IP_address(self, sender, stem):
#        print("I have received an IP address block from %s" % sender)
        if self.homies[sender].fernetkey is None:
            raise ValueError("I do not possess %s's fernetkey. Please negotiate one" % sender)
        cipher_suite = Fernet(self.homies[sender].fernetkey)
        try:
            decoded_msg = cipher_suite.decrypt(stem)
        except InvalidToken:
            return "Warning - failed to decode %s's message. " % sender
        ipaddr = decoded_msg.decode()
        self.homies[sender].ipaddr = ipaddr
#        print("Received IP address (%s) for %s" % (ipaddr, sender))

    def get_pubkey_from_whois(self, user):
        whois_res = self.ircbot.connection.whois(user)
        try:
            squozed_key = whois_res.split(' ', 3)[-1]
            return unsqueeze_da_keez(squozed_key)
        except (AttributeError, ValueError, IndexError):
            return None

    def encrypt_fernetkey(self, user, fernetkey):
        if user not in self.homies or fernetkey is None:
            raise ValueError("Do not try to encrypt the fernetkey until you've CREATED a fernetkey.")
        encrypted_fernetkey = rsa_encrypt(message=fernetkey, public_key=self.homies[user].pubkey)
        b64_encrypted_fernetkey = base64.b64encode(encrypted_fernetkey).decode()
        return b64_encrypted_fernetkey

    def introduce_myself_to_everyone(self):
        all_users = list(self.ircbot.channels[self.channel].users())
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
        if self.homies[user].fernetkey is None and self.homies[user]._his_fernet is None:
            self.ircbot.put(user, "RQFERN")  # Request his fernet key
            return
        if self.homies[user].fernetkey is None and self.homies[user]._his_fernet is not None:
            print("our two fernet keys are", self.homies[user]._his_fernet, "and", self.homies[user]._my_fernet)
            self.homies[user].fernetkey = self.homies[user]._his_fernet if self.homies[user]._his_fernet > self.homies[user]._my_fernet else self.homies[user]._my_fernet
            print("We choose", self.homies[user].fernetkey, "as our fernet key.")
            return
        if self.homies[user].ipaddr is None:
            self.ircbot.put(user, "RQIPAD")  # Request his IP address

##########################################################################################################


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
    svr = MyWrapperForTheGroovyTestBot(channel=my_channel, desired_nickname=desired_nickname,
                                       rsa_key=MY_RSAKEY.public_key(),
                                       irc_server=my_irc_server, port=my_port)
    while not svr.ready:
        sleep(1)

    svr.ircbot.connection.whois('mchobbit')

    print("Press CTRL-C to quit.")
    try:
        my_ip_addr = get_my_public_ip_address()
    except Exception as e:
        my_ip_addr = '127.0.0.1'

    while True:
        # if svr.nickname != desired_nickname or svr.ircbot.connection.get_nickname() != desired_nickname:
        #     print("HEYYY. Our new nickname is", svr.nickname)
        sleep(5)
        # SAY HELLO, RIFF!
#         for user in svr.homies:
# #            s = get_random_Cicero_line()
#             s = "I am %s at %s; I say hello to you, %s, at %s" % (svr.nickname, my_ip_addr, user, svr.homies[user].ipaddr)
# #            print("s =", s)
#             if svr.homies[user].fernetkey is not None:
#                 svr.crypto_put(user, s.encode())
        svr.show_users_dct_info(force=True)
        svr.introduce_myself_to_everyone()

