# -*- coding: utf-8 -*-
"""
Created on Jan 22, 2025

@author: mchobbit

IRC Tools library, for my testbot project.

This module contains useful functions for the testbot project, such as:-
    skinny_key()
    unskin_key()
    rsa_encrypt()
    rsa_decrypt()
    get_random_Cicero_line()

It also contains an important class, named:-
    MyGroovyTestBot

This class wraps around jaraco's IRC library.

Example:

        $ python3.12

        from my.irctools import *
        svr = MyGroovyTestBot("#test", "voodoochile", "irc.dal.net", 6667)
        while not svr.connected:
            sleep(1)
        while "#test" not in svr.channels:
            sleep(1)
        list_of_users = list(svr.channels['#test'].users())
        svr.put(list_of_users[0], "HELLO THERE.")
        txt = svr.get()
        svr.quit()

There's more to it than that.

Todo:
    * Finish docs
    * WRITE UNIT TESTS!

"""

import requests
import types
import irc.bot
import sys
import queue

import datetime
from time import sleep
from my.stringtools import generate_irc_handle, get_word_salad, get_bits_to_be_encoded, encode_via_steg, decode_via_steg, strict_encode_via_steg, multiline_encode_via_steg
from random import randint, choice, shuffle
from threading import Thread
from _queue import Empty

from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP
from cryptography.fernet import Fernet, InvalidToken
import base64
from dns.rdataclass import NONE
from my.globals import RPL_WHOISUSER, RPL_ENDOFWHOIS, WHOIS_ERRORS_LST, WHOIS_RESPCODE_LST
from my.globals.poetry import CICERO
from my.classes.readwritelock import ReadWriteLock
from my.irctools.jaracorocks import add_whois_support_to_ircbot, SingleServerIRCBotWithWhoisSupport


class Backthread1SvrIRCBotWithWhoisSupport(SingleServerIRCBotWithWhoisSupport):
    """Background-thread wraparound for a SingleServerIRCBotWithWhoisSupport class.

    """

    def __init__(self, channel, nickname, realname, server, port=6667):
        super().__init__(channel, nickname, realname, server, port)
        self.__time_to_quit = False
        self.__irc_thread = Thread(target=self._start_server, daemon=True)
        self.__irc_thread.start()

    def _start_server(self):
        self.start()


