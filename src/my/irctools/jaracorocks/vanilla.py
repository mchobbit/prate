# -*- coding: utf-8 -*-
"""Classes and functions from (or inspired by) Jaraco's IRC project

Created on Jan 22, 2025

@author: mchobbit

This module contains the class VanillaBot, which wraps around
DualQueuedFingerprintedSingleServerIRCBotWithWhoisSupport and
provides an enhanced IRC bot that runs in the background.

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
from time import sleep
from queue import Queue
from my.classes.readwritelock import ReadWriteLock
from threading import Thread
from my.irctools.cryptoish import generate_fingerprint
import datetime
import validators

from my.stringtools import generate_irc_handle, generate_random_alphanumeric_string  # @UnusedImport
from my.classes.exceptions import IrcFingerprintMismatchCausedByServer, IrcInitialConnectionTimeoutError, IrcBadServerNameError, IrcBadChannelNameError, IrcChannelNameTooLongError, IrcBadServerPortError, \
    IrcStillConnectingError, IrcNicknameTooLongError, IrcJoiningChannelTimeoutError, IrcPartingChannelTimeoutError, IrcRanOutOfReconnectionsError, IrcBadNicknameError, \
    IrcPrivateMessageTooLongError, IrcPrivateMessageContainsBadCharsError, IrcAlreadyDisconnectedError, IrcYouCantUseABotAfterQuittingItError
from my.irctools.jaracorocks import DualQueuedFingerprintedSingleServerIRCBotWithWhoisSupport
from my.globals import MAX_NICKNAME_LENGTH, JOINPARTCHAN_TIMEOUT, MAX_CHANNEL_LENGTH, DEFAULT_WHOIS_TIMEOUT, MAX_PRIVMSG_LENGTH, A_TICK, ENDTHREAD_TIMEOUT


class VanillaBot:
    """Bot for dual-queue IRC bot with fingerprinting and with Whois support.

    The VanillaBot class runs an enhanced IRC bot in the background. It
    reconnects it if it disconnects. It allows for nickname collision
    and can resolve it by reconnecting with a new nick (if wished). It
    offers rudimentary buffered private message sending and receiving.
    It offers up a userlist of all users in all channels that the bot
    has joined.

    Note:
        There is no did-the-message-arrive-or-not checking.

    Args:

        channels (list of str): The channels to join, e.g. ['#test','#test2']
        nickname (str): The ideal nickname. The actual nickname is
            that one, unless there's a collision reported by the
            server. In that case, a new nick will be chosen at
            random & submitted if strictly_nick is False.
            The current nick is always available from the attribute
            .nickname .
        irc_server (str): The server, e.g. irc.dal.net
        port (int): The port# to use.
        startup_timeout (int): How long should we wait to connect?
        maximum_reconnections (int): Maximum number of permitted
            reconnection attempts.
        autoreconnect (bool): If True, autoreconnect should a
            disconnection occur. If False, don't.
        strictly_nick (bool): If True, and the nickname is
            rejected by the IRC server for being a dupe, abort.

    Example:
        $ bot = VanillaBot(['#prate'], 'mac1', 'cinqcent.local', 6667, 30, 2, True, True)
        $ bot.put("mac1", "WORD")
        $ bot.get()
        ("mac1", "WORD")
        $ bot.quit()

