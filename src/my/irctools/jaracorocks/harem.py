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
from functools import partial
from Crypto.PublicKey import RSA
from my.classes.exceptions import IrcInitialConnectionTimeoutError, IrcFingerprintMismatchCausedByServer, IrcStillConnectingError, IrcNicknameTooLongError, PublicKeyUnknownError
from time import sleep
from my.irctools.cryptoish import squeeze_da_keez, bytes_64bit_cksum, skinny_key
from queue import Queue, Empty
from my.irctools.jaracorocks.pratebot import PrateBot
from my.globals import A_TICK, MAX_NICKNAME_LENGTH, SENSIBLE_NOOF_RECONNECTIONS, MAXIMUM_HAREM_BLOCK_SIZE, ENDTHREAD_TIMEOUT, STARTUP_TIMEOUT
import datetime
from my.classes import MyTTLCache
from random import choice, shuffle, randint
from my.classes.readwritelock import ReadWriteLock
from my.stringtools import s_now


class HaremOfPrateBots:
# Eventually, make it threaded!

    def __init__(self, channels, desired_nickname, list_of_all_irc_servers, rsa_key,
                 startup_timeout=STARTUP_TIMEOUT, maximum_reconnections=SENSIBLE_NOOF_RECONNECTIONS,
                 autohandshake=True):
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
        self.__paused = False
        self.__paused_lock = ReadWriteLock()
        self.port = 6667
        self.__bots = {}
        self.__autohandshake = autohandshake
        self.__ready = False
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
    def autohandshake(self):
        return self.__autohandshake

    @property
    def paused(self):
        self.__paused_lock.acquire_read()
        try:
            retval = self.__paused
            return retval
        finally:
            self.__paused_lock.release_read()

    @paused.setter
    def paused(self, value):
        self.__paused_lock.acquire_write()
        try:
            self.__paused = value
        finally:
            self.__paused_lock.release_write()

    @property
    def privmsgs_from_harem_bots(self):
        return self.__privmsgs_from_harem_bots

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

    @property
    def ready(self):
        """False UNTIL all bots have been launched (pass/fail, idc) and handshaking has been initiated (ditto).

        This is no guarantee of connectivity *nor* successful handshaking. It merely means,
        all the things that can be attempted have been attempted."""
        return self.__ready

    def __my_main_loop(self):
        t = datetime.datetime.now()
        self.log_into_all_functional_IRC_servers()
        msgthr = Thread(target=self.keep_piping_the_privmsgs_out_of_bots_and_into_our_queue, daemon=True)
        msgthr.start()
        print("%s %s: waiting for bots to log in or timeout" % (s_now(), self.desired_nickname))
        while (datetime.datetime.now() - t).seconds < self.startup_timeout and False in [self.bots[k].ready for k in self.bots]:
            sleep(1)
        if self.autohandshake:
            print("%s %s: triggering handshake now" % (s_now(), self.desired_nickname))
            self.trigger_handshaking()
        print("%s %s: All bots in my harem are ready to be addressed. (I'm not promising they're connected, though.)" % (s_now(), self.desired_nickname))
        self.__ready = True
        while not self.gotta_quit:
            sleep(A_TICK)
            if not self.paused:
                self.process_incoming_buffer()
        msgthr.join(timeout=ENDTHREAD_TIMEOUT)

    def keep_piping_the_privmsgs_out_of_bots_and_into_our_queue(self):
        while not self.gotta_quit:
            try:
                the_bots = list(set(self.bots))
            except Exception as e:
                print("%s %s: did the dictionary change? =>" % (s_now(), self.desired_nickname), e)
                sleep(A_TICK)
                continue
            else:
                for k in the_bots:
                    try:
                        src, msg = self.bots[k].crypto_get_nowait()
                        self.privmsgs_from_harem_bots.put((src, k, msg))
                    except Empty:
                        sleep(A_TICK)

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
    def outgoing_packetnumbers_dct(self):
        return self.__outgoing_packetnumbers_dct

    def put(self, pubkey, datablock):
        if self.paused:
            raise ValueError("Set paused=False and try again.")
        # FIXME: If receiving party requests a copy of a cached packet from <255 ago, that's just too bad.
        assert(type(pubkey) is RSA.RsaKey)
        assert(type(datablock) is bytes)
        useful_homies = [h for h in self.homies if h.pubkey is not None and h.pubkey == pubkey]
        if 0 == len(useful_homies):
            raise PublicKeyUnknownError("I cannot send a datablock: NO ONE LOGGED-IN IS OFFERING THIS PUBKEY.")
        outpackets_lst = self.generate_packets_list_for_transmission(pubkey, datablock)
        print("%s %s: okay. Transmitting the outpackets." % (s_now(), self.desired_nickname))
        order_of_transmission_groupA = list(range(0, len(outpackets_lst)))
        order_of_transmission_groupB = list(range(0, len(outpackets_lst)))
        shuffle(order_of_transmission_groupA)
        shuffle(order_of_transmission_groupB)
        order_of_transmission = order_of_transmission_groupA + order_of_transmission_groupB
        botno_offset = randint(0, 100)
        for i in range(0, len(outpackets_lst)):
            botno = (i + botno_offset) % len(useful_homies)
            pktno = order_of_transmission[i]
            self.bots[useful_homies[botno].irc_server].crypto_put(
                user=useful_homies[botno].nickname, byteblock=bytes(outpackets_lst[pktno]))

    def process_incoming_buffer(self):
        final_packetnumber = -1
        pubkey = None
        while not self.paused and not self.gotta_quit and \
        (final_packetnumber < 0 or [] != [i for i in range(self.our_getq_alreadyspatout, final_packetnumber + 1) if self.our_getq_cache[i % 65536] is None]):
            # FIXME: Prone to lockups and gridlock because it'll wait indefinitely for a missing packet.
            if self.gotta_quit or self.paused:
                return
            else:
                try:
                    user, irc_server, frame = self.privmsgs_from_harem_bots.get_nowait()
                    if pubkey is None:
                        pubkey = self.bots[irc_server].homies[user].pubkey  # else assert(pubkey == self.bots[irc_server].homies[user].pubkey)
                except Empty:
                    pass  # sleep(A_TICK)
                else:
                    packetno = int.from_bytes(frame[0:4], 'little')
                    if packetno < 256 * 256 and self.our_getq_alreadyspatout > 256 * 256 * 256 * 64:  # FIXME: ugly kludge
                        print("%s %s: I think we've wrapped around." % (s_now(), self.desired_nickname))
                        self.our_getq_alreadyspatout = 0
                    if packetno < self.our_getq_alreadyspatout:
                        print("%s %s: ignoring packet#%d, as it's a duplicate" % (s_now(), self.desired_nickname, packetno))
                    else:
                        assert(packetno < 256 * 256 * 256 * 127)  # FIXME: PROGRAM A WRAPAROUND.
                        self.our_getq_cache[packetno % 65536] = frame
                        framelength = int.from_bytes(frame[4:6], 'little')
                        checksum = frame[framelength + 6:framelength + 14]
                        print("%s %s: rx'd pkt#%d of %d bytes" % (s_now(), self.desired_nickname, packetno, len(frame)))
                        if checksum != bytes_64bit_cksum(frame[0:6 + framelength]):
                            print("%s %s: bad checksum for pkt#%d. You should request a fresh copy." % (s_now(), self.desired_nickname, packetno))
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

    def find_field_by_pubkey(self, pubkey, fieldname, handshook_only):
        if type(pubkey) not in (str, RSA.RsaKey):
            raise ValueError("find_nickname_by_pubkey() takes a pubkey or a nickname")
        squeezed_pk = squeeze_da_keez(pubkey)
        useful_bots_dct = {}
        for bot in [self.bots[b] for b in self.bots]:
            for homie in [bot.homies[h] for h in bot.homies]:
                if homie.pubkey is not None \
                and squeeze_da_keez(homie.pubkey) == squeezed_pk \
                and (handshook_only is False or homie.ipaddr is not None):
                    useful_bots_dct[bot.irc_server] = getattr(homie, fieldname)  # if we have ipaddr, it means we already have pubkey
        return useful_bots_dct

    def find_nickname_by_pubkey(self, pubkey, handshook_only=False):
        return self.find_field_by_pubkey(pubkey, 'nickname', handshook_only)

    def generate_packets_list_for_transmission(self, pubkey, datablock):
        outpackets_lst = []
        bytes_remaining = len(datablock)
        pos = 0
        squeezed_pk = squeeze_da_keez(pubkey)
        # if squeezed_pk not in self.outgoing_caches_dct:
        #     self.outgoing_caches_dct[squeezed_pk] = [None] * 256
        if squeezed_pk not in self.outgoing_packetnumbers_dct:
            self.outgoing_packetnumbers_dct[squeezed_pk] = 0
        if self.outgoing_packetnumbers_dct[squeezed_pk] >= 256 * 256 * 256 * 127:
            self.outgoing_packetnumbers_dct[squeezed_pk] -= 256 * 256 * 256 * 127
        while True:
            bytes_for_this_frame = min(MAXIMUM_HAREM_BLOCK_SIZE, bytes_remaining)
            our_block = datablock[pos:pos + bytes_for_this_frame]
            frame = bytearray()
            frame += self.outgoing_packetnumbers_dct[squeezed_pk].to_bytes(4, 'little')  # packet#
            frame += len(our_block).to_bytes(2, 'little')  # length
            frame += our_block  # data block
            frame += bytes_64bit_cksum(bytes(frame[0:len(frame)]))  # checksum
            outpackets_lst.append(frame)
            print("%s %s: sent pkt#%d of %d bytes" % (s_now(), self.desired_nickname, self.outgoing_packetnumbers_dct[squeezed_pk], len(frame)))
            bytes_remaining -= bytes_for_this_frame
            pos += bytes_for_this_frame
            self.outgoing_packetnumbers_dct[squeezed_pk] += 1
            if bytes_for_this_frame == 0:
                break
        return outpackets_lst

    @property
    def users(self):
        """Users in our chatroom(s). THAT INCLUDES US: being in there is mandatory whereas being a homie is optional."""
        retval = []
        for k in self.bots:
            for u in self.bots[k].users:
                if u not in retval:
                    retval.append(u)
        return list(set(retval))

    @property
    def homies(self):
        retval = []
        for k in self.bots:
            for h in self.bots[k].homies:
                retval.append(self.bots[k].homies[h])
        return retval

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
            for pk in self.bots[k].pubkeys:
                if pk not in retval:
                    retval.append(pk)
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
        print("%s %s: triggering handshaking" % (s_now(), self.desired_nickname))
        # for k in self.bots:
        #     self.bots[k].trigger_handshaking()
        my_threads = []
