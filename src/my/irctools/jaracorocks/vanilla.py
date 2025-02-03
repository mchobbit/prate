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
try:
    from my.stringtools import generate_irc_handle  # @UnusedImport
except ImportError:
    print("generate_irc_handle() is missing. Fine. We'll do it the hard way.")
    generate_irc_handle = lambda: ''.join(choice(string.ascii_lowercase) for _ in range(16))


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
        self.__initial_nickname = nickname
        self.__initial_channel = channel  # This channel will automatically joined at Welcome stage
        self.__whois_dct = {}  # Results of /whois will be stored here
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
    def initial_channel(self):
        """The channel that the server was meant to join for me."""
        return self.__initial_channel

    @property
    def nickname(self):
        """The nickname that the server currently uses for me."""
        while not hasattr(self.connection, 'real_nickname'):
            sleep(.1)
        return self.connection.get_nickname()

    @nickname.setter
    def nickname(self, value):
        """Tell the server to change the nickname that it uses for me."""
        self.connection.nick(value)

    @property
    def realname(self):
        """The realname that was specified by me for the server."""
        return self._realname

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
        self.__whois_dct[nick] = ' '.join([r for r in e.arguments])

    def _on_nosuchnick(self, _c, e):
        """Triggered when the event-handler receives ERR_NOSUCHNICK."""
        self.__whois_dct[e.arguments[0]] = None

    def on_nicknameinuse(self, _c, _e):
        """Triggered when the event-handler receives ERR_NICKNAMEINUSE."""
        new_nick = generate_irc_handle() + str(randint(11, 99))
        self.nickname = new_nick

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
        elif cmd.startswith("whois"):
            i = cmd.find(' ')
            if i < 0:
                found = None
            else:
                user = cmd[i + 1:]
                found = self.call_whois_and_wait_for_response(user)
                if found:
                    c.notice(nick, found)
                else:
                    c.notice(nick, "The server does not recognize the user %s" % user)
        else:
            c.notice(nick, "Unknown command => " + cmd)

    def call_whois_and_wait_for_response(self, user, timeout=5):
        """Sends a /whois to the server. Waits for a response. Returns the response."""
        if not self.connected:
            raise TimeoutError("I cannot /whois, because I am not connected. Please connect to the server and try again.")
        self.connection.whois(user)  # Send request to the IRC server
        for _ in range(0, timeout * 10):
            self.reactor.process_once()  # Process incoming & outgoing events w/ IRC server
            try:
                return self.__whois_dct[user]  # Results, sent by IRC server, will be recorded when _no_whoisuser() is triggered
            except KeyError:
                sleep(.1)  # Still waiting for answer
        raise TimeoutError("Timeout while waiting for answer to /whois %s" % user)

####################################################################################


if __name__ == "__main__":

    ircbot = SingleServerIRCBotWithWhoisSupport(channel="#prate", nickname='clyde', realname='ccllyyddee', irc_server='cinqcent.local', port=6667)
    ircbot.connect("cinqcent.local", 6667, "clyde")
    ircbot.start()
