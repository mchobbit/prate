# -*- coding: utf-8 -*-
"""Harem class: a rookery with simpipes.

Created on Jan 30, 2025

@author: mchobbit

This module contains CORRIDOR class & singleton.

Todo:
    * Better docs

.. _Google Python Style Guide:
   http://google.github.io/styleguide/pyguide.html

.. _Napoleon Style Guide:
   https://sphinxcontrib-napoleon.readthedocs.io/en/latest/example_google.html

Example:


"""

from threading import Thread
from my.classes.exceptions import RookerySimpipeAlreadyClosedError, RookerySimpipeError
from time import sleep
from my.irctools.cryptoish import squeeze_da_keez, bytes_64bit_cksum
from queue import Empty, Queue
from random import randint, shuffle
from my.stringtools import s_now
from my.classes.readwritelock import ReadWriteLock
import datetime
from my.globals import ENDTHREAD_TIMEOUT


def receive_data_from_simpipe(simpipe, timeout=5):
    timenow = datetime.datetime.now()
    received_data = bytearray()
    while (datetime.datetime.now() - timenow).seconds < timeout:
        try:
            rxd_dat = simpipe.get(timeout=1)
            received_data += rxd_dat
        except Empty:
            sleep(.1)
    return bytes(received_data)


class Simpipe:
    """The class for handling interaction between two harems.

    Each harem (a collection of IRC bots) acts as one virtual IRC-style server.
    By sending harem.put(pubkey, datablock) to a harem instance, a programmer can
    send a block of data from one Prate user to another. There is an assumption
    that each user is using a different harem.

    The simpipe is a higher-level abstraction that facilitates direct(ish)
    communication betwen two Prate users. Each instance of a Simpipe has
    its own input and output methods. The interface between each simpipe and
    its harem is handled in the background. The programmer doesn't need to
    know any of that.

    Args:
        harem (Harem): Harem to which this simpipe belongs.
        pubkey (RSA.RsaKey): The public key of the other user with whom I
            am communicating. This channel is how I talk to that user.
    """

    def __init__(self, harem, pubkey, uid):
        self.q4me_via_harem = Queue()  # Used by HAREM.
        self.my_get_queue = Queue()
        self.__harem = harem  # FIXME: make harem AND uid threadsafe
        self.__uid = uid
        if uid < 1 or uid > 256 * 256 * 256 * 127:
            raise ValueError("uid must be between 1 and 256*256*256*127 inclusive")
        self.__streaming = False  # If True, feed incoming data to buffer as it comes in; don't wait for the final packet!
        self.__streaming_lock = ReadWriteLock()
        self.__pubkey = pubkey  # public key of other end
        self.__pubkey_lock = ReadWriteLock()
        self.__is_closed = False
        self.__is_closed_lock = ReadWriteLock()
        self.__frames_dct = {}
        self.__frames_dct_lock = ReadWriteLock()
        self.__frameno = 0
        self.__frameno_lock = ReadWriteLock()
        self.__frame_size = 256  # Maximum is 256.
        self.__frame_size_lock = ReadWriteLock()
        self.__dupes = 1  # How many duplicates (of each frame) should be sent?
        self.__dupes_lock = ReadWriteLock()
        self.__lastframethatispatout = -1
        self.__lastframethatispatout_lock = ReadWriteLock()
        self.__my_framing_thread = Thread(target=self.__my_framing_loop, daemon=True)
        self.__my_framing_thread.start()

    @property
    def harem(self):
        return self.__harem

    @property
    def uid(self):
        return self.__uid

    @property
    def pubkey(self):
        self.__pubkey_lock.acquire_read()
        try:
            retval = self.__pubkey
            return retval
        finally:
            self.__pubkey_lock.release_read()

    @property
    def streaming(self):
        self.__streaming_lock.acquire_read()
        try:
            retval = self.__streaming
            return retval
        finally:
            self.__streaming_lock.release_read()

    @streaming.setter
    def streaming(self, value):
        self.__streaming_lock.acquire_write()
        try:
            self.__streaming = value
        finally:
            self.__streaming_lock.release_write()

    @property
    def is_closed(self):
        self.__is_closed_lock.acquire_read()
        try:
            retval = self.__is_closed
            if retval is False and self.harem.gotta_quit is True:
                print("WARNING --- closed should be true, as harem is quitting. It's not true though. Weird!")  #  Returning True.")
