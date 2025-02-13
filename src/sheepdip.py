# -*- coding: utf-8 -*-
'''
Created on Jan 21, 2025

@author: mchobbit

# print(key.get_base64())  # print public key
# key.write_private_key(sys.stdout)


from random import shuffle, randint
from my.stringtools import generate_irc_handle
from Crypto.PublicKey import RSA
from my.globals import PARAGRAPH_OF_ALL_IRC_NETWORK_NAMES, JOINING_IRC_SERVER_TIMEOUT
from my.classes.exceptions import MyIrcInitialConnectionTimeoutError, MyIrcFingerprintMismatchCausedByServer
from time import sleep
from queue import Queue
'''

from Crypto.PublicKey import RSA
from time import sleep
from my.globals import ALL_IRC_NETWORK_NAMES
from my.stringtools import generate_random_alphanumeric_string
from my.irctools.jaracorocks.vanilla import BotForDualQueuedSingleServerIRCBotWithWhoisSupport
from queue import Empty
from random import randint
from IPython.testing.plugin.dtexample import random_all


def join_as_many_irc_servers_as_possible(channel, desired_nickname, my_port=6667):
    bots = {}
    for my_irc_server in ALL_IRC_NETWORK_NAMES:
        bots[my_irc_server] = BotForDualQueuedSingleServerIRCBotWithWhoisSupport([channel], desired_nickname, my_irc_server, my_port)
    return bots


Xbots = join_as_many_irc_servers_as_possible('#prate', 'xmchob%d' % randint(100, 999))
Ybots = join_as_many_irc_servers_as_possible('#prate', 'ymchob%d' % randint(100, 999))
successes_thus_far = -1
while successes_thus_far < len([k for k in ALL_IRC_NETWORK_NAMES if Xbots[k].ready and Ybots[k].ready]):
    successes_thus_far = len([k for k in ALL_IRC_NETWORK_NAMES if Xbots[k].ready and Ybots[k].ready])
    sleep(10)

goodKs = [k for k in ALL_IRC_NETWORK_NAMES if Xbots[k].ready and Ybots[k].ready]

for k in goodKs:
    for xy in (Xbots, Ybots):
        try:
            while True:
                _ = xy[k].get_nowait()
        except Empty:
            break

stem = generate_random_alphanumeric_string(30)
for k in goodKs:
    if Xbots[k].ready and Ybots[k].ready:
        p = stem
        Xbots[k].put(Ybots[k].nickname, p)

defective_items = []
for k in goodKs:
    if Xbots[k].ready and Ybots[k].ready:
        p = stem
        try:
            (src, msg) = Ybots[k].get(timeout=2)
            if p == msg:
                print("%s is gooood" % k)
            else:
                print("%s is defective" % k)
                defective_items += [k]
        except:
            print("No response from %s" % k)

stem = generate_random_alphanumeric_string(30)
for k in goodKs:
    if Ybots[k].ready and Ybots[k].ready:
        p = stem
        Ybots[k].put(Xbots[k].nickname, p)

defective_items = []
for k in goodKs:
    if Ybots[k].ready and Xbots[k].ready:
        p = stem
        try:
            (src, msg) = Xbots[k].get(timeout=2)
            if p == msg:
                print("%s is gooood" % k)
            else:
                print("%s is defective" % k)
                defective_items += [k]
        except:
            print("No response from %s" % k)

for k in defective_items:
    goodKs.remove(k)

