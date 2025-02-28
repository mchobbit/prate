# -*- coding: utf-8 -*-
"""Corridor class.

This module contains the Corridor class.

Todo:
    * Better docs

.. _Google Python Style Guide:
   http://google.github.io/styleguide/pyguide.html

.. _Napoleon Style Guide:
   https://sphinxcontrib-napoleon.readthedocs.io/en/latest/example_google.html

"""

from threading import Thread
from Crypto.PublicKey import RSA
from my.classes.exceptions import PublicKeyBadKeyError, RookeryCorridorAlreadyClosedError, PublicKeyUnknownError, RookeryCorridorNoTrueHomiesError
from time import sleep
from my.irctools.cryptoish import squeeze_da_keez, sha1, bytes_64bit_cksum
from queue import Empty, Queue
from my.globals import A_TICK, SENSIBLE_NOOF_RECONNECTIONS, STARTUP_TIMEOUT, ALL_SANDBOX_IRC_NETWORK_NAMES, ENDTHREAD_TIMEOUT  # ALL_REALWORLD_IRC_NETWORK_NAMES
from random import randint
from my.stringtools import s_now, generate_random_alphanumeric_string
from my.classes.readwritelock import ReadWriteLock
from my.irctools.jaracorocks.praterookery import PrateRookery
import datetime
import hashlib
import base64

ENCRYPTED_MSG_BLOCK_SIZE_INSIDE_OVERALL_FRAME = 288


