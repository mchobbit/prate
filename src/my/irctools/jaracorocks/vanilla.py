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
    IrcPrivateMessageTooLongError, IrcPrivateMessageContainsBadCharsError
from my.irctools.jaracorocks import DualQueuedFingerprintedSingleServerIRCBotWithWhoisSupport, SingleServerIRCBotWithWhoisSupport
from my.globals import MAX_NICKNAME_LENGTH, SENSIBLE_TIMEOUT, MAX_CHANNEL_LENGTH, DEFAULT_WHOIS_TIMEOUT, MAX_PRIVMSG_LENGTH


class VanillaBot:
    """Bot for dual-queue IRC bot with fingerprinting and with Whois support.

    This class provides a self-sustaining connection to the IRC server of
    choice. It offers up a simple interface for sending and receiving
    private messages, irrespective of the connecting/disconnecting/
    reconnecting behind the scenes.

    Note:
        This includes very little error-handling & virtually no
        did-the-message-arrive-or-not checking.

    Args:
        channels (list of str): The channels to join, e.g. #test
        nickname (str): The ideal nickname. The actual nickname is
            that one, unless there's a collision reported by the
            server. In that case, _on_nicknameinuse() will be
            triggered and a new nick will be chosen & submitted.
            The current nick is always available from the attribute
            .nickname .
        irc_server (str): The server, e.g. irc.dal.net
        port (int): The port# to use.
        startup_timeout (int): How long should we wait to connect?
        maximum_reconnections (int): Maximum number of permitted
            reconnection attempts.
        strictly_nick (bool): If True, and the nickname is
            rejected by the IRC server for being a dupe, abort.
        autoreconnect (bool): If True, autoreconnect should a
            disconnection occur. If False, don't.

    Attributes:
        nickname (str): The current nickname, per the IRC server.

    Example:
        $ bot = BotForDualQueuedSingleServerIRCBotWithWhoisSupport('#prate', 'mac1', 'cinqcent.local', 6667)
        $ while not bot.ready: sleep(1)
        $ bot.put("mac1", "WORD")
        $ bot.get()
        ("mac1", "WORD")

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
        self.__my_main_thread = Thread(target=self._main_loop, daemon=True)
        self.__my_client_start_thread = Thread(target=self._client_start, daemon=True)
        self.__my_main_thread.start()
        self.__my_client_start_thread.start()
        starttime = datetime.datetime.now()
        while not self.ready and (self._client is None or self._client.err is None) and (datetime.datetime.now() - starttime).seconds < self.__startup_timeout:
            sleep(.1)
        if not self.ready:
            self.quit()
            if self._client and self._client.err:
                raise self._client.err
            else:
                raise IrcInitialConnectionTimeoutError("%s completely failed to connect to %s" % (self.initial_nickname, self.irc_server))

    def reconnect_server_connection(self, my_nick):
#        print("*** Connecting to %s as %s  ***" % (self.irc_server, my_nick))
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
            sleep(.1)
        if not self.ready:
            raise IrcInitialConnectionTimeoutError("After %d seconds, we still aren't connected to server; aborting!" % self.__startup_timeout)
        if generate_fingerprint(self._client.nickname) != self._client.realname:
            raise IrcFingerprintMismatchCausedByServer("The server detected a nickname collision and changed mine, causing my fingerprint to be invalid.")

    @property
    def irc_server(self):
        return self.__irc_server

    @property
    def initial_channels(self):
        return self.__initial_channels

    @property
    def strictly_nick(self):
        return self.__strictly_nick

    @property
    def port(self):
        return self.__port

    @property
    def err(self):
        return self.__err

    @property
    def channels(self):
        return self._client.channels

    def join(self, channel):
        self._client.connection.join(channel)
        for _ in range(0, SENSIBLE_TIMEOUT * 10):
            sleep(.1)
            if channel in list(self.channels.keys()):
                return
        raise IrcJoiningChannelTimeoutError("%s --- %s timed out while joining #%d" % (self.irc_server, self.nickname, channel))

    def part(self, channel):
        self._client.connection.part(channel)
        for _ in range(0, SENSIBLE_TIMEOUT * 10):
            sleep(.1)
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
#         print("SingleServerIRCBotWithWhoisSupport --- entering.")
        while not self.should_we_quit:
            try:
                self._client.start()
            except (ValueError, OSError, AttributeError):
                sleep(.1)

    def _main_loop(self):
        my_nick = self.initial_nickname

        while not self.should_we_quit and (self.maximum_reconnections is None or self.noof_reconnections < self.maximum_reconnections):
            sleep(.1)
            if self.should_we_quit is False and self._client is None and self.autoreconnect is True:
                self.noof_reconnections += 1
                try:
                    self.reconnect_server_connection(my_nick)  # If its fingerprint is wonky, quit&reconnect.
#                    print("**** CONNECTED TO %s AS %s ****" % (self.irc_server, my_nick))
                    self.noof_reconnections = 0
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
                    self.__err = self._client.err
                    self.should_we_quit = True
                else:
                    my_nick = self._client.nickname  # print("*** RECONNECTED AS %s" % self._client.nickname)
        if self.maximum_reconnections is not None and self.noof_reconnections >= self.maximum_reconnections:
            self.__err = IrcRanOutOfReconnectionsError("%s disconnected %d times. That's enough. It's over. This connection has died and I'll not resurrect it. Instead, I'll wait until this bot is told to quit; then, I'll exit/join/whatever." % (self.irc_server, self.noof_reconnections))
        while not self.should_we_quit:
            sleep(.1)

    @property
    def initial_nickname(self):
        return self.__initial_nickname

    @property
    def fingerprint(self):
        return self._client.realname

    @property
    def currentlyexpected_nickname(self):
        return self.__currentlyexpected_nickname

    @currentlyexpected_nickname.setter
    def currentlyexpected_nickname(self, value):
        self.__currentlyexpected_nickname = value

    @property
    def _client(self):
        return self.__client

    @_client.setter
    def _client(self, value):
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

    def whois(self, user, timeout=DEFAULT_WHOIS_TIMEOUT):
        if type(user) is not str or len(user) < 2 or not user[0].isalpha():
            raise IrcBadNicknameError("Nickname is bad (non-string, empty, starts with a digit, too short)")
        return self._client.call_whois_and_wait_for_response(user, timeout)

    @property
    def nickname(self):
        return self._client.nickname

    def empty(self):
        return self._client.empty()

    @property
    def not_empty(self):
        return self._client.not_empty

    def put(self, user, msg):
        if type(user) is not str or len(user) < 2 or not user[0].isalpha():
            raise IrcBadNicknameError("Nickname is bad (non-string, empty, starts with a digit, too short)")
        if len(user) > MAX_NICKNAME_LENGTH:
            raise IrcNicknameTooLongError("Nickname is too long")
        if self._client is None or not self._client.ready:
            raise IrcStillConnectingError("Try again when I'm ready (when self.ready==True)")
        if msg in (None, '') or type(msg) is not str or len([c for c in msg if ord(c) < 32 or ord(c) >= 128]) > 0:
            raise IrcPrivateMessageContainsBadCharsError("I cannot send this message: it is empty and/or contains characters that IRC wouldn't like. => %s" % str(msg))
        if len(msg) + len(user) > MAX_PRIVMSG_LENGTH:
            raise IrcPrivateMessageTooLongError("I cannot send this message: the combined length of the nickname and the message would exceed the IRC server's limit.")
        return self._client.put(user, msg)

    def get(self, block=True, timeout=None):
        if self._client is None or not self._client.ready:
            raise IrcStillConnectingError("Try again when I'm ready (when self.ready==True)")
        return self._client.get(block, timeout)

    def get_nowait(self):
        if self._client is None or not self._client.ready:
            raise IrcStillConnectingError("Try again when I'm ready (when self.ready==True)")
        return self._client.get_nowait()

    @property
    def maximum_reconnections(self):
        return self.__maximum_reconnections

    @property
    def ready(self):
        if self._client is None:
            return False
        elif not hasattr(self._client, 'ready'):
            return False
        else:
            return self._client.ready

    def transmit_this_data(self, data_to_transmit):
        (user, message) = data_to_transmit
        self._client.put(user, message)

    def quit(self):  # Do we need this?
        """Quit this bot."""
        self.autoreconnect = False
#        self._client.disconnect("Bye")
        self.should_we_quit = True
        self.__my_main_thread.join()  # print("Joining server thread")
        self.__my_client_start_thread.join()
        self._client.quit()
        while self._client.connected:
            sleep(.1)
        sleep(1)

####################################################################################


if __name__ == "__main__":

    ircbot = SingleServerIRCBotWithWhoisSupport(channels=["#prate"], nickname='clyde', realname='ccllyyddee', irc_server='cinqcent.local', port=6667)
    ircbot.connect("cinqcent.local", 6667, "clyde")
    ircbot.start()