#        print("Triggering handshaking")
        for k in self.bots:
            my_threads += [Thread(target=self.bots[k].trigger_handshaking, daemon=True)]  # args=[k]
#        print("Starting handshaking")
        for thr in my_threads:
            thr.start()
#        print("Joining handshaking")
        for thr in my_threads:
            thr.join()
#        print("Exiting handshaking")

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
        for k in self.list_of_all_irc_servers:
#             self.try_to_log_into_this_IRC_server(k)
            pratestartup_threads_lst += [Thread(target=self.try_to_log_into_this_IRC_server, args=[k], daemon=True)]
        for t in pratestartup_threads_lst:
            t.start()
        for t in pratestartup_threads_lst:
            if self.gotta_quit:
                break
            t.join(timeout=ENDTHREAD_TIMEOUT)  # Wait until the connection attempt completes (success?failure?doesn't matter)

    def try_to_log_into_this_IRC_server(self, k):
        try:
            bot = PrateBot(channels=self.channels,
                                   nickname=self.desired_nickname,
                                   irc_server=k,
                                   port=self.port,
                                   rsa_key=self.rsa_key,
                                   startup_timeout=self.startup_timeout,
                                   maximum_reconnections=self.maximum_reconnections,
                                   strictly_nick=False,
                                   autohandshake=self.autohandshake)
        except (IrcInitialConnectionTimeoutError, IrcFingerprintMismatchCausedByServer):
            pass  # print("Failed to join", k)
        else:
#            print("Connected to", k)
            self.bots[k] = bot  # FIXME: NOT THREADSAFE!

    def quit(self):
        for k in self.bots:
            try:
                self.bots[k].quit()
            except Exception as e:
                print("Exception while quitting", k, "==>", e)


if __name__ == "__main__":
    print("Hi.")
    # my_rsa_key1 = RSA.generate(2048)
    # my_rsa_key2 = RSA.generate(2048)
    #
    # h1 = HaremOfPrateBots(['#prate'], 'mac3333', ALL_SANDBOX_IRC_NETWORK_NAMES, my_rsa_key1, startup_timeout=30, maximum_reconnections=2)
    # h2 = HaremOfPrateBots(['#prate'], 'mac4444', ALL_SANDBOX_IRC_NETWORK_NAMES, my_rsa_key2, startup_timeout=30, maximum_reconnections=2)
    # print("Yay.")
    # print("<fin?")