class Corridor:
    """Handle for reading from and writing to another SmartHarem via IRC servers.

    The Corridor class is issued by a Harem as a handle for reading and
    writing another Harem. It mimics the

    Note:
        There is no did-the-message-arrive-or-not checking.

    Args:
        harem (PrateHarem): The harem that issued me.
        destination (RSAKey.public_key): The public key that the
            destination harem uses.
        uid (str, optional): The unique ID associated with this
            corridor.

    """

    def __init__(self, harem, destination, uid=None):
        if type(destination) is not RSA.RsaKey:
            raise ValueError("destination must be a public key")  # PublicKeyBadKeyError
        if destination not in [h.pubkey for h in harem.true_homies]:
            raise PublicKeyBadKeyError("Please handshake first. Then I'll be able to find your guy w/ his pubkey.")
        self.__uid = uid
        while self.__uid is None or self.__uid in [i.uid for i in harem.corridors]:
            self.__uid = sha1("%s%s%s" % (squeeze_da_keez(destination), harem.desired_nickname, generate_random_alphanumeric_string(32)))
            assert(len(self.__uid) == 25)
        self.__harem = harem
        self.__frameno = 0
        self.__frameno_lock = ReadWriteLock()
        self.__closed = False
        self.__gotta_quit = False
        self.__destination = destination
        self.__our_getq_alreadyspatout = -1
        self.__our_getq_alreadyspatout_lock = ReadWriteLock()
        self.our_getq_cache = [None] * 65536

        # self.__rxQ = Queue()
        # self.__rxQ_lock = ReadWriteLock()
        # self.__txQ = Queue()
        # self.__txQ_lock = ReadWriteLock()
        self.__mythread = Thread(target=self.__mymainloop, daemon=True)
        self.__mythread.start()

    @property
    def frameno(self):
        """Have I been instructed to start quitting?"""
        self.__frameno_lock.acquire_read()
        try:
            retval = self.__frameno
            return retval
        finally:
            self.__frameno_lock.release_read()

    @frameno.setter
    def frameno(self, value):
        self.__frameno_lock.acquire_write()
        try:
            self.__frameno = value
        finally:
            self.__frameno_lock.release_write()

    @property
    def our_getq_alreadyspatout(self):
        """Have I been instructed to start quitting?"""
        self.__our_getq_alreadyspatout_lock.acquire_read()
        try:
            retval = self.__our_getq_alreadyspatout
            return retval
        finally:
            self.__our_getq_alreadyspatout_lock.release_read()

    @our_getq_alreadyspatout.setter
    def our_getq_alreadyspatout(self, value):
        self.__our_getq_alreadyspatout_lock.acquire_write()
        try:
            self.__our_getq_alreadyspatout = value
        finally:
            self.__our_getq_alreadyspatout_lock.release_write()
    # @property
    # def rxQ(self):
    #     """The queue of messages received by me from the other end."""
    #     self.__rxQ_lock.acquire_read()
    #     try:
    #         retval = self.__rxQ
    #         return retval
    #     finally:
    #         self.__rxQ_lock.release_read()
    #
    # @rxQ.setter
    # def rxQ(self, value):
    #     self.__rxQ_lock.acquire_write()
    #     try:
    #         self.__rxQ = value
    #     finally:
    #         self.__rxQ_lock.release_write()
    #
    # @property
    # def txQ(self):
    #     """The queue of messages to be sent to the other end."""
    #     self.__txQ_lock.acquire_read()
    #     try:
    #         retval = self.__txQ
    #         return retval
    #     finally:
    #         self.__txQ_lock.release_read()
    #
    # @txQ.setter
    # def txQ(self, value):
    #     self.__txQ_lock.acquire_write()
    #     try:
    #         self.__txQ = value
    #     finally:
    #         self.__txQ_lock.release_write()

    @property
    def mythread(self):
        return self.__mythread

    @property
    def source(self):
        """What is my public key? This is the source of this message."""
        return self.harem.rsa_key.public_key()

    @property
    def uid(self):
        return self.__uid

    @property
    def gotta_quit(self):
        return self.__gotta_quit

    def __mymainloop(self):
        self.harem.put(self.destination, ("OPENCORRIDOR %s" % self.uid).encode())
        print("%s %-26s: %-10s: Mainloop starting 'tween me and %s" % (s_now(), self.uid, self.harem.desired_nickname, squeeze_da_keez(self.destination)[:16]))
        while not self.gotta_quit:
            sleep(A_TICK)
        print("%s %-26s: %-10s: Mainloop stopping 'tween me and %s" % (s_now(), self.uid, self.harem.desired_nickname, squeeze_da_keez(self.destination)[:16]))

    def close(self):
        if self.__closed:
            raise RookeryCorridorAlreadyClosedError("Corridor %s is already closed" % self.uid)
        else:
            self.__closed = True
            self.quit()
        sleep(1)

    def quit(self, timeout=ENDTHREAD_TIMEOUT):
        print("%s %-26s: %-10s: Corridor QUITTING 'tween me and %s" % (s_now(), self.uid, self.harem.desired_nickname, squeeze_da_keez(self.destination)[:16]))
        self.__gotta_quit = True
        self.harem.put(self.destination, ("CLOSECORRIDOR %s" % self.uid).encode())
        self.harem.corridors.remove(self)
        self.mythread.join(timeout=timeout)
        print("%s %-26s: %-10s: Corridor HAS QUIT 'tween me and %s" % (s_now(), self.uid, self.harem.desired_nickname, squeeze_da_keez(self.destination)[:16]))

    @property
    def harem(self):
        """The harem that issued me."""
        return self.__harem

    @property
    def destination(self):
        """The intended destination to which I'll connect."""
        return self.__destination

    def _the_frames_to_be_written(self, datablock):
        pos = 0
        squeezed_pk = squeeze_da_keez(self.destination)
        bytes_remaining = len(datablock)
        the_frames = []
        while True:
            bytes_for_this_frame = min(ENCRYPTED_MSG_BLOCK_SIZE_INSIDE_OVERALL_FRAME, bytes_remaining)
            our_block = datablock[pos:pos + bytes_for_this_frame]
            frame = bytearray()
            frame += self.frameno.to_bytes(4, 'little')  # packet#
            frame += len(our_block).to_bytes(2, 'little')  # length
            frame += our_block  # data block
            frame += bytes_64bit_cksum(bytes(frame[0:len(frame)]))  # checksum
            the_frames += [bytes(frame)]  # print("%s %-26s              Sent pkt#%d of %d bytes" % (s_now(), self.harem.desired_nickname, self.outgoing_packetnumbers_dct[squeezed_pk], len(frame)))
            bytes_remaining -= bytes_for_this_frame
            pos += bytes_for_this_frame
            self.frameno += 1
            if bytes_for_this_frame == 0:
                break
        return the_frames

    def write(self, datablock, timeout=-1):
        """Write data to the destination."""
        assert(type(datablock) is bytes)
        print("%s %-26s: %-10s: Transmitting frames to %s..." % (s_now(), self.uid, self.harem.desired_nickname, squeeze_da_keez(self.destination)[:16]))
        if 0 == len(self.harem.true_homies):
            raise RookeryCorridorNoTrueHomiesError("I cannot send a datablock: NO ONE LOGGED-IN IS OFFERING THIS PUBKEY.")
        our_homies = self.harem.true_homies
        noof_homies = len(our_homies)
        the_frames = self._the_frames_to_be_written(datablock)
        noof_frames = len(the_frames)
        frame_vs_elementno_offset = self.frameno - noof_frames
        if 0 == len(our_homies):
            raise PublicKeyUnknownError("I cannot send a datablock: NO ONE LOGGED-IN IS OFFERING THIS PUBKEY.")
        framestatuses = {}
        is_homie_busy = [False] * noof_homies
        el = 0
        # Send a frame to every homie, in order.
        while el < noof_frames or True in is_homie_busy:
            sleep(.1)
            if el < noof_frames:
                frame = bytes(the_frames[el])
                for homieno in range(0, noof_homies):
                    if not is_homie_busy[homieno]:
                        is_homie_busy[homieno] = True
                        homie = our_homies[homieno]
                        frameno = int.from_bytes(frame[0:4], 'little')
                        print("Sending frame #%d to %s via %s" % (frameno, homie.nickname, homie.irc_server))
                        framestatuses[frameno] = [homie.irc_server, datetime.datetime.now(), None]
                        self.harem.bots[homie.irc_server].crypto_put(homie.nickname, frame)
                        el += 1
            for homieno in range(0, noof_homies):
                if is_homie_busy[homieno]:
                    try:
                        (src, rxd) = self.harem.bots[our_homies[homieno].irc_server].get_nowait()
                    except Empty:
                        pass
                    else:
                        receipt_frameno = int(rxd.split(' ')[0])
                        receipt_irc_server = rxd.split(' ')[1]
                        receipt_cksum = rxd.split(' ')[2]
                        if receipt_irc_server != our_homies[homieno].irc_server:
                            raise ValueError("I think I've mistakenly handled a frame that was from a different destination.")
                        assert(receipt_cksum == base64.b85encode(hashlib.sha1(bytes(the_frames[receipt_frameno - frame_vs_elementno_offset])).digest()).decode())
                        if frame_vs_elementno_offset > 0:
                            print("frame_vs_elementno_offset =", frame_vs_elementno_offset)
                        assert(framestatuses[receipt_frameno][1] is not None)
                        assert(framestatuses[receipt_frameno][2] is None)
                        homie = our_homies[homieno]
                        if src != homie.nickname:
                            raise ValueError("WARNING -- src was not %s. Should I reinsert it in rx queue?" % homie.nickname)
                        #     self.harem.bots[homie.irc_server].reinsert((src, rxd))
                        # else:
                        framestatuses[receipt_frameno][2] = datetime.datetime.now()
                        print("CONFIRM frame #%d to %s via %s rx'd okay" % (receipt_frameno, homie.nickname, homie.irc_server))
                        is_homie_busy[homieno] = False
                        print("%s is now free." % homie.irc_server)

    def read(self, timeout=-1):
        """Read data from the destination."""
        datablock = None
        final_framenumber = -1
        pubkey = None
        while not not self.gotta_quit and \
        (final_framenumber < 0 or [] != [i for i in range(self.our_getq_alreadyspatout, final_framenumber + 1) if self.our_getq_cache[i % 65536] is None]):
            # Prone to lockups and gridlock because it'll wait indefinitely for a missing frame.
            try:
                user, irc_server, frame = self.harem.privmsgs_from_rookery_bots.get_nowait()
