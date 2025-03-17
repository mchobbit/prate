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
import requests
from Crypto.PublicKey import RSA
from my.stringtools.pybase122 import b122encode, b122decode
from my.stringtools import MAX_NICKNAME_LENGTH
SENSIBLE_NOOF_RECONNECTIONS = 2
JOINPARTCHAN_TIMEOUT = 15
STARTUP_TIMEOUT = 30
HANDSHAKE_TIMEOUT = 30
ANTIOVERLOAD_CACHE_TIME = 10  # pings, dupe msgs, etc.
DEFAULT_WHOIS_TIMEOUT = 10  # how long should we wait for a response to a /whois call?
RSA_KEY_SIZE = 1024  # 2048 is normal
MAX_PRIVMSG_LENGTH = 500  # 500 works; 501 does not.
MAX_CHANNEL_LENGTH = 10  # I made it up.
ENDTHREAD_TIMEOUT = 20
MAX_CRYPTO_MSG_LENGTH = int((MAX_PRIVMSG_LENGTH - MAX_NICKNAME_LENGTH) * 0.618)
A_TICK = 0.1  # ... as in, 'hold on a tick!'


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
    response = get(endpoint, timeout=30, verify=True)
    if response.status_code != 200:
        ip1 = None
        # print('Status:', response.status_code, 'Problem with the request. Exiting.')
        # raise ValueError("UNABLE TO GET IP ADDRESS : %s" % response.reason)
    else:
        data = response.json()
        ip1 = data['ip']
    ip2 = get('https://api.ipify.org', timeout=30).content.decode('utf8')
    if ip1 is None:
        ip1 = ip2
    if ip1 != ip2:
        print("Warning -- ip1 != ip2")
    return ip2


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
except Exception as e:  # pylint: disable=broad-exception-caught
    print("Warning — unable to grab IP address:", e)
    MY_IP_ADDRESS = "127.0.0.1"

PARAGRAPH_OF_ALL_IRC_NETWORK_NAMES = """
irc.libera.chat
irc.oftc.net
irc.undernet.org
irc.IRCnet.net
irc.IRCnet.com
irc.hackint.org
irc.rizon.net
irc.hybridirc.com
irc.efnet.org
irc.chatzona.org
irc.quakenet.org
irc.azirc.net
irc.freeunibg.eu
irc.p2p-network.net
irc.chathispano.com
irc.snoonet.org
irc.simosnap.com
irc.aaviera.com
irc.europnet.org
irc.kampungchat.org
irc.abjects.net
irc.link-net.be
irc.gamesurge.net
irc.synirc.net
irc.esper.net
irc.chaat.fr
irc.eXpLoSioNiRc.net
irc-nerds.net
irc.digitalirc.org
irc.chattersnet.nl
irc.irchighway.net
irc.scenep2p.net
irc.tilde.chat
irc.bgirc.com
irc.orixon.org
irc.geeknode.org
irc.ptirc.org
irc.skychatz.org
irc.allnetwork.org
irc.globalirc.it
irc.sohbet.net
irc.darkfasel.net
irc.dejatoons.net
irc.euirc.net
irc.furnet.org
irc.bol-chat.com
irc.xxxchatters.com
irccloud.com
irc.virtualife.org
irc.openjoke.org
irc.Kalbim.Net
irc.ptnet.org
irc.allnightcafe.com
irc.rezosup.org
irc.darkworld.network
irc.net-tchat.fr
irc.sorcery.net
irc.mindforge.org
irc.slashnet.org
irc.abandoned-irc.net
irc.redesul.net.br
irc.tamarou.com
irc.do-dear.com
irc.evilnet.org
irc.afternet.org
irc.deutscher-chat.de
irc.global-irc.eu
irc.swiftirc.net
irc.redebrasnet.org
irc.pirc.pl
irc.epiknet.org
irc.SohbetBurada.Com
irc.soyle.net
irc.librairc.net
irc.oddprotocol.org
irc2.acc.umu.se
irc.bigua.org
irc.smurfnet.ch
irc.atrum.org
irc.twistednet.org
irc.cord.atw.hu
irc.lewdchat.com
irc.aitvaras.eu
irc.lunarirc.net
irc.chatlounge.net
irc.w3.org
irc.bondage.international
irc.zenet.org
irc.german-elite.net
irc.cool.chat
irc.luatic.net
irc.2600.net
irc.data.it
irc.anthrochat.net
irc.arcnet-irc.org
irc.austnet.org
irc.canternet.org
irc.chat4all.org
irc.chatjunkies.org
irc.unibg.net
irc.chatspike.net
irc.dairc.net
irc.darkmyst.org
irc.darkscience.net
irc.digitalirc.org
irc.entropynet.net
irc.interlinked.me
irc.irc4fun.net
irc.othernet.org
irc.spotchat.org
irc.dal.net
irc.underworld.no
irc.freenode.net
irc.evochat.id
irc.choopa.net
irc.geekshed.net
"""

ALL_REALWORLD_IRC_NETWORK_NAMES = [r for r in PARAGRAPH_OF_ALL_IRC_NETWORK_NAMES.replace('\n', ' ').split(' ') if r != '']

ALL_SANDBOX_IRC_NETWORK_NAMES = ('rpi0irc2.local', 'rpi0irc3.local', 'rpi0irc1.local',
                               'rpi0irc4.local', 'rpi0irc5.local', 'rpi0irc6.local',
                               'rpi0irc7.local', 'rpi0irc8.local', 'rpi0irc9.local',
                               'rpi0irc10.local', 'rpi0irc11.local', 'rpi0irc12.local',
                               'rpi0irc13.local', 'rpi0irc14.local', 'rpi0irc15.local',
                               'rpi0irc16.local', 'rpi0irc17.local', 'rpi0irc18.local',
                               'gmkone.local', 'gmktwo.local', 'rpi4b.local', 'cinqcent.local')