#                retval = True
            return retval
        finally:
            self.__is_closed_lock.release_read()

    @is_closed.setter
    def is_closed(self, value):
        self.__is_closed_lock.acquire_write()
        try:
            self.__is_closed = value
        finally:
            self.__is_closed_lock.release_write()

    @property
    def dupes(self):
        self.__dupes_lock.acquire_read()
        try:
            retval = self.__dupes
            return retval
        finally:
            self.__dupes_lock.release_read()

    @dupes.setter
    def dupes(self, value):
        if type(value) is not int or value < 0:
            raise ValueError("dupes must be int and >=0")
        self.__dupes_lock.acquire_write()
        try:
            self.__dupes = value
        finally:
            self.__dupes_lock.release_write()

    @property
    def frame_size(self):
        self.__frame_size_lock.acquire_read()
        try:
            retval = self.__frame_size
            return retval
        finally:
            self.__frame_size_lock.release_read()

    @frame_size.setter
    def frame_size(self, value):
        if type(value) is not int or value < 4 or value > 256:
            raise ValueError("frame_size must be int and between 4&256 (inclusive)")
        self.__frame_size_lock.acquire_write()
        try:
            self.__frame_size = value
        finally:
            self.__frame_size_lock.release_write()

    @property
    def _frameno(self):
        self.__frameno_lock.acquire_read()
        try:
            retval = self.__frameno
            return retval
        finally:
            self.__frameno_lock.release_read()

    @_frameno.setter
    def _frameno(self, value):
        self.__frameno_lock.acquire_write()
        try:
            self.__frameno = value
        finally:
            self.__frameno_lock.release_write()

    @property
    def _frames_dct(self):
        self.__frames_dct_lock.acquire_read()
        try:
            retval = self.__frames_dct
            return retval
        finally:
            self.__frames_dct_lock.release_read()

    @_frames_dct.setter
    def _frames_dct(self, value):
        self.__frames_dct_lock.acquire_write()
        try:
            self.__frames_dct = value
        finally:
            self.__frames_dct_lock.release_write()

    @property
    def _lastframethatispatout(self):
        self.__lastframethatispatout_lock.acquire_read()
        try:
            retval = self.__lastframethatispatout
            return retval
        finally:
            self.__lastframethatispatout_lock.release_read()

    @_lastframethatispatout.setter
    def _lastframethatispatout(self, value):
        self.__lastframethatispatout_lock.acquire_write()
        try:
            self.__lastframethatispatout = value
        finally:
            self.__lastframethatispatout_lock.release_write()

    def __repr__(self):
        class_name = type(self).__name__
        pk_nicks = self.harem.nicks_for_pk(self.pubkey)
        irc_servers = self.irc_servers
        pk = squeeze_da_keez(self.pubkey)[:16] + '...'
        return f"{class_name}: uid={self.uid!r}; is_closed={self.is_closed!r}; me={self.harem.desired_nickname!r}; them={pk_nicks!r}; irc_servers={irc_servers!r}; pubkey={pk!r}"

    def __my_framing_loop(self):
        nicks4pk = self.harem.nicks_for_pk(self.pubkey)
        if nicks4pk == '':
            nicks4pk = '(zombie)'  # print("WARNING -- cannot find any nicknames for this public key. This suggests that it's a leftover from a previous simpipe.")
        loopcounter = -1
        while not self.is_closed:
            if self.q4me_via_harem.empty():
                sleep(1)
                loopcounter += 1
                if loopcounter % 60 == 0:
                    print("%s [#%-5d] src %-10s dst %-10s  %s is listening for incoming frames from %s" % (s_now(), self.uid, self.harem.desired_nickname, nicks4pk, self.harem.desired_nickname, nicks4pk))
            else:
                try:
#                    print("Reading packet from q4me")
                    frame = self.q4me_via_harem.get(timeout=1)
