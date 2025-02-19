# -*- coding: utf-8 -*-
'''
Created on Jan 21, 2025

@author: mchobbit

# print(key.get_base64())  # print public key
# key.write_private_key(sys.stdout)
'''
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
from Crypto.PublicKey import RSA
from my.globals import PARAGRAPH_OF_ALL_IRC_NETWORK_NAMES
from time import sleep
from queue import Queue, Full

from Crypto.PublicKey import RSA
from time import sleep
from my.stringtools import *
from my.globals import *
import os
import socket
import datetime
from my.irctools.cryptoish import squeeze_da_keez
from my.irctools.jaracorocks.harem import HaremOfPrateBots
import wave
from pydub.audio_segment import AudioSegment
from my.classes.readwritelock import ReadWriteLock

my_nickname = 'me%s' % generate_random_alphanumeric_string(6)  # my_nickname = socket.gethostname().replace('.', '_')[:MAX_NICKNAME_LENGTH]
the_room = "#prattling"
alice_rsa_key = RSA.generate(2048)
bob_rsa_key = RSA.generate(2048)
the_irc_server_URLs = ALL_SANDBOX_IRC_NETWORK_NAMES  # ALL_REALWORLD_IRC_NETWORK_NAMES
alice_harem = HaremOfPrateBots([the_room], my_nickname, the_irc_server_URLs, alice_rsa_key)
bob_harem = HaremOfPrateBots([the_room], my_nickname, the_irc_server_URLs, bob_rsa_key)
while not (alice_harem.ready and bob_harem.ready):
    sleep(1)

print("Opening harems")
while len(alice_harem.users) < 2 and len(bob_harem.users) < 2:
    sleep(1)

while len(alice_harem.ipaddrs) < 1 and len(bob_harem.ipaddrs) < 1:
    sleep(1)

