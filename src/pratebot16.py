# -*- coding: utf-8 -*-
"""Example Google style docstrings.

Created on Jan 30, 2025

@author: mchobbit

This module contains classes for creating a Prate class that monitors the IRC
server and sets up secure comms between users.

Todo:
    * Better docs
    * Detect if users' nicknames change
    * Make the users' dictionary threadsafe
    * Make the entire class threadsafe
    * Use the public keys' fingerprints, not the users' nicknames, as the key for the dictionary
    * Turn the users' dictionary into a class
    * Auto-check the nicknames whenever using a dictionary entry

.. _Google Python Style Guide:
   http://google.github.io/styleguide/pyguide.html

.. _Napoleon Style Guide:
   https://sphinxcontrib-napoleon.readthedocs.io/en/latest/example_google.html

Example:

from Crypto.PublicKey import RSA
from pratebot16 import *
import queue
desired_nickname = 'mac1'
my_irc_server = 'cinqcent.local'
my_channel = '#prate'
rx_q = queue.LifoQueue()
tx_q = queue.LifoQueue()
my_rsa_key = RSA.generate(2048)
bot = PrateBot(channel=my_channel, nickname=desired_nickname,
                rsa_key=my_rsa_key,
                irc_server=my_irc_server,
                port=6667,
                startup_timeout=30)

"""

import sys
from time import sleep
# from threading import Thread

from _queue import Empty
from random import randint, choice, shuffle
from Crypto.PublicKey import RSA
from my.irctools.jaracorocks.pratebot import PrateBot

##########################################################################################################

if __name__ == "__main__":
    if len(sys.argv) != 5:
#        print("Usage: %s <URL> <port> <channel> <nickname>" % sys.argv[0])
#        sys.exit(1)
        my_irc_server = 'cinqcent.local'
        my_port = 6667
        my_channel = '#prate'
        desired_nickname = 'mac1'
    else:
        my_irc_server = sys.argv[1]
        my_port = int(sys.argv[2])
        my_channel = sys.argv[3]
        desired_nickname = sys.argv[4]

    my_rsa_key = RSA.generate(2048)
    bot = PrateBot(my_channel, desired_nickname, my_rsa_key, my_irc_server, my_port, startup_timeout=30)
    while True:
        sleep(1)
        if bot.svr is None:
            continue
        bot.svr.show_users_dct_info(True if randint(0, 10) == 0 else False)
        try:
            u = choice(list(bot.svr.homies.keys()))
        except IndexError:
            pass
        else:
            if bot.svr.homies[u].ipaddr is not None and randint(0, 10) == 0:
                bot.crypto_tx_queue.put((u, ('HELLO from %s to %s' % (bot.svr.nickname, u)).encode()))
            try:
                while True:
                    the_user, the_blk = bot.crypto_rx_queue.get_nowait()
                    assert("HELLO from" in the_blk.decode())
                    print(the_user, "==>", the_blk)
            except Empty:
                pass
