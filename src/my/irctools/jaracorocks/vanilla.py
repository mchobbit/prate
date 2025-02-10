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
from random import randint
import irc.bot
from time import sleep
from my.classes.exceptions import MyIrcStillConnectingError, MyIrcInitialConnectionTimeoutError, MyIrcFingerprintMismatchCausedByServer
from my.classes import MyTTLCache
from my.globals import ANTIOVERLOAD_CACHE_TIME, JOINING_IRC_SERVER_TIMEOUT, MAX_PRIVMSG_LENGTH, MAX_NICKNAME_LENGTH
from irc.client import ServerNotConnectedError
from queue import Queue
from my.classes.readwritelock import ReadWriteLock
from threading import Thread
from my.irctools.cryptoish import generate_fingerprint
from _queue import Empty
import datetime
import validators

from my.stringtools import generate_irc_handle, generate_random_alphanumeric_string  # @UnusedImport


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

    def __init__(self, channel, nickname, realname, irc_server, port):
        if None in (channel, nickname, irc_server, port):
            raise ValueError("Do not supply None as a parameter")
        elif type(channel) is not str or channel[0] != '#':
            raise ValueError("channel must begin with a '#'")
        elif type(port) is not int:
            raise ValueError("port must be an integer")
        irc.bot.SingleServerIRCBot.__init__(self, [(irc_server, port)], nickname, realname)
        if type(realname) is not str:
            raise ValueError("Realname should be a string, not", type(realname))
        self.__privmsg_cache = MyTTLCache(ANTIOVERLOAD_CACHE_TIME)  # Don't send the same private message to the same person more than once every ten seconds
        self.__privmsg_c_hits_dct = {}
        self.__whois_request_cache = MyTTLCache(ANTIOVERLOAD_CACHE_TIME)
        self.__whois_request_c_hits_v_misses = [0, 0]
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
        try:
            sn = self.nickname
            if len(sn) > MAX_NICKNAME_LENGTH:
                raise ValueError("WTF")
            return self.call_whois_and_wait_for_response(sn).split(' ', 4)[-1]
        except (AttributeError, TimeoutError):
            print("There is no realname: I'm offline.")
            return None

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
        new_nick = 'R' + generate_random_alphanumeric_string(MAX_NICKNAME_LENGTH - 1)
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
        else:
            c.notice(nick, "Unknown command => " + cmd)

    def call_whois_and_wait_for_response(self, user, timeout=10):
        """Call /whois, and use __whois_request_cache to get answer."""
        if type(user) is not str or len(user) < 2 or not user[0].isalpha() or len(user) > MAX_NICKNAME_LENGTH:
            raise ValueError("Nickname is bad (non-string, empty, starts with a digit, too short, or too long)")
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
                print("Our whois cache has a %d%% hit rate" % percentage)
        return self.__whois_request_cache.get(user)

    def __call_whois_and_wait_for_response(self, user, timeout):
        """Sends a /whois to the server. Waits for a response. Returns the response."""
        if type(user) is not str or len(user) < 2 or not user[0].isalpha() or len(user) > MAX_NICKNAME_LENGTH:
            raise ValueError("Nickname is bad (non-string, empty, starts with a digit, too short, or too long)")
