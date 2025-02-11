"""PrateBot class(es) for miniircd-ish... boring.

Created on Jan 30, 2025

@author: mchobbit

This module contains classes for creating a Prate class that monitors the IRC
server and sets up secure comms between users.

Todo:
    * Better docs
    * Detect if users' nicknames change
    * Make the users' dictionary threadsafe
    * Make the entire class threadsafe
    * Use the public keys' fingerprints, not the users' nicknames, as the key for the dictionary
    * Turn the users' dictionary into a class
    * Auto-check the nicknames whenever using a dictionary entry

.. _Google Python Style Guide:
   http://google.github.io/styleguide/pyguide.html

.. _Napoleon Style Guide:
   https://sphinxcontrib-napoleon.readthedocs.io/en/latest/example_google.html

Example:



"""

from my.irctools.cryptoish import sha1, squeeze_da_keez
import sys
import queue
from time import sleep
from threading import Thread, Lock

from cryptography.fernet import Fernet, InvalidToken
import base64
from my.globals import MY_IP_ADDRESS
from my.classes.readwritelock import ReadWriteLock
from my.irctools.cryptoish import rsa_decrypt, rsa_encrypt, unsqueeze_da_keez
from _queue import Empty
from random import randint, choice, shuffle
from my.irctools.jaracorocks.vanilla import SingleServerIRCBotWithWhoisSupport
import datetime
from my.classes import MyTTLCache
import time
from my.classes.homies import HomiesDct
from my.classes.exceptions import IrcInitialConnectionTimeoutError, IrcFingerprintMismatchCausedByServer

