# -*- coding: utf-8 -*-
"""Jaraco-style IRC bot classes.

Created on Jan 30, 2025

@author: mchobbit

This module contains classes for creating a Jaraco-style class of bot
that monitors an IRC server and sets up secure comms between users.

Classes:-
    irc.bot.SingleServerIRCBot (declared elsewhere)
        SingleServerIRCBotWithWhoisSupport
            DualQueuedFingerprintedSingleServerIRCBotWithWhoisSupport

Todo:
    * Better docs

.. _Google Python Style Guide:
   http://google.github.io/styleguide/pyguide.html

.. _Napoleon Style Guide:
   https://sphinxcontrib-napoleon.readthedocs.io/en/latest/example_google.html

Example:

"""

from random import randint
import irc.bot
from time import sleep
from my.classes.myttlcache import MyTTLCache
from my.globals import ANTIOVERLOAD_CACHE_TIME, MAX_PRIVMSG_LENGTH, MAX_NICKNAME_LENGTH, \
    MAX_CHANNEL_LENGTH, DEFAULT_WHOIS_TIMEOUT, A_TICK
from irc.client import ServerNotConnectedError
from queue import Queue
from my.classes.readwritelock import ReadWriteLock
from threading import Thread
from my.irctools.cryptoish import generate_fingerprint
from queue import Empty
import datetime
import validators

