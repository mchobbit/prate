# -*- coding: utf-8 -*-
"""Class TTLCache.

Created on Feb 4, 2025

@author: mchobbit

This module contains the MyTTLCache class. This class offers a cache
whose data expires (ceases to be cached) after N seconds.

Example:
    Here is how to use one of these classes, for example::

    $ python3.12
    >>> from time import sleep
    >>> from my.classes.ttlcache import MyTTLCache
    >>> cache = MyTTLCache(10)
    >>> cache.set('foo', 69)
    >>> cache.get('foo')
    69
    >>> sleep(3)
    >>> cache.get('foo')
    69
    >>> sleep(7)
    >>> cache.get('foo')
    >>>

    You get the idea.

Now, here is a section break. Section breaks
are also implicitly created anytime a new section starts.

Attributes:
    None.

Todo:
    * For module TODOs
    * You have to also use ``sphinx.ext.todo`` extension

.. _Google Python Style Guide:
   http://google.github.io/styleguide/pyguide.html

.. _Napoleon Style Guide:
   https://sphinxcontrib-napoleon.readthedocs.io/en/latest/example_google.html

"""

import time
from my.classes.readwritelock import ReadWriteLock


class MyTTLCache:
    """Cache with self-expiring data after N seconds.

    This class offers a cache whose data self-expires after N seconds. That
    way, stale data is automatically dropped from the cache.

    This offers advantages when one is coding for pings, whois calls, and
    other network-related things.

    Attributes:
        attr1 (str): Description of `attr1`.
        attr2 (:obj:`int`, optional): Description of `attr2`.

    """

    def __init__(self, ttl):
        if type(ttl) is not int or ttl < 1:
            raise ValueError("Supply a positive integer for ttl, please")

        self.ttl = ttl
        self.__cache = {}
        self.__cache_lock = ReadWriteLock()

    @property
    def cache(self):
        """Cache itself."""
        self.__cache_lock.acquire_read()
        try:
            retval = self.__cache
            return retval
        finally:
            self.__cache_lock.release_read()

    @cache.setter
    def cache(self, value):
        self.__cache_lock.acquire_write()
        try:
            self.__cache = value
        finally:
            self.__cache_lock.release_write()

    def set(self, key, value):
        """Set cache value."""
        self.cache[key] = {'value': value, 'time': time.time()}

    def get(self, key):
        """Get cache value.

        Example:
            >>> cache = MyTTLCache(10)
            >>> cache.set('foo', 69)
            >>> cache.get('foo')
            69
            >>> sleep(10); cache.get('foo')
            >>>
        """
        if key in self.cache:
            entry = self.cache[key]
            if time.time() - entry['time'] < self.ttl:
                return entry['value']
            else:
                del self.cache[key]
        return None
