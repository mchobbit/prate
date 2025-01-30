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
THE_CHANNEL_MEMBERS = {}
QUESTIONABLE_NICKS = []
MY_KEY = paramiko.RSAKey.generate(4096)
# STEGGED_KEY_MSG = encode_via_steg("Hello from %s" % socket.gethostname(), salad_txt=CICERO, random_offset=True, max_out_len=500)

# #_plaintext = key.get_base64()  #  "Word up, homie G."  # key.get_base64() # key.asbytes()
# _ciphertext = encode_via_steg(plaintext, salad_txt=VANILLA_WORD_SALAD, random_offset=True)
# _destegged = decode_via_steg(ciphertext, output_in_bytes=False)
# assert(destegged == plaintext)
# fingerprint = key.fingerprint


def scan_this_for_steg(cmd):
    print("Scanning", cmd)


def get_random_Cicero_line():
    all_useful_lines = [r for r in CICERO.split('\n') if len(r) >= 5]
    return choice(all_useful_lines)


class TestBotThree(irc.bot.SingleServerIRCBot):

    def __init__(self, channel, nickname, server, port=6667):
        irc.bot.SingleServerIRCBot.__init__(self, [(server, port)], nickname, nickname)
        self.channel = channel

    def on_nicknameinuse(self, c, e):
        n = c.get_nickname()
        while len(n) > 1 and n[-1] in ('0123456789'):
            n = n[:-1]
        c.nick(c.get_nickname() + str(randint(11111, 99999)))

    def on_welcome(self, c, e):
        global THE_CHANNEL_MEMBERS
        c.join(self.channel)
        print("I am announcing myself (%s) publicly" % c.nickname)
        # I trust myself, because I *am* myself.
        THE_CHANNEL_MEMBERS[c.nickname] = {'ip':get_my_public_ip_address(), 'fingerprint':MY_KEY.fingerprint}
        c.privmsg(self.channel, "PublicHello %s" % THE_CHANNEL_MEMBERS[c.nickname]['fingerprint'])
        print("Known:", ''.join([r + ' ' for r in THE_CHANNEL_MEMBERS.keys()]))
        print("I hope the other members of the channel will send me their fingerprints.")

    def on_pubmsg(self, c, e):
        sleep(randint(10, 15) / 10)
        incoming = e.arguments[0]
        spkr_nickname = e.source.nick
        cmd_lst = incoming.split(' ')
        if cmd_lst[0] == 'PublicHello':
            spkr_fingerprint = cmd_lst[1]
            THE_CHANNEL_MEMBERS[spkr_nickname] = {'ip':None, 'fingerprint':spkr_fingerprint}
            print("%s has announced himself publicly. I shall initiate a private handshake." % spkr_nickname)
            c.privmsg(spkr_nickname, "PrivateAlice %s %s" % (THE_CHANNEL_MEMBERS[c.nickname]['ip'],
                                                       THE_CHANNEL_MEMBERS[c.nickname]['fingerprint']))
            print("Known:", ''.join([r + ' ' for r in THE_CHANNEL_MEMBERS.keys()]))
        else:
            print("Oi!! %s! What's this for? => %s" % (spkr_nickname, incoming))

    def on_privmsg(self, c, e):
        global THE_CHANNEL_MEMBERS
        sleep(randint(10, 15) / 10)
        incoming = e.arguments[0]
        cmd_lst = incoming.split(' ')
        spkr_nickname = e.source.nick
        if cmd_lst[0] == 'PrivateAlice':
            spkr_ip = cmd_lst[1]
            spkr_fingerprint = cmd_lst[2]
            print("%s has contacted me privately. I shall accept his private handshake." % spkr_nickname)
            THE_CHANNEL_MEMBERS[spkr_nickname] = {'ip':spkr_ip, 'fingerprint':spkr_fingerprint}
            c.privmsg(spkr_nickname, "PrivateBob %s %s" % (THE_CHANNEL_MEMBERS[c.nickname]['ip'],
                                                       THE_CHANNEL_MEMBERS[c.nickname]['fingerprint']))
            print("Known:", ''.join([r + ' ' for r in THE_CHANNEL_MEMBERS.keys()]))
        elif cmd_lst[0] == 'PrivateBob':
            spkr_ip = cmd_lst[1]
            spkr_fingerprint = cmd_lst[2]
            print("%s has accepted my private handshake. Huzzah." % spkr_nickname)
            if THE_CHANNEL_MEMBERS[spkr_nickname]['ip'] is None:
                THE_CHANNEL_MEMBERS[spkr_nickname]['ip'] = spkr_ip
            assert(THE_CHANNEL_MEMBERS[spkr_nickname]['fingerprint'] == spkr_fingerprint)
            print("WE SHOULD DCC %s AND SWAP KEYS!" % spkr_nickname)
#            c.notice(c.channel, "HEY %s! LET'S GO DO SOMETHING!" % spkr_nickname)
            print("Known:", ''.join([r + ' ' for r in THE_CHANNEL_MEMBERS.keys()]))
        else:
            print("Psst %s! What's this for? => %s" % (spkr_nickname, incoming))


class ServerThread:  # FIXME: NOT THREADSAFE

    def __init__(self, channel, nickname, irc_server, port):
        self._channel = channel
        self._nickname = nickname
        self._irc_server = irc_server
        self._port = port
        self.bot = None  # FIXME: NOT THREADSAFE
        self.__time_to_join = False
        self.__my_thread = Thread(target=self._heartbeat)
        self.__my_thread.daemon = True
        self.__my_thread.start()
        super().__init__()

    def join(self):
        """Join the thread and return."""
        self.__time_to_join = True
        self.bot.disconnect("Toodles")
        sleep(2)
        # self.bot.joint()
        self.__my_thread.join()

    def service_me(self):
        pass  # I don't do anything... yet.

    def _heartbeat(self):
        """Run me, over and over, in background.

        Note:
            This runs in the background. To end it, run
                i.join() if 'i' the instance of this class.

        """
        self.bot = TestBotThree(self._channel, self._nickname, self._irc_server, self._port)
        self.bot.start()
        while not self.__time_to_join:
            self.service_me()
            sleep(randint(1, 10) / 10.)

'''
from testbot3 import *
server_thread = ServerThread('#prate', 'hobbit1', 'cinqcent.local', 6667)
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
    server_thread = ServerThread(my_channel, my_nickname, my_irc_server, my_port)
    print("Yay.")
    sleep(5)
    server_thread.join()

