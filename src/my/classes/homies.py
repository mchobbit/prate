# -*- coding: utf-8 -*-
"""Array of relevant users of a given IRC network (usu. channel)

Created on Jan 30, 2025

@author: mchobbit

This module contains classes for managing a list of users whose idents contain
public keys, thus making them relevant to the class that uses these records.
Each 'homie' record contains a nickname, a realname (usually a public key),
a fernet key (symmetric), and a flag to say if the user actually *has* a public
key.

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

    def __init__(self, nickname, pubkey=None, remotely_supplied_fernetkey=None, ipaddr=None):
        self.__nickname_lock = ReadWriteLock()
        self.__pubkey_lock = ReadWriteLock()
        self.__fernetkey_lock = ReadWriteLock()
        self.__ipaddr_lock = ReadWriteLock()
        self.__nickname = nickname
        self.__keyless = False
        self.__keyless_lock = ReadWriteLock()
        self.__pubkey = pubkey
        self.__remotely_supplied_fernetkey = remotely_supplied_fernetkey
        self.__remotely_supplied_fernetkey_lock = ReadWriteLock()
        k = Fernet.generate_key()
        self.__locally_generated_fernetkey = k
        self.__locally_generated_fernetkey_lock = ReadWriteLock()
        self.__ipaddr = ipaddr
        super().__init__()

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
                if self.__remotely_supplied_fernetkey != value:
                    raise AttributeError("remotely_supplied_fernetkey already set! I don't want to replace it. You're being fishy.")
            if self.__remotely_supplied_fernetkey == value:
                print("remotely_supplied_fernetkey is already", value, "... and that makes me wonder, why are you setting it to the same value that it already holds?")
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
                raise ValueError("When setting nickname, specify a string & not a {t}".format(t=str(type(value))))
            self.__nickname = value
        finally:
            self.__nickname_lock.release_write()

    @property
    def pubkey(self):
        """RSA.RsaKey: The public key that other computers should use when exchanging fernet keys with me."""
        self.__pubkey_lock.acquire_read()
        if self.keyless:
            raise AttributeError("%s is keyless" % self.nickname)
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
            self.keyless = False
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
    def keyless(self):
        """keyless (bool): True if this user has no key at all. False otherwise.
            This is useful because a pubkey set to None might indicate that
            we haven't run /whois yet. After /whois has been run, either
            there is no key (in which case, keyless is set to True and
            pubkey becomes inaccessible), or there *is* a key (meaning,
            pubkey is set to a public key and keyless is set to False)."""
        self.__keyless_lock.acquire_read()
        try:
            return self.__keyless
        finally:
            self.__keyless_lock.release_read()

    @keyless.setter
    def keyless(self, value):
        self.__keyless_lock.acquire_write()
        try:
            self.__keyless = value
        finally:
            self.__keyless_lock.release_write()

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
            if value is None or type(value) is not str:
                raise ValueError("When setting ipaddr, specify a string & not a {t}".format(t=str(type(value))))
            self.__ipaddr = value
        finally:
            self.__ipaddr_lock.release_write()


class HomiesDct(dict):

    def __init__(self):
        super().__init__()

    def __setitem__(self, key, item):
        self.__dict__[key] = item

    def __getitem__(self, key):
        if key not in self.__dict__:
            self.__setattr__(key, Homie(nickname=key))
        return self.__dict__[key]

    def __repr__(self):
        return repr(self.__dict__)

    def __len__(self):
        return len(self.__dict__)

    def __delitem__(self, key):
        del self.__dict__[key]

    def clear(self):
        return self.__dict__.clear()

    def copy(self):
        return self.__dict__.copy()

    def has_key(self, k):
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
        return item in self.__dict__

    def __iter__(self):
        return iter(self.__dict__)
    # def __unicode__(self):
    #     return unicode(repr(self.__dict__))