"""

    def __init__(self, channels:list, nickname:str, irc_server:str, port:int,
                 startup_timeout:int, maximum_reconnections:int, autoreconnect:bool, strictly_nick:bool):
        if startup_timeout is None or type(startup_timeout) is not int or startup_timeout <= 0:
            raise ValueError(str(startup_timeout) + " is a goofy startup_timeout. Fix it.")
        if channels is None or type(channels) not in (list, tuple):
            raise IrcBadChannelNameError(str(channels) + " needs to be a list or tuple of channels, please.")
        for ch in channels:
            if type(ch) is not str or len(ch) < 2 or ' ' in ch or ch[0] != '#':
                raise IrcBadChannelNameError("%s is a defective channel name." % ch)
            if len(ch) > MAX_CHANNEL_LENGTH:
                raise IrcChannelNameTooLongError(str(ch) + " is too long")
        if nickname is None or len(nickname) < 2 or not nickname[0].isalpha() or ' ' in nickname:
            raise IrcBadNicknameError(str(nickname) + " is a goofy nickname. Fix it.")
        if len(nickname) > MAX_NICKNAME_LENGTH:
            raise IrcNicknameTooLongError(str(nickname) + " is too long. Shorten it.")
        if irc_server is None or type(irc_server) is not str or len(irc_server) < 2 or ' ' in irc_server or validators.url(irc_server) is False:
            raise IrcBadServerNameError(str(irc_server) + "is a goofy IRC server URL. Fix it.")
        if port is None or type(port) is not int or port <= 0:
            raise IrcBadServerPortError(str(port) + " is a goofy port number. Fix it.")
        self.__startup_timeout = startup_timeout
        self.__received_queue = Queue()
        self.__strictly_nick = strictly_nick
        self.__transmit_queue = Queue()
        self.__should_we_quit = False
        self.__should_we_quit_lock = ReadWriteLock()
        self.__initial_channels = channels
        self.__initial_nickname = nickname
        self.__irc_server = irc_server
        self.__port = port
        self.__err = None
        self.__client = None  # Set by self.maintain_server_connection()
        self.__maximum_reconnections = maximum_reconnections
        self.__should_we_quit = False
        self.__autoreconnect = autoreconnect  # Set to False to suspend autoreconnection. Set to True to resume autoreconnecting.
        self.__autoreconnect_lock = ReadWriteLock()
        self.__noof_reconnections = 0
        self.__noof_reconnections_lock = ReadWriteLock()
        self.__my_client_start_thread = Thread(target=self._client_start, daemon=True)
        self.__my_main_thread = Thread(target=self._main_loop, daemon=True)
        self.__my_client_start_thread.start()
        self.__my_main_thread.start()
        self.__quitted = False
        starttime = datetime.datetime.now()
        # Make initial attempt to join IRC server
        while not self.ready and not self.should_we_quit and (self._client is None or self._client.err is None) and (datetime.datetime.now() - starttime).seconds < self.__startup_timeout:
            sleep(A_TICK)
        if not self.ready:
            _ = [sleep(A_TICK) for __ in range(0, 50) if self.err is None]
            if self._client is not None and self._client.err is not None:
                self.quit()
                raise self._client.err
            elif self.err is not None:
                self.quit()
                raise self.err
            else:
                self.quit(yes_even_the_reactor_thread=True)
                raise IrcInitialConnectionTimeoutError("%s completely failed to connect to %s" % (self.initial_nickname, self.irc_server))

    @property
    def quitted(self):
        """Have I run my course, and have I been terminated (by a self.quit() call)?"""
        return self.__quitted

    def reconnect_server_connection(self, my_nick):
        """Reconnect to the IRC server."""
        if self._client is not None:
            print("WARNING --- you're asking me to reconnect, but I'm already connected. That is a surprise.")
            try:
                self._client.disconnect("Bye")
            except Exception as e:  # pylint: disable=broad-exception-caught
                print("reconnect_server_connection() caught an exception:", e)
            self._client = None
        self.noof_reconnections += 1
        self._client = DualQueuedFingerprintedSingleServerIRCBotWithWhoisSupport(
            channels=self.initial_channels,
            nickname=my_nick,
            irc_server=self.irc_server,
            port=self.port,
            strictly_nick=self.strictly_nick)
        starting_datetime = datetime.datetime.now()
        if self._client.err:
            raise self._client.err
        while not self.ready and (datetime.datetime.now() - starting_datetime).seconds < self.__startup_timeout:
            sleep(A_TICK)
        if not self.ready:
            raise IrcInitialConnectionTimeoutError("After %d seconds, we still aren't connected to server; aborting!" % self.__startup_timeout)
        if generate_fingerprint(self._client.nickname) != self._client.realname:
            raise IrcFingerprintMismatchCausedByServer("The server detected a nickname collision and changed mine, causing my fingerprint to be invalid.")

    @property
    def irc_server(self):
        """URL of the IRC server."""
        return self.__irc_server

    @property
    def initial_channels(self):
        """The initial channels that I was told to join."""
        return self.__initial_channels

    @property
    def strictly_nick(self):
        """Should I insist on using the given nickname & not negotiating another if a collision occurs?"""
        return self.__strictly_nick

    @property
    def port(self):
        """Port# to use when connecting to the IRC server."""
        return self.__port

    @property
    def err(self):
        """The exception, if any, that occurred during the main background loop."""
        return self.__err

    @err.setter
    def err(self, value):
        self.__err = value

    @property
    def channels(self):
        """List of the IRC channels that I've joined and am in now."""
        return self._client.channels

    def join(self, channel):
        """Join this IRC channel."""
        self._client.connection.join(channel)
        for _ in range(0, JOINPARTCHAN_TIMEOUT * 10):
            sleep(A_TICK)
            if channel in list(self.channels.keys()):
                return
        raise IrcJoiningChannelTimeoutError("%s --- %s timed out while joining #%d" % (self.irc_server, self.nickname, channel))

    def part(self, channel):
        """Leave this IRC channel."""
        self._client.connection.part(channel)
        for _ in range(0, JOINPARTCHAN_TIMEOUT * 10):
            sleep(A_TICK)
            if channel not in list(self.channels.keys()):
                return
        raise IrcPartingChannelTimeoutError("%s --- %s timed out while joining #%d" % (self.irc_server, self.nickname, channel))

    @property
    def users(self):
        """Get list of all users in all my channels."""
        lst = []
        for ch in self.channels:
            try:
                for nickname in [str(u) for u in self._client.channels[ch].users()]:
                    if nickname not in lst:
                        lst += [nickname]
            except (KeyError, AttributeError) as e:
                if ch not in self._client.channels:
                    print("I (%s on %s) am not in %s. Therefore, I cannot obtain a list of its users." % (self.nickname, self.irc_server, ch))
                    # raise IrcIAmNotInTheChannelError("I am not in %s. Therefore, I cannot obtain a list of its users." % ch) from e
                else:
                    raise e
        return lst

    def _client_start(self):
        """Start a Jaraco-ish bot class instance."""
        while not self._client and not self.should_we_quit:
            sleep(A_TICK)
        while self._client and not self.should_we_quit:
            try:
                self._client.start()
            except (ValueError, OSError, AttributeError):  # as e:
#                print("Client is stopping, I think:", e)
                sleep(A_TICK)

    def _main_loop(self):
        """The main background loop. It maintains our connection with the IRC server."""
        have_we_ever_successfully_connected = False
        my_nick = self.initial_nickname
        while not self.should_we_quit and (self.maximum_reconnections is None or self.noof_reconnections < self.maximum_reconnections):
            # if randint(0, 10) == 0:
            #     print("%s is still trying to connect" % self.irc_server)
            sleep(A_TICK)
            if self.should_we_quit is False and self._client is None and self.autoreconnect is True:
                self.noof_reconnections += 1
                try:
                    self.reconnect_server_connection(my_nick)  # If its fingerprint is wonky, quit&reconnect.
#                    print("**** CONNECTED TO %s AS %s ****" % (self.irc_server, my_nick))
                    self.noof_reconnections = 0
                    have_we_ever_successfully_connected = True
                except IrcInitialConnectionTimeoutError:
                    pass  # print("Timeout error. Retrying.")
                except IrcFingerprintMismatchCausedByServer:
                    pass  # print("The IRC server %s changed my nickname from %s to %s, to prevent a collision." % (self.irc_server, my_nick, self.nickname))
            # channels_weve_dropped_out_of = [ch for ch in self.channels if ch not in self._client.channels]
            # if self._client.connected and channels_weve_dropped_out_of != []:
            #     print("WARNING -- we dropped out of", channels_weve_dropped_out_of)
            #     for ch in channels_weve_dropped_out_of:
            #         try:
            #             self._client.connection.join(ch)
            #             print("Rejoined %s" % ch)
            #         except Exception as e:  # pylint: disable=broad-exception-caught
            #             print("I tried and failed to rejoin", ch, "==>", e)
            if self._client is not None and my_nick != self._client.nickname:  # This means we RECONNECTED after fixing our nickname.
                if self.strictly_nick:
                    print("Not reconnecting: our preferred nick is unavailable.")
                    self.err = self._client.err
                    self.should_we_quit = True
                else:
                    my_nick = self._client.nickname  # print("*** RECONNECTED AS %s" % self._client.nickname)
        if self.maximum_reconnections is not None and self.noof_reconnections >= self.maximum_reconnections:
            if self.err is None:
                if have_we_ever_successfully_connected:
                    self.err = IrcRanOutOfReconnectionsError("%s disconnected %d times. That's enough. It's over. This connection has died and I'll not resurrect it. Instead, I'll wait until this bot is told to quit; then, I'll exit/join/whatever." % (self.irc_server, self.noof_reconnections))
                else:
                    self.err = IrcInitialConnectionTimeoutError("We tried %d times to connect to %s. We failed." % (self.noof_reconnections, self.irc_server))
            else:
                print("Client had error:", self.err)
        while not self.should_we_quit:
            sleep(A_TICK)

    @property
    def initial_nickname(self):
        """What was the initial nickname that I was told to use?"""
        return self.__initial_nickname

    @property
    def fingerprint(self):
        """What is the realname (AKA fingerprint) according to the IRC server's /whois record?"""
        return self._client.realname

    @property
    def _client(self):
        """Our instance of a Jaraco-style bot that runs in the background & talks to the IRC server."""
        return self.__client

    @_client.setter
    def _client(self, value):
        self.__client = value

    @property
    def noof_reconnections(self):
        """How many reconnections have already been attempted?"""
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
        """How many seconds should elapse before the initial connection attempt is reported as a failure?"""
        return self.__startup_timeout

    @property
    def received_queue(self):
        """FIFO queue of private messages that were sent to my nickname at the IRC server by other users."""
        return self.__received_queue

    @property
    def transmit_queue(self):
        """FIFO queue of private messages that I have been told to send to other users on the IRC server."""
        return self.__transmit_queue

    @property
    def autoreconnect(self):
        """Should I autoreconnect?"""
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
        """Have I been instructed to start quitting?"""
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

    def whois(self, user, timeout=DEFAULT_WHOIS_TIMEOUT):
        """Obtain the /whois record of the specified user."""
        if self.quitted:
            raise IrcYouCantUseABotAfterQuittingItError("%s was quitted. You can't use it after that." % self.irc_server)
        if type(user) is not str or len(user) < 2 or not user[0].isalpha():
            raise IrcBadNicknameError("Nickname %s is bad (non-string, empty, starts with a digit, too short)" % str(user))
        return self._client.call_whois_and_wait_for_response(user, timeout)

    @property
    def nickname(self):
        """What is my current nickname on the IRC server?"""
        return self._client.nickname

    def empty(self):  # FUNCTION
        """Is my queue (of private messages from the IRC server's users) empty?"""
        return self._client.empty()

    @property
    def not_empty(self):  # ATTRIBUTE
        """Is my queue (of private messages from the IRC server's users) not empty?"""
        return self._client.not_empty

    def put(self, user, msg):
        """Send a private message to the specified user on the IRC server."""
        if type(user) is not str or len(user) < 2 or not user[0].isalpha():
            raise IrcBadNicknameError("Nickname %s is bad (non-string, empty, starts with a digit, too short)" % str(user))
        if len(user) > MAX_NICKNAME_LENGTH:
            raise IrcNicknameTooLongError("Nickname %s is too long" % user)
        if self._client is None or not self._client.ready:
            raise IrcStillConnectingError("Try again when I'm ready (when self.ready==True)")
        if msg in (None, '') or type(msg) is not str or len([c for c in msg if ord(c) < 32 or ord(c) >= 128]) > 0:
            raise IrcPrivateMessageContainsBadCharsError("I cannot send this message: it is empty and/or contains characters that IRC wouldn't like. => %s" % str(msg))
        if len(msg) + len(user) > MAX_PRIVMSG_LENGTH:
            raise IrcPrivateMessageTooLongError("I cannot send this message: the combined length of the nickname and the message would exceed the IRC server's limit.")
        return self._client.put(user, msg)

    def get(self, block=True, timeout=None):
        """Retrieve the next private message from our queue, sent by a user on the IRC server."""
        if self._client is None or not self._client.ready:
            raise IrcStillConnectingError("Try again when I'm ready (when self.ready==True)")
        return self._client.get(block, timeout)

    def get_nowait(self):
        """Retrieve the next private message from our queue, sent by a user on the IRC server."""
        if self._client is None or not self._client.ready:
            raise IrcStillConnectingError("Try again when I'm ready (when self.ready==True)")
        return self._client.get_nowait()

    @property
    def maximum_reconnections(self):
        """How many reconnections will the main loop be allowed to attempt to make, if the IRC connection drops?"""
        return self.__maximum_reconnections

    @property
    def ready(self):
        """Is our bot connected to the IRC server and has it joined our desired rooms?"""
        if self._client is None:
            return False
        elif not hasattr(self._client, 'ready'):
            return False
        else:
            return self._client.ready

    def quit(self, yes_even_the_reactor_thread=False, timeout=ENDTHREAD_TIMEOUT):
        """Quit this bot."""
        if self.quitted:
            raise IrcAlreadyDisconnectedError("Trying to quit %s twice. This should be unnecessary." % self.irc_server)
        self.autoreconnect = False
        self.should_we_quit = True
        self.__my_main_thread.join(timeout=timeout)
        if self._client:
            self._client.reactor.disconnect_all()
            self._client.quit()
            while self._client.connected:
                sleep(A_TICK)
        if yes_even_the_reactor_thread:
            self.__my_client_start_thread.join(timeout)  # jaraco
        self.__quitted = True

