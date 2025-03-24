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
from queue import Queue, Empty
from my.audiotools import MyMic, raw_to_ogg
import os
import datetime
from my.irctools.jaracorocks.harem222 import Harem
from my.irctools.jaracorocks.harem222.simpipe import receive_data_from_simpipe

alices_rsa_key = RSA.generate(RSA_KEY_SIZE)
bobs_rsa_key = RSA.generate(RSA_KEY_SIZE)
alices_PK = alices_rsa_key.public_key()
bobs_PK = bobs_rsa_key.public_key()

noof_servers = 20
my_list_of_all_irc_servers = ALL_SANDBOX_IRC_NETWORK_NAMES[:noof_servers]  # ALL_REALWORLD_IRC_NETWORK_NAMES
the_room = '#room' + generate_random_alphanumeric_string(5)
alice_nick = 'alice%d' % randint(111, 999)
bob_nick = 'bob%d' % randint(111, 999)

print("                                                 Creating harems for Alice and Bob")
alice_harem = Harem([the_room], alice_nick, my_list_of_all_irc_servers, alices_rsa_key, autohandshake=False)
bob_harem = Harem([the_room], bob_nick, my_list_of_all_irc_servers, bobs_rsa_key, autohandshake=False)
while not (alice_harem.connected_and_joined and bob_harem.connected_and_joined):
    sleep(1)

print("                                                 Waiting for harems to shake hands")
alice_harem.trigger_handshaking()
bob_harem.trigger_handshaking()
the_noof_homies = -1
while the_noof_homies != len(alice_harem.get_homies_list(True)):
    the_noof_homies = len(alice_harem.get_homies_list(True))
    sleep(STARTUP_TIMEOUT // 3 + 1)

print("                                                 Opening a simpipe between Alice and Bob")
alice_simpipe = alice_harem.open(bobs_PK)
bob_simpipe = bob_harem.open(alices_PK)
sleep(10)

'''
with open("/tmp/my.raw", "rb") as f:
    raw_data = f.read()

with open("/tmp/my.ogg", "wb") as f:
    f.write(raw_to_ogg(raw_data))


# os.system("/opt/homebrew/bin/mpv /tmp/my.ogg")

alice_simpipe.put(raw_data)
sleep(10)
msg = receive_data_from_simpipe(bob_simpipe)
sleep(1)


# d = bob_simpipe.get()

alice_simpipe.put(raw_data)
sleep(15)
bufsize = 4096
incoming_data = bytearray()

while True:
    try:
        incoming_data += bytearray(bob_simpipe.get(timeout=5))
        if len(incoming_data) >= bufsize:
            with open("/tmp/oops.ogg", "wb") as f:
                f.write(raw_to_ogg(bytes(incoming_data[:bufsize])))
            os.system("/opt/homebrew/bin/mpv /tmp/oops.ogg")
            incoming_data = incoming_data[bufsize:]
    except Empty:
        break

while True:
    bob_simpipe.get_nowait()



with open("/tmp/received.ogg", "wb") as f:
    f.write(raw_to_ogg(incoming_data))
'''

print("SAY WORDS!")
audio_queue = Queue()
mic = MyMic(audio_queue, squelch=200)
fileno = 0

while True:
    try:
        raw_audio = audio_queue.get(timeout=1)
    except Empty:
        sleep(.05)
    except KeyboardInterrupt:
        break
    else:
        print("Sending to Alice")
        alice_simpipe.put(raw_to_ogg(raw_audio))
        # fname = "/tmp/out_%d.ogg" % fileno
        # with open(fname, "wb") as f:
        #     f.write(raw_to_ogg(raw_audio))
        # with open(fname.replace('ogg', 'raw'), "wb") as f:
        #     f.write(raw_audio)
        # os.system("/opt/homebrew/bin/mpv %s" % fname)
        # fileno += 1
        print("Waiting for Bob")
        ogg_data = receive_data_from_simpipe(bob_simpipe, timeout=5)
        with open('/tmp/recent_%d.ogg' % fileno, 'wb') as f:
            f.write(ogg_data)
        print("Playing audio")
        os.system("/opt/homebrew/bin/mpv /tmp/recent_%d.ogg" % fileno)
        fileno += 1
        # bufsize = 4096
        # incoming_data = bytearray()
        # while True:
        #     fileno = 0
        #     try:
        #         incoming_data += bytearray(bob_simpipe.get(timeout=1))
        #         if len(incoming_data) >= bufsize:
        #             print("Retrieving #%d from Bob" % fileno)
        #             fname = "/tmp/oops_%d.ogg" % fileno
        #             with open(fname, "wb") as f:
        #                 f.write(raw_to_ogg(bytes(incoming_data[:bufsize])))
        #             os.system("/opt/homebrew/bin/mpv %s &" % fname)
        #             incoming_data = incoming_data[bufsize:]
        #             fileno += 1
        #     except Empty:
        #         break

'''
while True:
    bob_simpipe.get_nowait()


        msg = receive_data_from_simpipe(bob_simpipe)
    #        msg = bob_simpipe.get_nowait()
        fileno += 1
        with open("/tmp/out_%d.raw" % fileno, "wb") as f:
            f.write(msg)

        fname = "/tmp/out_%d.ogg" % fileno
        with open(fname, "wb") as f:
            f.write(raw_to_ogg(msg))
        os.system("/opt/homebrew/bin/mpv %s" % fname)
    except Empty:
        sleep(.05)
'''