#                    print("Processing packet from q4me")
                    self.process_frame(frame)
                except Empty:
                    sleep(.1)
        print("%s [#%-5d] src %-10s dst %-10s  Framing loop is ending" % (s_now(), self.uid, self.harem.desired_nickname, nicks4pk))

    def process_frame(self, frame):
        if self.uid not in self._frames_dct:
            self._frames_dct[self.uid] = [None]
#                print("%s %-10s<==%-10s  Simpipe rx'd packet" % (s_now(), self.harem.desired_nickname, self.harem.nicks_for_pk(self.pubkey)), frame)
        frame_uid = int.from_bytes(frame[:4], 'little')
        this_frameno = int.from_bytes(frame[4:8], 'little')
        block_len = int.from_bytes(frame[8:10], 'little')
        subframe = frame[10:(block_len + 10)]
        if len(subframe) != block_len:
            assert(len(subframe) == block_len)
        cksum = frame[(block_len + 10):]
        if frame_uid != self.uid:
            print("%s [#%-5d] src %-10s dst %-10s  Rx'd #%3d frame (was for simpipe #%d; I suspect someone closed a simpipe somewhere & I should ignore this packet. So, I'll ignore it.)" % (s_now(), frame_uid, self.harem.nicks_for_pk(self.pubkey), self.harem.desired_nickname, this_frameno, self.uid))
            pass
        else:
            print("%s [#%-5d] src %-10s dst %-10s  Rx'd #%3d frame" % (s_now(), frame_uid, self.harem.nicks_for_pk(self.pubkey), self.harem.desired_nickname, this_frameno))
        if frame_uid not in self._frames_dct:
            self._frames_dct[frame_uid] = [None]
        while len(self._frames_dct[frame_uid]) <= this_frameno:
            self._frames_dct[frame_uid] += [None]
        if self._frames_dct[frame_uid][this_frameno] is None:
            assert(cksum == bytes_64bit_cksum(frame[:block_len + 10]))
            self._frames_dct[frame_uid][this_frameno] = subframe
            print("%s [#%-5d] src %-10s dst %-10s  Rx'd #%3d frame %s" % (s_now(), frame_uid, self.harem.desired_nickname, self.harem.nicks_for_pk(self.pubkey), this_frameno,
                            ' ' * this_frameno + ''.join(('.' if r is None else '+') for r in self._frames_dct[frame_uid][self._lastframethatispatout + 1:this_frameno + 1])))  # , frame)
        if self._lastframethatispatout < this_frameno and (None not in self._frames_dct[self.uid][self._lastframethatispatout + 1:this_frameno + 1]):
            if self.streaming or block_len == 0:
                print("%s [#%-5d] src %-10s dst %-10s  Que'd %3d thru %3d (inclusive)" % (s_now(), self.uid, self.harem.nicks_for_pk(self.pubkey), self.harem.desired_nickname, self._lastframethatispatout + 1, this_frameno))
                outdat = b''.join([self._frames_dct[self.uid][i] for i in range(self._lastframethatispatout + 1, this_frameno + 1)])
                self.my_get_queue.put(outdat)
                # print("Data sent: %d bytes" % len(outdat))
                self._lastframethatispatout = this_frameno
    #            else:
    #                print("Rx'd #%d frame" % this_frameno)

    def empty(self):
        return self.my_get_queue.empty()

    def get(self, block=True, timeout=None):
        """Receive packet."""
        return self.__getSUB(block, timeout, nowait=False)

    def get_nowait(self):
        """Receive packet."""
        return self.__getSUB(nowait=True)

    def __getSUB(self, block=True, timeout=None, nowait=False):
        if self.is_closed:
            raise RookerySimpipeAlreadyClosedError("You (%s) cannot receive from %s simpipe #%d: it is closed." % (self.harem.desired_nickname, self.harem.nicks_for_pk(self.pubkey), self.uid))
        retval = self.my_get_queue.get_nowait() if nowait else self.my_get_queue.get(block=block, timeout=timeout)
