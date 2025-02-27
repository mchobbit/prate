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
from my.classes.exceptions import PublicKeyBadKeyError, RookeryCorridorAlreadyClosedError, PublicKeyUnknownError
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
        self.__uid = uid
        while self.__uid is None or self.__uid in [i.uid for i in harem.corridors]:
            self.__uid = sha1("%s%s%s" % (squeeze_da_keez(destination), harem.desired_nickname, generate_random_alphanumeric_string(32)))
            assert(len(self.__uid) == 25)
        self.__harem = harem
        self.__closed = False
        self.__gotta_quit = False
        self.__destination = destination
        self.__my_main_thread = Thread(target=self.__my_main_loop, daemon=True)
        self.__my_main_thread.start()

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

    def __my_main_loop(self):
        self.harem.put(self.harem.destination, ("OPENCORRIDOR %s" % self.uid).encode())
        print("%s %-20s              Starts main loop corridor %s to %s..." % (s_now(), self.harem.desired_nickname, self.uid, squeeze_da_keez(self.harem.destination)[:16]))
        while not self.gotta_quit:
            sleep(A_TICK)
        print("%s %-20s              Ending main loop corridor %s to %s..." % (s_now(), self.harem.desired_nickname, self.uid, squeeze_da_keez(self.harem.destination)[:16]))

    def close(self):
        if self.__closed:
            raise RookeryCorridorAlreadyClosedError("Corridor %s is already closed" % self.uid)
        else:
            self.__closed = True
            self.harem.put(self.harem.destination, ("CLOSECORRIDOR %s" % self.uid).encode())
            self.quit()
        sleep(1)

    def quit(self, timeout=ENDTHREAD_TIMEOUT):
        print("%s %-20s              I am closing the corridor %s to %s..." % (s_now(), self.harem.desired_nickname, self.uid, squeeze_da_keez(self.harem.destination)[:16]))
        try:
            the_corridor_to_be_deleted = [e for e in self.harem.corridors if e.uid == self.uid][0]
            self.harem.corridors.remove(the_corridor_to_be_deleted)
        except (KeyError, IndexError):
            print("%s %-20s              Failed to delete corridor %s to %s..." % (s_now(), self.harem.desired_nickname, self.uid, squeeze_da_keez(self.harem.destination)[:16]))
        self.__gotta_quit = True
        self.__my_main_thread.join(timeout=timeout)
        print("%s %-20s              I have closed th'corridor %s to %s..." % (s_now(), self.harem.desired_nickname, self.uid, squeeze_da_keez(self.harem.destination)[:16]))

    @property
    def harem(self):
        """The harem that issued me."""
        return self.__harem

    @property
    def destination(self):
        """The intended destination to which I'll connect."""
        return self.__destination

    def write(self, datablock, timeout=-1):
        """Write data to the destination."""
        print("QQQ WRITE DATA QQQ")

    def read(self, timeout=-1):
        """Read data from the destination."""
        print("QQQ READ DATA QQQ")
        datablock = None
        return datablock

