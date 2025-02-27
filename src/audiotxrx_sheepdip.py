# -*- coding: utf-8 -*-
"""
Created on Jan 21, 2025

@author: mchobbit

# print(key.get_base64())  # print public key
# key.write_private_key(sys.stdout)
"""

from Crypto.PublicKey import RSA
from my.stringtools import *
from my.globals import *
from time import sleep
from my.irctools.jaracorocks.pratebot import PrateBot
import datetime
from queue import Queue, Empty
from my.audiotools import MyMic, raw_to_ogg
import os
from my.irctools.jaracorocks.praterookery import PrateRookery

alices_preferred_nickname = 'alice123'
bobs_preferred_nickname = 'bob456'
the_room = "#prankrr"
alice_rsa_key = RSA.generate(RSA_KEY_SIZE)
bob_rsa_key = RSA.generate(RSA_KEY_SIZE)
the_irc_server_URLs = ALL_SANDBOX_IRC_NETWORK_NAMES  # ALL_SANDBOX_IRC_NETWORK_NAMES  # ALL_REALWORLD_IRC_NETWORK_NAMES
# alice_bot = PrateBot([the_room], alices_preferred_nickname, "irc.libera.chat", 6667, alice_rsa_key)
# bob_bot = PrateBot([the_room], bobs_preferred_nickname, "irc.libera.chat", 6667, bob_rsa_key)
# while not (alice_bot.ready and bob_bot.ready):
#    sleep(1)
print("Opening rookerys")
alice_rookery = PrateRookery([the_room], alices_preferred_nickname, the_irc_server_URLs, alice_rsa_key)
bob_rookery = PrateRookery([the_room], bobs_preferred_nickname, the_irc_server_URLs, bob_rsa_key)
while not (alice_rookery.ready and bob_rookery.ready):
    sleep(10)

alice_rookery.trigger_handshaking()
bob_rookery.trigger_handshaking()
sleep(60)

print("SAY WORDS!")
audio_queue = Queue()
mic = MyMic(audio_queue, squelch=200)
fileno = 0
while True:
    try:
        raw_audio = audio_queue.get_nowait()
    except Empty:
        sleep(.05)
    except KeyboardInterrupt:
        break
    else:
        alice_rookery.put(bob_rsa_key.public_key(), raw_to_ogg(raw_audio))
    try:
        src, msg = bob_rookery.get_nowait()
        fileno += 1
        fname = "/tmp/out_%d.ogg" % fileno
        with open(fname, "wb") as f:
            f.write(msg)
        os.system("/opt/homebrew/bin/mpv %s" % fname)
    except Empty:
        sleep(.05)
# alice_rookery.put(bob_rsa_key.public_key(), b"HELLO WORLDDD")
# bob_rookery.get()

# with open("/Users/mchobbit/Downloads/side_cushion.stl", "rb") as f:
#     outdat = f.read()
#
# import datetime
# t = datetime.datetime.now()
# alice_rookery.put(bob_rsa_key.public_key(), outdat)
# u = datetime.datetime.now()
# sender, in_dat = bob_rookery.get()
# v = datetime.datetime.now()

