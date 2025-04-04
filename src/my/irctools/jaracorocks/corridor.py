# -*- coding: utf-8 -*-
"""Corridor class: a corridor between harems.

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

from threading import Thread, Lock
from Crypto.PublicKey import RSA
from my.classes.exceptions import RookeryCorridorAlreadyClosedError, PublicKeyUnknownError, RookeryCorridorTimeoutError
from time import sleep
from my.irctools.cryptoish import squeeze_da_keez, datetimenow_to_4bytes, datetimenow_to_int
from queue import Empty, Queue
from random import choice
from my.stringtools import s_now
from my.classes.readwritelock import ReadWriteLock
from my.globals import _THIS_IS_A_DATA_FRAME_, HANDSHAKE_TIMEOUT, A_TICK, _CLOSE_A_CORRIDOR_, _RECEIVEDFRAMES_SITREP_
import datetime
import pickle
from math import sqrt


class Corridor:

    def __init__(self, our_uid, his_uid, destination_pk, harem):  # pubkey is HIS PUBKEY
        if our_uid is None and his_uid is None:
            raise ValueError("At least one of the UIDs mustn't be None.")
        if type(destination_pk) is not RSA.RsaKey or (our_uid is None and his_uid is None):
            raise ValueError("Corridor params are wrong types")
        self.__server_availability = {}
        self.__server_availability_lock = ReadWriteLock()
        self.__chooseserver_lock = Lock()
        self.__is_closed = False
        self.__is_closed_lock = ReadWriteLock()
        self.__our_uid = our_uid
        self.__our_uid_lock = ReadWriteLock()
        self.__his_uid = his_uid
        self.__his_uid_lock = ReadWriteLock()
        self.__q4me_via_harem = Queue()
        self.__gotta_close = False
        self.my_get_queue = Queue()
        self.__streaming = False  # If True, feed incoming data to buffer as it comes in; don't wait for the final packet!
        self.__streaming_lock = ReadWriteLock()
        self.__frames_lst = []
        self.__frames_lst_lock = ReadWriteLock()
        self.__frameno = 0
        self.__frameno_lock = ReadWriteLock()
        self.__frame_size = 256  # Maximum is 256.
        self.__frame_size_lock = ReadWriteLock()
        self.__dupes = 1  # How many duplicates (of each frame) should be sent?
        self.__dupes_lock = ReadWriteLock()
        self.__lastframethatispatout = -1
        self.__lastframethatispatout_lock = ReadWriteLock()
        self.__destination_pk = destination_pk  # his pubkey
        self.__harem = harem
        self.__my_framing_thread = Thread(target=self.__my_framing_loop, daemon=True)
        self.__my_framing_thread.start()

    def __repr__(self):
        class_name = type(self).__name__
        pk = self.destination_pk
        if pk is not None:
            pk = squeeze_da_keez(pk)
            pk = "%s..." % (pk[:16])
        try:
            uid = self.uid
        except AttributeError:
            uid = 'n/a'
        return f"{class_name}(uid={uid!r}, our_uid={self.our_uid!r}, his_uid={self.his_uid!r}, pubkey={pk!r}"

    @property
    def gotta_close(self):
        return self.__gotta_close

    @gotta_close.setter
    def gotta_close(self, value):
        self.__gotta_close = value

    @property
    def irc_servers(self):
#         return list(self.harem.bots.keys())
        return ([k for k in list(self.harem.bots.keys()) if k in [h.irc_server for h in self.harem.true_homies]])

    @property
    def q4me_via_harem(self):
        return self.__q4me_via_harem

    @property
    def frame_size(self):
        self.__frame_size_lock.acquire_read()
        try:
            retval = self.__frame_size
            return retval
        finally:
            self.__frame_size_lock.release_read()

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
    def server_availability(self):
        self.__server_availability_lock.acquire_read()
        try:
            retval = self.__server_availability
            return retval
        finally:
            self.__server_availability_lock.release_read()

    @server_availability.setter
    def server_availability(self, value):
        self.__server_availability_lock.acquire_write()
        try:
            self.__server_availability = value
        finally:
            self.__server_availability_lock.release_write()

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
    def _frames_lst(self):
        self.__frames_lst_lock.acquire_read()
        try:
            retval = self.__frames_lst
            return retval
        finally:
            self.__frames_lst_lock.release_read()

    @_frames_lst.setter
    def _frames_lst(self, value):
        self.__frames_lst_lock.acquire_write()
        try:
            self.__frames_lst = value
        finally:
            self.__frames_lst_lock.release_write()

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

    @property
    def our_uid(self):
        """Each element contains a Corridor instance. Each corridor contains both public keys (mine and his), a UID, and a packet counter."""
        self.__our_uid_lock.acquire_read()
        try:
            retval = self.__our_uid
            return retval
        finally:
            self.__our_uid_lock.release_read()

    @our_uid.setter
    def our_uid(self, value):
        self.__our_uid_lock.acquire_write()
        try:
            self.__our_uid = value
        finally:
            self.__our_uid_lock.release_write()

    @property
    def his_uid(self):
        """Each element contains a Corridor instance. Each corridor contains both public keys (mine and his), a UID, and a packet counter."""
        self.__his_uid_lock.acquire_read()
        try:
            retval = self.__his_uid
            return retval
        finally:
            self.__his_uid_lock.release_read()

    @his_uid.setter
    def his_uid(self, value):
        self.__his_uid_lock.acquire_write()
        try:
            self.__his_uid = value
        finally:
            self.__his_uid_lock.release_write()

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
    def destination_pk(self):
        return self.__destination_pk

    @property
    def uid(self):
        if self.our_uid is None or self.his_uid is None:
            raise AttributeError("We do not know this corridor's uid yet: we haven't finished negotiating it.")
        else:
            return max(self.his_uid, self.our_uid)

    @property
    def str_uid(self):
        try:
            return '#%-9d' % self.uid
        except AttributeError:
            if self.his_uid is not None:
                return "?%-8d?" % self.his_uid
            elif self.our_uid is not None:
                return "?%-8d?" % self.our_uid
            else:
                return "?????"

    @property
    def is_closed(self):
        self.__is_closed_lock.acquire_read()
        try:
            retval = self.__is_closed
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
    def harem(self):
        return self.__harem

    def __my_framing_loop(self):
        nicks4pk = self.harem.nicks_for_pk(self.destination_pk)
        if nicks4pk == '':
            nicks4pk = '(zombie)'  # print("WARNING -- cannot find any nicknames for this public key. This suggests that it's a leftover from a previous corridor.")
        print("%s [%s]     %s is listening for frames from %s" % (s_now(), self.str_uid, self.harem.desired_nickname, nicks4pk))
        while not self.gotta_close:
            if self.q4me_via_harem.empty():
                sleep(A_TICK)
                if datetime.datetime.now().second == 0:
                    print("%s [%s]     %s is still listening for frames from %s" % (s_now(), self.str_uid, self.harem.desired_nickname, nicks4pk))
                    sleep(1)
            else:
                try:
                    frame = self.q4me_via_harem.get(timeout=1)
                    self.process_frame(frame)
                except Empty:
                    sleep(A_TICK)
        self.is_closed = True
        self.harem.corridors.remove(self)
        print("%s [%s]     %s has stopped listening for frames from %s" % (s_now(), self.str_uid, self.harem.desired_nickname, nicks4pk))

    def put(self, datablock):
        if self.gotta_close or self.is_closed:
            raise RookeryCorridorAlreadyClosedError("You (%s) cannot send to %s corridor #%d: it is not open." % (self.harem.desired_nickname, self.harem.nicks_for_pk(self.destination_pk), self.uid))
        if type(datablock) is not bytes:
            raise ValueError("Corridor.put() takes BYTES!")
        assert(type(self.uid) is int)
        indexpos = 0
        length_of_all_data = len(datablock)
        block_len = 999999
        while block_len > 0 and not self.gotta_close:
            block_len = min(self.frame_size, length_of_all_data - indexpos)
            this_block = datablock[indexpos:(indexpos + block_len)]
            frame = bytes(_THIS_IS_A_DATA_FRAME_ + self.uid.to_bytes(3, 'little') + self._frameno.to_bytes(4, 'little') + \
                              datetimenow_to_4bytes() + block_len.to_bytes(2, 'little') + this_block)
            # print("%s %-10s<==%-10s  put%3d bytes packet" % (s_now(), self.harem.desired_nickname, self.harem.nicks_for_pk(self.destination_pk), len(this_block)), frame, "  to corridor")
            t = datetime.datetime.now()
            done = False
            while not self.gotta_close and not done:
                the_server_to_use = None
                with self.__chooseserver_lock:
                    for s in self.irc_servers:
                        if s not in self.server_availability:
                            self.server_availability[s] = None
                        if self.server_availability[s] is None:
                            self.server_availability[s] = self._frameno
                            the_server_to_use = s
                            break
                if the_server_to_use is not None:
                    print("%s [#%-9d]     %-10s---> %-10s  Tx'd #%3d frame of %3d bytes w/ %s" % (s_now(), self.uid, self.harem.desired_nickname, self.harem.nicks_for_pk(self.destination_pk), self._frameno, len(frame), the_server_to_use))
                    self.harem.put(self.destination_pk, frame, the_server_to_use, bypass_harem=True)
                    indexpos += block_len
                    self._frameno += 1
                    done = True
                else:
                    sleep(A_TICK)
            if (datetime.datetime.now() - t).seconds >= HANDSHAKE_TIMEOUT:
                raise RookeryCorridorTimeoutError("Ran out of time while trying to find a server that will send frame #%d down corridor %s" % (self._frameno, self.uid))

    def empty(self):
        return self.my_get_queue.empty()

    def get(self, block=True, timeout=None):
        """Receive packet."""
        return self.__getSUB(block, timeout, nowait=False)

    def get_nowait(self):
        """Receive packet."""
        return self.__getSUB(nowait=True)

    def __getSUB(self, block=True, timeout=None, nowait=False):
        if self.gotta_close or self.is_closed:
            raise RookeryCorridorAlreadyClosedError("You (%s) cannot receive from %s corridor #%d: it is closed." % (self.harem.desired_nickname, self.harem.nicks_for_pk(self.destination_pk), self.uid))
        retval = self.my_get_queue.get_nowait() if nowait else self.my_get_queue.get(block=block, timeout=timeout)
#        print("%s %-10s<==%-10s  %s" % (s_now(), self.harem.desired_nickname, self.harem.nicks_for_pk(self.destination_pk), retval))
        return retval

    def process_frame(self, frame):
        control_cmd = frame[0]
        frame_uid = int.from_bytes(frame[1:4], 'little')
        this_frameno = int.from_bytes(frame[4:8], 'little')
        timestamp = int.from_bytes(frame[8:12], 'little')
        block_len = int.from_bytes(frame[12:14], 'little')
        this_block = frame[14:]
        if len(this_block) != block_len:
            assert(len(this_block) == block_len)
        if frame_uid != self.uid:
            print("%s [#%-9d]                    %-10s  Rx'd #%3d frame (was for corridor #%d; I suspect someone closed a corridor somewhere & I should ignore this packet. So, I'll ignore it.)" % (s_now(), frame_uid, self.harem.desired_nickname, this_frameno, self.uid))
        elif control_cmd == ord(_RECEIVEDFRAMES_SITREP_):
            self._process_a_sitrep_frame(this_block)
        elif control_cmd == ord(_THIS_IS_A_DATA_FRAME_):
            self._process_a_data_frame(this_frameno, timestamp, this_block)
        else:
            print("Warning -- process_frame() -- incoming frame is not a data frame")
            print("frame:", frame)
            print("ctrl :", control_cmd)
            assert(control_cmd == ord(_THIS_IS_A_DATA_FRAME_))

    def _process_a_sitrep_frame(self, this_block):
        try:
            alleged_corridor_uid, this_frameno, transmission_timestamp, receipt_timestamp = pickle.loads(this_block)
            assert(alleged_corridor_uid == self.uid)
        except (ValueError, IndexError, AssertionError):
            print("%s [#%-9d]                    %-10s  SITREP IS ALL JACKED UP -- cannot understand the sitrep frame" % (s_now(), self.uid, self.harem.nicks_for_pk(self.destination_pk)))
        else:
            now = datetimenow_to_int()
            tx_time_in_us = receipt_timestamp - transmission_timestamp
            pingback_time_in_us = now - receipt_timestamp
            try:
                svr_name = [k for k in self.server_availability if self.server_availability[k] == this_frameno][0]
                self.server_availability[svr_name] = None
                s = "%s [#%-9d]                    %-10s  frame#%3d rx'd  (%1.2f, %1.2f seconds); releasing %s" % \
                    (s_now(), self.uid, self.harem.nicks_for_pk(self.destination_pk), this_frameno, tx_time_in_us / 1000000, pingback_time_in_us / 1000000, svr_name)
                print(s)
            except (IndexError, KeyError):
                print("%s [#%-9d]                    %-10s  SITREP IS ALL JACKED UP -- cannot find this irc server in our magic list" % (s_now(), self.uid, self.harem.nicks_for_pk(self.destination_pk)))

    def _process_a_data_frame(self, this_frameno, timestamp, this_block):
        block_len = len(this_block)
        while len(self._frames_lst) <= this_frameno:
            self._frames_lst += [None]
        if self._frames_lst[this_frameno] != this_block:
            self._frames_lst[this_frameno] = this_block
            sitrep_dat = pickle.dumps([self.uid, this_frameno, timestamp, datetimenow_to_int()])
            self.harem.put(self.destination_pk, bytes(_RECEIVEDFRAMES_SITREP_
                                           +self.uid.to_bytes(3, 'little')
                                           +self._frameno.to_bytes(4, 'little')
                                           +datetimenow_to_4bytes()
                                           +len(sitrep_dat).to_bytes(2, 'little')
                                           +sitrep_dat
                                           ),
                                       choice(self.irc_servers), bypass_harem=True)
        else:
            print("DUPE. That's ok -- no hard feelings")
        write_up_to_here = self._lastframethatispatout + 1
        while write_up_to_here < len(self._frames_lst) and self._frames_lst[write_up_to_here] is not None:
            write_up_to_here += 1
        write_up_to_here -= 1
        print("Corridor #%-5d Frame #%-5d    %2d bytes" % (self.uid, this_frameno, block_len))
        if write_up_to_here > self._lastframethatispatout \
        and (self.streaming is True or len(self._frames_lst[write_up_to_here]) == 0):
            print("%s [#%-9d]                    %-10s  Que'd %3d thru %3d (inclusive)" % (s_now(), self.uid, self.harem.desired_nickname, self._lastframethatispatout + 1, this_frameno))
            outdat = b''.join([self._frames_lst[i] for i in range(self._lastframethatispatout + 1, write_up_to_here)])
            self.my_get_queue.put(outdat)
            self._lastframethatispatout = write_up_to_here
        else:
            print("%s [#%-9d]                    %-10s  Rx'd #%3d frame %s" % (s_now(), self.uid, self.harem.nicks_for_pk(self.destination_pk), this_frameno,
                            ' ' * int(sqrt(this_frameno)) + ''.join(('.' if r is None else '+') for r in self._frames_lst[self._lastframethatispatout + 1:this_frameno + 1])))  # , frame)

    def close(self, timeout=HANDSHAKE_TIMEOUT):
        """Tell the other end of the corridor to shut down. Then, shut our own end down."""
        nicks4pk = self.harem.nicks_for_pk(self.destination_pk)
        if nicks4pk == '':
            nicks4pk = '(zombie)'  # print("WARNING -- cannot find any nicknames for this public key. This suggests that it's a leftover from a previous corridor.")
        print("%s [?%-8d?]     %-10s---> %-10s  DESTROYING & FORGETTING CORRIDOR" % (s_now(), self.uid, nicks4pk, self.harem.desired_nickname))
        print("%s [%s]                    %-10s  I have told %s to close corridor... and now, I'm waiting to be told to do the same." % (s_now(), self.str_uid, nicks4pk, self.harem.desired_nickname))
        try:
            bout = bytes(_CLOSE_A_CORRIDOR_ + self.his_uid.to_bytes(3, 'little'))
            self.harem.put(self.destination_pk, bout, bypass_harem=True)
        except PublicKeyUnknownError:
            print("%s [%s]     %-10s---> %-10s  We've already closed the other end, apparently? (The PK is invalid now.) Cool." % (s_now(), self.str_uid, nicks4pk, self.harem.desired_nickname))
        t = datetime.datetime.now()
        while self in self.harem.corridors:
            if (datetime.datetime.now() - t).seconds >= timeout:
                raise RookeryCorridorTimeoutError("Timed out while closing corridor")
            if t.second % 4 == 4:
                print("%s [%s]     %-10s---> %-10s  Waiting for me to be deleted from harem's list of corridors" % (s_now(), self.str_uid, nicks4pk, self.harem.desired_nickname))
            sleep(.5)
        assert(self.gotta_close is True)
        assert(self.is_closed is True)
        assert(self not in self.harem.corridors)
        print("%s [?%-8d?]     %-10s---> %-10s  CORRIDOR DESTROYED & FORGOTTEN" % (s_now(), self.uid, nicks4pk, self.harem.desired_nickname))
        if len(self.harem.corridors) > 0:
            self.harem.display_corridors()

