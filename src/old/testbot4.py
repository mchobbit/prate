#! /usr/bin/env python3

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


class TestBotFour(irc.bot.SingleServerIRCBot):

    def __init__(self, channel, nickname, server, port=6667):
        self._initial_nickname = nickname
        irc.bot.SingleServerIRCBot.__init__(self, [(server, port)], nickname, nickname)
        self.channel = channel
        self.input_queue = queue.LifoQueue()
        self.output_queue = queue.LifoQueue()
        self.__time_to_quit = False
        self.__my_main_thread = Thread(target=self._start_server, daemon=True)
        self.__my_worker_thread = Thread(target=self._worker_loop, daemon=True)
        self.__my_main_thread.start()
        self.__my_worker_thread.start()
        self.connection_cache = {}

    def nickname(self):
        if self._initial_nickname in self.connection_cache:
            return self.connection_cache[self._initial_nickname].get_nickname()
        else:
            return self._initial_nickname

    def quit(self):
        self.__time_to_quit = True
        super().disconnect("Toodles.")  # print("Joining worker thread")
        self.__my_worker_thread.join()  # print("Joining server thread")
        self.__my_main_thread.join()  # print("Yay. Quitting OK.")

    def on_nicknameinuse(self, c, e):
        n = c.get_nickname()
        while len(n) > 1 and n[-1] in ('0123456789'):
            n = n[:-1]
        c.nick(c.get_nickname() + str(randint(11111, 99999)))

    def on_welcome(self, c, e):
        c.join(self.channel)  # Join channel. (This is not a Thread thing.)
        self.connection_cache[e.target] = c
        self.connection_cache[self.channel] = c

    def on_pubmsg(self, c, e):
        self.connection_cache[e.target] = c
        self.input_queue.put(['public', c, e])

    def on_privmsg(self, c, e):
        self.connection_cache[e.target] = c
        self.input_queue.put(['private', c, e])

    def send_private_message(self, user, txt):
        if user in self.connection_cache:
            self.connection_cache[user].privmsg(user, txt)
        elif self.nickname in self.connection_cache:
            self.connection_cache[self.nickname].privmsg(user, txt)
        else:
            self.connection_cache[self._initial_nickname].privmsg(user, txt)

    def send_public_message(self, channel, txt):
        if channel not in self.channels:
            raise ValueError("Please join %s and try again." % channel)
        if channel in self.connection_cache:
            self.connection_cache[channel].notice(channel, txt)
        elif self.nickname in self.connection_cache:
            self.connection_cache[self.nickname].notice(channel, txt)
        else:
            self.connection_cache[self._initial_nickname].notice(channel, txt)

    def _start_server(self):
        self.start()

    def _worker_loop(self):
        while not self.__time_to_quit:
            try:
                (priv_or_pub, user, msg_txt) = self.output_queue.get_nowait()
                if priv_or_pub == 'private':
                    print("Privat msg for %s: %s" % (user, msg_txt))
#                    self.my_channels[user].connection.privmsg(user, msg_txt)
                elif priv_or_pub == 'public':
                    print("Public msg for %s: %s" % (user, msg_txt))
#                    self.my_channels[user].connection.publicmsg(user, msg_txt)
                else:
                    print("Qui??? msg for %s: %s" % (user, msg_txt))
            except Empty:
                sleep(randint(1, 10) // 10.)
#            finally:

'''
from testbot4 import *
my_server = TestBotFour('#prate', 'mac1', 'cinqcent.local', 6667)
my_server.output_queue.put(['public','#prate','hello'])
my_server.send_public_message('#prate', "My bologna")
my_server.send_public_message('mchobbit', "Sharona")
'''
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
    my_server = TestBotFour(my_channel, my_nickname, my_irc_server, my_port)
    print("Yay.")
    sleep(5)
    my_server.quit()

