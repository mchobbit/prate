# -*- coding: utf-8 -*-
'''
Created on Jan 21, 2025

@author: mchobbit

# print(key.get_base64())  # print public key
# key.write_private_key(sys.stdout)
'''

# if __name__ == '__main__':
#    print("HI")
# word_salad_str = '''Do you hear the people sing? Singing a song of angry men? It is the music of a people Who will not be slaves again! When the beating of your heart Echoes the beating of the drums There is a life about to start When tomorrow comes!'''

import os
import paramiko
import sys
from time import sleep
from copy import deepcopy
from my.stringtools import generate_irc_handle, get_word_salad, get_bits_to_be_encoded, encode_via_steg, decode_via_steg, strict_encode_via_steg, multiline_encode_via_steg
import base64
from my.globals import steg_dct_CLUMPS, VANILLA_WORD_SALAD
from random import randint, choice, shuffle
import string
from my.globals.poetry import CICERO, HAMLET
import socket

key = paramiko.RSAKey.generate(4096)
plaintext = key.get_base64()  #  "Word up, homie G."  # key.get_base64() # key.asbytes()
ciphertext = encode_via_steg(plaintext, salad_txt=VANILLA_WORD_SALAD, random_offset=True)
destegged = decode_via_steg(ciphertext, output_in_bytes=False)
assert(plaintext == destegged)
#
# lst = multiline_encode_via_steg(plaintext, salad_txt=VANILLA_WORD_SALAD, random_offset=True, maxlen=499)
# for i in lst:
#     print(i)
#     sleep(.5)

# my_irc_handle = generate_irc_handle(minimum_desired_length=24)
# print("Creating public/private key pair")
# my_rsakey = paramiko.RSAKey.generate(4096)
# my_stegged_fingerprint = strict_encode_via_steg(my_rsakey.fingerprint, lambda: CICERO)
# all_possible_channels = generate_all_possible_channel_names()
# shuffle(all_possible_channels)
# gmt_time = time.gmtime()
# gmt_time_to_dt = datetime.datetime.fromtimestamp(mktime(gmt_time), tz=pytz.timezone('GMT'))
# room_suffix = gmt_time_to_dt.strftime('%d%H%M')[:-1]  # gmt_time_to_dt.strftime('%Y-%m-%dT%H:%M:%S%Z')
# servers_dct = {}
# for irc_network in ('irc.2600.net', 'irc.afternet.org'):  # ALL_IRC_NETWORK_NAMES
#     print("Joining %s IRC server with IRC handle %s" % (irc_network, my_irc_handle))
#     servers_dct[irc_network] = join_irc_network(irc_network, my_irc_handle)
#     for channel_name_root in all_possible_channels:
#         channel_name = "%s%s" % (channel_name_root, room_suffix)
#         join_irc_channel(servers_dct[irc_network], channel_name)
#
# while
#         users_in_channel = get_list_of_users_in_channel(servers_dct[irc_network], channel_name)
#         if len(users_in_channel) == 1:
#             assert(users_in_channel[0] == my_irc_handle)
#             print("I'll do something clever, because I'm the only one here. Perhaps I'll set the room's topic.")
#             set_irc_channel_topic(servers_dct[irc_network], channel_name, "The new topic is something or other.")
#         else:
#             print("Ah. I'm not the only one here. I'll exchange keys with the other people in the room.")
#             for user in users_in_channel:
#                 exchange_keys_with_user(servers_dct[irc_network], channel_name, user)
#
# print("Waiting for incoming messages from visitors")

