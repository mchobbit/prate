#!/usr/bin/env python3

"""
sayhello(str, ip)
    - send a simple hello, quoting Cicero, to other members of the channel.

"""
from my.classes.selfcachingcall import SelfCachingCall
import irc.bot
import irc.strings
from irc.client import ip_numstr_to_quad, ip_quad_to_numstr
from random import randint
import os
import paramiko
import sys
import pwd
import threading
import time
import textwrap
import irc.client

from time import sleep
from copy import deepcopy
from my.stringtools import generate_irc_handle, multiline_encode_via_steg, get_word_salad, get_bits_to_be_encoded, encode_via_steg, decode_via_steg, strict_encode_via_steg, multiline_encode_via_steg
import base64
from my.globals import steg_dct_CLUMPS, VANILLA_WORD_SALAD
from random import randint, choice, shuffle
import string
from my.globals.poetry import CICERO, HAMLET
import socket
import requests
from my.irctools import get_my_public_ip_address
from threading import Thread
from _queue import Empty
THE_CHANNEL_MEMBERS = {}
QUESTIONABLE_NICKS = []
MY_KEY = paramiko.RSAKey.generate(4096)
assert(len(MY_KEY.get_base64()) < 800)
# STEGGED_KEY_MSG = encode_via_steg("Hello from %s" % socket.gethostname(), salad_txt=CICERO, random_offset=True, max_out_len=500)

# #_plaintext = key.get_base64()  #  "Word up, homie G."  # key.get_base64() # key.asbytes()
# _ciphertext = encode_via_steg(plaintext, salad_txt=VANILLA_WORD_SALAD, random_offset=True)
# _destegged = decode_via_steg(ciphertext, output_in_bytes=False)
# assert(destegged == plaintext)
# fingerprint = key.fingerprint
import threading
import queue


def scan_this_for_steg(cmd):
    print("Scanning", cmd)


def get_random_Cicero_line():
    all_useful_lines = [r for r in CICERO.split('\n') if len(r) >= 5]
    return choice(all_useful_lines)


class MyObject(object):
    pass


