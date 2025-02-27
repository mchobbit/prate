# -*- coding: utf-8 -*-
"""Harem class: a rookery with corridors.

Created on Jan 30, 2025

@author: mchobbit

This module contains classes for creating a Harem Prate class that controls
a rookery and adds [open/close/read/write] handles, frames, checksums, etc.
Whereas a PrateRookery wraps around a group of PrateBots and uses them to
communicate collectively with other PrateRookery instances, a Harem wraps
around a PrateRookery and *adds* all sorts of good things:-

- opening/closing of streams (AKA corridors)
- checking that each packet arrived
- quiet, nonchalant retransmission of packets that don't arrive (until they do arrive)

See my __main__() function for an example.

Todo:
    * Better docs

.. _Google Python Style Guide:
   http://google.github.io/styleguide/pyguide.html

.. _Napoleon Style Guide:
   https://sphinxcontrib-napoleon.readthedocs.io/en/latest/example_google.html

Example:


"""

from threading import Thread
from Crypto.PublicKey import RSA
from my.classes.exceptions import PublicKeyBadKeyError, RookeryCorridorAlreadyClosedError, PublicKeyUnknownError
from time import sleep
from my.irctools.cryptoish import squeeze_da_keez, sha1, bytes_64bit_cksum
from queue import Empty
from my.globals import A_TICK, SENSIBLE_NOOF_RECONNECTIONS, STARTUP_TIMEOUT, ALL_SANDBOX_IRC_NETWORK_NAMES, ENDTHREAD_TIMEOUT, RSA_KEY_SIZE  # ALL_REALWORLD_IRC_NETWORK_NAMES
from random import randint
from my.stringtools import s_now, generate_random_alphanumeric_string
from my.classes.readwritelock import ReadWriteLock
from my.irctools.jaracorocks.praterookery import PrateRookery
import datetime
import hashlib
import base64
from my.irctools.jaracorocks.harem.corridor import Corridor


class Harem(PrateRookery):  # smart rookery
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
    alice_rsa_key = RSA.generate(RSA_KEY_SIZE)
    bob_rsa_key = RSA.generate(RSA_KEY_SIZE)
    alice_pk = alice_rsa_key.public_key()
    bob_pk = bob_rsa_key.public_key()
    alice_nick = 'alice%d' % randint(111, 999)
    bob_nick = 'bob%d' % randint(111, 999)

    print("Creating harems for Alice and Bob")
    alice_harem = Harem([the_room], alice_nick, my_list_of_all_irc_servers, alice_rsa_key, autohandshake=False)
    bob_harem = Harem([the_room], bob_nick, my_list_of_all_irc_servers, bob_rsa_key, autohandshake=False)
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
