# -*- coding: utf-8 -*-
"""Classes and functions from (or inspired by) Jaraco's IRC project

Created on Jan 22, 2025

@author: mchobbit

This module contains classes, functions, and other tools that were inspired
by or taken from the work that Jaraco did on an IRC project. That project
helps programmers to speak to IRC servers in meaningful ways. For example,
some of the classes and subclasses facilitate asynchronous communication
with a chosen server, sending messages, running channels, etc.

URL of Jaraco's project:
    https://github.com/jaraco/irc/blob/main/scripts/irccat.py

Todo:
    * Finish docs
    * WRITE UNIT TESTS!
    * Make _whois_dct threadsafe

..  _Google Python Style Guide:
   http://google.github.io/styleguide/pyguide.html

.. _Napoleon/Sphinx Guide:
   https://sphinxcontrib-napoleon.readthedocs.io/en/latest/example_google.html

"""

from random import randint, choice
import irc.bot
from time import sleep
import string
from my.classes.exceptions import MyIrcStillConnectingError
from my.classes import MyTTLCache
from threading import Lock

try:
    from my.stringtools import generate_irc_handle  # @UnusedImport
except ImportError:
    print("generate_irc_handle() is missing. Fine. We'll do it the hard way.")
    generate_irc_handle = lambda: ''.join(choice(string.ascii_lowercase) for _ in range(16))

ANTIOVERLOAD_CACHE_TIME = 15


