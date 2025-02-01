# -*- coding: utf-8 -*-
"""Global variables and consts, used by our project.

This module contains various constants and global variables that our project
uses.

Todo:
    * Better docs

.. _Google Python Style Guide:
   http://google.github.io/styleguide/pyguide.html

.. _Napoleon Style Guide:
   https://sphinxcontrib-napoleon.readthedocs.io/en/latest/example_google.html

"""
from my.globals.poetry import CICERO, HAMLET
import requests
from Crypto.PublicKey import RSA
from my.pybase122 import b122encode, b122decode
VANILLA_WORD_SALAD = CICERO  # + ". " + HAMLET + ". "
MY_RSAKEY = RSA.generate(1024)


def get_my_public_ip_address():
    """Get my public IP address.

    Deduce my public IP address. Return it as a string.

    Args:
        none

    Returns:
        str: The IP address, or None if failure.

    """
    from requests import get
    endpoint = 'https://ipinfo.io/json'
    response = get(endpoint, verify=True)
    if response.status_code != 200:
        ip1 = None
        # print('Status:', response.status_code, 'Problem with the request. Exiting.')
        # raise ValueError("UNABLE TO GET IP ADDRESS : %s" % response.reason)
    else:
        data = response.json()
        ip1 = data['ip']
    ip2 = get('https://api.ipify.org').content.decode('utf8')
    if ip1 is None:
        ip1 = ip2
    if ip1 != ip2:
        print("Warning -- ip1 != ip2")
    return ip2


steg_dct_CLUMPS = {'a':
                   {'а':'0', 'ạ':'1', 'ą':'00', 'ä':'01', 'à':'10', 'á':'11', 'ą':'000'},
                   'c':
                   {'с':'0', 'ƈ':'1', 'ċ':'00'},
                   'd':
                   {'ԁ':'0', 'ɗ':'1'},
                   'e':
                   {'е':'0', 'ẹ':'1', 'ė':'00', 'é':'01', 'è':'10'},
                   'g':
                   {'ġ':'0'},
                   'h':
                   {'һ':'1'},
                   'i':
                   {'і':'0', 'í':'1', 'ï':'10'},
                   'j':
                   {'j':'0', 'ʝ':'1'},
                   'k':
                   {'κ':'1'},
                   'l':
                   {'ӏ':'0', 'ḷ':'1'},
                   'n':
                   {'ո':'0'},
                   'o':
                   {'о':'0', 'ο':'1', 'օ':'00', 'ȯ':'01', 'ọ':'10', 'ỏ':'11', 'ơ':'000', 'ó':'111', 'ò':'101', 'ö':'010'},
                   'p':
                   {'р':'1'},
                   'q':
                   {'զ':'0'},
                   's':
                   {'ʂ':'1'},
                   'u':
                   {'υ':'0', 'ս':'1', 'ü':'00', 'ú':'01', 'ù':'10'},
                   'v':
                   {'ν':'0', 'ѵ':'1'},
                   'x':
                   {'х':'0', 'ҳ':'1'},
                   'y':
                   {'у':'0', 'ý':'1'},
                   'z':
                   {'ʐ':'0', 'ż':'1'}}

ALL_IRC_NETWORK_NAMES = ('irc.2600.net', 'irc.afternet.org', 'irc.data.it', 'irc.anthrochat.net',
                    'arcnet-irc.org', 'irc.austnet.org', 'irc.canternet.org', 'irc.chat4all.org',
                    'irc.chatjunkies.org', 'irc.unibg.net', 'irc.chatspike.net', 'irc.dairc.net',
                    'us.dal.net', 'irc.darkmyst.org', 'irc.darkscience.net', 'irc.digitalirc.org',
                    'irc.choopa.net', 'irc.underworld.no', 'efnet.port80.se', 'irc.entropynet.net',
                    'irc.euirc.net', 'irc.interlinked.me', 'irc.irc4fun.net', 'open.ircnet.net',
                    'irc.libera.chat', 'irc.othernet.org', 'irc.quakenet.org', 'irc.swiftirc.net',
                    'irc.undernet.org')

ERR_NOSUCHNICK = 401
ERR_NOSUCHSERVER = 402
ERR_NONICKNAMEGIVEN = 431
RPL_WHOISCERTFP = 276
RPL_WHOISREGNICK = 307
RPL_WHOISUSER = 311  # response to /WHOIS <user>
RPL_WHOISSERVER = 312
RPL_WHOISOPERATOR = 313
RPL_WHOISIDLE = 317
RPL_WHOISCHANNELS = 319
RPL_WHOISSPECIAL = 320
RPL_WHOISACCOUNT = 330
RPL_WHOISACTUALLY = 338
RPL_WHOISHOST = 378
RPL_WHOISMODES = 379
RPL_WHOISSECURE = 671
RPL_ENDOFWHOIS = 318
RPL_AWAY = 301
RPL_NAMREPLY = 353  # response to /NAMES
RPL_ENDOFNAMES = 366

WHOIS_ERRORS_LST = [ERR_NOSUCHNICK, ERR_NOSUCHSERVER, ERR_NOSUCHSERVER]
WHOIS_RESPCODE_LST = [ERR_NOSUCHNICK, ERR_NOSUCHSERVER, ERR_NONICKNAMEGIVEN, RPL_WHOISCERTFP,
            RPL_WHOISREGNICK, RPL_WHOISUSER, RPL_WHOISSERVER, RPL_WHOISOPERATOR, RPL_WHOISIDLE,
            RPL_WHOISCHANNELS, RPL_WHOISSPECIAL, RPL_WHOISACCOUNT, RPL_WHOISACTUALLY,
            RPL_WHOISHOST, RPL_WHOISMODES, RPL_WHOISSECURE, RPL_AWAY, RPL_ENDOFWHOIS]

try:
    MY_IP_ADDRESS = get_my_public_ip_address()
except:
    MY_IP_ADDRESS = "127.0.0.1"

