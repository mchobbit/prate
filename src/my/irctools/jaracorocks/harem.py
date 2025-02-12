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


from my.irctools.jaracorocks.pratebot import HaremOfPrateBots
from Crypto.PublicKey import RSA
from time import sleep
from my.stringtools import *
from my.globals import *
my_rsa_key1 = RSA.generate(2048)
my_rsa_key2 = RSA.generate(2048)
list_of_all_irc_servers = PARAGRAPH_OF_ALL_IRC_NETWORK_NAMES.split(' ')
h1 = HaremOfPrateBots(['#prate', '#etarp'], list_of_all_irc_servers, my_rsa_key1)
h2 = HaremOfPrateBots(['#prate', '#etarp'], list_of_all_irc_servers, my_rsa_key2)
h1.log_into_all_functional_IRC_servers()
h2.log_into_all_functional_IRC_servers()
while len(h1.ready_bots(my_rsa_key2.public_key())) < 3 and len(h2.ready_bots(my_rsa_key2.public_key())) < 3:
    sleep(.1)

h1.put(my_rsa_key2.public_key(), b"HELLO WORLD.")
h2.process_incoming_data()

"""

import sys
from threading import Thread

# from my.classes.readwritelock import ReadWriteLock
from random import randint, shuffle, choice
from Crypto.PublicKey import RSA
from my.stringtools import generate_irc_handle
from my.classes.exceptions import FernetKeyIsUnknownError, \
                            PublicKeyBadKeyError, IrcPrivateMessageTooLongError, PublicKeyUnknownError, \
                            IrcInitialConnectionTimeoutError, IrcFingerprintMismatchCausedByServer, IrcIAmNotInTheChannelError, IrcStillConnectingError, FernetKeyIsInvalidError

from my.irctools.jaracorocks.vanilla import BotForDualQueuedSingleServerIRCBotWithWhoisSupport
from time import sleep
from my.globals import MY_IP_ADDRESS, MAX_PRIVMSG_LENGTH, MAX_NICKNAME_LENGTH, MAX_CRYPTO_MSG_LENGTH, JOINING_IRC_SERVER_TIMEOUT, DEFAULT_NOOF_RECONNECTIONS
from my.irctools.cryptoish import generate_fingerprint, squeeze_da_keez, rsa_encrypt, unsqueeze_da_keez, rsa_decrypt, bytes_64bit_cksum, receive_and_decrypt_message
from cryptography.fernet import Fernet, InvalidToken
import base64
from my.classes.readwritelock import ReadWriteLock
from my.classes.homies import HomiesDct
import datetime
from queue import Queue, Empty
from my.irctools.jaracorocks.pratebot import PrateBot


class HaremOfPrateBots:
# Eventually, make it threaded!

    def __init__(self, channels, list_of_all_irc_servers, rsa_key):
        if type(list_of_all_irc_servers) not in (list, tuple):
            raise ValueError("list_of_all_irc_servers should be a list or a tuple.")
        self.__channels = channels
        self.__rsa_key = rsa_key
        self.__list_of_all_irc_servers = list_of_all_irc_servers
        self.__desired_nickname = "%s%d" % (generate_irc_handle(MAX_NICKNAME_LENGTH + 10, MAX_NICKNAME_LENGTH - 2), randint(11, 99))
        self.port = 6667
        self.__bots = {}
        self.__outgoing_caches_dct = {}
        self.__outgoing_packetnumbers_dct = {}
        self.__incoming_queue = Queue()
        self.__incoming_cache = [None] * 65536
        self.__incoming_alreadyspatout = 0
        assert(not hasattr(self, '__my_main_thread'))
        assert(not hasattr(self, '__my_main_loop'))
        self.__gotta_quit = False
        self.__my_main_thread = Thread(target=self.__my_main_loop, daemon=True)
        self.__my_main_thread.start()

    @property
    def gotta_quit(self):
        return self.__gotta_quit

    @gotta_quit.setter
    def gotta_quit(self, value):
        self.__gotta_quit = value

    @property
    def ready(self):
        try:
            return super().ready
        except AttributeError:
            return False

    def __my_main_loop(self):
        print("Harem rx queue servicing loop -- starting")
        while not self.gotta_quit:
            sleep(.1)
            self.process_incoming_buffer()
        print("Harem rx queue servicing loop -- ending")

    @property
    def incoming_queue(self):
        return self.__incoming_queue

    @property
    def incoming_cache(self):
        return self.__incoming_cache

    @property
    def incoming_alreadyspatout(self):
        return self.__incoming_alreadyspatout

    @incoming_alreadyspatout.setter
    def incoming_alreadyspatout(self, value):
        self.__incoming_alreadyspatout = value

    @property
    def outgoing_caches_dct(self):
        return self.__outgoing_caches_dct

    @property
    def outgoing_packetnumbers_dct(self):
        return self.__outgoing_packetnumbers_dct

    def ready_bots(self, pubkey):
        potential_bots = {}
        for k in self.bots:
            bot = self.bots[k]
            try:
                nickname = [u for u in bot.homies if bot.ready \
                            and bot.homies[u].pubkey is not None \
                            and bot.homies[u].fernetkey is not None \
                            and bot.homies[u].ipaddr is not None \
                            and bot.homies[u].pubkey == pubkey][0]
            except IndexError:
                pass
            else:
                potential_bots[k] = nickname
        return potential_bots

    def randomly_chosen_bot_and_corresponding_nickname(self, pubkey):
        ready_bots = self.ready_bots(pubkey)
        bot_key = choice(list(set(ready_bots.keys())))
        bot = self.bots[bot_key]
        nickname = ready_bots[bot_key]
        return(bot, nickname)

    def send_cryptoput_to_randomly_chosen_pratebot(self, pubkey, frame):
        try:
            bot, nickname = self.randomly_chosen_bot_and_corresponding_nickname(pubkey)
        except IndexError as e:
            raise IrcStillConnectingError("My harem has no viable bots yet. Please try again in a minute or two.") from e
        else:
            bot.crypto_put(nickname, bytes(frame))

    def put(self, pubkey, datablock):
        assert(type(pubkey) is RSA.RsaKey)
        assert(type(datablock) is bytes)
        bytes_remaining = len(datablock)
        pos = 0
        k = squeeze_da_keez(pubkey)
        if k not in self.outgoing_caches_dct:
            self.outgoing_caches_dct[k] = [None] * 65536
        if k not in self.outgoing_packetnumbers_dct:
            self.outgoing_packetnumbers_dct[k] = 0
        if self.outgoing_packetnumbers_dct[k] >= 256 * 256 * 256 * 127:
            self.outgoing_packetnumbers_dct[k] -= 256 * 256 * 256 * 127
        while True:
            bytes_for_this_frame = min(288, bytes_remaining)
            our_block = datablock[pos:pos + bytes_for_this_frame]
            frame = bytearray()
            frame += self.outgoing_packetnumbers_dct[k].to_bytes(4, 'little')  # packet#
            frame += len(our_block).to_bytes(2, 'little')  # length
            frame += our_block  # data block
            frame += bytes_64bit_cksum(bytes(frame[0:len(frame)]))  # checksum
            self.outgoing_caches_dct[k][self.outgoing_packetnumbers_dct[k] % 65536] = frame
            self.send_cryptoput_to_randomly_chosen_pratebot(pubkey, frame)
            bytes_remaining -= bytes_for_this_frame
            pos += bytes_for_this_frame
            self.outgoing_packetnumbers_dct[k] += 1
            if bytes_for_this_frame == 0:
                break

    def process_incoming_buffer(self):
        final_packetnumber = -1
        pubkey = None
        while final_packetnumber < 0 or [] != [i for i in range(self.incoming_alreadyspatout, final_packetnumber + 1) if self.incoming_cache[i % 65536] is None]:
            if self.gotta_quit:
                return
            else:
                for k in self.bots:
                    try:
                        user, frame = self.bots[k].crypto_get_nowait()
                        if pubkey is None:
                            pubkey = self.bots[k].homies[user].pubkey
                        else:
                            assert(pubkey == self.bots[k].homies[user].pubkey)
                    except Empty:
                        sleep(.1)
                    else:
                        packetno = int.from_bytes(frame[0:4], 'little')
                        if packetno < 256 * 256 and self.incoming_alreadyspatout > 256 * 256 * 256 * 64:  # FIXME: ugly kludge
                            print("I think we've wrapped around.")
                            self.incoming_alreadyspatout = 0
                        assert(packetno < 256 * 256 * 256 * 127)  # FIXME: PROGRAM A WRAPAROUND.
                        self.incoming_cache[packetno % 65536] = frame
                        framelength = int.from_bytes(frame[4:6], 'little')
                        checksum = frame[framelength + 6:framelength + 14]
                        if checksum != bytes_64bit_cksum(frame[0:6 + framelength]):
                            print("Bad checksum for packet #%d. You should request a fresh copy." % packetno)
                        if framelength == 0:
                            final_packetnumber = packetno
        data_to_be_returned = bytearray()
        for i in range(self.incoming_alreadyspatout, final_packetnumber + 1):
            data_to_be_returned += self.incoming_cache[i][6:-8]
            self.incoming_cache[i] = None
        self.incoming_alreadyspatout = final_packetnumber + 1
        self.incoming_queue.put((pubkey, data_to_be_returned))

    @property
    def not_empty(self):
        return self.incoming_queue.not_empty

    def empty(self):
        return self.incoming_queue.empty()

    def get(self, block=True, timeout=None):
        return self.incoming_queue.get(block, timeout)

    def get_nowait(self):
        return self.incoming_queue.get_nowait()

    @property
    def bots(self):
        return self.__bots  # TODO: make threadsafe

    @property
    def list_of_all_irc_servers(self):
        return self.__list_of_all_irc_servers

    @property
    def channels(self):
        return self.__channels

    @property
    def rsa_key(self):
        return self.__rsa_key

    @property
    def desired_nickname(self):
        return self.__desired_nickname

    def log_into_all_functional_IRC_servers(self):
        shuffle(self.list_of_all_irc_servers)
#        print("Trying all IRC servers")
        for k in self.list_of_all_irc_servers:
#            print("Trying", k)
            self.try_to_log_into_this_IRC_server(k)
#        failures = lambda: [k for k in self.bots if self.bots[k].noof_reconnections >= 3 and not self.bots[k].client]
#        successes = lambda: [k for k in self.bots if self.bots[k].client and self.bots[k].client.joined]
#        print("successes:", successes)
        # while len(failures()) + len(successes()) < len(self.bots):
        #     sleep(1)
#        for k in list(failures()):
#            print("Deleting", k)
#            self.bots[k].autoreconnect = False
#            del self.bots[k]  # Triggers quit()
#        print("Huzzah. We are logged into %d functional IRC servers." % len(self.bots))

    def try_to_log_into_this_IRC_server(self, k):
        try:
            self.bots[k] = PrateBot(channels=self.channels,
                                   nickname=self.desired_nickname,
                                   irc_server=k,
                                   port=self.port,
                                   rsa_key=self.rsa_key)
        except (IrcInitialConnectionTimeoutError, IrcFingerprintMismatchCausedByServer):
            self.bots[k] = None

    def quit(self):
        for k in self.bots:
            try:
                self.bots[k].quit()
            except Exception as e:
                print("Exception while quitting", k, "==>", e)


if __name__ == "__main__":
    print("Hi.")

