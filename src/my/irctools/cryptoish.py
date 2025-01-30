'''
Created on Jan 30, 2025

@author: mchobbit
'''

import requests
import types
import irc.bot
import sys
import queue

import datetime
from time import sleep
from my.stringtools import generate_irc_handle, get_word_salad, get_bits_to_be_encoded, encode_via_steg, decode_via_steg, strict_encode_via_steg, multiline_encode_via_steg
from random import randint, choice, shuffle
from threading import Thread
from _queue import Empty

from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP
from cryptography.fernet import Fernet, InvalidToken
import base64
from dns.rdataclass import NONE
from my.globals import RPL_WHOISUSER, RPL_ENDOFWHOIS, WHOIS_ERRORS_LST, WHOIS_RESPCODE_LST
from my.globals.poetry import CICERO
from my.classes.readwritelock import ReadWriteLock
from my.irctools.jaracorocks import add_whois_support_to_ircbot


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
        raise ValueError("Invalid key") from e


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
        raise ValueError("Invalid key") from e


def pubkey_to_b85(pubkey):
    return pubkey_to_bXX(pubkey, base64.b85encode)


def b85_to_pubkey(b85slim):
    return bXX_to_pubkey(b85slim, base64.b85decode)


def pubkey_to_b64(pubkey):
    return pubkey_to_bXX(pubkey, base64.b64encode)


def b64_to_pubkey(b64slim):
    return bXX_to_pubkey(b64slim, base64.b64decode)

# def pubkey_to_b85(pubkey):
#     assert(type(pubkey) is RSA.RsaKey)  # e.g.
#     hex_key_n = hex(pubkey.n)[2:]
#     hex_key_e = hex(pubkey.e)[2:]
#     if len(hex_key_n) % 2 == 1:
#         hex_key_n = '0' + hex_key_n
#     if len(hex_key_e) % 2 == 1:
#         hex_key_e = '0' + hex_key_e
#     bytekey_n = bytearray.fromhex(hex_key_n)
#     bytekey_e = bytearray.fromhex(hex_key_e)
#     b85key_n = base64.b85encode(bytekey_n)
#     b85key_e = base64.b85encode(bytekey_e)
#     b85slim = "%s %s" % (b85key_n.decode(), b85key_e.decode())
#     return b85slim
#
#
# def b85_to_pubkey(b85slim):
#     _b85key_n, _b85key_e = [r.encode() for r in  b85slim.split(' ')]
#     _bytekey_n = base64.b85decode(_b85key_n)
#     _bytekey_e = base64.b85decode(_b85key_e)
#     _hex_key_n = ''.join('{:02x}'.format(x) for x in _bytekey_n)
#     _hex_key_e = ''.join('{:02x}'.format(x) for x in _bytekey_e)
#     _n = int("0x%s" % _hex_key_n, 16)
#     _e = int("0x%s" % _hex_key_e, 16)
#     pubkey = RSA.RsaKey(n=_n, e=_e)
#     return pubkey


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


def rsa_decrypt(cipher_text:bytes) -> bytes:
    """Decrypt a binary block, using a public key.

    Args:
        cipher_text: The ciphertext.

    Returns:
        The plaintext.

    """
    from my.globals import MY_RSAKEY
    private_key = MY_RSAKEY.export_key()
    cipher_rsa = PKCS1_OAEP.new(RSA.import_key(private_key))
    plain_text = cipher_rsa.decrypt(cipher_text)
    return plain_text  # .decode()  # print(f"Decrypted: {plain_text.decode()}")


def get_random_Cicero_line() -> str:
    """Return a randomly chosen passage from Cicero.

    Returns:
        Cicero's wisdom.

    """
    all_useful_lines = [r for r in CICERO.split('\n') if len(r) >= 5]
    return str(choice(all_useful_lines))

