# -*- coding: utf-8 -*-
"""
Created on Jan 22, 2025

@author: mchobbit
"""

import os
from Crypto.PublicKey import RSA
import paramiko
import sys
from my.stringtools import generate_irc_handle, get_word_salad, get_bits_to_be_encoded, encode_via_steg, decode_via_steg, \
    generate_all_possible_channel_names, strict_encode_via_steg
import base64
from random import randint, choice, shuffle
import string
import time
from time import mktime
import pytz
import datetime

import lzma
from io import BytesIO
from threading import Event, Thread
from queue import Empty
from my.audiotools import MyMic, DESIRED_AUDIO_FORMAT, FRAME_RATE, NOOF_CHANS, SAMPLE_WIDTH, raw_to_ogg
import datetime
from array import array
from queue import Queue, Full, Empty
from pydub import AudioSegment
import pyaudio
from random import shuffle, randint
from my.stringtools import generate_irc_handle, generate_random_alphanumeric_string
from my.globals import PARAGRAPH_OF_ALL_IRC_NETWORK_NAMES
from time import sleep
from queue import Queue, Full

from time import sleep
from my.stringtools import *
from my.globals import *
import os
import socket
import datetime
from my.irctools.cryptoish import squeeze_da_keez
import wave
from pydub.audio_segment import AudioSegment
from my.classes.readwritelock import ReadWriteLock
from my.irctools.jaracorocks.praterookery import PrateRookery


def loopback_audio_transmission_and_reception_over_IRC_harem():
    my_nickname = 'me%s' % generate_random_alphanumeric_string(6)  # my_nickname = socket.gethostname().replace('.', '_')[:MAX_NICKNAME_LENGTH]
    the_room = "#prattling"
    alice_rsa_key = RSA.generate(2048)
    bob_rsa_key = RSA.generate(2048)
    the_irc_server_URLs = ALL_SANDBOX_IRC_NETWORK_NAMES  # ALL_REALWORLD_IRC_NETWORK_NAMES
    alice_harem = PrateRookery([the_room], my_nickname, the_irc_server_URLs, alice_rsa_key)
    bob_harem = PrateRookery([the_room], my_nickname, the_irc_server_URLs, bob_rsa_key)
    while not (alice_harem.ready and bob_harem.ready):
        sleep(1)

    print("Opening harems")
    while len(alice_harem.users) < 2 and len(bob_harem.users) < 2:
        sleep(1)

    while len(alice_harem.true_homies) < 1 and len(bob_harem.true_homies) < 1:
        sleep(1)

    # print("Sending a file from %s to %s" % (alice_harem.desired_nickname, bob_harem.desired_nickname))
    # alice_harem.put(bob_rsa_key.public_key(), b"HELLO WORLDIEWOO")
    # src, msg = bob_harem.get()

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
            alice_harem.put(bob_rsa_key.public_key(), raw_to_ogg(raw_audio))
        try:
            src, msg = bob_harem.get_nowait()
            fileno += 1
            fname = "/tmp/out_%d.ogg" % fileno
            with open(fname, "wb") as f:
                f.write(msg)
            os.system("/opt/homebrew/bin/mpv %s &" % fname)
        except Empty:
            sleep(.05)

#################################################################################


if __name__ == "__main__":
    loopback_audio_transmission_and_reception_over_IRC_harem()