#        with self.__whois_request_cache_mutex:
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
        if type(user) is not str or len(user) < 2 or not user[0].isalpha() or len(user) > MAX_NICKNAME_LENGTH:
            raise ValueError("Nickname is bad (non-string, empty, starts with a digit, too short, or too long)")
        if msg in (None, '') or type(msg) is not str or len([c for c in msg if ord(c) < 32 or ord(c) >= 128]) > 0:
            raise ValueError("I cannot send this message: it is empty and/or contains characters that IRC wouldn't like. =>", msg)
        if len(msg) + len(user) > MAX_PRIVMSG_LENGTH:
            raise ValueError("I cannot send this message: the combined length of the nickname and the message would exceed the IRC server's limit.")
        retval = None
        cached_data = user + '///' + msg
        if user not in self.__privmsg_c_hits_dct:
            self.__privmsg_c_hits_dct[user] = 0
        if self.__privmsg_cache.get(cached_data) is None:
            self.__privmsg_cache.set(cached_data, cached_data)
            if self.__privmsg_c_hits_dct[user] > 3:
                print("Cached %d x %s=>%s" % (self.__privmsg_c_hits_dct[user], msg[:4], user))
            self.__privmsg_c_hits_dct[user] = 0
            try:
                self.connection.privmsg(user, msg)  # Don't send the same message more than once every N seconds
                retval = len(msg)
            except ServerNotConnectedError:
                print("WARNING --- unable to send %s to %s: server is no connected" % (msg, user))
                retval = -1
            sleep(randint(16, 20) / 10.)  # 20 per 30s... or 2/3 per 1s... or 1s per 3/2... or 1.5 per second.
        else:
            self.__privmsg_c_hits_dct[user] += 1
            retval = 0
            if self.__privmsg_c_hits_dct[user] in (2, 5, 10, 20, 50, 100, 200, 500, 1000):
                print("Cached %d x %s=>%s" % (self.__privmsg_c_hits_dct[user], msg[:4], user))
            else:
                pass
        return retval


class DualQueuedSingleServerIRCBotWithWhoisSupport(SingleServerIRCBotWithWhoisSupport):
    """Dual-queued IRC server with Whois support.

    This class lets the programmer connect, join, etc. to an IRC server and
    send&receive messages via LIFO queues. The processes run in the background.
    The goal is to make it easy to send and receive private messages. At
    present, only private messages and /whois are supported.

    Note:
        Don't park on railroad tracks.

    Args:
        channel (str): Channel to join, beginning with '#'.
        nickname (str): Nickname to use when joining.
        irc_server (str): URL of IRC server.
        port (int): Port# to use.

    """

    def __init__(self, channel, nickname, irc_server, port):
        self.__received_queue = Queue()
        self.__transmit_queue = Queue()
        self.__wannaquit = False
        self.__wannaquit_lock = ReadWriteLock()
        super().__init__(channel, nickname, generate_fingerprint(nickname), irc_server, port)
        self.__my_tx_thread = Thread(target=self._tx_start, daemon=True)
        self.__my_tx_thread.start()

    def _tx_start(self):
        """Start the transmission buffer thread."""
        while not self.wannaquit:
            try:
                user, msg = self.transmit_queue.get_nowait()
                self.privmsg(user, msg)
            except Empty:
                sleep(.1)
        try:
            self.disconnect('Bye')
        except Exception as e:  # pylint: disable=broad-exception-caught
            print("Exception occurred while disconnecting:", e)
        print("DualQueuedSingleServerIRCBotWithWhoisSupport is quitting.")

    def quit(self):  # Do we need this?
        """Quit this bot."""
        self.wannaquit = True
        self.__my_tx_thread.join()

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
        if type(user) is not str or len(user) < 2 or not user[0].isalpha() or len(user) > MAX_NICKNAME_LENGTH:
            raise ValueError("Nickname is bad (non-string, empty, starts with a digit, too short, or too long)")
        if msg in (None, '') or type(msg) is not str or len([c for c in msg if ord(c) < 32 or ord(c) >= 128]) > 0:
            raise ValueError("I cannot send this message: it is empty and/or contains characters that IRC wouldn't like. =>", msg)
        if len(msg) + len(user) > MAX_PRIVMSG_LENGTH:
            raise ValueError("I cannot send this message: the combined length of the nickname and the message would exceed the IRC server's limit.")

        self.transmit_queue.put((user, msg))


