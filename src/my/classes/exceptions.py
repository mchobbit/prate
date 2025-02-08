# -*- coding: utf-8 -*-
"""my.classes.exceptions

Created on Jan 21, 2025

@author: mchobbit

This module contains every custom exception that the app uses. The classes
and subclasses are named accordingly.

Error
    StartupError
        AudioStartupError
            PygameStartupError
        PyQtStartupError
            PyQtUICompilerError
        VersionError
            PythonVersionError
    WebAPIError
        WebAPIOutputError
        WebAPITimeoutError
    CachingError
        MissingFromCacheError
        StillAwaitingCachedValue
    MyIrcError
        MyIrcConnectionError
            MyIrcInitialConnectionTimeoutError
            MyIrcStillConnectingError
            MyIrcRealnameTruncationError
            MyIrcFingerprintMismatchCausedByServer
            MyIrcNicknameChangedByServer
        MyIrcMessagingError
            MyIrcUnknownIncomingCommandError
    MyEncryptionError
        MyKeyError
            MyPublicKeyError
                MyPublicKeyUnknownError
                MyPublicKeyIncompleteError
                MyPublicKeyTooBigError
            MyFernetKeyError
                MyFernetKeyUnknownError
        MyFailedToEncryptError
        MyFailedToDecryptError


Example:
    n/a

Attributes:
    none

"""


class Error(Exception):
    """Base class for other exceptions"""

    def __init__(self, message):  # pylint: disable=useless-parent-delegation
        super().__init__(message)


class StartupError(Error):
    """Class for all startup errors"""

    def __init__(self, message):  # pylint: disable=useless-parent-delegation
        super().__init__(message)


class MainAppStartupError(StartupError):
    """Class for all main app startup errors"""

    def __init__(self, message):  # pylint: disable=useless-parent-delegation
        super().__init__(message)


class VersionError(StartupError):
    """Class for all main app startup errors"""

    def __init__(self, message):  # pylint: disable=useless-parent-delegation
        super().__init__(message)


class PythonVersionError(VersionError):
    """Class for all main app startup errors"""

    def __init__(self, message):  # pylint: disable=useless-parent-delegation
        super().__init__(message)


class AudioStartupError(StartupError):
    """Class for all audio startup errors"""

    def __init__(self, message):  # pylint: disable=useless-parent-delegation
        super().__init__(message)


class PygameStartupError(StartupError):
    """Class for pygame startup errors"""

    def __init__(self, message):  # pylint: disable=useless-parent-delegation
        super().__init__(message)


class PyQtStartupError(StartupError):
    """Class for all PyQt startup errors"""

    def __init__(self, message):  # pylint: disable=useless-parent-delegation
        super().__init__(message)


class PyQtUICompilerError(PyQtStartupError):
    """Class for all PyQt startup errors"""

    def __init__(self, message):  # pylint: disable=useless-parent-delegation

        super().__init__(message)


class WebAPIError(Error):
    """Class for web API errors"""

    def __init__(self, message):  # pylint: disable=useless-parent-delegation

        super().__init__(message)


class WebAPIOutputError(WebAPIError):
    """Class for web API output errors"""

    def __init__(self, message):  # pylint: disable=useless-parent-delegation

        super().__init__(message)


class WebAPIOverloadError(WebAPIError):
    """Class for web API output errors"""

    def __init__(self, message):  # pylint: disable=useless-parent-delegation

        super().__init__(message)


class WebAPITimeoutError(WebAPIError):
    """Class for web API timeout errors"""

    def __init__(self, message):  # pylint: disable=useless-parent-delegation

        super().__init__(message)


class CachingError(Error):
    """Class for all caching errors"""

    def __init__(self, message):  # pylint: disable=useless-parent-delegation

        super().__init__(message)


class MissingFromCacheError(Error):
    """If the value *should* have been cached already but *hasn't*, raise this."""

    def __init__(self, message):  # pylint: disable=useless-parent-delegation

        super().__init__(message)


class StillAwaitingCachedValue(CachingError):
    """If we're trying to access a cached value that hasn't been cached yet.

    The class SelfCachingCall() calls the supplied function every N seconds
    and stores the result. If the result is an exception, it stores that.
    Either way, it replies with the result (or the exception) when the
    programmer asks for it. In this way, the programmer can receive
    instantaneously the result of a function call without having to wait
    for it to run.

    Of course, this means that there won't be a result at first. Otherwise,
    the programmer would have to wait until the first result had been cached:
    the opposite of the intended purpose of this class. Granted, the programmer
    would have to wait only once. Still, I don't like that. I would rather
    raise an exception and say, "We haven't cached the first value yet."

    Example:
        >>> from my.classes import SelfCachingCall
        >>> c = SelfCachingCall(2, myfunc, 100)
        >>> c.result
        my.globals.exceptions.StillAwaitingCachedValue: We have not cached the first result yet
        >>> sleep(1); c.result
        605

    Args:
        msg (str): Human readable string describing the exception.
        code (:obj:`int`, optional): Error code.

    Attributes:
        msg (str): Human readable string describing the exception.
        code (int): Exception error code.

    """

    def __init__(self, message):  # pylint: disable=useless-parent-delegation

        super().__init__(message)


