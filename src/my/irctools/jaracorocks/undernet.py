# -*- coding: utf-8 -*-
"""PrateBot class(es) for undernet-ish... boring.

Created on Jan 30, 2025

@author: mchobbit

s = 'm&4c;;B32a?eKNjw~g*;$0{=kLOVcOcgu2HzbjBk98m2hvhGq~'
desired_nickname = 'mac1'
desired_fullname = squeeze_da_keez(MY_RSAKEY.public_key())
irc_server = 'cinqcent.local'
from pratebot13 import *
rx_q = queue.LifoQueue()
tx_q = queue.LifoQueue()
svr = PrateBot(channel='#prate', nickname=desired_nickname, realname=desired_fullname,
                irc_server=irc_server, port=6667, crypto_rx_queue=rx_q, crypto_tx_queue=tx_q,
                max_realname_len=50)

assert(svr.nickname == desired_nickname)
assert(svr.fullname == desired_fullname)



TESTPORPOISES__MAXIMUM_REALNAME_LENGTH_SUPPORTED_BY_SERVER = 20
"""

import sys
import queue
from time import sleep
from threading import Thread, Lock

from cryptography.fernet import Fernet, InvalidToken
import base64
from my.globals import MY_IP_ADDRESS, MY_RSAKEY
from my.classes.readwritelock import ReadWriteLock
from my.irctools.cryptoish import rsa_decrypt, rsa_encrypt, unsqueeze_da_keez, squeeze_da_keez
from _queue import Empty
from random import randint, choice
from my.classes.homies import HomiesDct
from my.irctools.jaracorocks.vanilla import SingleServerIRCBotWithWhoisSupport
from my.irctools.jaracorocks.miniircd import CryptoOrientedSingleServerIRCBotWithWhoisSupport


class FullnameTruncatingCryptoOrientedSingleServerIRCBotWithWhoisSupport(CryptoOrientedSingleServerIRCBotWithWhoisSupport):
    raise AttributeError("NOT WRITTEN YET QQQ")

