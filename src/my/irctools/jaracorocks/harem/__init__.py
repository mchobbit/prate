# -*- coding: utf-8 -*-
"""Harem class: a rookery with simpipes.

Created on Jan 30, 2025

@author: mchobbit

This module contains classes for creating a Harem Prate class that controls
a rookery and adds [open/close/read/write] handles, frames, checksums, etc.
Whereas a PrateRookery wraps around a group of PrateBots and uses them to
communicate collectively with other PrateRookery instances, a Harem wraps
around a PrateRookery.

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
from my.classes.exceptions import PublicKeyBadKeyError, RookerySimpipeAlreadyClosedError, PublicKeyUnknownError, RookerySimpipeNoTrueHomiesError
from time import sleep
from my.irctools.cryptoish import squeeze_da_keez, sha1, bytes_64bit_cksum
from queue import Empty, Queue
from my.globals import A_TICK, SENSIBLE_NOOF_RECONNECTIONS, STARTUP_TIMEOUT, ALL_SANDBOX_IRC_NETWORK_NAMES, ENDTHREAD_TIMEOUT, RSA_KEY_SIZE  # ALL_REALWORLD_IRC_NETWORK_NAMES
from random import randint, choice, shuffle
from my.stringtools import s_now, generate_random_alphanumeric_string
from my.classes.readwritelock import ReadWriteLock
from my.irctools.jaracorocks.praterookery import PrateRookery
import datetime
import hashlib
import base64
from my.irctools.jaracorocks.harem.simpipe import Simpipe


def wait_for_harem_to_stabilize(harem):
    the_noof_homies = -1
    while the_noof_homies != len(harem.get_homies_list(True)):
        the_noof_homies = len(harem.get_homies_list(True))
        sleep(STARTUP_TIMEOUT // 2 + 1)


class Harem(PrateRookery):
    """Harem class: a Rookery with load balancing and TCP-style packet tracking.

    The Harem class adds streaming to PrateRookery. It uses checksums, packet
    numbering, and packet retransmission options, to ensure that data is sent
    and received. ... At least, it WILL do that. It doesn't do it yet.

    It uses the Simpipe class for the fancy stuff.

    Args:

        channels (list of str): The channels to join, e.g. ['#test','#test2']
        desired_nickname (str): The ideal nickname. A randomly generated one
            will be used if the desired nickname is unavailable. This is on a
            case-by-case basis. Each IRC server is handled separately in this
            regard.
        list_of_all_irc_servers (list of str): The IRC servers to be used.
        rsa_key (RSA.RsaKey): My private+public key pair.
        startup_timeout (optional, int): How long should we wait to connect?
        maximum_reconnections (optional, int): Maximum number of permitted
            reconnection attempts.
        autohandshake (optional, bool): If True, find and shake hands with other Prate
            users now. If False, don't.
        return_immediately (optional, bool): If True, don't wait for harem to be
            ready; return immediately instead. If False, wait for .ready to turn
            True, and *THEN* return. Timeout applies though.

    Example:
        $ alice_rsa_key = RSA.generate(1024)
        $ bob_rsa_key = RSA.generate(1024)
        $ alice_harem = Harem(['#prate'], 'alice123', ['cinqcent.local','rpi0irc1.local'], alice_rsa_key, autohandshake=False)
        $ bob_harem = Harem(['#prate'], 'alice123', ['cinqcent.local','rpi0irc1.local'], alice_bob_key, autohandshake=False)
        $ alice_harem.trigger_handshake()
        $ bob_harem.trigger_handshake()
        $ alice_simpipe = alice_harem.open(bob_rsa_key.public_key())
        $ bob_simpipe = bob_harem.open(alice_rsa_key.public_key())
        $ alice_simpipe.put(bob_rsa_key.public_key(), b"MARCO!")
        $ assert(bob_simpipe.get() == (bob_rsa_key.public_key(), b"MARCO!")
    """

    def __init__(self, channels, desired_nickname, list_of_all_irc_servers, rsa_key,
                 startup_timeout=STARTUP_TIMEOUT, maximum_reconnections=SENSIBLE_NOOF_RECONNECTIONS,
                 autohandshake=True):
        super().__init__(channels, desired_nickname, list_of_all_irc_servers, rsa_key,
                         startup_timeout, maximum_reconnections, autohandshake)
        self.__simpipes = []
        self.__simpipes_lock = ReadWriteLock()
        assert(not hasattr(self, '__my_simpipeservicing_thread'))
        assert(not hasattr(self, '__my_simpipeservicing_loop'))
        self.__my_simpipeservicing_thread = Thread(target=self.__my_simpipeservicing_loop, daemon=True)
        self.__my_simpipeservicing_thread.start()

    def __repr__(self):
        class_name = type(self).__name__
        pk = self.my_pubkey
        if pk is not None:
            pk = squeeze_da_keez(pk)
            pk = "%s..." % (pk[:16])
        irc_servers_description_str = "1 item" if len(self.list_of_all_irc_servers) == 1 else "%d items" % len(self.list_of_all_irc_servers)
        return f"{class_name}(channels={self.channels!r}, desired_nickname={self.desired_nickname!r}, rsa_key={pk!r}, list_of_all_irc_servers={irc_servers_description_str!r}, simpipes={self.simpipes!r})"

    def obtain_simpipe(self, pubkey, uid):
        """Generate a Simpipe instance... or at least spit out an existing instance."""
        matching_simpipes = [r for r in self.simpipes if r.pubkey == pubkey]
        if matching_simpipes == []:
            print("%s [#%-5d] src %-10s dst %-10s  %s is opening a new simpipe for talking to %s" % (s_now(), uid, self.desired_nickname, self.nicks_for_pk(pubkey), self.desired_nickname, self.nicks_for_pk(pubkey)))
            retval = Simpipe(self, pubkey, uid)
            retval.description = "This is the corridor for %s=>%s" % (self.desired_nickname, self.nicks_for_pk(pubkey))  # squeeze_da_keez(pubkey)
            self.simpipes.append(retval)
        else:
            print("%s [#%-5d] src %-10s dst %-10s  %s uses an existing simpipe for talking to %s" % (s_now(), uid, self.desired_nickname, self.nicks_for_pk(pubkey), self.desired_nickname, self.nicks_for_pk(pubkey)))
            retval = matching_simpipes[0]
            if len(matching_simpipes) > 1:
                print("WARNING --- >1 MATCHING SIMPIPES")
                print(matching_simpipes)
        return retval

    def nicks_for_pk(self, pubkey):
        retval = '/'.join(list(set([h.nickname for h in self.true_homies if h.pubkey == pubkey])))
        return retval

    def empty(self, yes_really=False):
        if yes_really:
            return super().empty()
        else:
            raise AttributeError("Use a simpipe for empty/get/get_nowait/put.")
        raise AttributeError("Use a simpipe for empty/get/get_nowait/put.")

    def get(self, block=True, timeout=None, yes_really=False):
        if yes_really:
            return super().get(block, timeout)
        else:
            raise AttributeError("Use a simpipe for empty/get/get_nowait/put.")

    def get_nowait(self, yes_really=False):
        if yes_really:
            return super().get_nowait()
        else:
            raise AttributeError("Use a simpipe for empty/get/get_nowait/put.")

    def put(self, pubkey, datablock, irc_server=None, yes_really=False):
        if yes_really:
            super().put(pubkey, datablock, irc_server)
        else:
            raise AttributeError("Use a simpipe for empty/get/get_nowait/put.")

    @property
    def simpipes(self):
        self.__simpipes_lock.acquire_read()
        try:
            retval = self.__simpipes
            return retval
        finally:
            self.__simpipes_lock.release_read()

    @simpipes.setter
    def simpipes(self, value):
        self.__simpipes_lock.acquire_write()
        try:
            self.__simpipes = value
        finally:
            self.__simpipes_lock.release_write()

    def __my_simpipeservicing_loop(self):
        """Service incoming messages from the rookery.

        Messages come in three flavors:-
        1. An instruction to open a simpipe.
        2. An instruction to close a simpipe
        3. A data frame that should be sent to one particular simpipe.

        """
        print("%s %-10s   %-10s  Harem's main loop starts" % (s_now(), self.desired_nickname, ''))
        while not self.gotta_quit:
            sleep(A_TICK)
            try:
                source, frame = self.get_nowait(yes_really=True)
            except Empty:
                pass
            else:
                if type(source) is not RSA.RsaKey:
                    raise ValueError("source must be a public key")  # PublicKeyBadKeyError
                else:
                    this_uid = int.from_bytes(frame[:4], 'little')
                    the_right_simpipes = [c for c in self.simpipes if c.uid == this_uid]  # c.pubkey == source]
                    if the_right_simpipes == []:
                        try:
                            the_sender_told_us_to_use_this_uid_for_simpipe = int.from_bytes(frame[:4], 'little')
                            the_right_simpipe = self.open(source, uid=the_sender_told_us_to_use_this_uid_for_simpipe)
                            if len(self.simpipes) > 1:
                                print("WARNING -- >1 simpipes now")
                                print(self.simpipes)
                            print("%s [#%-5d] src %-10s dst %-10s  The former has sent data packets to the latter, me. I'll accept his simpipe with his UID." % (s_now(), the_right_simpipe.uid, self.nicks_for_pk(source), self.desired_nickname))
                        except PublicKeyBadKeyError:
                            print("%s [#%-5d] src %-10s dst %-10s  This simpipe appears not to exist. So, I'll ignore this frame." % (s_now(), this_uid, self.nicks_for_pk(source), self.desired_nickname))
                            return
                    else:
                        the_right_simpipe = the_right_simpipes[0]
                        if len(the_right_simpipes) > 1:
                            print("WARNING --- there are %d simpipes" % len(the_right_simpipes))
                    print("%s [#%-5d] src %-10s dst %-10s  Routing a frame to this simpipe" % (s_now(), this_uid, self.nicks_for_pk(source), self.desired_nickname), frame)
                    the_right_simpipe.q4me_via_harem.put(frame)
        print("%s %-10s   %-10s  Harem's main loop ends" % (s_now(), self.desired_nickname, ''))

    def open(self, destination, uid=None):
        """Generate a file(?)-style handle for reading and writing to/from the other harem."""
        if uid is None:
            uid = randint(11111, 99999)
        if type(destination) is not RSA.RsaKey:
            raise ValueError("pubkey must be a public key")  # PublicKeyBadKeyError
        if destination not in [h.pubkey for h in self.get_homies_list(True)]:
            raise PublicKeyBadKeyError("Please handshake first. Then I'll be able to find your guy w/ his pubkey.")
        simpipe = self.obtain_simpipe(pubkey=destination, uid=uid)  # generate if necessary
        self.display_corridors()
        return simpipe

    def display_corridors(self):
        print("%s╔=== %-10s  We now have %s====╗" % (s_now(), self.desired_nickname, '1 simpipe ' if len(self.simpipes) == 1 else '%d simpipes' % len(self.simpipes)))
        simpipenumber = 1
        for c in self.simpipes:
            print("        ╠[#%-5d] %2d of %-2d       dst %-10s    ╣ %s" % (c.uid, simpipenumber, len(self.simpipes), self.nicks_for_pk(c.pubkey), c.description))
            simpipenumber += 1
        print("        ╚==========================================╝")

    @property
    def homies_pubkeys(self):
        retval = []
        for homie in self.true_homies:
            if homie.pubkey not in retval:
                retval += [homie.pubkey]
        return retval

    def is_handshook_with(self, pubkey):
        """True if we've exchanged keys with this user. Else, False."""
        return True if pubkey in self.homies_pubkeys else False

    def quit(self):
        print("%s %-10s   %-10s  Harem is telling its simpipes to quit" % (s_now(), self.desired_nickname, ''))
        while len(self.simpipes) > 0:
            self.simpipes[0].close()
        print("%s %-10s   %-10s  Harem itself is quitting" % (s_now(), self.desired_nickname, ''))
        self.gotta_quit = True
        self.__my_simpipeservicing_thread.join(timeout=ENDTHREAD_TIMEOUT)
        super().quit()
        sleep(1)
        print("%s %-10s   %-10s  Harem has quit!" % (s_now(), self.desired_nickname, ''))