from my.stringtools import generate_irc_handle, generate_random_alphanumeric_string, s_now  # @UnusedImport
from my.classes.exceptions import IrcBadNicknameError, IrcPrivateMessageContainsBadCharsError, IrcPrivateMessageTooLongError, \
    IrcFingerprintMismatchCausedByServer, IrcInitialConnectionTimeoutError, IrcBadServerNameError, IrcBadChannelNameError, IrcChannelNameTooLongError, IrcBadServerPortError, \
    IrcStillConnectingError, IrcNicknameTooLongError, IrcNicknameChangedByServer, IrcJoiningChannelTimeoutError, IrcPartingChannelTimeoutError, IrcDuplicateNicknameError, \
    IrcConnectionError, IrcRanOutOfReconnectionsError


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
        irc_server (str): The server, e.g. irc.dal.net
        port (int): The port# to use.

    Attributes:
        nickname (str): The current nickname, per the IRC server.

    Examples:

        $ from my.irctools.jaracorocks import SingleServerIRCBotWithWhoisSupport
        $ svr = SingleServerIRCBotWithWhoisSupport('#prate', 'clyde', 'Clyde Barrow, a naughty boy', 'cinqcent.local')
        $ svr.start()

    """

    def __init__(self, channels, nickname, realname, irc_server, port, strictly_nick=False):
#        print("CHANNELS = >>>", channels , "<<<")
#        print("Type of CHANNELS =", type(channels))
        irc.client.ServerConnection.buffer_class.encoding = "latin-1"
        irc.client.ServerConnection.buffer_class.errors = "replace"
        if type(channels) not in (list, tuple):
            raise IrcBadChannelNameError("channels must be a list or a tuple")
        for ch in channels:
            if type(ch) is not str or ch[0] != '#' or ' ' in ch:
                raise IrcBadChannelNameError("%s is a dodgy channel name. Fix it." % str(ch))
        if type(port) is not int:
            raise ValueError("port must be an integer")
        irc.bot.SingleServerIRCBot.__init__(self, [(irc_server, port)], nickname, realname)
        if type(realname) is not str:
            raise ValueError("Realname should be a string, not %s" + str(type(realname)))
        self.__privmsg_cache = MyTTLCache(ANTIOVERLOAD_CACHE_TIME)  # Don't send the same private message to the same person more than once every ten seconds
        self.__privmsg_c_hits_dct = {}
        self.__whois_request_cache = MyTTLCache(ANTIOVERLOAD_CACHE_TIME)
        self.__whois_request_c_hits_v_misses = [0, 0]
        self.__initial_nickname = nickname
        self.__irc_server = irc_server
        self.__strictly_nick = strictly_nick
        self.__initial_realname = realname
        self.__err = None
        self.__initial_channels = channels  # These channels will automatically joined at Welcome stage
        self.__whois_results_dct = {}  # Messages incoming from reactor, re: /whois, will be stored here
        self.connection.add_global_handler('whoisuser', self._on_whoisuser, -1)
        self.connection.add_global_handler('nosuchnick', self._on_nosuchnick, -1)

    @property
    def err(self):
        return self.__err

    @err.setter
    def err(self, value):
        self.__err = value

    @property
    def irc_server(self):
        return self.__irc_server

    @property
    def ready(self):
        """bool: Are we connected to the IRC server *and* have we joined the room that we want?"""
        if not self.connected:
            return False
        elif not self.joined:  # Joined ALL the channels we want
            return False
        else:
            return True

    @property
    def strictly_nick(self):
        """The nickname that the server was meant to use for me."""
        return self.__strictly_nick

    @property
    def initial_nickname(self):
        """The nickname that the server was meant to use for me."""
        return self.__initial_nickname

    @property
    def initial_realname(self):
        """The realname that the server was meant to use for me."""
        return self.__initial_realname

    @property
    def initial_channels(self):
        """The channel that the server was meant to join for me."""
        return self.__initial_channels

    @property
    def nickname(self):
        """The nickname that the server currently uses for me."""
        if not hasattr(self, 'connection'):
            raise IrcStillConnectingError("There's no connection yet: I'm still connecting.")
        if not hasattr(self.connection, 'real_nickname'):
            raise IrcStillConnectingError("I don't know my nickname yet: I'm still connecting.")
        return self.connection.get_nickname()

    @nickname.setter
    def nickname(self, value):
        """Tell the server to change the nickname that it uses for me."""
        self.connection.nick(value)

    @property
    def realname(self):
        """The realname that the server currently has for me."""
        try:
            sn = self.nickname
            if len(sn) > MAX_NICKNAME_LENGTH:
                raise IrcNicknameTooLongError("WTF")
            return self.call_whois_and_wait_for_response(sn).split(' ', 4)[-1]
        except (AttributeError, TimeoutError):
            print("%s %-20s: %-10s: There is no realname: I'm offline." % (s_now(), self.irc_server, self.nickname))
            return None

    @property
    def connected(self):
        """Am I connected to the server?"""
        return self.connection.is_connected()

    @property
    def joined(self):
        """Am I a member of this channel?"""
        return ([] == [ch for ch in self.initial_channels if ch not in self.channels])

    def _on_whoisuser(self, _c=None, e=None):
        """Triggered when the event-handler receives RPL_WHOISUSER."""
        nick = e.arguments[0]  # Also, channel = e.target
        self.__whois_results_dct[nick] = ' '.join([r for r in e.arguments])

    def _on_nosuchnick(self, _c, e):
        """Triggered when the event-handler receives ERR_NOSUCHNICK."""
        self.__whois_results_dct[e.arguments[0]] = None

    def on_nicknameinuse(self, _c, _e):
        """Triggered when the event-handler receives ERR_NICKNAMEINUSE."""
        if self.strictly_nick:
            self.connection.disconnect()
            self.err = IrcDuplicateNicknameError("%s was already in use at %s" % (self.nickname, self.irc_server))
        else:
            new_nick = 'R' + generate_random_alphanumeric_string(MAX_NICKNAME_LENGTH - 1)
            self.nickname = new_nick

    def on_welcome(self, c, _e):
        """Triggered when the event-handler receives RPL_WELCOME."""
        for ch in self.initial_channels:
            c.join(ch)

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

    def call_whois_and_wait_for_response(self, user, timeout=DEFAULT_WHOIS_TIMEOUT):
        """Call /whois, and use __whois_request_cache to get answer."""
        if type(user) is not str or len(user) < 2 or not user[0].isalpha():
            raise IrcBadNicknameError("Nickname %s is bad (non-string, empty, starts with a digit, too short)" % str(user))
        # if len(user) > MAX_NICKNAME_LENGTH:
        #     raise IrcNicknameTooLongError("Nickname %s is too long" % user)
        if self.__whois_request_cache.get(user) is None:
            self.__whois_request_c_hits_v_misses[1] += 1
            try:
                self.__whois_request_cache.set(user, self.__call_whois_and_wait_for_response(user, timeout))
            except TimeoutError:
                return None
        else:
            self.__whois_request_c_hits_v_misses[0] += 1
            if self.__whois_request_c_hits_v_misses[0] % 2000 == 0:
                hits, misses = self.__whois_request_c_hits_v_misses
                percentage = hits * 100 / (hits + misses)
                print("%s %-20s: %-10s: Our whois cache has a %d%% hit rate" % (s_now(), self.irc_server, self.nickname, percentage))
        return self.__whois_request_cache.get(user)

    def __call_whois_and_wait_for_response(self, user, timeout):
        """Sends a /whois to the server. Waits for a response. Returns the response."""
        if type(user) is not str or len(user) < 2 or not user[0].isalpha():
            raise IrcBadNicknameError("Nickname %s is bad (non-string, empty, starts with a digit, too short)" % str(user))
        # if len(user) > MAX_NICKNAME_LENGTH:
        #     raise IrcNicknameTooLongError("Nickname is too long")
#        with self.__whois_request_cache_mutex:
        if not self.connected:
            raise TimeoutError("I cannot /whois, because I am not connected. Please connect to the server and try again.")
        self.connection.whois(user)  # Send request to the IRC server
        for _ in range(0, timeout * 10):
            self.reactor.process_once()  # Process incoming & outgoing events w/ IRC server
            try:
                return self.__whois_results_dct[user]  # Results, sent by IRC server, will be recorded when _no_whoisuser() is triggered
            except KeyError:
                sleep(A_TICK)  # Still waiting for answer
        raise TimeoutError("Timeout while waiting for answer to /whois %s" % user)

    def privmsg(self, user, msg):
        """Send a private message on IRC. Then, pause; don't overload the server."""
        if type(user) is not str or len(user) < 2 or not user[0].isalpha():
            raise IrcBadNicknameError("Nickname %s is bad (non-string, empty, starts with a digit, too short)" % str(user))
        if len(user) > MAX_NICKNAME_LENGTH:
            raise IrcNicknameTooLongError("Nickname %s is too long" % user)
        if msg in (None, '') or type(msg) is not str or len([c for c in msg if ord(c) < 32 or ord(c) >= 128]) > 0:
            raise IrcPrivateMessageContainsBadCharsError("I cannot send this message: it is empty and/or contains characters that IRC wouldn't like. => %s" % str(msg))
        if len(msg) + len(user) > MAX_PRIVMSG_LENGTH:
            raise IrcPrivateMessageTooLongError("I cannot send this message: the combined length of the nickname and the message would exceed the IRC server's limit.")
        retval = None
        cached_data = user + '///' + msg
        if user not in self.__privmsg_c_hits_dct:
            self.__privmsg_c_hits_dct[user] = 0
        if self.__privmsg_cache.get(cached_data) is None:
            self.__privmsg_cache.set(cached_data, cached_data)
            if self.__privmsg_c_hits_dct[user] > 3:
                print("%s %-20s: %-10s: Cached %d x %s=>%s" % (s_now(), self.irc_server, self.nickname, self.__privmsg_c_hits_dct[user], msg, user))
            self.__privmsg_c_hits_dct[user] = 0
            try:
                self.connection.privmsg(user, msg)  # Don't send the same message more than once every N seconds
                retval = len(msg)
            except ServerNotConnectedError:
                print("%s %-20s: %-10s: Can't send msg to %s: server is not connected." % (s_now(), self.irc_server, self.nickname, user))
                retval = -1
            sleep(randint(16, 20) / 10.)  # 20 per 30s... or 2/3 per 1s... or 1s per 3/2... or 1.5 per second.
        else:
            self.__privmsg_c_hits_dct[user] += 1
            retval = 0
            if self.__privmsg_c_hits_dct[user] in (2, 5, 10, 20, 50, 100, 200, 500, 1000):
                print("%s %-20s: %-10s: Cached %d x %s=>%s" % (s_now(), self.irc_server, self.nickname, self.__privmsg_c_hits_dct[user], msg, user))
            else:
                pass
        return retval