class LifoQueuedSimpleIRCBot(SingleServerIRCBotWithWhoisSupport):
    """The groovy test bot, to wrap around jaraco's irc library.

    This class is a subclass of jaraco's irc bot class. The server itself
    runs in the background, thanks to a Thread. Then, I (the subclass) can
    talk to the bot via the LIFO queues (one for reading; one for writing).
    In this way, the library can let jaraco's irc bot run in the background,
    can talk to it, and can persuade it to interact with other users in
    whichever room the bot is in.

    """

    def quit(self):
        self.__time_to_quit = True
        super().disconnect("Toodles.")  # print("Joining worker thread")
        self.__irc_thread.join()  # print("Yay. Quitting OK.")

    def on_welcome(self, c, e):
        c.join(self.channel)  # Join channel. (This is not a Thread thing.)
        self.connection_cache[e.target] = c
        self.connection_cache[self.channel] = c

    def on_pubmsg(self, c, e):
        """When a public message arrives in the chatroom, jaraco's irc bot will
        detect and send the event here. From here, it will be added to our queue."""
        self.connection_cache[e.target] = c
        self.input_queue.put([c, e])

    def on_notice(self, c, e):  # Is this necessary?
        """When a notice arrives in the chatroom, jaraco's irc bot will detect
        and send the event here. From here, it will be added to our queue."""
        self.connection_cache[e.target] = c
        self.input_queue.put([c, e])

    def on_privmsg(self, c, e):
        """When a private message reaches the user, jaraco's irc bot will detect
        and send the event here. From here, it will be added to our queue."""
        self.connection_cache[e.target] = c
        self.input_queue.put([c, e])

    def _send_private_message(self, user, txt):
        if user.startswith('#'):
            raise ValueError("User not must begin with a #; %s is bad." % user)
        if user not in self.connection_cache or self.connection_cache[user] is None:
            self.connection_cache[user] = self.connection
        for i in (user, self.nickname, self._initial_nickname):
            if i in self.connection_cache:
                self.connection_cache[i].privmsg(user, txt)
                return
        self.connection.privmsg(user, txt)
        print("WARNING - Cannot send private message to %s" % user)

    def _send_notice(self, channel, txt):
        if not channel.startswith('#'):
            raise ValueError("Channel must begin with a #; %s doesn't." % channel)
        if channel not in self.channels:
            raise ValueError("Please join %s and try again." % channel)
        if channel not in self.connection_cache or self.connection_cache[channel] is None:
            self.connection_cache[channel] = self.connection
        for i in (channel, self.nickname, self._initial_nickname):
            if i in self.connection_cache:
                self.connection_cache[i].notice(channel, txt)
                return
        print("WARNING - Cannot send notice to %s" % channel)

    def put(self, dest, txt):
        """Add a queue request, to send the specified text to the destination user."""
        if dest.startswith('#'):
            raise ValueError("Public messaging is broken in this app.")
        elif type(txt) is bytes:
            raise ValueError("txt must not be bytes")
        self.output_queue.put([dest, txt])

    def _output_worker_loop(self):
        """Thread that unendingly services the output queue."""
        while not self.__time_to_quit:
            try:
                (a_user, msg_txt) = self.output_queue.get_nowait()
                self._send_private_message(a_user, msg_txt)
                sleep(randint(16, 20) // 10.)  # Do not send more than 20 messages in 30 seconds! => 30/(((20+16)/2)/10)=16.7 messages per 30 seconds.
            except Empty:
                pass

    @property
    def empty(self):
        """Is the input queue empty? (the queue of msgs that have been sent to me)"""
        return self.input_queue.empty()

    def get(self):
        """Use this method to read the latest incoming sender+message from the input queue."""
        s = self.input_queue.get()
        if type(s) is bytes:
            raise ValueError("s must not be bytes")
        return s

    def get_nowait(self):
        """Use this method to read the latest incoming sender+message from the input queue."""
        s = self.input_queue.get_nowait()
        if type(s) is bytes:
            raise ValueError("s must not be bytes")
        return s

    @property
    def connected(self):
        """Is the irc bot connected to the IRC server on the Internet?"""
        if self.nickname in self.connection_cache:
            return self.connection_cache[self.nickname].is_connected()
        elif len(self.connection_cache) > 0:
            return self.connection_cache[list(self.connection_cache.keys())[0]].is_connected()
        else:
            return False


def simple_irc_client_for_testing_porpoises():
    import socket
    my_input = """cinqcent.local:6667
    clyde
    clyde
    John Doe"""

    # Parse input.
    ping = 'PING '
    pong = 'PONG '
    lines = my_input.split('\n')
    host = lines[0].split(':')

    # Connect.
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((host[0], int(host[1])))

    # Handshake.
    client.send(('NICK ' + lines[1] + '\r\n').encode())
    client.send(('USER ' + lines[2] + ' 0 * :' + lines[3] + '\r\n').encode())

    # Output and ping/pong.
    while True:
        data = client.recv(1024)
        print(data)

        if data.startswith(ping):
            resp = data.strip(ping)
            client.send(pong + resp)
            print(pong + resp)

'''
from my.globals import *
from my.irctools import *
import base64
pubslim = skinny_key(MY_RSAKEY.public_key())
b85slim = pubkey_to_b85(MY_RSAKEY.public_key())
b64slim = pubkey_to_b64(MY_RSAKEY.public_key())
assert(b85_to_pubkey(b85slim) == MY_RSAKEY.public_key())
assert(b64_to_pubkey(b64slim) == MY_RSAKEY.public_key())
assert(unskin_key(pubslim) == MY_RSAKEY.public_key())
print("pubslim: %d chars" % len(pubslim))
print("b85    : %d chars" % len(b85slim))
print("b64    : %d chars" % len(b64slim))
'''

if __name__ == "__main__":

    ircbot = MyGroovyTestBot(channel="#prate", nickname='clyde', realname='clyde', server='cinqcent.local', port=6667)
    add_whois_support_to_ircbot(ircbot)
    ircbot.connect("cinqcent.local", 6667, "clyde")
    ircbot.start()
