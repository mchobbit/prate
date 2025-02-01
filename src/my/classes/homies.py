# -*- coding: utf-8 -*-
'''
Created on Jan 30, 2025

@author: mchobbit
'''

from Crypto.PublicKey import RSA
from cryptography.fernet import Fernet
from my.classes.readwritelock import ReadWriteLock


class Homie:

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
        self.__locally_generated_fernetkey_lock.acquire_read()
        try:
            retval = self.__locally_generated_fernetkey
            return retval
        finally:
            self.__locally_generated_fernetkey_lock.release_read()

    @property
    def nickname(self):
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
        self.__fernetkey_lock.acquire_read()
        try:
            x = self.remotely_supplied_fernetkey
            y = self.locally_generated_fernetkey
            return None if x is None or y is None else max(x, y)
        finally:
            self.__fernetkey_lock.release_read()

    # @fernetkey.setter
    # def fernetkey(self, value):
    #     self.__fernetkey_lock.acquire_write()
    #     try:
    #         if value is None or type(value) is not bytes:
    #             raise ValueError("When setting fernetkey, specify bytes & not a {t}".format(t=str(type(value))))
    #         self.__fernetkey = value
    #     finally:
    #         self.__fernetkey_lock.release_write()

    @property
    def keyless(self):
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

    # def __cmp__(self, dict_):
    #     return self.__cmp__(self.__dict__, dict_)

    def __contains__(self, item):
        return item in self.__dict__

    def __iter__(self):
        return iter(self.__dict__)
    # def __unicode__(self):
    #     return unicode(repr(self.__dict__))

