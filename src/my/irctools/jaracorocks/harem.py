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
from my.classes.exceptions import IrcInitialConnectionTimeoutError, IrcFingerprintMismatchCausedByServer, IrcStillConnectingError, IrcNicknameTooLongError, PublicKeyUnknownError, \
    FernetKeyIsInvalidError
from time import sleep
from my.irctools.cryptoish import squeeze_da_keez, bytes_64bit_cksum, skinny_key, sha1
from queue import Queue, Empty
from my.irctools.jaracorocks.pratebot import PrateBot
from my.globals import A_TICK, MAX_NICKNAME_LENGTH, SENSIBLE_NOOF_RECONNECTIONS, MAXIMUM_HAREM_BLOCK_SIZE, ENDTHREAD_TIMEOUT, STARTUP_TIMEOUT, ALL_SANDBOX_IRC_NETWORK_NAMES, \
    ALL_REALWORLD_IRC_NETWORK_NAMES
import datetime
from my.classes import MyTTLCache
from random import choice, shuffle, randint
from my.stringtools import s_now, generate_random_alphanumeric_string
import cProfile
from pstats import Stats
import base64
import hashlib
import os


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
        retval = self.__paused
        return retval

    @paused.setter
    def paused(self, value):
        self.__paused = value

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
        assert(type(pubkey) is RSA.RsaKey)
        assert(type(datablock) is bytes)
        outpackets_lst = self.generate_packets_list_for_transmission(pubkey, datablock)
        packetnum_offset = self.outgoing_packetnumbers_dct[squeeze_da_keez(pubkey)] - len(outpackets_lst)
        print("%s %s: okay. Transmitting the outpackets." % (s_now(), self.desired_nickname))
        our_homies = [h for h in self.connected_homies_lst if h.pubkey == pubkey]
        if 0 == len(our_homies):
            raise PublicKeyUnknownError("I cannot send a datablock: NO ONE LOGGED-IN IS OFFERING THIS PUBKEY.")
        noof_packets = len(outpackets_lst)
        noof_homies = len(our_homies)
        packetstatuses = {}
        is_homie_busy = [False] * noof_homies
        el = 0
        # Send a packet to every homie, in order.
        while el < noof_packets or True in is_homie_busy:
            sleep(.1)
            if el < noof_packets:
                frame = bytes(outpackets_lst[el])
                for homieno in range(0, noof_homies):
                    if not is_homie_busy[homieno]:
                        is_homie_busy[homieno] = True
                        homie = our_homies[homieno]
                        frameno = int.from_bytes(frame[0:4], 'little')
                        print("Sending frame #%d to %s via %s" % (frameno, homie.nickname, homie.irc_server))
                        packetstatuses[frameno] = [homie.irc_server, datetime.datetime.now(), None]
                        self.bots[homie.irc_server].crypto_put(homie.nickname, frame)
                        el += 1
            for homieno in range(0, noof_homies):
                if is_homie_busy[homieno]:
                    try:
                        (src, rxd) = self.bots[self.homies_lst[homieno].irc_server].get_nowait()
                    except Empty:
                        pass
                    else:
                        receipt_packetno = int(rxd.split(' ')[0])
                        receipt_irc_server = rxd.split(' ')[1]
                        receipt_cksum = rxd.split(' ')[2]
                        if receipt_irc_server != our_homies[homieno].irc_server:
                            raise ValueError("I think I've mistakenly handled a packet that was from a different destination.")