#        print("%s %-10s<==%-10s  %s" % (s_now(), self.harem.desired_nickname, self.harem.nicks_for_pk(self.pubkey), retval))
        return retval

    def put(self, datablock):
        if self.is_closed:
            raise RookerySimpipeAlreadyClosedError("You (%s) cannot send to %s simpipe #%d: it is closed." % (self.harem.desired_nickname, self.harem.nicks_for_pk(self.pubkey), self.uid))
        if type(datablock) is not bytes:
            raise ValueError("Simpipe.put() takes BYTES!")
        assert(type(self.uid) is int)
        # if self.uid is None:
        #     self.__uid = randint(0, 256 * 256 * 256 * 256 - 1)
        #     print("%s %-10s<==%-10s  Tx'd #  0 frame w/ UID %d for outgoing simpipe." % (s_now(), self.harem.desired_nickname, self.harem.nicks_for_pk(self.pubkey), self.uid))
        indexpos = 0
        length_of_all_data = len(datablock)
        ircsvrs = self.irc_servers
        noof_ircsvrs = len(ircsvrs)
        shuffle(ircsvrs)
        block_len = 999999
        while block_len > 0 and not self.is_closed:
            block_len = min(self.frame_size, length_of_all_data - indexpos)
            this_block = datablock[indexpos:(indexpos + block_len)]
            subframe = bytes(self.uid.to_bytes(4, 'little') + self._frameno.to_bytes(4, 'little') + block_len.to_bytes(2, 'little') + this_block)
            frame = bytes(subframe + bytes_64bit_cksum(subframe))
            print("%s [#%-5d] dst %-10s dst %-10s  Tx'd #%3d frame of %3d bytes" % (s_now(), self.uid, self.harem.desired_nickname, self.harem.nicks_for_pk(self.pubkey), self._frameno, len(frame)))
            # print("%s %-10s<==%-10s  put%3d bytes packet" % (s_now(), self.harem.desired_nickname, self.harem.nicks_for_pk(self.pubkey), len(this_block)), frame, "  to simpipe")
            for i in range(0, self.dupes + 1):
                self._put(frame, ircsvrs[(self._frameno + i) % noof_ircsvrs])
            indexpos += block_len
            self._frameno += 1

    def _put(self, datablock, irc_server=None):
        """By hook or by crook (w/ signaling & perhaps randomly picking from harem bots), send packet."""
        if self.is_closed:
            raise RookerySimpipeAlreadyClosedError("You cannot use %s-to-%s simpipe: it is closed." % (self.harem.desired_nickname, self.harem.nicks_for_pk(self.pubkey)))
        self.harem.put(self.pubkey, datablock, irc_server, yes_really=True)

    def close(self):
        nicks4pk = self.harem.nicks_for_pk(self.pubkey)
        if nicks4pk == '':
            nicks4pk = '(zombie)'  # print("WARNING -- cannot find any nicknames for this public key. This suggests that it's a leftover from a previous simpipe.")
        print("%s [#%-5d] src %-10s dst %-10s  Closing this simpipe" % (s_now(), self.uid, nicks4pk, self.harem.desired_nickname))
        if self.is_closed:
            print("%s-to-%s simpipe was already closed." % (self.harem.desired_nickname, nicks4pk))
            # RookerySimpipeAlreadyClosedError
        self.is_closed = True
        sleep(ENDTHREAD_TIMEOUT // 2 + 1)
        print("%s [#%-5d] src %-10s dst %-10s  Terminating the main loop" % (s_now(), self.uid, nicks4pk, self.harem.desired_nickname))
        try:
            self.harem.simpipes.remove(self)
        except ValueError:
            pass  # It's not in the list. Fine.
        self.harem.display_corridors()
        self.__my_framing_thread.join(timeout=ENDTHREAD_TIMEOUT)
        print("%s [#%-5d] src %-10s dst %-10s  Main loop terminated" % (s_now(), self.uid, nicks4pk, self.harem.desired_nickname))

    @property
    def irc_servers(self):
#         return list(self.harem.bots.keys())
        return ([k for k in list(self.harem.bots.keys()) if k in [h.irc_server for h in self.harem.true_homies]])