#                    if pubkey is None:
                pubkey = self.harem.bots[irc_server].homies[user].pubkey  # else assert(pubkey == self.harem.bots[irc_server].homies[user].pubkey)
            except Empty:
                sleep(A_TICK)  # pass
            else:
                frameno = int.from_bytes(frame[0:4], 'little')
                if frameno < 256 * 256 and self.our_getq_alreadyspatout > 256 * 256 * 256 * 64:  #  ugly kludge
                    print("%s %-26s: %-10s: I think we've wrapped around." % (s_now(), self.uid, self.harem.desired_nickname))
                    self.our_getq_alreadyspatout = 0
                if frameno < self.our_getq_alreadyspatout:
                    print("%s %-26s: %-10s: ignoring frame#%d, as it's a duplicate." % (s_now(), self.uid, self.harem.desired_nickname, frameno))
                else:
                    assert(frameno < 256 * 256 * 256 * 127)  # PROGRAM A WRAPAROUND.
                    self.our_getq_cache[frameno % 65536] = frame
                    framelength = int.from_bytes(frame[4:6], 'little')
                    checksum = frame[framelength + 6:framelength + 14]
                    print("%s %-26s: %-10s: rx'd pkt#%d of %3d bytes" % (s_now(), self.uid, self.harem.desired_nickname, frameno, len(frame)))
                    if checksum != bytes_64bit_cksum(frame[0:6 + framelength]):
                        print("%s %s: bad checksum for pkt#%d. You should request a fresh copy." % (s_now(), self.harem.desired_nickname, frameno))
                    if framelength == 0:
                        final_framenumber = frameno
                    our_cksum = base64.b85encode(hashlib.sha1(bytes(frame)).digest()).decode()
                    print("Confirming receipt of frame #%d from %s; cksum %s" % (frameno, irc_server, our_cksum))
                    self.harem.bots[irc_server].put(user, "%d %s %s" % (frameno, irc_server, our_cksum))
        data_to_be_returned = bytearray()
        for i in range(self.our_getq_alreadyspatout, final_framenumber + 1):
            data_to_be_returned += self.our_getq_cache[i][6:-8]
            self.our_getq_cache[i] = None
        self.our_getq_alreadyspatout = final_framenumber + 1
        return data_to_be_returned if not self.gotta_quit else None

