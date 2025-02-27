# -*- coding: utf-8 -*-
"""Rookery class.

Created on Jan 30, 2025

@author: mchobbit

This module contains a class -- PrateRookery -- that controls a gang of PrateBots. Ever PrateBot
joins a specific IRC server and one or more rooms (channels) in that server. The PrateRookery
instance lashes those bots together and uses them to communicate with other rookeries.

As you are aware, every user (of Prate) has an RSA key. The public key is distributed automatically
via private handshaking between bots. If a rookery is given a list of five IRC servers, it will
assign a bot to each of those servers and use the bot to log into each server. Each bot will log
in and handshake with the other users. This will cause each bot to become aware of the friendly
(Prate) users in the specified room(s) of that IRC server. Well, after the bots have made a good-
faith effort to log in, join channels, and handshake with (Prate) users in those channels, the
rookery will examine those bots' lists of friendly users, amalgamate those lists, and deduce a
list of true homies: Prate users with whom we've shaken hands and built secure communications.

From that point on, it is possible to use the rookery to send and receive short messages, via
get() and put(), to a destination user identified by public key. These functions conceal the
bots behind a layer of magic. The IRC servers used by this data transmission/receiption are
chosen at random. There is no 'did that data block arrive' signaling, although every block does
have a checksum and a packet number (which is per-destination, not per-message-length; so, each
time a packet is sent to a given destination, that destination's packet# increases by one).

See my __main__() function for an example.

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

from threading import Thread, Lock
from Crypto.PublicKey import RSA
from my.classes.exceptions import IrcInitialConnectionTimeoutError, IrcFingerprintMismatchCausedByServer, IrcNicknameTooLongError, PublicKeyUnknownError
from time import sleep
from my.irctools.cryptoish import squeeze_da_keez, bytes_64bit_cksum
from queue import Queue, Empty
from my.irctools.jaracorocks.pratebot import PrateBot
import datetime
from random import shuffle, randint
from my.stringtools import s_now, generate_random_alphanumeric_string, MAX_NICKNAME_LENGTH
from my.globals import STARTUP_TIMEOUT, SENSIBLE_NOOF_RECONNECTIONS, A_TICK, ENDTHREAD_TIMEOUT, ALL_SANDBOX_IRC_NETWORK_NAMES
# from my.classes.readwritelock import ReadWriteLock
MAXIMUM_ENCRYPTED_MSG_BLOCK_SIZE = 288


class PrateRookery:
# Eventually, make it threaded!

    def __init__(self, channels, desired_nickname, list_of_all_irc_servers, rsa_key,
                 startup_timeout=STARTUP_TIMEOUT, maximum_reconnections=SENSIBLE_NOOF_RECONNECTIONS,
                 autohandshake=True):
        print("%s %-20s              Initializing rookery" % (s_now(), desired_nickname))
        if type(list_of_all_irc_servers) not in (list, tuple):
            raise ValueError("list_of_all_irc_servers should be a list or a tuple.")
        if len(desired_nickname) > MAX_NICKNAME_LENGTH:
            raise IrcNicknameTooLongError("Your nickname is too long")
        self.__channels = channels
        self.__rsa_key = rsa_key
        self.__startup_timeout = startup_timeout
        self.__maximum_reconnections = maximum_reconnections
        self.__list_of_all_irc_servers = list_of_all_irc_servers
        self.__desired_nickname = desired_nickname
        self.__paused = False
        self.port = 6667
        self.__bots = {}
        self.__autohandshake = autohandshake
        self.__ready = False
        self.__outgoing_packetnumbers_dct = {}
        self.__privmsgs_from_rookery_bots = Queue()
        self.__our_getqueue = Queue()
        self.__our_getq_cache = [None] * 65536
        self.__our_getq_alreadyspatout = 0
        assert(not hasattr(self, '__my_main_thread'))
        assert(not hasattr(self, '__my_main_loop'))
        self.__gotta_quit = False
        self.__my_main_thread = Thread(target=self.__my_main_loop, daemon=True)
        self.__my_main_thread.start()
        self.__log_into_all_functional_IRC_servers_mutex = Lock()

    @property
    def autohandshake(self):
        return self.__autohandshake

    @property
    def paused(self):
        retval = self.__paused
        return retval

    @paused.setter
    def paused(self, value):
        self.__paused = value

    @property
    def privmsgs_from_rookery_bots(self):
        return self.__privmsgs_from_rookery_bots

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
        print("%s %-20s              Starting main loop" % (s_now(), self.desired_nickname))
        t = datetime.datetime.now()
        self.log_into_all_functional_IRC_servers()
        msgthr = Thread(target=self.keep_piping_the_privmsgs_out_of_bots_and_into_our_queue, daemon=True)
        msgthr.start()
        while (datetime.datetime.now() - t).seconds < self.startup_timeout and False in [self.bots[k].ready for k in self.bots]:
            sleep(1)
        if self.autohandshake:
            self.trigger_handshaking()
        self.__ready = True
        print("%s %-20s              Processing incoming buffer... indefinitely" % (s_now(), self.desired_nickname))
        while not self.gotta_quit:
            sleep(A_TICK)
            if not self.paused:
                self.process_incoming_buffer()
        msgthr.join(timeout=ENDTHREAD_TIMEOUT)
        print("%s %-20s              Leaving main loop" % (s_now(), self.desired_nickname))

    def keep_piping_the_privmsgs_out_of_bots_and_into_our_queue(self):
        while not self.gotta_quit:
            try:
                the_bots = list(set(self.bots))
            except Exception as e:  # pylint: disable=broad-exception-caught
                print("%s %-20s              Did the dictionary change? =>" % (s_now(), self.desired_nickname), e)
                sleep(A_TICK)
                continue
            else:
                for k in the_bots:
                    try:
                        src, msg = self.bots[k].crypto_get_nowait()
                        self.privmsgs_from_rookery_bots.put((src, k, msg))
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

    @property
    def true_homies(self):
        """Homies with whom we have exchanged public keys, fernet keys, and IP addresses."""
        return self.get_homies_list(True)

    def put(self, pubkey, datablock):
        if self.paused:
            raise ValueError("Set paused=False and try again.")
        # FIXME: If receiving party requests a copy of a cached packet from <255 ago, that's just too bad.
        assert(type(pubkey) is RSA.RsaKey)
        assert(type(datablock) is bytes)
        connected_homies = self.get_homies_list(True)
        if 0 == len(connected_homies):
            raise PublicKeyUnknownError("I cannot send a datablock: NO ONE LOGGED-IN IS OFFERING THIS PUBKEY.")
        outpackets_lst = self.generate_packets_list_for_transmission(pubkey, datablock)
        print("%s %-20s              Okay. Transmitting the outpackets." % (s_now(), self.desired_nickname))
        order_of_transmission = list(range(0, len(outpackets_lst)))
        shuffle(order_of_transmission)
        botno_offset = randint(0, 100)
        for i in range(0, len(outpackets_lst)):
            botno = (i + botno_offset) % len(connected_homies)
            pktno = order_of_transmission[i]
            self.bots[connected_homies[botno].irc_server].crypto_put(
                user=connected_homies[botno].nickname, byteblock=bytes(outpackets_lst[pktno]))

    def process_incoming_buffer(self):
        final_packetnumber = -1
        pubkey = None
        while not self.paused and not self.gotta_quit and \
        (final_packetnumber < 0 or [] != [i for i in range(self.our_getq_alreadyspatout, final_packetnumber + 1) if self.our_getq_cache[i % 65536] is None]):
            # FIXME: Prone to gridlock: it'll wait indefinitely for a missing packet.
            if self.gotta_quit or self.paused:
                return
            else:
                try:
                    user, irc_server, frame = self.privmsgs_from_rookery_bots.get_nowait()
                    if pubkey is None:
                        pubkey = self.bots[irc_server].homies[user].pubkey  # else assert(pubkey == self.bots[irc_server].homies[user].pubkey)
                except Empty:
                    sleep(A_TICK)
                else:
                    packetno = int.from_bytes(frame[0:4], 'little')
                    if packetno < 256 * 256 and self.our_getq_alreadyspatout > 256 * 256 * 256 * 64:
                        print("%s %-20s              I think we've wrapped around." % (s_now(), self.desired_nickname))
                        self.our_getq_alreadyspatout = 0
                    if packetno < self.our_getq_alreadyspatout:
                        print("%s %-20s              Ignoring packet#%d, as it's a duplicate" % (s_now(), self.desired_nickname, packetno))
                    else:
                        assert(packetno < 256 * 256 * 256 * 127)  # FIXME: PROGRAM A WRAPAROUND. Oh, and the '256*256*64' thing is an ugly kludge, too.
                        self.our_getq_cache[packetno % 65536] = frame
                        framelength = int.from_bytes(frame[4:6], 'little')
                        checksum = frame[framelength + 6:framelength + 14]
                        print("%s %-20s              Rx'd pkt#%d of %d bytes" % (s_now(), self.desired_nickname, packetno, len(frame)))
                        if checksum != bytes_64bit_cksum(frame[0:6 + framelength]):
                            print("%s %-20s              FIXME Bad checksum for pkt#%d. FIXME request a fresh copy. FIXME" % (s_now(), self.desired_nickname, packetno))
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
            bytes_for_this_frame = min(MAXIMUM_ENCRYPTED_MSG_BLOCK_SIZE, bytes_remaining)
            our_block = datablock[pos:pos + bytes_for_this_frame]
            frame = bytearray()
            frame += self.outgoing_packetnumbers_dct[squeezed_pk].to_bytes(4, 'little')  # packet#
            frame += len(our_block).to_bytes(2, 'little')  # length
            frame += our_block  # data block
            frame += bytes_64bit_cksum(bytes(frame[0:len(frame)]))  # checksum
            outpackets_lst.append(frame)  # print("%s %-20s              Sent pkt#%d of %d bytes" % (s_now(), self.desired_nickname, self.outgoing_packetnumbers_dct[squeezed_pk], len(frame)))
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

    def get_homies_list(self, connected=False):
        retval = []
        for bot in [self.bots[k] for k in self.bots]:
            for homie in [bot.homies[h] for h in bot.homies]:
                if connected is False or (homie.ipaddr is not None and homie.nickname in bot.users):
                    retval.append(homie)
        return retval

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
        print("%s %-20s              Triggering handshaking" % (s_now(), self.desired_nickname))
        for k in self.bots:
            # bot = self.bots[k]
            # if k == self.bots[k].nickname: # I don't need to shake hands with myself :)
            #     pass # print("%s %-20s: %-10s: no need to trigger handshaking w/ %s" % (s_now(), bot.irc_server, bot.nickname, k))
            # else:
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
        for k in self.list_of_all_irc_servers:
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
        else:  # print("Connected to", k)
            with self.__log_into_all_functional_IRC_servers_mutex:
                self.bots[k] = bot

    def quit(self):
        for k in self.bots:
            try:
                self.bots[k].quit()
            except Exception as e:  # pylint: disable=broad-exception-caught
                print("Exception while quitting", k, "==>", e)

########################################################################################################


if __name__ == "__main__":
    print("Generating RSA keys for Alice and Bob")
    the_room = '#room' + generate_random_alphanumeric_string(5)
    my_list_of_all_irc_servers = ALL_SANDBOX_IRC_NETWORK_NAMES  # ALL_REALWORLD_IRC_NETWORK_NAMES[:1]  # ALL_SANDBOX_IRC_NETWORK_NAMES  # ALL_REALWORLD_IRC_NETWORK_NAMES
    noof_servers = len(my_list_of_all_irc_servers)
    alice_rsa_key = RSA.generate(2048)
    bob_rsa_key = RSA.generate(2048)
    alice_pk = alice_rsa_key.public_key()
    bob_pk = bob_rsa_key.public_key()
    alice_nick = 'alice%d' % randint(111, 999)
    bob_nick = 'bob%d' % randint(111, 999)

    print("Creating rookerys for Alice and Bob")
    alice_rookery = PrateRookery([the_room], alice_nick, my_list_of_all_irc_servers, alice_rsa_key, autohandshake=False)
    bob_rookery = PrateRookery([the_room], bob_nick, my_list_of_all_irc_servers, bob_rsa_key, autohandshake=False)
    while not (alice_rookery.ready and bob_rookery.ready):
        sleep(1)

    print("Waiting for rookerys to shake hands")
    alice_rookery.trigger_handshaking()
    bob_rookery.trigger_handshaking()
    the_noof_homies = -1
    while the_noof_homies != len(alice_rookery.get_homies_list(True)):
        the_noof_homies = len(alice_rookery.get_homies_list(True))
        sleep(STARTUP_TIMEOUT // 2 + 1)

    alice_rookery.put(bob_pk, b"MARCO?")
    who_said_it, what_did_they_say = bob_rookery.get()
    assert(who_said_it == alice_pk)
    assert(what_did_they_say == b"MARCO?")
    bob_rookery.put(alice_pk, b"POLO!")
    who_said_it, what_did_they_say = bob_rookery.get()
    assert(who_said_it == bob_pk)
    assert(what_did_they_say == b"POLO!")

    alice_rookery.quit()
    bob_rookery.quit()
