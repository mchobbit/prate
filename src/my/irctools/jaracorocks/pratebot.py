# -*- coding: utf-8 -*-
"""PrateBot class code.

Created on Jan 30, 2025

@author: mchobbit

This module contains the code for PrateBot, a Jaraco-class IRC bot to
connect to an IRC server and maintain secure communication channels with
some of its users.

Todo:
    * Better docs

.. _Google Python Style Guide:
   http://google.github.io/styleguide/pyguide.html

.. _Napoleon Style Guide:
   https://sphinxcontrib-napoleon.readthedocs.io/en/latest/example_google.html

Example:


"""

import sys
from threading import Thread
from Crypto.PublicKey import RSA
from my.classes.exceptions import PublicKeyBadKeyError, IrcIAmNotInTheChannelError, IrcStillConnectingError, FernetKeyIsInvalidError, FernetKeyIsUnknownError, \
                IrcNicknameTooLongError, IrcBadNicknameError, IrcYouCantUseABotAfterQuittingItError, IrcPrivateMessageTooLongError, PublicKeyUnknownError

from time import sleep
from my.globals import MY_IP_ADDRESS, MAX_PRIVMSG_LENGTH, MAX_CRYPTO_MSG_LENGTH, A_TICK, STARTUP_TIMEOUT, ENDTHREAD_TIMEOUT, RSA_KEY_SIZE
from my.irctools.cryptoish import generate_fingerprint, squeeze_da_keez, rsa_encrypt, unsqueeze_da_keez, rsa_decrypt, receive_and_decrypt_message
from cryptography.fernet import Fernet
import base64
# from my.classes.readwritelock import ReadWriteLock
from my.classes.homies import HomiesDct
from queue import Queue, Empty
import datetime
from my.stringtools import s_now
from my.irctools.jaracorocks.vanilla import VanillaBot

_REQUEST_PUBLICKEY_ = "He"
_TRANSMIT_PUBLICKEY_ = "TK"
_REQUEST__FERNETKEY_ = "RE"
_TRANSMIT_FERNETKEY_ = "TE"
_REQUEST__IPADDRESS_ = "RP"
_TRANSMIT_IPADDRESS_ = "TP"
_TRANSMITCIPHERTEXT_ = "CX"
_TRANSMIT_PLAINTEXT_ = "PX"