class DualQueuedFingerprintedSingleServerIRCBotWithWhoisSupport(SingleServerIRCBotWithWhoisSupport):
    """Dual-queued IRC server with Whois support.

    This class lets the programmer connect, join, etc. to an IRC server and
    send&receive messages via LIFO queues. The processes run in the background.
    The goal is to make it easy to send and receive private messages. At
    present, only private messages and /whois are supported.

    Note:
        Don't park on railroad tracks.

    Args:
        channels (list of str): Channels to join, each beginning with '#'.
        nickname (str): Nickname to use when joining.
        irc_server (str): URL of IRC server.
        port (int): Port# to use.

    """

    def __init__(self, channels, nickname, irc_server, port, strictly_nick):
        if channels is None or type(channels) not in (list, tuple):
            raise IrcBadChannelNameError(str(channels) + " is a defective list of channels.")
        for ch in channels:
            if type(ch) is not str or len(ch) < 2 or ' ' in ch or ch[0] != '#':
                raise IrcBadChannelNameError("%s is a defective channel name." % ch)
            if len(ch) > MAX_CHANNEL_LENGTH:
                raise IrcChannelNameTooLongError(str(ch) + " is too long")
        self.__received_queue = Queue()
        self.__transmit_queue = Queue()
        self.__strictly_nick = strictly_nick
        self.__wannaquit = False
        self.__wannaquit_lock = ReadWriteLock()
        super().__init__(channels, nickname, generate_fingerprint(nickname), irc_server, port, strictly_nick)
        self.__my_tx_thread = Thread(target=self._tx_start, daemon=True)
        self.__my_tx_thread.start()

    def _tx_start(self):
        """Start the transmission buffer thread."""
        while not self.wannaquit:
            try:
                user, msg = self.transmit_queue.get_nowait()
                self.privmsg(user, msg)
            except Empty:
                sleep(A_TICK)
        try:
            self.disconnect('Bye')
        except Exception as e:  # pylint: disable=broad-exception-caught
            print("%s %-20s: %-10s: Exception occurred while disconnecting:" % (s_now(), self.irc_server, self.nickname), e)

    def quit(self):  # Do we need this?
        """Quit this bot."""
        self.wannaquit = True
        self.__my_tx_thread.join()

    @property
    def strictly_nick(self):
        return self.__strictly_nick

    @property
    def wannaquit(self):
        self.__wannaquit_lock.acquire_read()
        try:
            retval = self.__wannaquit
            return retval
        finally:
            self.__wannaquit_lock.release_read()

    @wannaquit.setter
    def wannaquit(self, value):
        self.__wannaquit_lock.acquire_write()
        try:
            self.__wannaquit = value
        finally:
            self.__wannaquit_lock.release_write()

    @property
    def received_queue(self):
        return self.__received_queue

    @property
    def transmit_queue(self):
        return self.__transmit_queue

    def on_privmsg(self, c, e):  # @UnusedVariable
        """Process on_privmsg event from the bot's reactor IRC thread."""
        if e is None:  # e is event
            raise AttributeError("act_on_msg_from_irc() has an e of None")
        if e.source:
            sender = e.source.split('@')[0].split('!')[0]
        else:
            sender = None
        txt = e.arguments[0]
        self.received_queue.put((sender, txt))

    def get(self, block=True, timeout=None):
        return self.received_queue.get(block, timeout)

    def get_nowait(self):
        return self.received_queue.get_nowait()

    def empty(self):
        return self.received_queue.empty()

    @property
    def not_empty(self):
        return self.received_queue.not_empty

    def put(self, user, msg):
        """Send private message (of text) to the specified user."""
        if type(user) is not str or len(user) < 2 or not user[0].isalpha():
            raise IrcBadNicknameError("Nickname %s is bad (non-string, empty, starts with a digit, too short)" % str(user))
        if len(user) > MAX_NICKNAME_LENGTH:
            raise IrcNicknameTooLongError("Nickname %s is too long" % user)
        if msg in (None, '') or type(msg) is not str or len([c for c in msg if ord(c) < 32 or ord(c) >= 128]) > 0:
            raise IrcPrivateMessageContainsBadCharsError("I cannot send this message: it is empty and/or contains characters that IRC wouldn't like. => %s" % str(msg))
        if len(msg) + len(user) > MAX_PRIVMSG_LENGTH:
            raise IrcPrivateMessageTooLongError("I cannot send this message: the combined length of the nickname and the message would exceed the IRC server's limit.")
        self.transmit_queue.put((user, msg))