class BotForDualQueuedSingleServerIRCBotWithWhoisSupport:
    """Bot for dual-queue IRC bot with Whois support.

    This class provides a self-sustaining connection to the IRC server of
    choice. It offers up a simple interface for sending and receiving
    private messages, irrespective of the connecting/disconnecting/
    reconnecting behind the scenes.

    Note:
        This includes very little error-handling & virtually no
        did-the-message-arrive-or-not checking.

    Args:
        channel (str): The channel to join, e.g. #test
        nickname (str): The ideal nickname. The actual nickname is
            that one, unless there's a collision reported by the
            server. In that case, _on_nicknameinuse() will be
            triggered and a new nick will be chosen & submitted.
            The current nick is always available from the attribute
            .nickname .
        irc_server (str): The server, e.g. irc.dal.net
        port (int): The port# to use.
        startup_timeout (int): How long should we wait to connect?
        maximum_reconnections (None): Maximum number of permitted
            reconnection attempts.

    Attributes:
        nickname (str): The current nickname, per the IRC server.

    Example:
        $ bot = BotForDualQueuedSingleServerIRCBotWithWhoisSupport('#prate', 'mac1', 'cinqcent.local', 6667)
        $ while not bot.ready: sleep(1)
        $ bot.put("mac1", "WORD")
        $ bot.get()
        ("mac1", "WORD")

"""

    def __init__(self, channel:str, nickname:str, irc_server:str, port:int,
                 startup_timeout=JOINING_IRC_SERVER_TIMEOUT,
                 maximum_reconnections=None):
        if None in (channel, nickname, irc_server, port):
            raise ValueError("Don't supply None (sounds wrong, I know)")
        if channel is None or type(channel) is not str or len(channel) < 2 or len(channel) > 19 or ' ' in channel or channel[0] != '#':
            raise ValueError(channel, "is a defective channel name. Remove spaces, make sure the first letter is '#', don't make it insanely long, etc.")
        if len(nickname) < 2 or not nickname[0].isalpha() or ' ' in nickname:
            raise ValueError(nickname, "is a goofy nickname. Fix it.")
        if len(nickname) > MAX_NICKNAME_LENGTH:
            raise ValueError(nickname, "is too long. Shorten it.")
        if irc_server is None or type(irc_server) is not str or len(irc_server) < 2 or ' ' in irc_server or validators.url(irc_server) is False:
            raise ValueError(irc_server, "is a goofy IRC server URL. Fix it.")
        if port is None or type(port) is not int or port <= 0:
            raise ValueError(port, "is a goofy port number. Fix it.")
        if startup_timeout is None or type(startup_timeout) is not int or startup_timeout <= 0:
            raise ValueError(startup_timeout, "is a goofy startup_timeout. Fix it.")
        self.__startup_timeout = startup_timeout
        self.__received_queue = Queue()
        self.__transmit_queue = Queue()
        self.__should_we_quit = False
        self.__should_we_quit_lock = ReadWriteLock()
        self.channel = channel
        self.__initial_nickname = nickname
        self.__desired_nickname = nickname
        self.__irc_server = irc_server
        self.__port = port
        self.__client = None  # Set by self.maintain_server_connection()
        self.__maximum_reconnections = maximum_reconnections
        self.__should_we_quit = False
        self.__autoreconnect = True  # Set to False to suspend autoreconnection. Set to True to resume autoreconnecting.
        self.__autoreconnect_lock = ReadWriteLock()
        self.__noof_reconnections = 0
        self.__noof_reconnections_lock = ReadWriteLock()
        self.__my_main_thread = Thread(target=self._main_loop, daemon=True)
        self.__my_client_start_thread = Thread(target=self._client_start, daemon=True)
        self.__my_main_thread.start()
        self.__my_client_start_thread.start()

    @property
    def irc_server(self):
        return self.__irc_server

    @property
    def port(self):
        return self.__port

    @property
    def users(self):
        return list(set([str(u) for u in self.client.channels[self.channel].users()]))

    def _client_start(self):
        while not self.should_we_quit:
            while not self.should_we_quit and not self.client:
                sleep(.1)
            try:
                self.client.start()
            except Exception as e:  # pylint: disable=broad-exception-caught
                print("_client_strt ==>", e)
        print("SingleServerIRCBotWithWhoisSupport is quitting.")

    def _main_loop(self):
        while not self.should_we_quit and (self.maximum_reconnections is None or self.noof_reconnections < self.maximum_reconnections):
            self.main_service_function()
        if self.maximum_reconnections is not None and self.noof_reconnections >= self.maximum_reconnections:
            print("We've reconnected %d times. That's enough. It's over. This connection has died and I'll not resurrect it. Instead, I'll wait until this bot is told to quit; then, I'll exit/join/whatever.")
        while not self.should_we_quit:
            sleep(.1)
        print("Quitting. Huzzah.")

    def main_service_function(self):
        """Do something while I'm connected."""
        sleep(.1)
        if self.client is None and self.autoreconnect is True:
            try:
                self.reconnect_server_connection()  # If its fingerprint is wonky, quit&reconnect.
                print("**** CONNECTED TO %s AS %s ****" % (self.irc_server, self.desired_nickname))
            except (MyIrcInitialConnectionTimeoutError, MyIrcFingerprintMismatchCausedByServer) as e:
                print("_main_loop() -->", str(e)[:48], '...')
                print("Let's keep looping and/or reconnecting")
            else:
                pass
        if self.client.connected and self.channel not in self.client.channels:
            print("WARNING -- we dropped out of %s" % self.channel)
            try:
                self.client.connection.join(self.channel)
            except Exception as e:  # pylint: disable=broad-exception-caught
                print("I tried and failed to rejoin the room. ==>", e)
        if self.client is not None and self.desired_nickname != self.client.nickname:  # This means we RECONNECTED after fixing our nickname.
            self.desired_nickname = self.client.nickname
            print("*** RECONNECTED AS %s" % self.client.nickname)

    @property
    def initial_nickname(self):
        return self.__initial_nickname

    @property
    def desired_nickname(self):
        return self.__desired_nickname

    @desired_nickname.setter
    def desired_nickname(self, value):
        self.__desired_nickname = value

    @property
    def client(self):
        return self.__client

    @client.setter
    def client(self, value):
        self.__client = value

    @property
    def noof_reconnections(self):
        self.__noof_reconnections_lock.acquire_read()
        try:
            retval = self.__noof_reconnections
            return retval
        finally:
            self.__noof_reconnections_lock.release_read()

    @noof_reconnections.setter
    def noof_reconnections(self, value):
        self.__noof_reconnections_lock.acquire_write()
        try:
            self.__noof_reconnections = value
        finally:
            self.__noof_reconnections_lock.release_write()

    @property
    def startup_timeout(self):
        return self.__startup_timeout

    @property
    def received_queue(self):
        return self.__received_queue

    @property
    def transmit_queue(self):
        return self.__transmit_queue

    @property
    def autoreconnect(self):
        self.__autoreconnect_lock.acquire_read()
        try:
            retval = self.__autoreconnect
            return retval
        finally:
            self.__autoreconnect_lock.release_read()

    @autoreconnect.setter
    def autoreconnect(self, value):
        self.__autoreconnect_lock.acquire_write()
        try:
            self.__autoreconnect = value
        finally:
            self.__autoreconnect_lock.release_write()

    @property
    def should_we_quit(self):
        self.__should_we_quit_lock.acquire_read()
        try:
            retval = self.__should_we_quit
            return retval
        finally:
            self.__should_we_quit_lock.release_read()

    @should_we_quit.setter
    def should_we_quit(self, value):
        self.__should_we_quit_lock.acquire_write()
        try:
            self.__should_we_quit = value
        finally:
            self.__should_we_quit_lock.release_write()

    def whois(self, user, timeout=10):
        if type(user) is not str or len(user) < 2 or not user[0].isalpha() or len(user) > MAX_NICKNAME_LENGTH:
            raise ValueError("Nickname is bad (non-string, empty, starts with a digit, too short, or too long)")
        return self.client.call_whois_and_wait_for_response(user, timeout)

    @property
    def nickname(self):
        return self.client.nickname

    def empty(self):
        return self.client.empty()

    @property
    def not_empty(self):
        return self.client.not_empty

    def put(self, user, msg):
        if type(user) is not str or len(user) < 2 or not user[0].isalpha() or len(user) > MAX_NICKNAME_LENGTH:
            raise ValueError("Nickname is bad (non-string, empty, starts with a digit, too short, or too long)")
        if self.client is None or not self.client.ready:
            raise MyIrcStillConnectingError("Try again when I'm ready (when self.ready==True)")
        if msg in (None, '') or type(msg) is not str or len([c for c in msg if ord(c) < 32 or ord(c) >= 128]) > 0:
            raise ValueError("I cannot send this message: it is empty and/or contains characters that IRC wouldn't like. =>", msg)
        if len(msg) + len(user) > MAX_PRIVMSG_LENGTH:
            raise ValueError("I cannot send this message: the combined length of the nickname and the message would exceed the IRC server's limit.")
        return self.client.put(user, msg)

    def get(self, block=True, timeout=None):
        if self.client is None or not self.client.ready:
            raise MyIrcStillConnectingError("Try again when I'm ready (when self.ready==True)")
        return self.client.get(block, timeout)

    def get_nowait(self):
        if self.client is None or not self.client.ready:
            raise MyIrcStillConnectingError("Try again when I'm ready (when self.ready==True)")
        return self.client.get_nowait()

    @property
    def maximum_reconnections(self):
        return self.__maximum_reconnections

    @property
    def ready(self):
        if self.client is None:
            return False
        elif not hasattr(self.client, 'ready'):
            return False
        else:
            return self.client.ready

    def reconnect_server_connection(self):
        print("*** Connecting to %s as %s  ***" % (self.irc_server, self.desired_nickname))
        if self.client is not None:
            print("WARNING --- you're asking me to reconnect, but I'm already connected. That is a surprise.")
            try:
                self.client.disconnect("Bye")
            except Exception as e:  # pylint: disable=broad-exception-caught
                print("reconnect_server_connection() caught an exception:", e)
            self.client = None
        self.noof_reconnections += 1
        self.client = DualQueuedSingleServerIRCBotWithWhoisSupport(channel=self.channel, nickname=self.desired_nickname,
            irc_server=self.irc_server,
            port=self.port)
        starting_datetime = datetime.datetime.now()
        while not self.client.ready and (datetime.datetime.now() - starting_datetime).seconds < self.__startup_timeout:
            sleep(.1)
        if not self.ready:
            raise MyIrcInitialConnectionTimeoutError("After %d seconds, we still aren't connected to server; aborting!" % self.__startup_timeout)
        if generate_fingerprint(self.client.nickname) != self.client.realname:
            raise MyIrcFingerprintMismatchCausedByServer("My fingerprint no longer matches my username. This may indicate that the server changed my nickname and didn't tell me. Please try again, with a different nickname.")

    def transmit_this_data(self, data_to_transmit):
        (user, message) = data_to_transmit
        self.client.put(user, message)

    def quit(self):  # Do we need this?
        """Quit this bot."""
        self.autoreconnect = False
        self.should_we_quit = True
        # if self.client:
        #     self.client.shut_down_threads()
        self.__my_main_thread.join()  # print("Joining server thread")

####################################################################################


if __name__ == "__main__":

    ircbot = SingleServerIRCBotWithWhoisSupport(channel="#prate", nickname='clyde', realname='ccllyyddee', irc_server='cinqcent.local', port=6667)
    ircbot.connect("cinqcent.local", 6667, "clyde")
    ircbot.start()
