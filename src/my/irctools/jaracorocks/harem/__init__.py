# -*- coding: utf-8 -*-
"""Harem class: a rookery with corridors.

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
from my.classes.exceptions import PublicKeyBadKeyError, RookeryCorridorAlreadyClosedError, PublicKeyUnknownError, RookeryCorridorNoTrueHomiesError
from time import sleep
from my.irctools.cryptoish import squeeze_da_keez, sha1, bytes_64bit_cksum
from queue import Empty, Queue
from my.globals import A_TICK, SENSIBLE_NOOF_RECONNECTIONS, STARTUP_TIMEOUT, ALL_SANDBOX_IRC_NETWORK_NAMES, ENDTHREAD_TIMEOUT, RSA_KEY_SIZE  # ALL_REALWORLD_IRC_NETWORK_NAMES
from random import randint, choice
from my.stringtools import s_now, generate_random_alphanumeric_string
from my.classes.readwritelock import ReadWriteLock
from my.irctools.jaracorocks.praterookery import PrateRookery
import datetime
import hashlib
import base64


class Corridor:
    """The class for handling interaction between two harems.

    123456789 123456789 123456789 123456789 123456789 123456789 123456789 123456789
    Each harem (a collection of IRC bots) acts as one virtual IRC-style server.
    By sending harem.put(pubkey,datablock) to a harem instance, a programmer can
    send a block of data from one Prate user to another. There is an assumption
    that each user is using a different harem.

    The corridor is a higher-level abstraction that facilitates direct(ish)
    communication betwen two Prate users. Each instance of a Corridor has
    its own input and output methods. The interface between each corridor and
    its harem is handled in the background. The programmer doesn't need to
    know any of that.

    Args:
        harem (Harem): Harem to which this corridor belongs.
        pubkey (RSA.RsaKey): The public key of the other user with whom I
            am communicating. This channel is how I talk to that user.
    """

    def __init__(self, harem, pubkey):
        self.myQ = Queue()
        self.harem = harem
        self.pubkey = pubkey  # public key of other end
        self.closed = False

    def __repr__(self):
        class_name = type(self).__name__
        pk_nicks = self.harem.nicks_for_pk(self.pubkey)
        return f"{class_name}: me={self.harem.desired_nickname!r}; them={pk_nicks!r})"

    def empty(self):
        return self.myQ.empty

    def get(self, block=True, timeout=None):
        return self.__getSUB(block, timeout, nowait=False)

    def get_nowait(self):
        return self.__getSUB(nowait=True)

    def __getSUB(self, block=True, timeout=None, nowait=False):
        if self.closed:
            raise RookeryCorridorAlreadyClosedError("You cannot use %s-to-%s corridor: it is closed." % (self.harem.desired_nickname, self.harem.nicks_for_pk(self.pubkey)))
        retval = self.myQ.get_nowait() if nowait else self.myQ.get(block, timeout)
        print("%s %-10s<==%-10s  %s" % (s_now(), self.harem.desired_nickname, self.harem.nicks_for_pk(self.pubkey), retval))
        return retval

    def put(self, datablock):
        if self.closed:
            raise RookeryCorridorAlreadyClosedError("You cannot use %s-to-%s corridor: it is closed." % (self.harem.desired_nickname, self.harem.nicks_for_pk(self.pubkey)))
        if self.closed:
            raise AttributeError()
        self.harem.put(self.pubkey, datablock, yes_really=True)

    def close(self):
        if self.closed:
            raise RookeryCorridorAlreadyClosedError("%s-to-%s corridor was already closed." % (self.harem.desired_nickname, self.harem.nicks_for_pk(self.pubkey)))
        self.harem.corridors.remove(self)
        self.closed = True


class Harem(PrateRookery):
    """Harem class: a Rookery with load balancing and TCP-style packet tracking.

    The Harem class adds streaming to PrateRookery. It uses checksums, packet
    numbering, and packet retransmission options, to ensure that data is sent
    and received for sure.

    Note:
        There is no did-the-message-arrive-or-not checking.

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

    Example:
        $ alice_rsa_key = RSA.generate(1024)
        $ bob_rsa_key = RSA.generate(1024)
        $ alice_harem = Harem(['#prate'], 'alice123', ['cinqcent.local','rpi0irc1.local'], alice_rsa_key, autohandshake=False)
        $ bob_harem = Harem(['#prate'], 'alice123', ['cinqcent.local','rpi0irc1.local'], alice_bob_key, autohandshake=False)
        $ alice_harem.trigger_handshake()
        $ bob_harem.trigger_handshake()
        $ alice_corridor = alice_harem.open(bob_rsa_key.public_key())
        $ bob_corridor = bob_harem.open(alice_rsa_key.public_key())
        $ alice_corridor.put(bob_rsa_key.public_key(), b"MARCO!")
        $ assert(bob_corridor.get() == (bob_rsa_key.public_key(), b"MARCO!")
    """

    def __init__(self, channels, desired_nickname, list_of_all_irc_servers, rsa_key,
                 startup_timeout=STARTUP_TIMEOUT, maximum_reconnections=SENSIBLE_NOOF_RECONNECTIONS,
                 autohandshake=True):
        super().__init__(channels, desired_nickname, list_of_all_irc_servers, rsa_key,
                         startup_timeout, maximum_reconnections, autohandshake)
        self.__corridors = []
        self.__corridors_lock = ReadWriteLock()
        assert(not hasattr(self, '__my_corridorservicing_thread'))
        assert(not hasattr(self, '__my_corridorservicing_loop'))
        self.__my_corridorservicing_thread = Thread(target=self.__my_corridorservicing_loop, daemon=True)
        self.__my_corridorservicing_thread.start()

    def __repr__(self):
        class_name = type(self).__name__
        pk = self.rsa_key.public_key()
        if pk is not None:
            pk = squeeze_da_keez(pk)
            pk = "%s..." % (pk[:16])
        irc_servers_description_str = "1 item" if len(self.list_of_all_irc_servers) == 1 else "%d items" % len(self.list_of_all_irc_servers)
        return f"{class_name}(channels={self.channels!r}, desired_nickname={self.desired_nickname!r}, rsa_key={pk!r}, list_of_all_irc_servers={irc_servers_description_str!r}, corridors={self.corridors!r})"

    def nicks_for_pk(self, pubkey):
        return '/'.join([h.nickname for h in self.true_homies if h.pubkey == pubkey])

    @property
    def corridors(self):
        return self._corridors

    def empty(self, yes_really=False):
        if yes_really:
            return super().empty
        else:
            raise AttributeError("Use a corridor for empty/get/get_nowait/put.")
        raise AttributeError("Use a corridor for empty/get/get_nowait/put.")

    def get(self, block=True, timeout=None, yes_really=False):
        if yes_really:
            return super().get(block, timeout)
        else:
            raise AttributeError("Use a corridor for empty/get/get_nowait/put.")

    def get_nowait(self, yes_really=False):
        if yes_really:
            return super().get_nowait()
        else:
            raise AttributeError("Use a corridor for empty/get/get_nowait/put.")

    def put(self, pubkey, datablock, irc_server=None, yes_really=False):
        if yes_really:
            super().put(pubkey, datablock, irc_server)
        else:
            AttributeError("Use a corridor for empty/get/get_nowait/put.")

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

    def __my_corridorservicing_loop(self):
        """Service incoming messages from the rookery.

        Messages come in three flavors:-
        1. An instruction to open a corridor.
        2. An instruction to close a corridor
        3. A data frame that should be sent to one particular corridor.

        """
        print("%s %-10s   %-10s  Harem's main loop starts" % (s_now(), self.desired_nickname, ''))
        while not self.gotta_quit:
            sleep(A_TICK)
            try:
                source, frame = self.get_nowait(yes_really=True)
                if type(source) is not RSA.RsaKey:
                    raise ValueError("source must be a public key")  # PublicKeyBadKeyError
                else:
                    the_right_corridors = [c for c in self.corridors if c.pubkey == source]
                    noof_right_corridors = len(the_right_corridors)
                    if noof_right_corridors >= 1:
                        if noof_right_corridors > 1:
                            print("WARNING --- there are %d corridors" % noof_right_corridors)
                            print(the_right_corridors)
                        the_right_corridors[0].myQ.put(frame)
                    else:
                        raise RookeryCorridorNoTrueHomiesError("%s %-10s<==%-10s  %s (BUT I'VE NO APPLICABLE CORRIDOR)" % (s_now(), self.desired_nickname, self.nicks_for_pk(source), str(frame)))
            except Empty:
                pass
        print("%s %-10s   %-10s  Harem's main loop ends" % (s_now(), self.desired_nickname, ''))

    def open(self, destination):
        """Generate a file(?)-style handle for reading and writing to/from the other harem."""
        if type(destination) is not RSA.RsaKey:
            raise ValueError("pubkey must be a public key")  # PublicKeyBadKeyError
        if destination not in [h.pubkey for h in self.get_homies_list(True)]:
            raise PublicKeyBadKeyError("Please handshake first. Then I'll be able to find your guy w/ his pubkey.")
        try:
            corridor = [c for c in self.corridors if c.pubkey == destination][0]
        except IndexError:
            corridor = Corridor(harem=self, pubkey=destination)
            print("%s %-10s<==%-10s  Opening a corridor" % (s_now(), self.desired_nickname, self.nicks_for_pk(destination)))
            self._corridors += [corridor]
        print("%s=== %-10s  We now have %s====╗" % (s_now(), self.desired_nickname, '1 corridor ' if len(self._corridors) == 1 else '%d corridors' % len(self._corridors)))
        corridornumber = 1
        for c in self.corridors:
            print("╠          %2d/%-2d               %-10s          ╣" % (corridornumber, len(self.corridors), self.nicks_for_pk(destination)))
            corridornumber += 1
        print("╚==================================================╝")
        return corridor

    def quit(self):
        print("%s %-10s   %-10s  Harem is quitting" % (s_now(), self.desired_nickname, ''))
        if len(self.corridors) > 0:
            corridors_to_be_deleted = self.corridors
            for c in list(set(corridors_to_be_deleted)):  # I'm not sure why we do this.
                c.close()
        super().quit()
        self.__my_corridorservicing_thread.join(timeout=ENDTHREAD_TIMEOUT)
        sleep(1)
        print("%s %-10s   %-10s  Harem has quit" % (s_now(), self.desired_nickname, ''))

