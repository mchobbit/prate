# -*- coding: utf-8 -*-
"""my.classes.selfcachingcall

Created on May 19, 2024

This module contains the SelfCachingCall class, for automatically updating
and caching the result of an OS call, Python function call, or external
binary call.

Examples:
    from my.classes.selfcachingcall import SelfCachingCall
    import time, os
    d = SelfCachingCall(5, os.system, "ping -W2 -c1 bbc.com > /dev/null 2> /dev/null")
    for i in range(0,10):
        time.sleep(1)
        print(d.result)
    d.join()

    def myfunc(addme):
        global GVAR
        GVAR += addme
        return GVAR

    GVAR = 5
    c = SelfCachingCall(2, myfunc, 100)
    while True:
        time.sleep(1)
        print(GVAR)
    c.join()

"""

from threading import Thread  # Condition, Lock,
from time import sleep
import copy
import random

from my.classes.exceptions import StillAwaitingCachedValue
from my.classes.readwritelock import ReadWriteLock


class SelfCachingCall:
    """Self-repeating call to function; saves result; caches it.

    SelfCachingCall() is a class instance that calls a specific function (with specified parameters)
    every N seconds. The result, including any error, is cached and is made available to the
    programmer. The call happens in the background. An instance of SelfCachingCall() encapsulates that
    functionality and caches the result of the call.

    e.g.
        >>> GVAR = 5
        >>> def myfunc(addme):
                global GVAR
                GVAR += addme
                return GVAR
        >>> from my.classes import SelfCachingCall
        >>> #................freq, func, paramsForfunc
        >>> c = SelfCachingCall(2, myfunc, 100)
        >>> c.result
        my.globals.exceptions.StillAwaitingCachedValue: We have not cached the first result yet
        >>> sleep(1); c.result
        605

    Note:
        If the programmer tries to read the cached value before the first call to the function,
        an exception will be thrown. If the most recent function call throws an exception, the act
        of reading c.result will cause that exception to be thrown.

    Args:
        refreshfrequency (int): How often should I call the function
        func: What is the function?
        args,kwargs: Pass these parameters to the function

    Methods:
        update_me(): Force a new call to the function; save the result in our cache.

    Attributes:
        result (int): result of most recent (cached) call to the function that's being cached
            FYI, if the most recent call threw an exception, then the act of getting the result
            attribute will throw that exception. I guess you could say the subroutine didn't
            only catch it; it cached it.

    Exceptions:
        StillAwaitingCachedValue: If we don't have a cached value yet, this exception is raised.

    """

    def __init__(self, refreshfrequency, func, *args, **kwargs):
        assert (isinstance(refreshfrequency, int)
                or isinstance(refreshfrequency, float))
        if refreshfrequency <= 0:
            raise ValueError("When declaring a SelfCachingCall instance, please specify a refreshfrequency greater than 0.")
        self.__args = args
        self.__kwargs = kwargs
        self.__func = func
        self.__refreshfrequency = refreshfrequency
        self.__refreshfreq_lock = ReadWriteLock()
        self.__update_lock = ReadWriteLock()
        self.__result = None
        self.__error = StillAwaitingCachedValue(
            'We have not cached the first result yet')
        self.__result_and_error_lock = ReadWriteLock()
        self.__time_to_join = False
        self.__keepupdating_thread = Thread(target=self._keep_updating)
        self.__keepupdating_thread.daemon = True
        self.__keepupdating_thread.start()
        super().__init__()

    def _keep_updating(self):
        """Run me, over and over, to keep cache populated.

        Note:
            This runs in the background. To end it, run
                i.join() if 'i' the instance of this class.

        """
        time_left_before_update = 0
        while not self.__time_to_join:
            if time_left_before_update <= 0:
                self.update_me()
                time_left_before_update = self.__refreshfrequency
            else:
                sleep_for_how_long = min(1, time_left_before_update)
                time_left_before_update -= sleep_for_how_long
                sleep(sleep_for_how_long)
#        logit('No more soup for you')

    def update_me(self):
        """Repopulate the cache. Wait for it to finish."""
        try:
            self.__update_lock.acquire_write()
            the_new_result = self.__func(*self.__args, **self.__kwargs)
            the_new_error = None
        except Exception as e:  # pylint: disable=broad-exception-caught
            the_new_result = None
            the_new_error = e
        finally:
            self.__update_lock.release_write()
        try:
            self.__result_and_error_lock.acquire_write()
            self.__error = the_new_error
            self.__result = the_new_result
        finally:
            self.__result_and_error_lock.release_write()

    @property
    def result(self):
        """Return the result, or raise exception if appropriate.

        If the result of the most recent caching attempt was an exception,
        raise that exception. Otherwise, return the aforementioned result.

        Returns:
            Result, whatever it was;... or exception, if an exception
                occurred during the call to the user-specific function.

        """
        try:
            self.__result_and_error_lock.acquire_write()
            while True:
                try:
                    retval = copy.deepcopy(self.__result)
                except RuntimeError:
                    print('value changed while iterating, or something; probably a race condition; retrying...')
                    sleep(.5 + random.randint(0, 4) / 10)
                else:
                    reterr = self.__error
                    break
        except Exception as e:  # pylint: disable=broad-exception-caught
            print('SelfCachingCall.result reported this ==> %s' % str(e))
            retval = None
            reterr = e
        finally:
            self.__result_and_error_lock.release_write()
        if reterr is not None:
            raise reterr
        else:
            return retval

    def join(self):
        """Join the thread and return."""
        self.__time_to_join = True
        self.__keepupdating_thread.join()

    @property
    def refreshfrequency(self):
        """float: How often does the cache update?"""
        self.__refreshfreq_lock.acquire_read()
        retval = self.__refreshfrequency
        self.__refreshfreq_lock.release_read()
        return retval

    @refreshfrequency.setter
    def refreshfrequency(self, value):
        """Set how often the cache updates."""
        self.__refreshfreq_lock.acquire_write()
        self.__refreshfrequency = value
        self.__refreshfreq_lock.release_write()