class SingleServerIRCBotWithWhoisSupport(irc.bot.SingleServerIRCBot):
    """Single-server IRC bot with Whois support.

    This class is a simple IRC bot. It logs into the specified IRC server,
    communicates with it, and responds accordingly. It runs in the foreground,
    thanks to the start() call, but many of the underlying activites occur
    in the background. Cf call_whois_and_wait_for_response().

    Note:
        This is only a simplistic example of how to use Jaraco's classes.

    Args:
        channel (str): The channel to join, e.g. #test
        nickname (str): The ideal nickname. The actual nickname is
            that one, unless there's a collision reported by the
            server. In that case, _on_nicknameinuse() will be
            triggered and a new nick will be chosen & submitted.
            The current nick is always available from the attribute
            .nickname .
        realname (str): The blurb that goes after the nickname in /whois.
            This could be dozens of characters long, per IRC's rules.
        server (str): The server, e.g. irc.dal.net
        port (int): The port# to use.

    Attributes:
        nickname (str): The current nickname, per the IRC server.

    Examples:

        $ from my.irctools.jaracorocks import SingleServerIRCBotWithWhoisSupport
        $ svr = SingleServerIRCBotWithWhoisSupport('#prate', 'clyde', 'Clyde Barrow, a naughty boy', 'cinqcent.local')
        $ svr.start()

    """

    def __init__(self, channel, nickname, realname, irc_server, port):
        irc.bot.SingleServerIRCBot.__init__(self, [(irc_server, port)], nickname, realname)
        if type(realname) is not str:
            raise ValueError("Realname should be a string, not", type(realname))
        self.__privmsg_cache = MyTTLCache(ANTIOVERLOAD_CACHE_TIME)  # Don't send the same private message to the same person more than once every ten seconds
        self.__privmsg_c_hits_dct = {}
        self.__whois_request_cache = MyTTLCache(ANTIOVERLOAD_CACHE_TIME)
        self.__whois_request_c_hits_v_misses = [0, 0]
        self.__whois_request_cache_mutex = Lock()
        self.__initial_nickname = nickname
        self.__initial_realname = realname
        self.__initial_channel = channel  # This channel will automatically joined at Welcome stage
        self.__whois_results_dct = {}  # Messages incoming from reactor, re: /whois, will be stored here
        self.connection.add_global_handler('whoisuser', self._on_whoisuser, -1)
        self.connection.add_global_handler('nosuchnick', self._on_nosuchnick, -1)

    @property
    def ready(self):
        """bool: Are we connected to the IRC server *and* have we joined the room that we want?"""
        if not self.connected:
            return False
        elif not self.joined:
            return False
        else:
            return True

    @property
    def initial_nickname(self):
        """The nickname that the server was meant to use for me."""
        return self.__initial_nickname

    @property
    def initial_realname(self):
        """The realname that the server was meant to use for me."""
        return self.__initial_realname

    @property
    def initial_channel(self):
        """The channel that the server was meant to join for me."""
        return self.__initial_channel

    @property
    def nickname(self):
        """The nickname that the server currently uses for me."""
        if not hasattr(self, 'connection'):
            raise MyIrcStillConnectingError("There's no connection yet: I'm still connecting.")
        if not hasattr(self.connection, 'real_nickname'):
            raise MyIrcStillConnectingError("I don't know my nickname yet: I'm still connecting.")
        return self.connection.get_nickname()

    @nickname.setter
    def nickname(self, value):
        """Tell the server to change the nickname that it uses for me."""
        self.connection.nick(value)

    @property
    def realname(self):
        """The realname that the server currently has for me."""
        return self.call_whois_and_wait_for_response(self.nickname).split(' ', 4)[-1]

    @property
    def connected(self):
        """Am I connected to the server?"""
        return self.connection.is_connected()

    @property
    def joined(self):
        """Am I a member of the channel that I wanted the server to join?"""
        return True if self.__initial_channel in self.channels else False

    def _on_whoisuser(self, _c=None, e=None):
        """Triggered when the event-handler receives RPL_WHOISUSER."""
        nick = e.arguments[0]  # Also, channel = e.target
        self.__whois_results_dct[nick] = ' '.join([r for r in e.arguments])

    def _on_nosuchnick(self, _c, e):
        """Triggered when the event-handler receives ERR_NOSUCHNICK."""
        self.__whois_results_dct[e.arguments[0]] = None

    def on_nicknameinuse(self, _c, _e):
        """Triggered when the event-handler receives ERR_NICKNAMEINUSE."""
        self.nickname = generate_irc_handle() + str(randint(11, 99))

    def on_welcome(self, c, _e):
        """Triggered when the event-handler receives RPL_WELCOME."""
        c.join(self.__initial_channel)

    def on_privmsg(self, c, e):
        """Triggered when the event-handler receives RPL_WHOISUSER."""
        cmd = e.arguments[0]
        nick = e.source.nick
        if cmd == "disconnect":
            self.disconnect()
        elif cmd == "die":
            self.die()
        else:
            c.notice(nick, "Unknown command => " + cmd)

    def call_whois_and_wait_for_response(self, user, timeout=10):
        if self.__whois_request_cache.get(user) is None:
            self.__whois_request_c_hits_v_misses[1] += 1
            self.__whois_request_cache.set(user, self.__call_whois_and_wait_for_response(user, timeout))
        else:
            self.__whois_request_c_hits_v_misses[0] += 1
            if self.__whois_request_c_hits_v_misses[0] % 100 == 0:
                hits, misses = self.__whois_request_c_hits_v_misses
                percentage = hits * 1000 / (hits + misses)
                print("Our whois cache has a %d%% hit rate" % percentage)
        return self.__whois_request_cache.get(user)

    def __call_whois_and_wait_for_response(self, user, timeout):
        """Sends a /whois to the server. Waits for a response. Returns the response."""
        with self.__whois_request_cache_mutex:
            if not self.connected:
                raise TimeoutError("I cannot /whois, because I am not connected. Please connect to the server and try again.")
            self.connection.whois(user)  # Send request to the IRC server
            for _ in range(0, timeout * 10):
                self.reactor.process_once()  # Process incoming & outgoing events w/ IRC server
                try:
                    return self.__whois_results_dct[user]  # Results, sent by IRC server, will be recorded when _no_whoisuser() is triggered
                except KeyError:
                    sleep(.1)  # Still waiting for answer
            raise TimeoutError("Timeout while waiting for answer to /whois %s" % user)

    def privmsg(self, user, msg):
        """Send a private message on IRC. Then, pause; don't overload the server."""
        cached_data = user + '///' + msg
        if user not in self.__privmsg_c_hits_dct:
            self.__privmsg_c_hits_dct[user] = 0
        if self.__privmsg_cache.get(cached_data) is None:
            self.__privmsg_cache.set(cached_data, cached_data)
            if self.__privmsg_c_hits_dct[user] > 5:
                print("I just saved %s from being sent the same message %d times by you" % (user, self.__privmsg_c_hits_dct[user]))
            self.__privmsg_c_hits_dct[user] = 0
            self.connection.privmsg(user, msg)  # Don't send the same message more than once every N seconds
            sleep(randint(16, 20) / 10.)  # 20 per 30s... or 2/3 per 1s... or 1s per 3/2... or 1.5 per second.
        else:
            self.__privmsg_c_hits_dct[user] += 1
            if self.__privmsg_c_hits_dct[user] % 100 == 0:
                print("WOAH!... %d times, for %s? Really?" % (self.__privmsg_c_hits_dct[user], user))
                pass

####################################################################################


if __name__ == "__main__":

    ircbot = SingleServerIRCBotWithWhoisSupport(channel="#prate", nickname='clyde', realname='ccllyyddee', irc_server='cinqcent.local', port=6667)
    ircbot.connect("cinqcent.local", 6667, "clyde")
    ircbot.start()
