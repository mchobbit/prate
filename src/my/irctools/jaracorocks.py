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

.. _Google Python Style Guide:
   http://google.github.io/styleguide/pyguide.html
"""

from random import randint
import irc.bot
from time import sleep
from my.stringtools import generate_irc_handle


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

    """

    def __init__(self, channel, nickname, realname, server, port=6667):
        irc.bot.SingleServerIRCBot.__init__(self, [(server, port)], nickname, realname)
        self._whois_dct = {}
        self._initial_nickname = nickname
        self.channel = channel  # This channel will automatically joined at Welcome stage
        self.connection.add_global_handler('whoisuser', self._on_whoisuser, -1)
        self.connection.add_global_handler('nosuchnick', self._on_nosuchnick, -1)

    def _on_nosuchnick(self, c, e):
        del c
        self._whois_dct[e.arguments[0]] = None

    def _on_whoisuser(self, c=None, e=None):
        del c
        nick = e.arguments[0]
        channel = e.target
        self._whois_dct[nick] = ' '.join([r for r in e.arguments])

    def on_nicknameinuse(self, c, e):
        del e
        n = c.get_nickname()
        new_nick = generate_irc_handle(13, 15) + str(randint(1111, 9999))
        print("NICKNAME IN USE. It was %s; now, it's %s." % (n, new_nick))
        c.nick(new_nick)

    def call_whois_and_wait_for_response(self, user, timeout=30):
        c = self.connection
        c.whois(user)  # make initial request
        for _ in range(0, timeout * 10):
            sleep(.1)
            self.reactor.process_once()
            try:
                return self._whois_dct[user]
            except KeyError:
                print("Still waiting")
        raise TimeoutError("Ran out of time, waiting for answer to /whois %s" % user)

    @property
    def nickname(self):
        return self.connection.get_nickname()

    @nickname.setter
    def nickname(self, value):
        raise ValueError("Do not try to set a readonly item. Use nick() instead.")

    def on_welcome(self, c, e):
        del e
        c.join(self.channel)

    def on_privmsg(self, c, e):  # Will be re-defined in any subclass, probably
        del c
        self.do_command(e, e.arguments[0])

    def do_command(self, e, cmd):
        nick = e.source.nick
        c = self.connection
        if cmd == "disconnect":
            self.disconnect()
        elif cmd == "die":
            self.die()
        elif cmd.startswith("whois"):
            i = cmd.find(' ')
            if i < 0:
                found = None
            else:
#                return self.
                user = cmd[i + 1:]
                found = self.call_whois_and_wait_for_response(user, timeout=3)
                if found:
                    c.notice(nick, found)
                else:
                    c.notice(nick, "I don't know. Ask me again in a few seconds.")
        else:
            c.notice(nick, "What? => " + cmd)


if __name__ == "__main__":

    ircbot = SingleServerIRCBotWithWhoisSupport(channel="#prate", nickname='clyde', realname='ccllyyddee', server='cinqcent.local', port=6667)
    ircbot.connect("cinqcent.local", 6667, "clyde")
    ircbot.start()

