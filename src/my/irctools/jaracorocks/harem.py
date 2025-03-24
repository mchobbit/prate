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
from my.classes.exceptions import PublicKeyBadKeyError, RookeryCorridorTimeoutError, RookeryCorridorMorethanoneError, RookeryCorridorNotFoundError
from time import sleep
from my.irctools.cryptoish import squeeze_da_keez
from queue import Empty
from my.globals import SENSIBLE_NOOF_RECONNECTIONS, STARTUP_TIMEOUT, ENDTHREAD_TIMEOUT, _OPEN_A_CORRIDOR_, \
    _RECIPROCATE_OPENING_, _CLOSE_A_CORRIDOR_, _RECIPROCATE_CLOSING_, HANDSHAKE_TIMEOUT, _THIS_IS_A_DATA_FRAME_, A_TICK  # ALL_REALWORLD_IRC_NETWORK_NAMES
from my.stringtools import s_now
from my.classes.readwritelock import ReadWriteLock
from my.irctools.jaracorocks.praterookery import PrateRookery
import datetime
from my.irctools.jaracorocks.corridor import Corridor


def uid_from_pubkey(pubkey):
    return pubkey.n % (256 * 256 * 255)


def receive_data_from_simpipe(simpipe, timeout=5):
    timenow = datetime.datetime.now()
    received_data = bytearray()
    while (datetime.datetime.now() - timenow).seconds < timeout:
        try:
            rxd_dat = simpipe.get(timeout=1)
            received_data += rxd_dat
        except Empty:
            sleep(A_TICK)
    return bytes(received_data)


class Harem(PrateRookery):
    """Harem class: a Rookery with load balancing (?) and TCP-style packet tracking.

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
        $ alice_corridor = alice_harem.open(bob_rsa_key.public_key())
        $ bob_corridor = bob_harem.open(alice_rsa_key.public_key())
        $ alice_simpipe.put(bob_rsa_key.public_key(), b"MARCO!")
        $ assert(bob_simpipe.get() == (bob_rsa_key.public_key(), b"MARCO!")
    """

    def __init__(self, channels, desired_nickname, list_of_all_irc_servers, rsa_key,
                 startup_timeout=STARTUP_TIMEOUT, maximum_reconnections=SENSIBLE_NOOF_RECONNECTIONS,
                 autohandshake=True):
        super().__init__(channels, desired_nickname, list_of_all_irc_servers, rsa_key,
                         startup_timeout, maximum_reconnections, autohandshake)
        self.__corridors = []
        self.__corridors_lock = ReadWriteLock()
        self.__kludge_counter_to_avoid_race_condition_later = 0.5
        assert(not hasattr(self, '__my_corridorservicing_thread'))
        assert(not hasattr(self, '__my_corridorservicing_loop'))
        self.__my_corridorservicing_thread = Thread(target=self.__my_corridorservicing_loop, daemon=True)
        self.__my_corridorservicing_thread.start()

    def __repr__(self):
        class_name = type(self).__name__
        pk = self.my_pubkey
        if pk is not None:
            pk = squeeze_da_keez(pk)
            pk = "%s..." % (pk[:16])
        irc_servers_description_str = "1 item" if len(self.list_of_all_irc_servers) == 1 else "%d items" % len(self.list_of_all_irc_servers)
        return f"{class_name}(channels={self.channels!r}, desired_nickname={self.desired_nickname!r}, rsa_key={pk!r}, list_of_all_irc_servers={irc_servers_description_str!r}, corridors={self.corridors!r})"

    def nicks_for_pk(self, pubkey):
        retval = '/'.join(list(set([h.nickname for h in self.true_homies if h.pubkey == pubkey])))
        return retval

    def empty(self, bypass_harem=False):
        """If bypass_harem is True, bypass the Harem layer and use the PrateRookery layer to interact with other harems. Otherwise, don't use me."""
        if bypass_harem:
            return super().empty()
        else:
            raise AttributeError("Do not interact directly with empty/get/get_nowait/put for this class. Use open() and close() with/for handles instead.")

    def get(self, block=True, timeout=None, bypass_harem=False):
        if bypass_harem:
            return super().get(block, timeout)
        else:
            raise AttributeError("Do not interact directly with empty/get/get_nowait/put for this class. Use open() and close() with/for handles instead.")

    def get_nowait(self, bypass_harem=False):
        if bypass_harem:
            return super().get_nowait()
        else:
            raise AttributeError("Do not interact directly with empty/get/get_nowait/put for this class. Use open() and close() with/for handles instead.")

    def put(self, pubkey, datablock, irc_server=None, bypass_harem=False):
        if bypass_harem:
            super().put(pubkey, datablock, irc_server)
        else:
            raise AttributeError("Do not interact directly with empty/get/get_nowait/put for this class. Use open() and close() with/for handles instead.")

    @property
    def corridors(self):
        """Each element contains a Corridor instance. Each corridor contains both public keys (mine and his), a UID, and a packet counter."""
        self.__corridors_lock.acquire_read()
        try:
            retval = self.__corridors
            return retval
        finally:
            self.__corridors_lock.release_read()

    @corridors.setter
    def corridors(self, value):
        self.__corridors_lock.acquire_write()
        try:
            self.__corridors = value
        finally:
            self.__corridors_lock.release_write()

    def __my_corridorservicing_loop(self):
        """Service incoming messages from the rookery.

        Messages come in three flavors:-
        1. An instruction to open a corridor.
        2. An instruction to close a corridor.
        3. A data frame that should be sent to one particular corridor.

        """
