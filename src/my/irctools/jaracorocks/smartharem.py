# -*- coding: utf-8 -*-
"""A smart harem: a rookery with corridors.

Created on Jan 30, 2025

@author: mchobbit

This module contains classes for creating a SmartHarem Prate class that controls
a rookery and adds [open/close/read/write] handles.

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

from threading import Thread
from Crypto.PublicKey import RSA
from my.classes.exceptions import PublicKeyBadKeyError, HaremCorridorAlreadyClosedError, PublicKeyUnknownError
from time import sleep
from my.irctools.cryptoish import squeeze_da_keez, sha1, bytes_64bit_cksum
from queue import Empty
from my.globals import A_TICK, SENSIBLE_NOOF_RECONNECTIONS, STARTUP_TIMEOUT, ALL_SANDBOX_IRC_NETWORK_NAMES, ENDTHREAD_TIMEOUT  # ALL_REALWORLD_IRC_NETWORK_NAMES
from random import randint
from my.stringtools import s_now, generate_random_alphanumeric_string
from my.classes.readwritelock import ReadWriteLock
from my.irctools.jaracorocks.praterookery import PrateRookery
import datetime
import hashlib
import base64


class Corridor:

    def __init__(self, harem, destination, uid=None):
        self.__uid = uid
        while self.__uid is None or self.__uid in [i.uid for i in harem.corridors]:
            self.__uid = sha1("%s%s%s" % (squeeze_da_keez(destination), harem.desired_nickname, generate_random_alphanumeric_string(16)))
        self.__harem = harem
        self.__closed = False
        self.__gotta_quit = False
        self.__destination = destination
        self.__my_main_thread = Thread(target=self.__my_main_loop, daemon=True)
        self.__my_main_thread.start()

    @property
    def source(self):
        return self.harem.rsa_key.public_key()

    @property
    def uid(self):
        return self.__uid

    @property
    def gotta_quit(self):
        return self.__gotta_quit

    def __my_main_loop(self):
        self.harem.put(self.destination, ("OPENCORRIDOR %s" % self.uid).encode())
        print("I am handling a corridor from %s to %s" % (self.harem.desired_nickname, "%s..." % squeeze_da_keez(self.destination)[:16]))
        while not self.gotta_quit:
            sleep(A_TICK)
        print("I have been asked to close my corridor from %s to %s" % (self.harem.desired_nickname, "%s..." % squeeze_da_keez(self.destination)[:16]))

    def close(self):
        if self.__closed:
            raise HaremCorridorAlreadyClosedError("Corridor %s is already closed" % self.uid)
        else:
            self.__closed = True
            self.harem.put(self.destination, ("CLOSECORRIDOR %s" % self.uid).encode())
            self.quit()
        sleep(1)

    def quit(self, timeout=ENDTHREAD_TIMEOUT):
        print("%s-%s corridor closing." % (self.harem.desired_nickname, "%s..." % squeeze_da_keez(self.destination)[:16]))
        try:
            the_corridor_to_be_deleted = [e for e in self.harem.corridors if e.uid == self.uid][0]
            self.harem.corridors.remove(the_corridor_to_be_deleted)
        except (KeyError, IndexError):
            print("Failed to delete corridor %s from %s's list of corridors" % (self.uid, self.harem.desired_nickname))
        self.__gotta_quit = True
        self.__my_main_thread.join(timeout=timeout)
        print("%s-%s corridor closed." % (self.harem.desired_nickname, "%s..." % squeeze_da_keez(self.destination)[:16]))

    @property
    def harem(self):
        return self.__harem

    @property
    def destination(self):
        return self.__destination

    def write(self, datablock, timeout=-1):
        print("QQQ WRITE DATA QQQ")

    def read(self, timeout=-1):
        print("QQQ READ DATA QQQ")
        datablock = None
        return datablock


class SmartHarem(PrateRookery):  # smart rookery
# Eventually, make it threaded!

    def __init__(self, channels, desired_nickname, list_of_all_irc_servers, rsa_key,
                 startup_timeout=STARTUP_TIMEOUT, maximum_reconnections=SENSIBLE_NOOF_RECONNECTIONS,
                 autohandshake=True):
        super().__init__(channels, desired_nickname, list_of_all_irc_servers, rsa_key,
                         startup_timeout, maximum_reconnections, autohandshake)
        self.__corridors = []
        self.__corridors_lock = ReadWriteLock()
        self.__my_harem_thread = Thread(target=self.__my_harem_loop, daemon=True)
        self.__my_harem_thread.start()

    @property
    def corridors(self):
        return self._corridors

    @property
    def _corridors(self):
        self.__corridors_lock.acquire_read()
        try:
            retval = self.__corridors
            return retval
        finally:
            self.__corridors_lock.release_read()

    @_corridors.setter
    def _corridors(self, value):
        self.__corridors_lock.acquire_write()
        try:
            self.__corridors = value
        finally:
            self.__corridors_lock.release_write()

    def __my_harem_loop(self):
        while not self.gotta_quit:
            sleep(A_TICK)
            try:
                src_pk, rxd = self.get_nowait()
            except Empty:
                pass
            else:
                try:
                    decoded_rxd = rxd.decode()
                except Exception as e:
                    print("Can't turn rxd into string: ", e)
                else:
                    if decoded_rxd.startswith("OPENCORRIDOR"):
                        uid = decoded_rxd.split(' ')[1]
                        print("Opening a corridor")
                        if uid in [c.uid for c in self.corridors]:
                            print("No need to create a corridor opening here: we've already got a corridor.")
                        else:
                            print("He opened a corridor. So, now, I'll open the other end here.")
                            self._corridors += [Corridor(uid=uid, harem=self, destination=src_pk)]
                    elif decoded_rxd.startswith("CLOSECORRIDOR"):
                        uid = decoded_rxd.split(' ')[1]
                        print("Closing a corridor")
                        if uid in [c.uid for c in self.corridors]:
                            print("Closing my end of the corridor")
                            m = [c for c in self.corridors if c.uid == uid][0]
                            self._corridors.remove(m)
                        else:
                            print("No need to close my end of corridor")
                    else:
                        print("What does this mean?", decoded_rxd)
                        self.put(src_pk, rxd)

    def open(self, destination):
        if type(destination) is not RSA.RsaKey:
            raise ValueError("pubkey must be a public key")  # PublicKeyBadKeyError
        if destination not in [h.pubkey for h in self.get_homies_list(True)]:
            raise PublicKeyBadKeyError("Please handshake first. Then I'll be able to find your guy w/ his pubkey.")
        while True:
            corridor = Corridor(harem=self, destination=destination)
            self.__corridors += [corridor]
            return corridor

    def FKDUP_put(self, pubkey, datablock):
        if self.paused:
            raise ValueError("Set paused=False and try again.")
        assert(type(pubkey) is RSA.RsaKey)
        assert(type(datablock) is bytes)
        outpackets_lst = self.generate_packets_list_for_transmission(pubkey, datablock)
        packetnum_offset = self.outgoing_packetnumbers_dct[squeeze_da_keez(pubkey)] - len(outpackets_lst)
        print("%s %s: okay. Transmitting the outpackets." % (s_now(), self.desired_nickname))
        our_homies = [h for h in self.get_homies_list(True) if h.pubkey == pubkey]
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
                        (src, rxd) = self.bots[our_homies[homieno].irc_server].get_nowait()
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

    def FKDUP_process_incoming_buffer(self):
        sleep(A_TICK)
        final_packetnumber = -1
        pubkey = None
        while not self.paused and not self.gotta_quit and \
        (final_packetnumber < 0 or [] != [i for i in range(self.our_getq_alreadyspatout, final_packetnumber + 1) if self.our_getq_cache[i % 65536] is None]):
            # FIXME: Prone to lockups and gridlock because it'll wait indefinitely for a missing packet.
            if self.gotta_quit or self.paused:
                return
            else:
                try:
                    user, irc_server, frame = self.privmsgs_from_rookery_bots.get_nowait()
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

    def quit(self):
        for corridor in self.corridors:
            corridor.quit()
        super().quit()
        sleep(1)


if __name__ == "__main__":
    print("Generating RSA keys for Alice and Bob")
    the_room = '#room' + generate_random_alphanumeric_string(5)
    my_list_of_all_irc_servers = ALL_SANDBOX_IRC_NETWORK_NAMES  # ALL_REALWORLD_IRC_NETWORK_NAMES
    noof_servers = len(my_list_of_all_irc_servers)
    alice_rsa_key = RSA.generate(2048)
    bob_rsa_key = RSA.generate(2048)
    alice_pk = alice_rsa_key.public_key()
    bob_pk = bob_rsa_key.public_key()
    alice_nick = 'alice%d' % randint(111, 999)
    bob_nick = 'bob%d' % randint(111, 999)

    print("Creating harems for Alice and Bob")
    alice_harem = SmartHarem([the_room], alice_nick, my_list_of_all_irc_servers, alice_rsa_key, autohandshake=False)
    bob_harem = SmartHarem([the_room], bob_nick, my_list_of_all_irc_servers, bob_rsa_key, autohandshake=False)
    while not (alice_harem.ready and bob_harem.ready):
        sleep(1)

    print("Waiting for harems to shake hands")
    alice_harem.trigger_handshaking()
    bob_harem.trigger_handshaking()
    the_noof_homies = -1
    while the_noof_homies != len(alice_harem.get_homies_list(True)):
        the_noof_homies = len(alice_harem.get_homies_list(True))
        sleep(STARTUP_TIMEOUT // 2 + 1)

    print("Opening a corridor between Alice and Bob")
    alice_corridor = alice_harem.open(bob_pk)
    bob_corridor = bob_harem.open(alice_pk)

    print("Write data from Alice to Bob and from Bob to Alice")
    alice_corridor.write(b"MARCO?")
    assert(bob_corridor.read() == b"MARCO?")
    bob_corridor.write(b"POLO!")
    assert(alice_corridor.read() == b"POLO!")

    print("Closing corridors")
    alice_corridor.close()
    bob_corridor.close()

    # fname = "/Users/mchobbit/Downloads/top_panel.stl"  # pi_holder.stl"
    # filelen = os.path.getsize(fname)
    # with open(fname, "rb") as f:
    #     the_data = f.read()
    #
    # t1 = datetime.datetime.now()
    #
    # import cProfile
    # from pstats import Stats
    # pr = cProfile.Profile()
    # pr.enable()
    #
    # alice_harem.put(bob_pk, the_data)
    # the_src, the_rxd = bob_harem.get()
    #
    # pr.disable()
    # stats = Stats(pr)
    # stats.sort_stats('cumtime').print_stats(10)  # tottime
    #
    # assert(the_src == alice_pk)
    # assert(the_rxd == the_data)
    # t2 = datetime.datetime.now()
    # timedur = (t2 - t1).microseconds
    # xfer_rate = filelen / (timedur / 1000000)
    # print("%s: it took %1.4f seconds to send %d bytes via %d servers. That is %1.4f bytes per second." % (s_now(), timedur // 1000000, filelen, len(alice_harem.get_homies_list(True)), xfer_rate))
    # pass
