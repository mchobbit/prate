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
rx_q = queue.Queue()
tx_q = queue.Queue()
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


def hacky_fracky_fruitcake():
    from queue import Queue
    from random import randint
    from Crypto.PublicKey import RSA
    # crypto_rx_queue = Queue()
    # crypto_tx_queue = Queue()
    my_startup_timeout = 20
    my_channel = '#prate'
    my_nickname = 'mac%d' % randint(111, 999)
    my_rsa_key = RSA.generate(2048)
    my_irc_server = 'cinqcent.local'
    my_port = 6667
    bot = PrateBot(my_channel, my_nickname, my_rsa_key, my_irc_server, my_port, startup_timeout=my_startup_timeout)
    while bot.svr is None:
        sleep(1)
    print("PLEASE LAUNCH ME IN BOTH SHELL WINDOWS! I'm waiting.")
    while len(bot.svr.channels[bot.svr.initial_channel].users()) < 3:
        sleep(1)
    irc_channel_members = list(bot.svr.channels[bot.svr.initial_channel].users())
    the_userlist = []
    new_users = [str(u) for u in irc_channel_members if u not in the_userlist and str(u) != bot.svr.nickname]
    dead_users = [str(u) for u in the_userlist if u not in irc_channel_members and str(u) != bot.svr.nickname]
    for user in dead_users:
        print("%-20s has died. Removing him from our list." % user)
        bot.svr.homies[user].pubkey_fragments_lst = None
        the_userlist.remove(user)
        if user in new_users:
            new_users.remove(user)
    for user in new_users:
        the_userlist += [user]
    shuffle(new_users)
    the_users_we_care_about = list(set([str(u) for u in the_userlist if str(u) != bot.svr.nickname]))
    user = the_users_we_care_about[0]
    print("Great! We are both present. I am %s, and I plan to talk to %s." % (bot.svr.nickname, user))
    return (bot, user)


def hi_my_names_Doechii_with_two_Is(bot, user):
    bot.svr.scan_a_user_for_fingerprints_publickeys_etc(user)
    lst = [bot.nickname, user]
    lst.sort()
    pitcher, catcher = lst
    if pitcher == bot.nickname:
        print("My name is %s and I am the pitcher" % bot.nickname)
    else:
        print("My name is %s and I am the catcher" % bot.nickname)
    return(pitcher, catcher)
'''
from pratebot16 import *
bot, user = hacky_fracky_fruitcake()
pitcher, catcher = hi_my_names_Doechii_with_two_Is(bot, user)


'''