#        print("%s %-10s   Harem's main loop starts" % (s_now(), self.desired_nickname))
        while not self.gotta_quit:
            try:
                source, frame = self.get_nowait(bypass_harem=True)
            except Empty:
                sleep(A_TICK)
            else:
                if type(source) is not RSA.RsaKey:
                    print("%s %-10s   SOURCE TYPE SHOULD BE RSA.RsaKey, NOT %s: >>>%s<<<" % (s_now(), self.desired_nickname, type(source), str(source)))
                else:
                    try:
                        self.__service_this_one_frame(source, frame)
                    except (RookeryCorridorMorethanoneError, RookeryCorridorNotFoundError) as e:
                        print("%s %-10s   INTERNAL ERROR: >>>%s<<<" % (s_now(), self.desired_nickname, str(e)))
        print("%s %-10s   Harem main loop has finished" % (s_now(), self.desired_nickname))

    def __service_this_one_frame(self, source, frame):
        control_cmd = frame[0:1]
        his_uid = int.from_bytes(frame[1:4], 'little')  # uid is THREE BYTES LONE
        corridor = None
        try:
            possible_corridors = [c for c in self.corridors if his_uid in (c.our_uid, c.his_uid)]  # c.his_uid == his_uid or c.our_uid == his_uid]
            corridor = possible_corridors[0]
            if len(possible_corridors) > 1:
                raise RookeryCorridorMorethanoneError("WHY ARE THERE %d MATCHING CORRIDORS?" % len(possible_corridors))
        except IndexError:
            if control_cmd in (_OPEN_A_CORRIDOR_, _RECIPROCATE_OPENING_):
                corridor = Corridor(our_uid=uid_from_pubkey(self.my_pubkey), his_uid=his_uid, pubkey=source, harem=self)
                self.corridors.append(corridor)
                print("%s [%s]     %-10s<==> %-10s  Creating corridor" % (s_now(), corridor.str_uid, self.nicks_for_pk(source), self.desired_nickname))
        if control_cmd == _OPEN_A_CORRIDOR_:
            bout = bytes(_RECIPROCATE_OPENING_ + corridor.our_uid.to_bytes(3, 'little'))  # Tell him our uid. Then, we both use the highest-value uid.
            self.put(source, bout, bypass_harem=True)
            print("%s [%s]                    %-10s  %s opened this corridor to me" % (s_now(), corridor.str_uid, self.desired_nickname, self.nicks_for_pk(source)))  #  if None in (corridor.our_uid, corridor.his_uid) else '==> #%d' % corridor.uid))
        elif control_cmd == _RECIPROCATE_OPENING_:
            print("%s [%s]                    %-10s  I opened %s's corridor" % (s_now(), corridor.str_uid, self.desired_nickname, self.nicks_for_pk(source)))  #  if None in (corridor.our_uid, corridor.his_uid) else '==> #%d' % corridor.uid))
        elif control_cmd == _CLOSE_A_CORRIDOR_:
            use_this_uid = his_uid if corridor is None else corridor.uid
            corridor.gotta_close = True  # Trigger the closure of main loop, which will also trigger corridor.is_closed=True
            print("%s [#%-9d]     %-10s<==> %-10s  As per %s's request, %s has closed their end" % (s_now(), use_this_uid, self.nicks_for_pk(source), self.desired_nickname, self.nicks_for_pk(source), self.desired_nickname))
            for i in range(0, 30):
                sleep(.1)
                if corridor.is_closed:
                    break
                if i % 5 == 0:
                    print("%s [%s]     %-10s<==> %-10s  Waiting for corridor's main loop to close" % (s_now(), corridor.str_uid, self.nicks_for_pk(source), self.desired_nickname))
            bout = bytes(_RECIPROCATE_CLOSING_ + use_this_uid.to_bytes(3, 'little'))  # Tell him our uid. Then, we both use the highest-value uid.
            self.put(source, bout, bypass_harem=True)
        elif control_cmd == _RECIPROCATE_CLOSING_:
            use_this_uid = his_uid if corridor is None else corridor.uid
            corridor.gotta_close = True  # Trigger the closure of main loop, which will also trigger corridor.is_closed=True
            print("%s [#%-9d]     %-10s<==> %-10s  %s confirms he has closed his end" % (s_now(), use_this_uid, self.nicks_for_pk(source), self.desired_nickname, self.nicks_for_pk(source)))
        # elif control_cmd == _GET_STATUS_OF_CORRIDOR_:
        #     print("%s [%s]     %-10s<==> %-10s  Get status of corridor? What should I do with this?" % (s_now(), corridor.str_uid, self.nicks_for_pk(source), self.desired_nickname))
        #     if corridor is None:
        #         raise RookeryCorridorNotFoundError("I cannot send a date frame to a nonexistent corridor")
        elif control_cmd == _THIS_IS_A_DATA_FRAME_:
#             print("%s [%s]     %-10s<==> %-10s  Routing a frame to this corridor" % (s_now(), corridor.str_uid, self.nicks_for_pk(source), self.desired_nickname))
            corridor.q4me_via_harem.put(frame)
        else:
            print("%s [%s]     %-10s<==> %-10s  WHAT IS THIS? =>" % (s_now(), corridor.str_uid, self.nicks_for_pk(source), self.desired_nickname), frame)

    def open(self, destination, timeout=HANDSHAKE_TIMEOUT):
        """Generate a file(?)-style handle for reading and writing to/from the other harem.
        ONE CORRIDOR PER PAIR OF PEOPLE!!!!

        If minimum_waittime < 2, there's a non-zero chance that opening two corridors in
        quick succession could cause a race condition later on (during the closing of both
        harems) that stops the harems' lists of corridors from being properly depopulated.

        """
#        self.display_corridors()
        if type(destination) is not RSA.RsaKey:
            raise ValueError("pubkey must be a public key")  # PublicKeyBadKeyError
        if destination not in [h.pubkey for h in self.get_homies_list(True)]:
            raise PublicKeyBadKeyError("Please handshake first. Then I'll be able to find your guy w/ his pubkey.")
        our_uid = uid_from_pubkey(self.my_pubkey)
        try:
            corridor = [c for c in self.corridors if c.uid == our_uid][0]
            print("%s [?%-8d?]     %-10s<==> %-10s  USING EXISTING CORRIDOR" % (s_now(), our_uid, self.desired_nickname, self.nicks_for_pk(destination)))
            return corridor
        except IndexError:
            print("%s [?%-8d?]     %-10s<==> %-10s  ESTABLISHING A CORRIDOR" % (s_now(), our_uid, self.desired_nickname, self.nicks_for_pk(destination)))
            bout = bytes(_OPEN_A_CORRIDOR_ + our_uid.to_bytes(3, 'little'))
            self.put(destination, bout, bypass_harem=True)
            sleep(self.__kludge_counter_to_avoid_race_condition_later)  # When closing two harems at once, ... you'll be glad I did this.
            self.__kludge_counter_to_avoid_race_condition_later = max(3, self.__kludge_counter_to_avoid_race_condition_later)
            t = datetime.datetime.now()
            while (datetime.datetime.now() - t).seconds < timeout:
                sleep(1)
                cs = [c for c in self.corridors if c.our_uid == our_uid and c.his_uid is not None]
                if cs != []:
                    if len(cs) > 1:
                        print("WARNING -- MULTIPLE CORRIDORS WITH OUR UID")
                    corridor = cs[0]
                    print("%s [%s]     %-10s<==> %-10s  CORRIDOR ESTABLISHED" % (s_now(), corridor.str_uid, self.desired_nickname, self.nicks_for_pk(destination)))
                    self.display_corridors()
                    return cs[0]
    #        self.display_corridors()
            raise RookeryCorridorTimeoutError("Timed out while opening corridor")

    def display_corridors(self):
        print("%s╔═══ %-10s  We now have %s════╗" % (s_now(), self.desired_nickname, '1 corridor ' if len(self.corridors) == 1 else '%d corridors' % len(self.corridors)))
        simpipenumber = 1
        for c in self.corridors:
            print("        ╠[%s]      %2d of %-2d      %-10s ╣" % (c.str_uid, simpipenumber, len(self.corridors), self.nicks_for_pk(c.pubkey)))
            simpipenumber += 1
        print("        ╚═══════════════════════════════════════════╝")

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

    def quit(self, timeout=ENDTHREAD_TIMEOUT):
        print("%s %-10s   Harem is telling its corridors to close down" % (s_now(), self.desired_nickname))
        remaining_corridors = set([c for c in self.corridors])
        for corridor in remaining_corridors:
            print("%s %-10s   Harem is telling corridor #%d to close down" % (s_now(), self.desired_nickname, corridor.uid))
            try:
                corridor.close(timeout=timeout)
            except RookeryCorridorTimeoutError:
                print("%s %-10s   Harem's attempt to close corridor #%d timed out" % (s_now(), self.desired_nickname, corridor.uid))
        print("%s %-10s   Harem is closing its main loop" % (s_now(), self.desired_nickname))
        self.gotta_quit = True
        self.__my_corridorservicing_thread.join(timeout=999999)  # ENDTHREAD_TIMEOUT)
        super().quit()
        self.display_corridors()
        print("%s %-10s   Harem has closed down" % (s_now(), self.desired_nickname))


def wait_for_harem_to_stabilize(harem):
    the_noof_homies = -1
    while the_noof_homies != len(harem.get_homies_list(True)):
        the_noof_homies = len(harem.get_homies_list(True))
        sleep(STARTUP_TIMEOUT // 2 + 1)

