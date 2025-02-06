# -*- coding: utf-8 -*-
'''
Created on Jan 21, 2025

@author: mchobbit

# print(key.get_base64())  # print public key
# key.write_private_key(sys.stdout)
'''

from random import shuffle, randint
from my.stringtools import generate_irc_handle
from Crypto.PublicKey import RSA
from my.globals import PARAGRAPH_OF_ALL_IRC_NETWORK_NAMES, JOINING_IRC_SERVER_TIMEOUT
from my.classes.exceptions import MyIrcInitialConnectionTimeoutError, MyIrcFingerprintMismatchCausedByServer
from time import sleep
from my.irctools.jaracorocks.pratebot import PrateBot
from queue import LifoQueue
import sys
from threading import Thread


class HaremOfBots:
# Eventually, make it threaded!

    def __init__(self, channel, desired_nickname, all_potential_servers, rsa_key, harem_rx_queue, harem_tx_queue):
        max_nickname_length = 9
        self.__desired_nickname = desired_nickname  # "%s%d" % (generate_irc_handle(max_nickname_length - 3, max_nickname_length - 3), randint(111, 999))
        self.__all_potential_servers = all_potential_servers
        self.__harem_rx_queue = harem_rx_queue
        self.__harem_tx_queue = harem_tx_queue
        self.__channel = channel
        self.__rsa_key = rsa_key
        self.port = 6667
        self.bots = {}

    @property
    def channel(self):
        return self.__channel

    @property
    def all_potential_servers(self):
        return self.__all_potential_servers

    @property
    def rsa_key(self):
        return self.__rsa_key

    @property
    def desired_nickname(self):
        return self.__desired_nickname

    @property
    def harem_rx_queue(self):
        return self.__harem_rx_queue

    @property
    def harem_tx_queue(self):
        return self.__harem_tx_queue

    def log_into_all_functional_IRC_servers(self):
        all_irc_servers_names = [r for r in PARAGRAPH_OF_ALL_IRC_NETWORK_NAMES.replace('\n', ' ').split(' ') if len(r) >= 5]
        all_irc_servers_names += ['irc.foo.bar', 'irc.wtf.bruh', 'newphone.who.dis']
        shuffle(all_irc_servers_names)
        print("Trying all IRC servers")
        for k in self.all_potential_servers:
            print("Trying", k)
            self.try_to_log_into_this_IRC_server(k)
        failures = lambda: [k for k in self.bots if self.bots[k].noof_reconnections >= 3 and not self.bots[k].svr]
        successes = lambda: [k for k in self.bots if self.bots[k].svr and self.bots[k].svr.joined]
        while len(failures()) + len(successes()) < len(self.bots):
            sleep(1)

        for k in list(failures()):
            print("Deleting", k)
            self.bots[k].autoreconnect = False
            if self.bots[k].svr:
                self.bots[k].svr.shut_down_threads()
            self.bots[k].time_to_quit = True
            Thread(target=self.bots[k].quit, daemon=True).start()
        for k in list(failures()):
            del self.bots[k]
#            self.bots[k].quit()
        print("Huzzah. We are logged into %d functional IRC servers." % len(self.bots))

    def try_to_log_into_this_IRC_server(self, k):
        try:
            print("Trying to log into", k)
            self.bots[k] = PrateBot(channel=self.channel,
                                   nickname=self.desired_nickname,
                                   rsa_key=self.rsa_key,
                                   irc_server=k,
                                   port=self.port,
                                   startup_timeout=JOINING_IRC_SERVER_TIMEOUT)
        except (MyIrcInitialConnectionTimeoutError, MyIrcFingerprintMismatchCausedByServer):
            self.bots[k] = None

################################################################################################

'''
from sheepdip import *
my_list_of_all_potential_servers = ['irc.foo.bar', 'irc.wtf.bruh', 'newphone.who.dis'] + \
        [r for r in PARAGRAPH_OF_ALL_IRC_NETWORK_NAMES.replace('\n', ' ').split(' ') if len(r) >= 5]
my_rsa_key = RSA.generate(2048)
my_channel = "#prate123"
my_desired_nickname = 'mac1'
my_harem_tx_q = LifoQueue()
my_harem_rx_q = LifoQueue()
harem = HaremOfBots(my_channel, my_desired_nickname, my_list_of_all_potential_servers, my_rsa_key, my_harem_rx_q, my_harem_tx_q)
harem.log_into_all_functional_IRC_servers()

'''

if __name__ == '__main__':
    my_list_of_all_potential_servers = ['irc.foo.bar', 'irc.wtf.bruh', 'newphone.who.dis'] + \
            [r for r in PARAGRAPH_OF_ALL_IRC_NETWORK_NAMES.replace('\n', ' ').split(' ') if len(r) >= 5]
    my_rsa_key = RSA.generate(2048)
    my_channel = "#prate123"
    my_desired_nickname = 'mac1'
    my_harem_tx_q = LifoQueue()
    my_harem_rx_q = LifoQueue()
    harem = HaremOfBots(my_channel, my_desired_nickname, my_list_of_all_potential_servers, my_rsa_key, my_harem_rx_q, my_harem_tx_q)
    harem.log_into_all_functional_IRC_servers()
    print("Exiting.")
    sys.exit(0)