#     def FKDUP_generate_packets_list_for_transmission(self, pubkey, datablock):
#         outpackets_lst = []
#         bytes_remaining = len(datablock)
#         pos = 0
#         squeezed_pk = squeeze_da_keez(pubkey)
#         # if squeezed_pk not in self.outgoing_caches_dct:
#         #     self.outgoing_caches_dct[squeezed_pk] = [None] * 256
#         if squeezed_pk not in self.outgoing_packetnumbers_dct:
#             self.outgoing_packetnumbers_dct[squeezed_pk] = 0
#         if self.outgoing_packetnumbers_dct[squeezed_pk] >= 256 * 256 * 256 * 127:
#             self.outgoing_packetnumbers_dct[squeezed_pk] -= 256 * 256 * 256 * 127
#         while True:
#             bytes_for_this_frame = min(ENCRYPTED_MSG_BLOCK_SIZE_INSIDE_OVERALL_FRAME, bytes_remaining)
#             our_block = datablock[pos:pos + bytes_for_this_frame]
#             frame = bytearray()
#             frame += self.outgoing_packetnumbers_dct[squeezed_pk].to_bytes(4, 'little')  # packet#
#             frame += len(our_block).to_bytes(2, 'little')  # length
#             frame += our_block  # data block
#             frame += bytes_64bit_cksum(bytes(frame[0:len(frame)]))  # checksum
#             outpackets_lst.append(frame)  # print("%s %-20s              Sent pkt#%d of %d bytes" % (s_now(), self.desired_nickname, self.outgoing_packetnumbers_dct[squeezed_pk], len(frame)))
#             bytes_remaining -= bytes_for_this_frame
#             pos += bytes_for_this_frame
#             self.outgoing_packetnumbers_dct[squeezed_pk] += 1
#             if bytes_for_this_frame == 0:
#                 break
#         return outpackets_lst
#
#     def FKDUP_put(self, pubkey, datablock):
#         if self.paused:
#             raise ValueError("Set paused=False and try again.")
#         assert(type(pubkey) is RSA.RsaKey)
#         assert(type(datablock) is bytes)
#         outpackets_lst = self.FKDUP_generate_packets_list_for_transmission(pubkey, datablock)
#         packetnum_offset = self.outgoing_packetnumbers_dct[squeeze_da_keez(pubkey)] - len(outpackets_lst)
#         print("%s %s: okay. Transmitting the outpackets." % (s_now(), self.desired_nickname))
#         our_homies = [h for h in self.get_homies_list(True) if h.pubkey == pubkey]
#         if 0 == len(our_homies):
#             raise PublicKeyUnknownError("I cannot send a datablock: NO ONE LOGGED-IN IS OFFERING THIS PUBKEY.")
#         noof_packets = len(outpackets_lst)
#         noof_homies = len(our_homies)
#         packetstatuses = {}
#         is_homie_busy = [False] * noof_homies
#         el = 0
#         # Send a packet to every homie, in order.
#         while el < noof_packets or True in is_homie_busy:
#             sleep(.1)
#             if el < noof_packets:
#                 frame = bytes(outpackets_lst[el])
#                 for homieno in range(0, noof_homies):
#                     if not is_homie_busy[homieno]:
#                         is_homie_busy[homieno] = True
#                         homie = our_homies[homieno]
#                         frameno = int.from_bytes(frame[0:4], 'little')
#                         print("Sending frame #%d to %s via %s" % (frameno, homie.nickname, homie.irc_server))
#                         packetstatuses[frameno] = [homie.irc_server, datetime.datetime.now(), None]
#                         self.bots[homie.irc_server].crypto_put(homie.nickname, frame)
#                         el += 1
#             for homieno in range(0, noof_homies):
#                 if is_homie_busy[homieno]:
#                     try:
#                         (src, rxd) = self.bots[our_homies[homieno].irc_server].get_nowait()
#                     except Empty:
#                         pass
#                     else:
#                         receipt_packetno = int(rxd.split(' ')[0])
#                         receipt_irc_server = rxd.split(' ')[1]
#                         receipt_cksum = rxd.split(' ')[2]
#                         if receipt_irc_server != our_homies[homieno].irc_server:
#                             raise ValueError("I think I've mistakenly handled a packet that was from a different destination.")
# #                        if our_pktno < len(outpackets_lst):
#                         assert(receipt_cksum == base64.b85encode(hashlib.sha1(bytes(outpackets_lst[receipt_packetno - packetnum_offset])).digest()).decode())
#                         if packetnum_offset > 0:
#                             print("packetnum_offset =", packetnum_offset)
#                         assert(packetstatuses[receipt_packetno][1] is not None)
#                         assert(packetstatuses[receipt_packetno][2] is None)
#                         homie = our_homies[homieno]
#                         if src != homie.nickname:
#                             raise ValueError("WARNING -- src was not %s. Should I reinsert it in rx queue?" % homie.nickname)
#                         #     self.bots[homie.irc_server].reinsert((src, rxd))
#                         # else:
#                         packetstatuses[receipt_packetno][2] = datetime.datetime.now()
#                         print("CONFIRM packet #%d to %s via %s rx'd okay" % (receipt_packetno, homie.nickname, homie.irc_server))
#                         is_homie_busy[homieno] = False
#                         print("%s is now free." % homie.irc_server)
#
#     def FKDUP_process_incoming_buffer(self):
#         sleep(A_TICK)
#         final_packetnumber = -1
#         pubkey = None
#         while not self.paused and not self.gotta_quit and \
#         (final_packetnumber < 0 or [] != [i for i in range(self.our_getq_alreadyspatout, final_packetnumber + 1) if self.our_getq_cache[i % 65536] is None]):
#             # Prone to lockups and gridlock because it'll wait indefinitely for a missing packet.
#             if self.gotta_quit or self.paused:
#                 return
#             else:
#                 try:
#                     user, irc_server, frame = self.privmsgs_from_rookery_bots.get_nowait()
# #                    if pubkey is None:
#                     pubkey = self.bots[irc_server].homies[user].pubkey  # else assert(pubkey == self.bots[irc_server].homies[user].pubkey)
#                 except Empty:
#                     sleep(A_TICK)  # pass
#                 else:
#                     packetno = int.from_bytes(frame[0:4], 'little')
#                     if packetno < 256 * 256 and self.our_getq_alreadyspatout > 256 * 256 * 256 * 64:  #  ugly kludge
#                         print("%s %s: I think we've wrapped around." % (s_now(), self.desired_nickname))
#                         self.our_getq_alreadyspatout = 0
#                     if packetno < self.our_getq_alreadyspatout:
#                         print("%s %s: ignoring packet#%d, as it's a duplicate" % (s_now(), self.desired_nickname, packetno))
#                     else:
#                         assert(packetno < 256 * 256 * 256 * 127)  # PROGRAM A WRAPAROUND.
#                         self.our_getq_cache[packetno % 65536] = frame
#                         framelength = int.from_bytes(frame[4:6], 'little')
#                         checksum = frame[framelength + 6:framelength + 14]
#                         print("%s %s: rx'd pkt#%d of %d bytes" % (s_now(), self.desired_nickname, packetno, len(frame)))
#                         if checksum != bytes_64bit_cksum(frame[0:6 + framelength]):
#                             print("%s %s: bad checksum for pkt#%d. You should request a fresh copy." % (s_now(), self.desired_nickname, packetno))
#                         if framelength == 0:
#                             final_packetnumber = packetno
#                         our_cksum = base64.b85encode(hashlib.sha1(bytes(frame)).digest()).decode()
#                         print("Confirming receipt of packet #%d from %s; cksum %s" % (packetno, irc_server, our_cksum))
#                         self.bots[irc_server].put(user, "%d %s %s" % (packetno, irc_server, our_cksum))
#         data_to_be_returned = bytearray()
#         for i in range(self.our_getq_alreadyspatout, final_packetnumber + 1):
#             data_to_be_returned += self.our_getq_cache[i][6:-8]
#             self.our_getq_cache[i] = None
#         self.our_getq_alreadyspatout = final_packetnumber + 1
#         self.our_getqueue.put((pubkey, data_to_be_returned))

