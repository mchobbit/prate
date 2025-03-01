# -*- coding: utf-8 -*-
"""Class for array of relevant users of an IRC network.

Created on Jan 30, 2025

@author: mchobbit

This module contains classes for managing a list of users whose idents reveal
them to be Prate users (because the realname is a hash of the nickname).
Each 'homie' record contains a nickname, a realname (usually a public key),
a fernet key (symmetric), and a flag to say if the user actually *has* a public
key.

Because of the inevitable collisions/race conditions that must be mitigated
during the key negotiation phase, there are two fernet keys: mine and his.
Naturally, I send him mine and he sends me his. The one with the higher ascii
value is the one that 'wins' and the one that we use. If we know only one
of the two, fernetkey returns None: we need both.

Todo:
    * Better docs

.. _Google Python Style Guide:
   http://google.github.io/styleguide/pyguide.html

.. _Napoleon Style Guide:
   https://sphinxcontrib-napoleon.readthedocs.io/en/latest/example_google.html

"""

from Crypto.PublicKey import RSA
from cryptography.fernet import Fernet
from my.classes.readwritelock import ReadWriteLock
from my.classes.exceptions import IrcBadNicknameError, PublicKeyBadKeyError, IrcNicknameTooLongError
from my.globals import MAX_NICKNAME_LENGTH
from my.irctools.cryptoish import squeeze_da_keez


class Homie:
    """The class for storing information about an IRC user, especially crypto.

    Each 'homie' record contains important info about the IRC user in question.
    It contains the user's nickname (although this *isn't* updated on its own),
    the public key (if there is one), the symmetric key (ditto), and the IP
    address (if we know it). You get the picture.

    Args:
        nickname (str): Nickname from IRC.
        pubkey (RSA.RsaKey): The public key that other computers should use when exchanging fernet keys with me.
        remotely_supplied_fernetkey (bytes): The fernet symmetric key supplied by the user's computer.
        ipadd (str): The IP address of the user.
    """

    def __init__(self, nickname, irc_server=None, pubkey=None, remotely_supplied_fernetkey=None, ipaddr=None):
        self.__nickname_lock = ReadWriteLock()
        self.__pubkey_lock = ReadWriteLock()
        self.__fernetkey_lock = ReadWriteLock()
        self.__ipaddr_lock = ReadWriteLock()
        self.__irc_server = irc_server
        self.__irc_server_lock = ReadWriteLock()
        self.__nickname = nickname
        self.__pubkey = pubkey
        self.__remotely_supplied_fernetkey = remotely_supplied_fernetkey
        self.__remotely_supplied_fernetkey_lock = ReadWriteLock()
        self.__locally_generated_fernetkey = Fernet.generate_key()
        self.__locally_generated_fernetkey_lock = ReadWriteLock()
        self.__ipaddr = ipaddr
        super().__init__()

    def __repr__(self):
        class_name = type(self).__name__
        pk = self.pubkey
        if pk is not None:
            pk = squeeze_da_keez(pk)
            pk = "%s..." % (pk[:16])
        fk = self.fernetkey
        if fk is not None:
            fk = "%s..." % str(fk)[:12]
        return f"{class_name}(irc_server={self.irc_server!r}, nickname={self.nickname!r}, pubkey={pk!r}, fernetkey={fk!r}, ipaddr={self.ipaddr!r})"