class TestBotFive(irc.bot.SingleServerIRCBot):

    def __init__(self, channel, nickname, server, port=6667):
        self._initial_nickname = nickname
        self._nickname = None
        irc.bot.SingleServerIRCBot.__init__(self, [(server, port)], nickname, nickname)
        self.channel = channel
        self.input_queue = queue.LifoQueue()
        self.output_queue = queue.LifoQueue()
        self.__time_to_quit = False
        self.__my_irc_server_thread = Thread(target=self._start_server, daemon=True)
        self.__my_output_worker_thread = Thread(target=self._output_worker_loop, daemon=True)
        self.__my_output_worker_thread.start()
        self.__my_irc_server_thread.start()
        self.connection_cache = {}

    @property
    def nickname(self):
        return self._nickname

    def quit(self):
        self.__time_to_quit = True
        super().disconnect("Toodles.")  # print("Joining worker thread")
        self.__my_output_worker_thread.join()  # print("Joining server thread")
        self.__my_irc_server_thread.join()  # print("Yay. Quitting OK.")

    def on_nicknameinuse(self, c, e):
        n = c.get_nickname()
        while len(n) > 1 and n[-1] in ('0123456789'):
            n = n[:-1]
        c.nick(c.get_nickname() + str(randint(11111, 99999)))
        self._nickname = c.get_nickname()

    def on_welcome(self, c, e):
        c.join(self.channel)  # Join channel. (This is not a Thread thing.)
        self.connection_cache[e.target] = c
        self.connection_cache[self.channel] = c
        self._nickname = c.get_nickname()

    def on_pubmsg(self, c, e):
        self.connection_cache[e.target] = c
        self.input_queue.put(['public', c, e])

    def on_notice(self, c, e):  # Is this necessary?
        self.connection_cache[e.target] = c
        self.input_queue.put(['public', c, e])

    def on_privmsg(self, c, e):
        self.connection_cache[e.target] = c
        self.input_queue.put(['private', c, e])

    def _send_private_message(self, user, txt):
        if user.startswith('#'):
            raise ValueError("User not must begin with a #; %s is bad." % user)
        for i in (user, self.nickname, self._initial_nickname):
            if i in self.connection_cache:
                self.connection_cache[i].privmsg(user, txt)
                return
        raise ValueError("Cannot send private message to %s" % user)

    def _send_notice(self, channel, txt):
        if not channel.startswith('#'):
            raise ValueError("Channel must begin with a #; %s doesn't." % channel)
        if channel not in self.channels:
            raise ValueError("Please join %s and try again." % channel)
        for i in (channel, self.nickname, self._initial_nickname):
            if i in self.connection_cache:
                self.connection_cache[i].notice(channel, txt)
                return
        raise ValueError("Cannot send notice to %s" % channel)

    def _start_server(self):
        self.start()

    def put(self, dest, txt):
        if dest.startswith('#'):
            raise ValueError("Public messaging is broken in this app.")
            self.output_queue.put(['public', dest, txt])
        else:
            self.output_queue.put(['private', dest, txt])

    def _output_worker_loop(self):
        while not self.__time_to_quit:
            try:
                (whatkind, user, msg_txt) = self.output_queue.get_nowait()
                if whatkind == 'private':
                    self._send_private_message(user, msg_txt)  #                    print("Privat msg for %s: %s" % (user, msg_txt))
                elif whatkind == 'public':
                    self._send_notice(user, msg_txt)  #                    print("Public msg for %s: %s" % (user, msg_txt))
                else:
                    print("Qui??? msg for %s: %s" % (user, msg_txt))
                sleep(randint(16, 20) // 10.)  # Do not send more than 20 messages in 30 seconds! => 30/(((20+16)/2)/10)=16.7 messages per 30 seconds.
            except Empty:
                pass
#            finally:

    @property
    def empty(self):
        return self.input_queue.empty()

    def get(self):
        return self.input_queue.get()

    def get_nowait(self):
        return self.input_queue.get_nowait()

    @property
    def connected(self):
        if self.nickname in self.connection_cache:
            return self.connection_cache[self.nickname].is_connected()
        elif len(self.connection_cache) > 0:
            return self.connection_cache[list(self.connection_cache.keys())[0]].is_connected()
        else:
            return False  #            raise ValueError("Unable to figure out if we're connected or not.")

'''
macno=2
from testbot5 import *
svr = TestBotFive('#prate', 'mac%d' % macno, 'cinqcent.local', 6667)
sleep(2)
print(svr.connected)
svr.put('mchobbit', 'HELLO HOMEY')
svr.put('#prate', 'HELLO EVERYONE')
# handshake, exchange, etc.
users_lst = svr.channels['#prate'].users()
svr.put('#prate', MY_KEY.fingerprint)
sleep(5)
while not svr.empty():
    r = svr.get()
    print(r)


'''

USERS_DCT = {}


def show_users_dct_info():
    for k in USERS_DCT:
        sender = USERS_DCT[k]['sender']
        if USERS_DCT[k] is None or USERS_DCT[k]['sender'] is None:
            pass
        elif USERS_DCT[k]['keyfA'] and USERS_DCT[k]['keyfB']:
            if USERS_DCT[k]['ipadd']:
                print("%s: I have the key and the IP address" % sender)
            else:
                print("%s: I have the key" % sender)
        else:
            print("%s: I have the fingerprint" % sender)


def process_incoming_message(svr):
    global USERS_DCT
    (w, connection, event) = svr.get()
    txt = event.arguments[0]
    sender = event.source.split('@')[0].split('!')[0]
    middleparam = txt.split(' ')[-2]
    fingerprint = txt.split(' ')[-1]
    if w == 'public':
        print("We don't use public msgs anymore")
        return
    if w == 'private':
        if fingerprint not in USERS_DCT:
            USERS_DCT[fingerprint] = {'sender':sender, 'keyfA':None, 'keyfB':None, 'ipadd':None}
        if txt[:5] in ("MARCO", "POLO!"):
            if txt[:5] == "MARCO":
#                print("%s has sent me his fingerprint. I'll send it (and my PK) back." % sender)
                svr.put(sender, "POLO! fingerprint %s" % MY_KEY.fingerprint)
            else:
                pass
#                print("%s has sent me his fingerprint (and my PK) in response to my fingerprint." % sender)
            svr.put(sender, "keyfA %s %s" % (MY_KEY.get_base64()[:400], MY_KEY.fingerprint))
            svr.put(sender, "keyfB %s %s" % (MY_KEY.get_base64()[400:], MY_KEY.fingerprint))
            svr.put(sender, "ipadd %s %s" % (get_my_public_ip_address(), MY_KEY.fingerprint))
        elif txt[:5] in ('keyfA', 'keyfB', 'ipadd'):
#            print("Saving %s from %s" % (txt[:5], sender))
            USERS_DCT[fingerprint][txt[:5]] = middleparam
        else:
            print("What is private message %s for?" % txt.split(' ')[0])
    else:
        print("What does % s mean?" % w)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        my_channel = "#prate"
        my_nickname = "mchobbit"
        print("Assuming my_channel is", my_channel, "and nickname is", my_nickname)
#        print("Usage: %s <channel> <nickname>" % sys.argv[0])
#        sys.exit(1)
    else:
        my_channel = sys.argv[1]
        my_nickname = sys.argv[2]
    my_irc_server = 'cinqcent.local'
    my_port = 6667
    svr = TestBotFive(my_channel, my_nickname, my_irc_server, my_port)

    print("Waiting for connection")
    while not svr.connected:
        sleep(1)

    print("Waiting to join channel")
    while my_channel not in svr.channels:
        sleep(1)

    pubkeys_dct = {}
    all_users = []
    while True:
        old_allusrs = all_users
        all_users = svr.channels[my_channel].users()
        new_users = []
        for user in all_users:
            if user not in old_allusrs and user != svr.nickname:
                new_users += [user]
        shuffle(new_users)
        for user in new_users:
            print("Introducing myself to %s" % user)
            svr.put(user, "MARCO fingerprint %s" % MY_KEY.fingerprint)
        while not svr.empty:
            process_incoming_message(svr)
            show_users_dct_info()
        sleep(randint(15, 20) / 10.)

'''
from testbot5 import *
my_channel = "#prate"
my_nickname = "macmiller"
my_irc_server = 'cinqcent.local'
my_port = 6667
svr = TestBotFive(my_channel, my_nickname, my_irc_server, my_port)
sleep(3)
pubkeys_dct = {}
for user in [r for r in svr.channels[my_channel].users() if r != svr.nickname]:
    svr.put(user, "MARCO fingerprint %s" % MY_KEY.fingerprint)
'''
