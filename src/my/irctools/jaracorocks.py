# -*- coding: utf-8 -*-
"""
Created on Jan 22, 2025

@author: mchobbit

Adjustment to jaraco's project
https://github.com/jaraco/irc/blob/main/scripts/irccat.py

Todo:
    * Finish docs
    * WRITE UNIT TESTS!

"""
from random import randint
import irc.bot
from time import sleep
from my.stringtools import generate_irc_handle


class SingleServerIRCBotWithWhoisSupport(irc.bot.SingleServerIRCBot):

    def __init__(self, channel, nickname, realname, server, port=6667):
        irc.bot.SingleServerIRCBot.__init__(self, [(server, port)], nickname, realname)
        self._whois_dct = {}
        self._initial_nickname = nickname
        self.channel = channel  # This channel will automatically joined at Welcome stage
        self.connection.add_global_handler('whoisuser', self._on_whoisuser, -1)
        self.connection.add_global_handler('nosuchnick', self._on_nosuchnick, -1)

    def _on_nosuchnick(self, c, e):
        self._whois_dct[e.arguments[0]] = None
        print("ERR_NOSUCHNICK")

    def _on_whoisuser(self, c=None, e=None):
        nick = e.arguments[0]
        channel = e.target
        self._whois_dct[nick] = ' '.join([r for r in e.arguments])

    def on_nicknameinuse(self, c, e):
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
        c.join(self.channel)

    def on_privmsg(self, c, e):  # Will be re-defined in any subclass, probably
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

