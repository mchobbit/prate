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
    IrcError
        IrcConnectionError
            IrcBadServerNameError
            IrcBadServerPortError
            IrcInitialConnectionTimeoutError
            IrcRanOutOfReconnectionsError
            IrcStillConnectingError
            IrcRealnameTruncationError
            IrcFingerprintMismatchCausedByServer
            IrcNicknameChangedByServer
        IrcDisconnectionError
            IrcDisconnectionTakingTooLongError
            IrcAlreadyDisconnectedError
            IrcYouCantUseABotAfterQuittingItError
        IrcChannelError
            IrcJoiningChannelTimeoutError
            IrcPartingChannelTimeoutError
            IrcBadChannelNameError
            IrcChannelNameTooLongError
            IrcIAmNotInTheChannelError
        IrcMessagingError
            IrcBadNicknameError
            IrcDuplicateNicknameError
            IrcNicknameTooLongError
            IrcUnknownIncomingCommandError
            IrcPrivateMessageTooLongError
            IrcPrivateMessageContainsBadCharsError
            IrcIncomingCommandFromMyselfError
    EncryptionError
        EncryptionHandshakingError
            EncryptionHandshakeTimeoutError
        EncryptionKeyError
            PublicKeyError
                PublicKeyBadKeyError
                PublicKeyUnknownError
                PublicKeyIncompleteError
                PublicKeyTooBigError
            FernetKeyError
                FernetKeyIsUnknownError
                FernetKeyIsInvalidError
    RookeryError
        RookeryCorridorError
            RookeryCorridorAlreadyClosedError
            RookeryCorridorNoTrueHomiesError
            RookeryCorridorNotOpenYetError

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


class IrcError(Error):
    """Class for all IrcErrors"""

    def __init__(self, message):  # pylint: disable=useless-parent-delegation

        super().__init__(message)


class IrcConnectionError(IrcError):
    """Class for all IrcConnectionError"""

    def __init__(self, message):  # pylint: disable=useless-parent-delegation

        super().__init__(message)


class IrcBadServerNameError(IrcConnectionError):
    """Class for all IrcConnectionError"""

    def __init__(self, message):  # pylint: disable=useless-parent-delegation

        super().__init__(message)


class IrcBadServerPortError(IrcConnectionError):
    """Class for all IrcConnectionError"""

    def __init__(self, message):  # pylint: disable=useless-parent-delegation

        super().__init__(message)


class IrcInitialConnectionTimeoutError(IrcConnectionError):
    """Connecting took too long."""

    def __init__(self, message):  # pylint: disable=useless-parent-delegation

        super().__init__(message)


class IrcRanOutOfReconnectionsError(IrcConnectionError):
    """Connecting took too long."""

    def __init__(self, message):  # pylint: disable=useless-parent-delegation

        super().__init__(message)


class IrcStillConnectingError(IrcConnectionError):
    """Still connecting (wait a few seconds, please)"""

    def __init__(self, message):  # pylint: disable=useless-parent-delegation

        super().__init__(message)


class IrcRealnameTruncationError(IrcConnectionError):
    """If the realname is truncated by the server"""

    def __init__(self, message):  # pylint: disable=useless-parent-delegation

        super().__init__(message)


class IrcFingerprintMismatchCausedByServer(IrcConnectionError):
    """My local fingerprint and the server's copy of my fingerprint do not match, perhaps because my nickname changed somewhere"""

    def __init__(self, message):  # pylint: disable=useless-parent-delegation

        super().__init__(message)


class IrcDisconnectionError(IrcError):
    """Class for all IrcDisConnectionError"""

    def __init__(self, message):  # pylint: disable=useless-parent-delegation

        super().__init__(message)


class IrcDisconnectionTakingTooLongError(IrcDisconnectionError):
    """Unknown incoming command."""

    def __init__(self, message):  # pylint: disable=useless-parent-delegation

        super().__init__(message)


class IrcAlreadyDisconnectedError(IrcDisconnectionError):
    """Unknown incoming command."""

    def __init__(self, message):  # pylint: disable=useless-parent-delegation

        super().__init__(message)


class IrcYouCantUseABotAfterQuittingItError(IrcDisconnectionError):
    """Unknown incoming command."""

    def __init__(self, message):  # pylint: disable=useless-parent-delegation

        super().__init__(message)


class IrcMessagingError(IrcError):
    """Class for all IrcMessagingError"""

    def __init__(self, message):  # pylint: disable=useless-parent-delegation

        super().__init__(message)


class IrcBadNicknameError(IrcMessagingError):
    """Unknown incoming command."""

    def __init__(self, message):  # pylint: disable=useless-parent-delegation

        super().__init__(message)


class IrcDuplicateNicknameError(IrcMessagingError):
    """Unknown incoming command."""

    def __init__(self, message):  # pylint: disable=useless-parent-delegation

        super().__init__(message)


class IrcNicknameTooLongError(IrcMessagingError):
    """Unknown incoming command."""

    def __init__(self, message):  # pylint: disable=useless-parent-delegation

        super().__init__(message)


