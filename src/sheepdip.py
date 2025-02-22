# -*- coding: utf-8 -*-
'''
Created on Jan 21, 2025

@author: mchobbit

# print(key.get_base64())  # print public key
# key.write_private_key(sys.stdout)
'''

from Crypto.PublicKey import RSA
from my.stringtools import *
from my.globals import *
from my.irctools.jaracorocks.harem import HaremOfPrateBots
from time import sleep
from my.irctools.jaracorocks.pratebot import PrateBot
import datetime
from queue import Queue, Empty
from my.audiotools import MyMic, raw_to_ogg
import os

noof_nicks = 10
bots = {}
rsakeys = {}
for i in range(0, noof_nicks):
    nickname = 'u%s%02d' % (generate_random_alphanumeric_string(5), i)
#    self.assertFalse(nickname in rsakeys)
#    self.assertFalse(nickname in bots)
    rsakeys[nickname] = RSA.generate(2048)
    bots[nickname] = PrateBot(['#prate'], nickname, 'cinqcent.local', 6667, rsakeys[nickname], autohandshake=False)

alice_bot = bots[list(bots)[0]]
bob_bot = bots[list(bots)[1]]
alice_bot.trigger_handshaking(bob_bot.nickname)
while alice_bot.homies[bob_bot.nickname].ipaddr is None or bob_bot.homies[alice_bot.nickname].ipaddr is None:
    print("Waiting for Alice and Bob to exchange keys...")
    sleep(3)

print("OK. Alice and Bob are connected.")

for k in bots:
    bots[k].quit()