#    def __str__(self):
#        return f'"{self.title}" by {self.author}'

    @property
    def irc_server(self):
        """irc_server (str: The irc_server that is associated with this record."""
        self.__irc_server_lock.acquire_read()
        try:
            retval = self.__irc_server
            return retval
        finally:
            self.__irc_server_lock.release_read()

    @irc_server.setter
    def irc_server(self, value):
        self.__irc_server_lock.acquire_write()
        try:
            self.__irc_server = value
        finally:
            self.__irc_server_lock.release_write()

    @property
    def remotely_supplied_fernetkey(self):
        """bytes: The symmetric key that was sent to me by the remote computer."""
        self.__remotely_supplied_fernetkey_lock.acquire_read()
        try:
            retval = self.__remotely_supplied_fernetkey
            return retval
        finally:
            self.__remotely_supplied_fernetkey_lock.release_read()

    @remotely_supplied_fernetkey.setter
    def remotely_supplied_fernetkey(self, value):
        self.__remotely_supplied_fernetkey_lock.acquire_write()
        try:
            if self.__remotely_supplied_fernetkey is not None:
                if self.__remotely_supplied_fernetkey != value and value is not None:
                    raise AttributeError("remotely_supplied_fernetkey already set! I don't want to replace it. You're being fishy.")
            if self.__remotely_supplied_fernetkey == value and value is not None:
                pass  # print("remotely_supplied_fernetkey is already", value, "... and that makes me wonder, why are you setting it to the same value that it already holds?")
            self.__remotely_supplied_fernetkey = value
        finally:
            self.__remotely_supplied_fernetkey_lock.release_write()

    @property
    def locally_generated_fernetkey(self):
        """bytes: The symmetric key that I created when this record was created."""
        self.__locally_generated_fernetkey_lock.acquire_read()
        try:
            retval = self.__locally_generated_fernetkey
            return retval
        finally:
            self.__locally_generated_fernetkey_lock.release_read()

    @property
    def nickname(self):
        """nickname (str: The nickname that is associated with this record."""
        self.__nickname_lock.acquire_read()
        try:
            retval = self.__nickname
            return retval
        finally:
            self.__nickname_lock.release_read()

    @nickname.setter
    def nickname(self, value):
        self.__nickname_lock.acquire_write()
        try:
            if value is not None and type(value) is not str:
                raise IrcBadNicknameError("When setting nickname, specify a string & not a {t}".format(t=str(type(value))))
            if len(value) > MAX_NICKNAME_LENGTH:
                raise IrcNicknameTooLongError("Nickname %s is too long" % value)
            self.__nickname = value
        finally:
            self.__nickname_lock.release_write()

    @property
    def pubkey(self):
        """RSA.RsaKey: The public key that other computers should use when exchanging fernet keys with me."""
        self.__pubkey_lock.acquire_read()
        try:
            retval = self.__pubkey
            return retval
        finally:
            self.__pubkey_lock.release_read()

    @pubkey.setter
    def pubkey(self, value):
        self.__pubkey_lock.acquire_write()
        try:
            if value is not None and type(value) is not RSA.RsaKey:
                raise ValueError("When setting pubkey, specify a RSA.RsaKey & not a {t}".format(t=str(type(value))))
            self.noof_fingerprinting_failures = 0
            self.__pubkey = value
        finally:
            self.__pubkey_lock.release_write()

    @property
    def fernetkey(self):
        """bytes: Whichever key -- local or remote -- is higher
            in ascii terms, that's the one that is returned when the
            programmer interrogates the fernetkey attribute. In this way,
            each computers can send the other his own key, but the 'higher'
            one always wins, because both sides choose the 'higher' one."""
        self.__fernetkey_lock.acquire_read()
        try:
            x = self.remotely_supplied_fernetkey
            y = self.locally_generated_fernetkey
            return None if x is None or y is None else max(x, y)
        finally:
            self.__fernetkey_lock.release_read()

    @property
    def ipaddr(self):
        """str: The IP address of this user, or None if we dont know."""
        self.__ipaddr_lock.acquire_read()
        try:
            retval = self.__ipaddr
            return retval
        finally:
            self.__ipaddr_lock.release_read()

    @ipaddr.setter
    def ipaddr(self, value):
        self.__ipaddr_lock.acquire_write()
        try:
            if value is not None and type(value) is not str:
                raise ValueError("When setting ipaddr, specify a string & not a {t}".format(t=str(type(value))))
            self.__ipaddr = value
        finally:
            self.__ipaddr_lock.release_write()


class HomiesDct(dict):
    """Dictionary of Homies

    This is a barely threadsafe, badly written subclass of dictionary class.
    Its one redeeming feature is its lazy attitude to new keys: if the user
    tries to use a nonexistent key to read/write a nonexistent item, the
    key entry is automatically created first.
    """

    def __setitem__(self, key, item):
        if type(key) is not str:
            raise AttributeError("key %s should be a string" % str(key))
        self.__dict__[str(key)] = item

    def __getitem__(self, key):
        if type(key) is not str:
            raise AttributeError("key %s should be a string" % str(key))
        if key not in self.__dict__:
            self.__setattr__(key, Homie(nickname=str(key)))
        return self.__dict__[key]

    def __repr__(self):
        return repr(self.__dict__)

    def __len__(self):
        return len(self.__dict__)

    def __delitem__(self, key):
        if type(key) is not str:
            raise AttributeError("key %s should be a string" % str(key))
        del self.__dict__[key]

    def clear(self):
        return self.__dict__.clear()

    def copy(self):
        return self.__dict__.copy()

    def has_key(self, k):
        if type(k) is not str:
            raise AttributeError("key %s should be a string" % str(k))
        return k in self.__dict__

    def update(self, *args, **kwargs):
        return self.__dict__.update(*args, **kwargs)

    def keys(self):
        return self.__dict__.keys()

    def values(self):
        return self.__dict__.values()

    def items(self):
        return self.__dict__.items()

    def pop(self, *args):
        return self.__dict__.pop(*args)

#    def __cmp__(self, dict_):
#        return self.__cmp__(self.__dict__, dict_)

    def __contains__(self, item):
        if type(item) is not str:
            print("__contains__ parameter item is", type(item), "and not a string. Is that okay? I'm not sure.")
        return item in self.__dict__

    def __iter__(self):
        return iter(self.__dict__)
    # def __unicode__(self):
    #     return unicode(repr(self.__dict__))