class IrcUnknownIncomingCommandError(IrcMessagingError):
    """Unknown incoming command."""

    def __init__(self, message):  # pylint: disable=useless-parent-delegation

        super().__init__(message)


class IrcPrivateMessageTooLongError(IrcMessagingError):
    """Message too long."""

    def __init__(self, message):  # pylint: disable=useless-parent-delegation

        super().__init__(message)


class IrcPrivateMessageContainsBadCharsError(IrcMessagingError):
    """Message contains bad chars."""

    def __init__(self, message):  # pylint: disable=useless-parent-delegation

        super().__init__(message)


class IrcIncomingCommandFromMyselfError(IrcMessagingError):
    """Why am I talking to myself?"""

    def __init__(self, message):  # pylint: disable=useless-parent-delegation

        super().__init__(message)


class IrcNicknameChangedByServer(IrcConnectionError):
    """If the nickname is CHANGED by the server, probably because of a nickname collision"""

    def __init__(self, message):  # pylint: disable=useless-parent-delegation

        super().__init__(message)


class IrcChannelError(IrcError):
    """Class for all channel errors"""

    def __init__(self, message):  # pylint: disable=useless-parent-delegation

        super().__init__(message)


class IrcJoiningChannelTimeoutError(IrcChannelError):
    """Class for all """

    def __init__(self, message):  # pylint: disable=useless-parent-delegation

        super().__init__(message)


class IrcPartingChannelTimeoutError(IrcChannelError):
    """Class for all """

    def __init__(self, message):  # pylint: disable=useless-parent-delegation

        super().__init__(message)


class IrcBadChannelNameError(IrcChannelError):
    """Class for all """

    def __init__(self, message):  # pylint: disable=useless-parent-delegation

        super().__init__(message)


class IrcChannelNameTooLongError(IrcChannelError):
    """Class for all """

    def __init__(self, message):  # pylint: disable=useless-parent-delegation

        super().__init__(message)


class IrcIAmNotInTheChannelError(IrcChannelError):
    """Class for all """

    def __init__(self, message):  # pylint: disable=useless-parent-delegation

        super().__init__(message)


class EncryptionError(Error):
    """Class for all EncryptionError"""

    def __init__(self, message):  # pylint: disable=useless-parent-delegation

        super().__init__(message)


class EncryptionHandshakingError(EncryptionError):
    """"""

    def __init__(self, message):  # pylint: disable=useless-parent-delegation

        super().__init__(message)


class EncryptionHandshakeTimeoutError(EncryptionHandshakingError):
    """"""

    def __init__(self, message):  # pylint: disable=useless-parent-delegation

        super().__init__(message)


class EncryptionKeyError(EncryptionError):
    """"""

    def __init__(self, message):  # pylint: disable=useless-parent-delegation

        super().__init__(message)


class PublicKeyError(EncryptionKeyError):
    """"""

    def __init__(self, message):  # pylint: disable=useless-parent-delegation

        super().__init__(message)


class PublicKeyBadKeyError(PublicKeyError):
    """"""

    def __init__(self, message):  # pylint: disable=useless-parent-delegation

        super().__init__(message)


class PublicKeyUnknownError(PublicKeyError):
    """I don't know his public key yet."""

    def __init__(self, message):  # pylint: disable=useless-parent-delegation

        super().__init__(message)


class PublicKeyIncompleteError(PublicKeyError):
    """Public key is incomplete."""

    def __init__(self, message):  # pylint: disable=useless-parent-delegation

        super().__init__(message)


class PublicKeyTooBigError(PublicKeyError):
    """Public key is too big for /whois."""

    def __init__(self, message):  # pylint: disable=useless-parent-delegation

        super().__init__(message)


class FernetKeyError(EncryptionKeyError):
    """Class for all ???"""

    def __init__(self, message):  # pylint: disable=useless-parent-delegation

        super().__init__(message)


class FernetKeyIsUnknownError(PublicKeyError):
    """I don't know his fernet key yet."""

    def __init__(self, message):  # pylint: disable=useless-parent-delegation

        super().__init__(message)


class FernetKeyIsInvalidError(EncryptionError):
    """Fernet key is invalid"""

    def __init__(self, message):  # pylint: disable=useless-parent-delegation

        super().__init__(message)


class RookeryError(Error):
    """Class for all RookeryError"""

    def __init__(self, message):  # pylint: disable=useless-parent-delegation

        super().__init__(message)


class RookeryCorridorError(RookeryError):
    """Class for all RookeryCorridorError"""

    def __init__(self, message):  # pylint: disable=useless-parent-delegation

        super().__init__(message)


class RookeryCorridorAlreadyClosedError(RookeryCorridorError):
    """"""

    def __init__(self, message):  # pylint: disable=useless-parent-delegation

        super().__init__(message)


class RookeryCorridorNoTrueHomiesError(RookeryCorridorError):
    """There are no available homies for this corridor."""

    def __init__(self, message):  # pylint: disable=useless-parent-delegation

        super().__init__(message)


class RookeryCorridorNotOpenYetError(RookeryCorridorError):
    """"""

    def __init__(self, message):  # pylint: disable=useless-parent-delegation

        super().__init__(message)

