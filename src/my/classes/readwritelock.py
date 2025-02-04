# -*- coding: utf-8 -*-
"""my.classes

Created on May 19, 2024

This module --- my.classes --- exists so that the programmer can keep all
the subclasses and homemade classes in one place.

Functions:
    singleton()

Classes:
    ReadWriteLock

Attributes:
    none

Example:
    from my.classes.randomquoteclass import SomeClassToBeSingletonized
    ClassySingleton = SomeClassToBeSingletonized()
    ...
    [elsewhere]
    from this.source.file import ClassySingleton as cs
    print(cs.value)
    cs.value = 5
    etc. etc.
"""

from threading import Condition, Lock, Thread
from time import sleep
import copy
import datetime
import random
import string
import time


def singleton(cls):
    """Generate a singleton.

    This function generates a singleton. You know what that is.
    See http://stackoverflow.com/questions/674304/pythons-use-of-new-and-init?ref=mythemeco&t=pack for explanation

    Args:
        cls (class): The class to be singleton-ized.

    Returns:
        class: The singleton-ized instance of cls.

    """
    instances = {}

    def getinstance():
        if cls not in instances:
            instances[cls] = cls()
        return instances[cls]

    return getinstance


class ReadWriteLock:
    """A lock object that allows many read locks but only one write lock.

    This is a lock object that allows many simultaneous "read locks", but
    only one "write lock". This is useful for functions and classes that
    need to permit a given variable to be read by multiple threads but
    be modified by only one thread.

    Attributes:
        locked: Status of lock. True if locked, False if not.

    """

    def __init__(self):
        self._read_ready_lck = Lock()
        self._read_ready = Condition(self._read_ready_lck)
        self._readers = 0

    @property
    def locked(self) -> bool:
        """bool: Return True if the underlying Lock is locked."""
        return self._read_ready_lck.locked()

    def acquire_read(self):
        """Acquire a read lock. Blocks only if a thread has
        acquired the write lock. """
        self._read_ready.acquire()
        try:
            self._readers += 1
        finally:
            self._read_ready.release()

    def release_read(self):
        """Release a read lock."""
        self._read_ready.acquire()
        try:
            self._readers -= 1
            if not self._readers:
                self._read_ready.notify_all()
        finally:
            self._read_ready.release()

    def acquire_write(self):
        """Acquire a write lock. Blocks until there are no
        acquired read or write locks."""
        self._read_ready.acquire()
        while self._readers > 0:
            self._read_ready.wait()

    def release_write(self):
        """Release a write lock."""
        self._read_ready.release()
