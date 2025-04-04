# -*- coding: utf-8 -*-
"""Crypto-related subroutines.

Created on Jan 30, 2025

@author: mchobbit

This module contains subroutines for handling Prate crypto. There is
more to it than that, of course.

Todo:
    * Better docs

.. _Google Python Style Guide:
   http://google.github.io/styleguide/pyguide.html

.. _Napoleon Style Guide:
   https://sphinxcontrib-napoleon.readthedocs.io/en/latest/example_google.html

Example:

"""

from random import choice
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP
import base64
from my.globals.poetry import CICERO
import hashlib
from my.classes.exceptions import PublicKeyBadKeyError, FernetKeyIsInvalidError, FernetKeyIsUnknownError
from cryptography.fernet import Fernet, InvalidToken
from threading import Lock
import datetime


def sha1(nickname):
    return base64.b85encode(hashlib.sha1(nickname.encode()).digest()).decode()


def datetimenow_to_4bytes():
    n = datetime.datetime.now()
    return (n.minute * 60000000 + n.second * 1000000 + n.microsecond).to_bytes(4, 'little')


def datetimenow_to_int():
    n = datetime.datetime.now()
    return (n.minute * 60000000 + n.second * 1000000 + n.microsecond)


def skinny_key(k:RSA.RsaKey) -> str:
    """Remove the header and footer from a generic public key, to prep it for transmission via IRC.

    Args:
        k: The regular public key.

    Returns:
        The stripped public key text, with all clever formatting removed.

    """
    return ''.join([r + '-' for r in k.export_key().decode().split('\n')[1:-1]]).strip()


def unskin_key(k:str) -> RSA.RsaKey:
    """Reconstitute a stripped generic public key, after receiving it via IRC.

    Args:
        k: The stripped public key text.

    Returns:
        The regular public key text, with all clever formatting restored.

    """
    s = '-----BEGIN PUBLIC KEY-----\n' + k.replace('-', '\n') + '\n-----END PUBLIC KEY-----'
    return RSA.import_key(s)


def pubkey_to_bXX(pubkey, the_encoder):
    if type(pubkey) is not RSA.RsaKey:
        raise ValueError("pubkey should be type RSA.RsaKey")
    try:
        hex_key_n = hex(pubkey.n)[2:]
        hex_key_e = hex(pubkey.e)[2:]
        if len(hex_key_n) % 2 == 1:
            hex_key_n = '0' + hex_key_n
        if len(hex_key_e) % 2 == 1:
            hex_key_e = '0' + hex_key_e
        bytekey_n = bytearray.fromhex(hex_key_n)
        bytekey_e = bytearray.fromhex(hex_key_e)
        bXXkey_n = the_encoder(bytekey_n)
        bXXkey_e = the_encoder(bytekey_e)
        bXXslim = "%s %s" % (bXXkey_n.decode(), bXXkey_e.decode())
        return bXXslim
    except Exception as e:
        raise PublicKeyBadKeyError("Invalid key") from e


def bXX_to_pubkey(bXXslim, the_decoder):
    try:
        _bXXkey_n, _bXXkey_e = [r.encode() for r in  bXXslim.split(' ')]
        _bytekey_n = the_decoder(_bXXkey_n)
        _bytekey_e = the_decoder(_bXXkey_e)
        _hex_key_n = ''.join('{:02x}'.format(x) for x in _bytekey_n)
        _hex_key_e = ''.join('{:02x}'.format(x) for x in _bytekey_e)
        _n = int("0x%s" % _hex_key_n, 16)
        _e = int("0x%s" % _hex_key_e, 16)
        pubkey = RSA.RsaKey(n=_n, e=_e)
        return pubkey
    except Exception as e:
        raise PublicKeyBadKeyError("Invalid key") from e


def pubkey_to_b85(pubkey):
    return pubkey_to_bXX(pubkey, base64.b85encode)


def b85_to_pubkey(b85slim):
    return bXX_to_pubkey(b85slim, base64.b85decode)


def pubkey_to_b64(pubkey):
    return pubkey_to_bXX(pubkey, base64.b64encode)


def b64_to_pubkey(b64slim):
    return bXX_to_pubkey(b64slim, base64.b64decode)


def rsa_encrypt(message:bytes, public_key) -> bytes:
    """Encrypt a binary block, using a public key.

    Args:
        message: The plaintext.
        public_key: The public key to use.

    Returns:
        The ciphertext.
    """
    cipher_rsa = PKCS1_OAEP.new(public_key)
    return cipher_rsa.encrypt(message)


def rsa_decrypt(cipher_text:bytes, rsakey) -> bytes:
    """Decrypt a binary block, using a public key.

    Args:
        cipher_text: The ciphertext.
        rsakey: My private RSA key.

    Returns:
        The plaintext.

    """
    cipher_rsa = PKCS1_OAEP.new(rsakey)
    plain_text = cipher_rsa.decrypt(cipher_text)
    return plain_text


def get_random_Cicero_line() -> str:
    """Return a randomly chosen passage from Cicero.

    Returns:
        Cicero's wisdom.

    """
    all_useful_lines = [r for r in CICERO.split('\n') if len(r) >= 5]
    return str(choice(all_useful_lines))


sdkmutex = Lock()


def squeeze_da_keez(i):
    """Compress the supplied RSA public key. Spit out b85 ascii."""
#    return skinny_key(i)
    with sdkmutex:
        return pubkey_to_b85(i)


def unsqueeze_da_keez(i):
    """Decompress the supplied b85 ascii. Spit out RSA public key."""
#    return unskin_key(i)
    return b85_to_pubkey(i)


def generate_fingerprint(s):
    if type(s) is not str:
        raise ValueError("generate_fingerprint() takes a string")
    return sha1(s)


def receive_and_decrypt_message(ciphertext, fernetkey):
    try:
        cipher_suite = Fernet(fernetkey)
        decoded_msg = cipher_suite.decrypt(ciphertext)
    except InvalidToken as e:
        raise FernetKeyIsInvalidError("Warning - failed to decode %s's message (key bad? ciphertext bad?)." % str(ciphertext)) from e
    except KeyError:
        raise FernetKeyIsUnknownError("Warning - failed to decode %s's message (fernet key not found?). Is his copy of my public key out of date?") from e
    else:
        return decoded_msg


def int_64bit_cksum(byteblock):
    return (int.from_bytes(bytes_64bit_cksum(byteblock), 'little'))


def bytes_64bit_cksum(byteblock):
    return hashlib.sha256(byteblock).digest()[:8]