class MyIrcError(Error):
    """Class for all MyIrcErrors"""

    def __init__(self, message):  # pylint: disable=useless-parent-delegation

        super().__init__(message)


class MyIrcConnectionError(MyIrcError):
    """Class for all MyIrcConnectionError"""

    def __init__(self, message):  # pylint: disable=useless-parent-delegation

        super().__init__(message)


class MyIrcInitialConnectionTimeoutError(MyIrcConnectionError):
    """Connecting took too long."""

    def __init__(self, message):  # pylint: disable=useless-parent-delegation

        super().__init__(message)


class MyIrcStillConnectingError(MyIrcConnectionError):
    """Still connecting (wait a few seconds, please)"""

    def __init__(self, message):  # pylint: disable=useless-parent-delegation

        super().__init__(message)


class MyIrcRealnameTruncationError(MyIrcConnectionError):
    """If the realname is truncated by the server"""

    def __init__(self, message):  # pylint: disable=useless-parent-delegation

        super().__init__(message)


class MyIrcFingerprintMismatchCausedByServer(MyIrcConnectionError):
    """My local fingerprint and the server's copy of my fingerprint do not match, perhaps because my nickname changed somewhere"""

    def __init__(self, message):  # pylint: disable=useless-parent-delegation

        super().__init__(message)


class MyIrcMessagingError(MyIrcError):
    """Class for all MyIrcMessagingError"""

    def __init__(self, message):  # pylint: disable=useless-parent-delegation

        super().__init__(message)


class MyIrcUnknownIncomingCommandError(MyIrcMessagingError):
    """Unknown incoming command."""

    def __init__(self, message):  # pylint: disable=useless-parent-delegation

        super().__init__(message)


class MyIrcIncomingCommandFromMyselfError(MyIrcMessagingError):
    """Why am I talking to myself?"""

    def __init__(self, message):  # pylint: disable=useless-parent-delegation

        super().__init__(message)


class MyIrcNicknameChangedByServer(MyIrcConnectionError):
    """If the nickname is CHANGED by the server, probably because of a nickname collision"""

    def __init__(self, message):  # pylint: disable=useless-parent-delegation

        super().__init__(message)


class MyEncryptionError(Error):
    """Class for all MyKeyError"""

    def __init__(self, message):  # pylint: disable=useless-parent-delegation

        super().__init__(message)


class MyKeyError(MyEncryptionError):
    """Class for all MyKeyError"""

    def __init__(self, message):  # pylint: disable=useless-parent-delegation

        super().__init__(message)


class MyPublicKeyError(MyKeyError):
    """Class for all MyPublicKeyError"""

    def __init__(self, message):  # pylint: disable=useless-parent-delegation

        super().__init__(message)


class MyPublicKeyUnknownError(MyPublicKeyError):
    """I don't know his public key yet."""

    def __init__(self, message):  # pylint: disable=useless-parent-delegation

        super().__init__(message)


class MyPublicKeyIncompleteError(MyPublicKeyError):
    """Public key is incomplete."""

    def __init__(self, message):  # pylint: disable=useless-parent-delegation

        super().__init__(message)


class MyPublicKeyTooBigError(MyPublicKeyError):
    """Public key is too big for /whois."""

    def __init__(self, message):  # pylint: disable=useless-parent-delegation

        super().__init__(message)


class MyFernetKeyError(MyKeyError):
    """Class for all MyPublicKeyError"""

    def __init__(self, message):  # pylint: disable=useless-parent-delegation

        super().__init__(message)


class MyFernetKeyUnknownError(MyPublicKeyError):
    """I don't know his fernet key yet."""

    def __init__(self, message):  # pylint: disable=useless-parent-delegation

        super().__init__(message)


class MyFailedtoEncryptError(MyEncryptionError):
    """Failed to encrypt"""

    def __init__(self, message):  # pylint: disable=useless-parent-delegation

        super().__init__(message)


class MyFailedtoDecryptError(MyEncryptionError):
    """Failed to decrypt"""

    def __init__(self, message):  # pylint: disable=useless-parent-delegation

        super().__init__(message)

