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


"""

from threading import Thread

from Crypto.PublicKey import RSA
from my.classes.exceptions import IrcInitialConnectionTimeoutError, IrcFingerprintMismatchCausedByServer, IrcStillConnectingError, IrcNicknameTooLongError
from time import sleep
from my.irctools.cryptoish import squeeze_da_keez, bytes_64bit_cksum
from queue import Queue, Empty
from my.irctools.jaracorocks.pratebot import PrateBot
from my.globals import A_TICK, MAX_NICKNAME_LENGTH, SENSIBLE_TIMEOUT, SENSIBLE_NOOF_RECONNECTIONS
import datetime

MAXIMUM_HAREM_BLOCK_SIZE = 288


class HaremOfPrateBots:
# Eventually, make it threaded!

    def __init__(self, channels, desired_nickname , list_of_all_irc_servers, rsa_key, startup_timeout=SENSIBLE_TIMEOUT, maximum_reconnections=SENSIBLE_NOOF_RECONNECTIONS):
        if type(list_of_all_irc_servers) not in (list, tuple):
            raise ValueError("list_of_all_irc_servers should be a list or a tuple.")
        if len(desired_nickname) > MAX_NICKNAME_LENGTH:
            raise IrcNicknameTooLongError("Your nickname is too long")
        self.__channels = channels
        self.__rsa_key = rsa_key
        self.__startup_timeout = startup_timeout
        self.__maximum_reconnections = maximum_reconnections
        self.__list_of_all_irc_servers = list_of_all_irc_servers
        self.__desired_nickname = desired_nickname  # "%s%d" % (generate_irc_handle(MAX_NICKNAME_LENGTH + 10, MAX_NICKNAME_LENGTH - 2), randint(11, 99))
        self.port = 6667
        self.__bots = {}
        self.__outgoing_caches_dct = {}
        self.__outgoing_packetnumbers_dct = {}
        self.__privmsgs_from_harem_bots = Queue()
        self.__our_getqueue = Queue()
        self.__our_getq_cache = [None] * 65536
        self.__our_getq_alreadyspatout = 0
        assert(not hasattr(self, '__my_main_thread'))
        assert(not hasattr(self, '__my_main_loop'))
        self.__gotta_quit = False
        self.__my_main_thread = Thread(target=self.__my_main_loop, daemon=True)
        self.__my_main_thread.start()

    @property
    def startup_timeout(self):
        return self.__startup_timeout

    @property
    def maximum_reconnections(self):
        return self.__maximum_reconnections

    @property
    def gotta_quit(self):
        return self.__gotta_quit

    @gotta_quit.setter
    def gotta_quit(self, value):
        self.__gotta_quit = value

    def __my_main_loop(self):
        print("Harem rx queue servicing loop -- starting")
        self.log_into_all_functional_IRC_servers()
        while not self.gotta_quit:
            sleep(A_TICK)
            self.process_incoming_buffer()
        print("Harem rx queue servicing loop -- ending")

    @property
    def our_getqueue(self):
        return self.__our_getqueue

    @property
    def our_getq_cache(self):
        return self.__our_getq_cache

    @property
    def our_getq_alreadyspatout(self):
        return self.__our_getq_alreadyspatout

    @our_getq_alreadyspatout.setter
    def our_getq_alreadyspatout(self, value):
        self.__our_getq_alreadyspatout = value

    @property
    def outgoing_caches_dct(self):
        return self.__outgoing_caches_dct

    @property
    def outgoing_packetnumbers_dct(self):
        return self.__outgoing_packetnumbers_dct

    def find_nickname_by_pubkey(self, pubkey):
        if type(pubkey) not in (str, RSA.RsaKey):
            raise ValueError("find_nickname_by_pubkey() takes a pubkey or a nickname")
        potential_bots = {}
        for k in self.bots:
            bot = self.bots[k]
            if bot.homies != {}:
                for h in bot.homies:
                    if h.pubkey == pubkey:
                        potential_bots[k.irc_server] = h.nickname
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
        ready_bots = self.find_nickname_by_pubkey(pubkey)
        bot_key = list(set(ready_bots.keys()))[self.outgoing_packetnumbers_dct[squeeze_da_keez(pubkey)] % len(ready_bots)]
        print("Writing to %s" % bot_key)
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
            bytes_for_this_frame = min(MAXIMUM_HAREM_BLOCK_SIZE, bytes_remaining)
            our_block = datablock[pos:pos + bytes_for_this_frame]
            frame = bytearray()
            frame += self.outgoing_packetnumbers_dct[k].to_bytes(4, 'little')  # packet#
            frame += len(our_block).to_bytes(2, 'little')  # length
            frame += our_block  # data block
            frame += bytes_64bit_cksum(bytes(frame[0:len(frame)]))  # checksum
            self.outgoing_caches_dct[k][self.outgoing_packetnumbers_dct[k] % 65536] = frame
            self.send_cryptoput_to_randomly_chosen_pratebot(pubkey, frame)
            print("Sent pkt#%d of %d bytes" % (self.outgoing_packetnumbers_dct[k], len(frame)))
            bytes_remaining -= bytes_for_this_frame
            pos += bytes_for_this_frame
            self.outgoing_packetnumbers_dct[k] += 1
            if bytes_for_this_frame == 0:
                break

    def process_incoming_buffer(self):
        final_packetnumber = -1
        pubkey = None
        while final_packetnumber < 0 or [] != [i for i in range(self.our_getq_alreadyspatout, final_packetnumber + 1) if self.our_getq_cache[i % 65536] is None]:
            if self.gotta_quit:
                return
            else:
                the_bots = self.bots
                for k in the_bots:
                    try:
                        user, frame = self.bots[k].crypto_get_nowait()
                        if pubkey is None:
                            pubkey = self.bots[k].homies[user].pubkey
                        else:
                            assert(pubkey == self.bots[k].homies[user].pubkey)
                    except Empty:
                        pass
                    else:
                        packetno = int.from_bytes(frame[0:4], 'little')
                        if packetno < 256 * 256 and self.our_getq_alreadyspatout > 256 * 256 * 256 * 64:  # FIXME: ugly kludge
                            print("I think we've wrapped around.")
                            self.our_getq_alreadyspatout = 0
                        assert(packetno < 256 * 256 * 256 * 127)  # FIXME: PROGRAM A WRAPAROUND.
                        self.our_getq_cache[packetno % 65536] = frame
                        framelength = int.from_bytes(frame[4:6], 'little')
                        checksum = frame[framelength + 6:framelength + 14]
                        print("Rx'd pkt#%d of %d bytes" % (packetno, len(frame)))
                        if checksum != bytes_64bit_cksum(frame[0:6 + framelength]):
                            print("Bad checksum for packet #%d. You should request a fresh copy." % packetno)
                            # for i in range(6, 6 + framelength):
                            #     frame[i] = 0  # FIXME: ugly kludge
                        if framelength == 0:
                            final_packetnumber = packetno
        data_to_be_returned = bytearray()
        for i in range(self.our_getq_alreadyspatout, final_packetnumber + 1):
            data_to_be_returned += self.our_getq_cache[i][6:-8]
            self.our_getq_cache[i] = None
        self.our_getq_alreadyspatout = final_packetnumber + 1
        self.our_getqueue.put((pubkey, data_to_be_returned))

    @property
    def not_empty(self):
        return self.our_getqueue.not_empty

    @property
    def users(self):
        """Users in our chatroom(s). THAT INCLUDES US: being in there is mandatory whereas being a homie is optional."""
        retval = []
        for k in self.bots:
            retval += [u for u in self.bots[k].users]
        return list(set(retval))

    @property
    def ipaddrs(self):
        """IP addresses of homies in our chatroom(s)."""
        retval = []
        for k in self.bots:
            for user in [u for u in self.bots[k].users]:
                ipaddr = self.bots[k].homies[user].ipaddr
                if ipaddr is not None:
                    retval += [ipaddr]
        return list(set(retval))

    @property
    def pubkeys(self):
        """Pubkeys of homies in our chatroom(s)."""
        retval = []
        for k in self.bots:
            for user in [u for u in self.bots[k].users]:
                pubkey = self.bots[k].homies[user].pubkey
                if pubkey is not None and pubkey not in retval:
                    retval += [pubkey]
        return retval

    def empty(self):
        return self.our_getqueue.empty()

    def get(self, block=True, timeout=None):
        return self.our_getqueue.get(block, timeout)

    def get_nowait(self):
        return self.our_getqueue.get_nowait()

    @property
    def bots(self):
        return self.__bots

    def trigger_handshaking(self):
        for k in self.bots:
            self.bots[k].trigger_handshaking()

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
        pratestartup_threads_lst = []
        print("Trying all IRC servers")
        for k in self.list_of_all_irc_servers:
            pratestartup_threads_lst += [Thread(target=self.try_to_log_into_this_IRC_server, args=[k], daemon=True)]
        for t in pratestartup_threads_lst:
            t.start()
        for t in pratestartup_threads_lst:
            if self.gotta_quit:
                break
            t.join(timeout=SENSIBLE_TIMEOUT)

    def try_to_log_into_this_IRC_server(self, k):
        try:
            bot = PrateBot(channels=self.channels,
                                   nickname=self.desired_nickname,
                                   irc_server=k,
                                   port=self.port,
                                   rsa_key=self.rsa_key,
                                   startup_timeout=self.startup_timeout,
                                   maximum_reconnections=self.maximum_reconnections,
                                   strictly_nick=False)
        except (IrcInitialConnectionTimeoutError, IrcFingerprintMismatchCausedByServer):
            pass  # print("Failed to join", k)
        else:
#            print("Connected to", k)
            self.bots[k] = bot

    def quit(self):
        for k in self.bots:
            try:
                self.bots[k].quit()
            except Exception as e:
                print("Exception while quitting", k, "==>", e)

    @property
    def ready(self):
        return [k for k in self.bots if self.bots[k].ready]


if __name__ == "__main__":
    print("Hi.")
    # my_rsa_key1 = RSA.generate(2048)
    # my_rsa_key2 = RSA.generate(2048)
    #
    # h1 = HaremOfPrateBots(['#prate'], 'mac3333', ALL_SANDBOX_IRC_NETWORK_NAMES, my_rsa_key1, startup_timeout=30, maximum_reconnections=2)
    # h2 = HaremOfPrateBots(['#prate'], 'mac4444', ALL_SANDBOX_IRC_NETWORK_NAMES, my_rsa_key2, startup_timeout=30, maximum_reconnections=2)
    # print("Yay.")
    # print("<fin?")