class PrateBot(VanillaBot):
    """Bot for encrypted communication with other IRC users.

    The PrateBot class runs an enhanced IRC bot in the background. It
    reconnects it if it disconnects. It allows for nickname collision
    and can resolve it by reconnecting with a new nick (if wished). It
    offers rudimentary buffered private message sending and receiving.
    It offers up a userlist of all users in all channels that the bot
    has joined. Also, it negotiates public keys, followed by symmetric
    keys, and finally IP addresses. This facilitates secure comms
    between IRC users.

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
        rsa_key (RSA.Key): The RSA key to use.
        startup_timeout (int): How long should we wait to connect?
        maximum_reconnections (int): Maximum number of permitted
            reconnection attempts.
        autoreconnect (bool): If True, autoreconnect should a
            disconnection occur. If False, don't.
        strictly_nick (bool): If True, and the nickname is
            rejected by the IRC server for being a dupe, abort.
        autohandshake (bool): If True, start handshaking ASAP.
            Otherwise, the programmer will have to initiate it.

    Example:
        $ my_rsa_key1 = RSA.generate(RSA_KEY_SIZE)
        $ my_rsa_key2 = RSA.generate(RSA_KEY_SIZE)
        $ bot1 = PrateBot(['#prate'], 'mac1', 'cinqcent.local', 6667, my_rsa_key1, 30, 2, True, True)
        $ bot2 = PrateBot(['#prate'], 'mac2', 'cinqcent.local', 6667, my_rsa_key2, 30, 2, True, True)
        $ sleep(30)
        $ bot1.crypto_put("mac1", "WORD")
        $ bot2.crypto_get()
        ("mac1", "WORD")
        $ bot1.quit()
        $ bot2.quit()

    """

    def __init__(self, channels, nickname, irc_server, port, rsa_key,
                 startup_timeout=STARTUP_TIMEOUT, maximum_reconnections=2,
                 autoreconnect=True, strictly_nick=True, autohandshake=True):
        self.__strictly_nick = strictly_nick
        if rsa_key is None or type(rsa_key) is not RSA.RsaKey:
            raise ValueError(str(rsa_key) + " is a goofy value for an RSA key. Fix it.")
        if type(startup_timeout) is not int or startup_timeout <= 0:
            raise ValueError("Startup_timeout should be a positive integer")
        super().__init__(channels=channels, nickname=nickname, irc_server=irc_server,
                         port=port, startup_timeout=startup_timeout,
                         maximum_reconnections=maximum_reconnections,
                         autoreconnect=autoreconnect, strictly_nick=strictly_nick)
        self.rsa_key = rsa_key
        self.__autohandshake = autohandshake
        self.__homies = HomiesDct()
        self.__crypto_rx_queue = Queue()
        self.__plain_rx_queue = Queue()
        self.__paused = False
        assert(not hasattr(self, '__my_main_thread'))
        assert(not hasattr(self, '__my_main_loop'))
        self.__my_main_thread = Thread(target=self.__my_main_loop, daemon=True)
        self.__my_main_thread.start()

    def __repr__(self):
        class_name = type(self).__name__
        pk = self.rsa_key
        if pk is not None:
            pk = squeeze_da_keez(pk)
            pk = "%s..." % (pk[:16])
        return f"{class_name}channels={self.channels!r}, nickname={self.nickname!r}, irc_server={self.irc_server!r}, \
port={self.port!r}, rsa_key={pk!r}, startup_timeout={self.startup_timeout!r}, maximum_reconnections={self.maximum_reconnections!r}, \
autoreconnect={self.autoreconnect!r}, strictly_nick={self.strictly_nick!r}, autohandshake={self.autohandshake!r})"

    @property
    def autohandshake(self):
        return self.__autohandshake

    @property
    def pubkeys(self):
        retval = []
        for user in [u for u in self.users if u != self.nickname]:
            pubkey = self.homies[user].pubkey
            if pubkey is not None and pubkey not in retval:
                retval += [pubkey]
        return retval

    @property
    def strictly_nick(self):
        return self.__strictly_nick

    @property
    def ready(self):
        try:
            return super().ready
        except AttributeError:
            return False

    def __my_main_loop(self):
        """The main loop of this PrateBot: login, join, handshake (maybe), service messages, and (eventually) signout&quit."""
        while not self.ready and not self.should_we_quit:
            sleep(A_TICK)
        sleep(3)
        while True:
            if self.should_we_quit:
                pass  # print("%s %-26s: %-10s: Quitting before we could finish handshakings." % (s_now(), self.irc_server, self.nickname))
            elif self.paused:
                sleep(A_TICK)
            elif not self.autohandshake:
                break
            else:
                try:
                    self.trigger_handshaking()
                except IrcStillConnectingError:
                    print("%s %-26s: %-10s: I'm not ready for handshaking yet (I'm still connecting)." % (s_now(), self.irc_server, self.nickname))
                except IrcIAmNotInTheChannelError:
                    print("%s %-26s: %-10s: I'm not ready for handshaking yet (I'm not in the channel yet)" % (s_now(), self.irc_server, self.nickname))
                else:
                    print("%s %-26s: %-10s: Handshaking initiated." % (s_now(), self.irc_server, self.nickname))
                    break
        while not self.should_we_quit:
            sleep(A_TICK)
            if self.paused:
                pass
            else:
                try:
                    self.read_messages_from_users()
                except IrcStillConnectingError:
                    pass
                except FernetKeyIsInvalidError:
                    print("%s %-26s: %-10s: fernet key is invalid, allegedly" % (s_now(), self.irc_server, self.nickname))
        print("%s %-26s: %-10s: Main loop is quitting." % (s_now(), self.irc_server, self.nickname))

    def read_messages_from_users(self):
        """Process private messages that other users sent to me via the IRC server."""
        while True:
            try:
                (sender, msg) = super().get_nowait()
            except Empty:
                return
            else:
                if msg.startswith(_REQUEST_PUBLICKEY_):
                    print("%s %-26s: %-10s: request for my pubkey    from %s" % (s_now(), self.irc_server, self.nickname, sender))
                    super().put(sender, "%s%s" % (_TRANSMIT_PUBLICKEY_, squeeze_da_keez(self.rsa_key.public_key())))
                elif msg.startswith(_TRANSMIT_PUBLICKEY_):
                    print("%s %-26s: %-10s: reciprocate my pubkey    to   %s" % (s_now(), self.irc_server, self.nickname, sender))
                    self.homies[sender].irc_server = self.irc_server  # just in case a Harem needs it
                    self.homies[sender].pubkey = unsqueeze_da_keez(msg[len(_TRANSMIT_PUBLICKEY_):])
                    super().put(sender, "%s%s" % (_REQUEST__FERNETKEY_, self.my_encrypted_fernetkey_for_this_user(sender)))
                elif msg.startswith(_REQUEST__FERNETKEY_):
                    print("%s %-26s: %-10s: request for my fernetkey from %s" % (s_now(), self.irc_server, self.nickname, sender))
                    if self.homies[sender].pubkey is None:
                        print("%s %-26s: %-10s: I'm being asked for my fernet key, but I don't have %s's public key yet. I'll ask for it now." % (s_now(), self.irc_server, self.nickname, sender))
                        super().put(sender, "%s%s" % (_REQUEST_PUBLICKEY_, squeeze_da_keez(self.rsa_key.public_key())))
                    else:
#                        print("%s %-26s: %-10s: I'm about to decrypt the fernet key that %s sent me." % (s_now(), self.irc_server, self.nickname, sender))
                        t1 = datetime.datetime.now()
                        dc = rsa_decrypt(base64.b64decode(msg[len(_REQUEST__FERNETKEY_):]), self.rsa_key)
                        t2 = datetime.datetime.now()
                        if (t2 - t1).seconds > 1:
                            print("%s %-26s: %-10s: it took %d seconds to decrypt the fernet key that %s sent me." % (s_now(), self.irc_server, self.nickname, (t2 - t1).seconds, sender))
                        if self.homies[sender].remotely_supplied_fernetkey != dc:
                            print("%s %-26s: %-10s: saving fernetkey receivd from %s" % (s_now(), self.irc_server, self.nickname, sender))
                            self.homies[sender].remotely_supplied_fernetkey = dc
                        super().put(sender, "%s%s" % (_TRANSMIT_FERNETKEY_, self.my_encrypted_fernetkey_for_this_user(sender)))
#                        print("%s %-26s: %-10s: I have encrypted and sent my fernet key to %s." % (s_now(), self.irc_server, self.nickname, sender))
                elif msg.startswith(_TRANSMIT_FERNETKEY_):
                    print("%s %-26s: %-10s: reciprocate my fernetkey to   %s" % (s_now(), self.irc_server, self.nickname, sender))
                    dc = rsa_decrypt(base64.b64decode(msg[len(_TRANSMIT_FERNETKEY_):]), self.rsa_key)
                    if self.homies[sender].remotely_supplied_fernetkey != dc:
                        print("%s %-26s: %-10s: saving his new fernetkey from %s" % (s_now(), self.irc_server, self.nickname, sender))
                        self.homies[sender].remotely_supplied_fernetkey = dc
                    if self.homies[sender].fernetkey is not None:
                        super().put(sender, "%s%s" % (_REQUEST__IPADDRESS_, self.my_encrypted_ipaddr(sender)))
                        print("%s %-26s: %-10s: also I want ur IP address bai %s" % (s_now(), self.irc_server, self.nickname, sender))
                elif msg.startswith(_REQUEST__IPADDRESS_):
                    print("%s %-26s: %-10s: request for my IP addr.  from %s" % (s_now(), self.irc_server, self.nickname, sender))
                    try:
                        new_ipaddr = receive_and_decrypt_message(msg[len(_REQUEST__IPADDRESS_):], self.homies[sender].fernetkey).decode()
                    except (ValueError, FernetKeyIsInvalidError, FernetKeyIsUnknownError):
                        print("%s %-26s: %-10s: unable to decode %s's IP address, re RQIP: fernet key issue? I'll send an RQIP to *them* and see what happens." % (s_now(), self.irc_server, self.nickname, sender))
                        super().put(sender, "%s%s" % (_REQUEST__IPADDRESS_, self.my_encrypted_ipaddr(sender)))
                    else:
                        if self.homies[sender].ipaddr != new_ipaddr:
                            self.homies[sender].ipaddr = new_ipaddr
                        super().put(sender, "%s%s" % (_TRANSMIT_IPADDRESS_, self.my_encrypted_ipaddr(sender)))
                elif msg.startswith(_TRANSMIT_IPADDRESS_):
                    print("%s %-26s: %-10s: reciprocate my IP addr.  from %s" % (s_now(), self.irc_server, self.nickname, sender))
                    try:
                        new_ipaddr = receive_and_decrypt_message(msg[len(_TRANSMIT_IPADDRESS_):], self.homies[sender].fernetkey).decode()
                    except (ValueError, FernetKeyIsInvalidError, FernetKeyIsUnknownError):
                        print("%s %-26s: %-10s: unable to decode %s's IP address re TXIP: fernet key issue? I'll send an RQIP to *them* and see what happens." % (s_now(), self.irc_server, self.nickname, sender))
                        super().put(sender, "%s%s" % (_REQUEST__IPADDRESS_, self.my_encrypted_ipaddr(sender)))
                    else:
                        if self.homies[sender].ipaddr != new_ipaddr:
                            self.homies[sender].ipaddr = new_ipaddr
                        print("%s %-26s: %-10s: completed all handshaking  w/ %s" % (s_now(), self.irc_server, self.nickname, sender))
                elif msg.startswith(_TRANSMITCIPHERTEXT_):
                    try:
                        self.crypto_rx_queue.put((sender, receive_and_decrypt_message(msg[len(_TRANSMITCIPHERTEXT_):], self.homies[sender].fernetkey)))
                    except (ValueError, FernetKeyIsInvalidError, FernetKeyIsUnknownError) as e:
                        print("%s %-26s: %-10s: cannot rx ciphertxt msg  from %s: fernet key issue? => %s" % (s_now(), self.irc_server, self.nickname, sender, str(e)))
                elif msg.startswith(_TRANSMIT_PLAINTEXT_):
                    try:
                        self.plain_rx_queue.put((sender, msg[len(_TRANSMIT_PLAINTEXT_):]))
                    except ValueError:
                        print("%s %-26s: %-10s: cannot rx plaintext msg  from %s" % (s_now(), self.irc_server, self.nickname, sender))
                else:
                    print("%s %-26s: %-10s: cannot rx plaintext msg  from %s => %s" % (s_now(), self.irc_server, self.nickname, sender, msg))

    def is_this_user_validly_fingerprinted(self, user):
        """Is this user's realname a hash of their nickname? If 'yes', they're a Prate user!"""
        try:
            return True if user != self.nickname \
                            and self.whois(user) is not None \
                            and generate_fingerprint(user) == self.whois(user).split('* ', 1)[-1] \
                            else False
        except (IrcBadNicknameError, IrcYouCantUseABotAfterQuittingItError):
            print("%s %-26s: %-10s: %s is a bad nickname. Ignoring." % (s_now(), self.irc_server, self.nickname, user))
            return False

    def trigger_handshaking(self, user=None):
        """Initiate handshaking for all users, *or* just the specified user."""
        for _ in range(0, STARTUP_TIMEOUT):
            if self.ready:
                break
            sleep(1)
        if not self.ready:
            raise IrcStillConnectingError("I cannot trigger handshaking with other users: I'm not even online/joinedroom yet.")
        elif user is None:
            for user in [u for u in self.users if u != self.nickname]:
                self.trigger_handshaking(user)
        elif type(user) is not str:
            raise ValueError("trigger_handshaking() takes user=str, not {t}".format(t=type(user)))
        else:
            try:
                if self.is_this_user_validly_fingerprinted(user):
                    if self.homies[user].pubkey is None:
                        print("%s %-26s: %-10s: pls gimme your pubkey ktxhbai %s" % (s_now(), self.irc_server, self.nickname, user))
                        super().put(user, "%sllo, %s! I am %s. May I please have a copy of your public key?" % (_REQUEST_PUBLICKEY_, user, self.nickname))
                    elif self.homies[user].fernetkey is None:
                        print("%s %-26s: %-10s: pls gimme your fernetkey kbai %s" % (s_now(), self.irc_server, self.nickname, user))
                        print("%s %-26s: %-10s: I lack %s's fernet key. Therefore, I'll ask for a copy." % (s_now(), self.irc_server, self.nickname, user))
                        super().put(user, "%s%s" % (_REQUEST__FERNETKEY_, self.my_encrypted_fernetkey_for_this_user(user)))
                    elif self.homies[user].ipaddr is None:
                        print("%s %-26s: %-10s: pls gimme your IP address bai %s" % (s_now(), self.irc_server, self.nickname, user))
                        super().put(user, "%s%s" % (_REQUEST__IPADDRESS_, self.my_encrypted_ipaddr(user)))
                    else:
                        print("%s %-26s: %-10s: Yay! I have shaken hands with %s" % (s_now(), self.irc_server, self.nickname, user))
            except (IrcBadNicknameError, IrcNicknameTooLongError):
                print("%s %-26s: %-10s: %s is a crappy username. I'll ignore it." % (s_now(), self.irc_server, self.nickname, user))

    def my_encrypted_ipaddr(self, user):
        """Encrypt our IP address w/ the user's fernet key."""
        if self.homies[user].fernetkey is None:
            raise FernetKeyIsUnknownError("Please download %s's fernet key before you try to encrypt." % user)
        cipher_suite = Fernet(self.homies[user].fernetkey)
        ipaddr_str = MY_IP_ADDRESS
        cipher_text = cipher_suite.encrypt(ipaddr_str.encode())
        return cipher_text.decode()

    def my_encrypted_fernetkey_for_this_user(self, user):
        """Encrypt the user's fernet key with the user's public key."""
        encrypted_fernetkey = rsa_encrypt(message=self.homies[user].locally_generated_fernetkey, public_key=self.homies[user].pubkey)
        b64_encrypted_fernetkey = base64.b64encode(encrypted_fernetkey).decode()
        return b64_encrypted_fernetkey

    @property
    def homies(self):
        """Dictionary of relevant IRC users."""
        return self.__homies

    @property
    def paused(self):
        retval = self.__paused
        return retval

    @paused.setter
    def paused(self, value):
        self.__paused = value

    @property
    def plain_rx_queue(self):
        return self.__plain_rx_queue

    @property
    def not_empty(self):
        return self.plain_rx_queue.not_empty

    def empty(self):
        return self.plain_rx_queue.empty()

    def get(self, block=True, timeout=None):
        return self.plain_rx_queue.get(block, timeout)

    def reinsert(self, value):
        self.plain_rx_queue.put(value)

    def get_nowait(self):
        return self.plain_rx_queue.get_nowait()

    def put(self, user, msg):
        """Write a plaintext message to this user via a private message on IRC."""
        if type(msg) is not str:
            raise ValueError("The msg must be a string.")
        elif type(user) is not str:
            raise ValueError("crypto_put() --- user must be a string")
        else:
            outgoing_str = "%s%s" % (_TRANSMIT_PLAINTEXT_, msg)
            if len(outgoing_str) > MAX_PRIVMSG_LENGTH - len(user):
                raise IrcPrivateMessageTooLongError("Cannot send %s to %s: message is too long" % (outgoing_str, user))
            super().put(user, outgoing_str)

    @property
    def crypto_rx_queue(self):
        return self.__crypto_rx_queue

    @property
    def crypto_not_empty(self):
        return self.crypto_rx_queue.not_empty

    def crypto_empty(self):
        return self.crypto_rx_queue.empty()

    def crypto_get(self, block=True, timeout=None):
        return self.crypto_rx_queue.get(block, timeout)

    def crypto_get_nowait(self):
        return self.crypto_rx_queue.get_nowait()

    def crypto_put(self, user, byteblock):
        """Write an encrypted message to this user via a private message on IRC."""
        if type(byteblock) is not bytes:
            raise ValueError("I cannot send a non-binary message to %s. The byteblock must be composed of bytes!" % user)
        elif type(user) is not str:
            raise ValueError("crypto_put() --- user must be a string")
        elif self.homies[user].fernetkey is None:
            raise FernetKeyIsUnknownError("I have not negotiated a fernet key with %s yet." % user)
        elif self.homies[user].pubkey is None:
            raise PublicKeyUnknownError("I do not know %s's public key." % user)
        elif len(byteblock) > MAX_CRYPTO_MSG_LENGTH:
            raise IrcPrivateMessageTooLongError("The encrypted message will be too long")
        else:
            cipher_suite = Fernet(self.homies[user].fernetkey)
            cipher_text = cipher_suite.encrypt(byteblock)
            outgoing_str = "%s%s" % (_TRANSMITCIPHERTEXT_, cipher_text.decode())
            if len(outgoing_str) > MAX_PRIVMSG_LENGTH - len(user):
                raise IrcPrivateMessageTooLongError("Cannot send %s to %s: message is too long" % (outgoing_str, user))
            super().put(user, outgoing_str)

    def quit(self, yes_even_the_reactor_thread=False, timeout=ENDTHREAD_TIMEOUT):
        super().quit(yes_even_the_reactor_thread=yes_even_the_reactor_thread, timeout=timeout)
        if hasattr(self, '__my_main_thread'):  # Is someone deleting it?
            print("HUZZAH! WE CAN CLOSE THE MAIN THREAD.")
            self.__my_main_thread.join(timeout=timeout)


if __name__ == "__main__":
    if len(sys.argv) != 5:
#        print("Usage: %s <URL> <port> <channel> <nickname>" % sys.argv[0])
#        sys.exit(1)
        my_irc_server = 'cinqcent.local'
        my_port = 6667
        my_channel = '#prate'
        desired_nickname = 'mac1'
    else:
        my_irc_server = sys.argv[1]
        my_port = int(sys.argv[2])
        my_channel = sys.argv[3]
        desired_nickname = sys.argv[4]

    my_rsa_key = RSA.generate(RSA_KEY_SIZE)
    my_bot = PrateBot([my_channel], desired_nickname, my_irc_server, my_port, my_rsa_key)
    while not my_bot.ready:
        sleep(1)
    print("Hi there.")