#                        if our_pktno < len(outpackets_lst):
                        assert(receipt_cksum == base64.b85encode(hashlib.sha1(bytes(outpackets_lst[receipt_packetno - packetnum_offset])).digest()).decode())
                        if packetnum_offset > 0:
                            print("packetnum_offset =", packetnum_offset)
                        assert(packetstatuses[receipt_packetno][1] is not None)
                        assert(packetstatuses[receipt_packetno][2] is None)
                        homie = our_homies[homieno]
                        if src != homie.nickname:
                            raise ValueError("WARNING -- src was not %s. Should I reinsert it in rx queue?" % homie.nickname)
                        #     self.bots[homie.irc_server].reinsert((src, rxd))
                        # else:
                        packetstatuses[receipt_packetno][2] = datetime.datetime.now()
                        print("CONFIRM packet #%d to %s via %s rx'd okay" % (receipt_packetno, homie.nickname, homie.irc_server))
                        is_homie_busy[homieno] = False
                        print("%s is now free." % homie.irc_server)

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
#                    if pubkey is None:
                    pubkey = self.bots[irc_server].homies[user].pubkey  # else assert(pubkey == self.bots[irc_server].homies[user].pubkey)
                except Empty:
                    sleep(A_TICK)  # pass
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
                        our_cksum = base64.b85encode(hashlib.sha1(bytes(frame)).digest()).decode()
                        print("Confirming receipt of packet #%d from %s; cksum %s" % (packetno, irc_server, our_cksum))
                        self.bots[irc_server].put(user, "%d %s %s" % (packetno, irc_server, our_cksum))
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
            outpackets_lst.append(frame)  # print("%s %s: sent pkt#%d of %d bytes" % (s_now(), self.desired_nickname, self.outgoing_packetnumbers_dct[squeezed_pk], len(frame)))
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

    def get_homies_list(self, demand_ipaddr=False):
        retval = []
        for bot in [self.bots[k] for k in self.bots]:
            for homie in [bot.homies[h] for h in bot.homies]:
                if demand_ipaddr is False or homie.ipaddr is not None:
                    retval.append(homie)
        return retval

    @property
    def homies_lst(self):
        return self.get_homies_list()

    @property
    def connected_homies_lst(self):
        return self.get_homies_list(demand_ipaddr=True)

    @property
    def ipaddrs(self):
        return [r.ipaddr for r in self.get_homies_list(demand_ipaddr=True) if r.ipaddr is not None]

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
        my_threads = []
        print("Starting handshaking")
        for k in self.bots:
            bot = self.bots[k]
            if k == self.bots[k].nickname:
                print("%s %s: %s: no need to trigger handshaking w/ %s" % (s_now(), bot.irc_server, bot.nickname, k))
            else:
                self.bots[k].trigger_handshaking()
        #         my_threads += [Thread(target=self.bots[k].trigger_handshaking, daemon=True)]  # args=[k]
        # for thr in my_threads:
        #     thr.start()
        # print("Joining handshaking")
        # for thr in my_threads:
        #     thr.join(timeout=ENDTHREAD_TIMEOUT)
        print("Exiting handshaking")

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
    the_room = '#room' + generate_random_alphanumeric_string(5)
    list_of_all_irc_servers = ALL_REALWORLD_IRC_NETWORK_NAMES[:1]  # ALL_SANDBOX_IRC_NETWORK_NAMES  # ALL_REALWORLD_IRC_NETWORK_NAMES
    noof_servers = len(list_of_all_irc_servers)
    alice_rsa_key = RSA.generate(2048)
    bob_rsa_key = RSA.generate(2048)
    alice_pk = alice_rsa_key.public_key()
    bob_pk = bob_rsa_key.public_key()
    alice_nick = 'alice%d' % randint(111, 999)
    bob_nick = 'bob%d' % randint(111, 999)
    alice_harem = HaremOfPrateBots([the_room], alice_nick, list_of_all_irc_servers, alice_rsa_key, autohandshake=False)
    bob_harem = HaremOfPrateBots([the_room], bob_nick, list_of_all_irc_servers, bob_rsa_key, autohandshake=False)
    while not (alice_harem.ready and bob_harem.ready):
        sleep(1)

    alice_harem.trigger_handshaking()
    bob_harem.trigger_handshaking()
    the_noof_homies = -1
    while the_noof_homies != len(alice_harem.connected_homies_lst):
        the_noof_homies = len(alice_harem.connected_homies_lst)
        sleep(STARTUP_TIMEOUT)

    fname = "/Users/mchobbit/Downloads/top_panel.stl"  # pi_holder.stl"
    filelen = os.path.getsize(fname)
    with open(fname, "rb") as f:
        the_data = f.read()

    t1 = datetime.datetime.now()

    import cProfile
    from pstats import Stats
    pr = cProfile.Profile()
    pr.enable()

    alice_harem.put(bob_pk, the_data)
    the_src, the_rxd = bob_harem.get()

    pr.disable()
    stats = Stats(pr)
    stats.sort_stats('cumtime').print_stats(10)  # tottime

    assert(the_src == alice_pk)
    assert(the_rxd == the_data)
    t2 = datetime.datetime.now()
    timedur = (t2 - t1).microseconds
    xfer_rate = filelen / (timedur / 1000000)
    print("%s: it took %1.4f seconds to send %d bytes via %d servers. That is %1.4f bytes per second." % (s_now(), timedur // 1000000, filelen, len(alice_harem.homies_lst), xfer_rate))
    pass
