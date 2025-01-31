'''
Created on Jan 30, 2025

@author: mchobbit
'''

from Crypto.PublicKey import RSA
from cryptography.fernet import Fernet
from my.classes.readwritelock import ReadWriteLock


class Homie:

    def __init__(self, nickname, pubkey=None, fernetkey=None, ipaddr=None):
        self.__nickname_lock = ReadWriteLock()
        self.__pubkey_lock = ReadWriteLock()
        self.__fernetkey_lock = ReadWriteLock()
        self.__ipaddr_lock = ReadWriteLock()
        self.__nickname = nickname
        self.__pubkey = pubkey
        self.__fernetkey = fernetkey
        self.__ipaddr = ipaddr
        self._my_fernet = Fernet.generate_key()
        self._his_fernet = None

        super().__init__()

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
            self.__pubkey = value
        finally:
            self.__pubkey_lock.release_write()

    @property
    def fernetkey(self):
        self.__fernetkey_lock.acquire_read()
        try:
            retval = self.__fernetkey
            return retval
        finally:
            self.__fernetkey_lock.release_read()

    @fernetkey.setter
    def fernetkey(self, value):
        self.__fernetkey_lock.acquire_write()
        try:
            if value is None or type(value) is not bytes:
                raise ValueError("When setting fernetkey, specify bytes & not a {t}".format(t=str(type(value))))
            self.__fernetkey = value
        finally:
            self.__fernetkey_lock.release_write()

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
