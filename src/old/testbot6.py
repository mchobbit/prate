#!/usr/bin/env python3

"""
sayhello(str, ip)
    - send a simple hello, quoting Cicero, to other members of the channel.

"""
import irc.bot
import sys
import queue

import datetime
from time import sleep
from my.stringtools import generate_irc_handle, multiline_encode_via_steg, get_word_salad, get_bits_to_be_encoded, encode_via_steg, decode_via_steg, strict_encode_via_steg, multiline_encode_via_steg
from random import randint, choice, shuffle
from my.globals.poetry import CICERO
from my.irctools import get_my_public_ip_address, MyGroovyTestBot
from threading import Thread
from _queue import Empty

from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP
from cryptography.fernet import Fernet, InvalidToken
import base64
from dns.rdataclass import NONE
# Generate RSA keys
MY_IP_ADDRESS = get_my_public_ip_address()
MY_RSAKEY = RSA.generate(1024)
MY_PUBLIC_KEY = MY_RSAKEY.publickey().export_key()

# pip3 install pycryptodome

# https://medium.com/@info_82002/a-beginners-guide-to-encryption-and-decryption-in-python-12d81f6a9eac


def skinny_key(k):
    return ''.join([r + '-' for r in k.decode().split('\n')[1:-1]]).strip()


def unskin_key(k):
    s = '-----BEGIN PUBLIC KEY-----\n' + k.replace('-', '\n') + '\n-----END PUBLIC KEY-----'
    return s.encode()


def rsa_encrypt(message, public_key=None):
    if public_key is None:
        public_key = MY_PUBLIC_KEY
    cipher_rsa = PKCS1_OAEP.new(RSA.import_key(public_key))
    return cipher_rsa.encrypt(message)


def rsa_decrypt(cipher_text):
    private_key = MY_RSAKEY.export_key()
    cipher_rsa = PKCS1_OAEP.new(RSA.import_key(private_key))
    plain_text = cipher_rsa.decrypt(cipher_text)
    return plain_text  # .decode()  # print(f"Decrypted: {plain_text.decode()}")


def get_random_Cicero_line():
    all_useful_lines = [r for r in CICERO.split('\n') if len(r) >= 5]
    return str(choice(all_useful_lines))


class MyObject(object):
    pass


USERS_DCT = {}


def send_encrypted_byteblock(server, dest, byteblock):
    assert(type(byteblock) is bytes)
    cipher_suite = Fernet(USERS_DCT[dest]['fernetkey'])
    cipher_text = cipher_suite.encrypt(byteblock)
    server.put(dest, "TXTXTX%s" % cipher_text.decode(), encrypted=False)


def show_users_dct_info():
    global LAST_SDDS
    for k in USERS_DCT:
        if USERS_DCT[k] is None:
            pass
        elif USERS_DCT[k]['ipaddr'] is not None:
            print("%-20s pubkey OK, fernetkey OK, IP=%s" % (k, USERS_DCT[k]['ipaddr']))
        elif USERS_DCT[k]['ipaddr'] is None:
            print("%-20s pubkey OK, fernetkey OK" % k)
        elif USERS_DCT[k]['fernetkey'] is None:
            print("%-20s pubkey OK" % k)
        elif USERS_DCT[k]['pubkey'] is None:
            print("%-20s ?" % k)
        else:
            print("%-20s ????" % k)


def wait_until_connected_and_joined(server, the_channel):
    print("Waiting for connection")
    while not server.connected:
        sleep(1)
    print("Connected. Waiting to join channel")
    while the_channel not in server.channels:
        sleep(1)
    print("*** MY NAME IS %s ***" % server.nickname)
    print("Joined. Waiting for incoming messages")


def process_incoming_message(server, wait=True):
    (connection, event) = get_from_irc(server, wait)
    return act_on_msg_from_irc(connection, server, event)


def get_from_irc(server, wait=True):
    return server.get() if wait else server.get_nowait()


def _pubkey(server, sender, stem):
    global USERS_DCT
    USERS_DCT[sender]['pubkey'] = unskin_key(stem)
    USERS_DCT[sender]['fernetkey'] = Fernet.generate_key()
    print("I have received %s's pubkey. Yay." % sender)
    print("Sending %s my fernet key:    %s" % (sender, str(USERS_DCT[sender]['fernetkey'])))
    ciphertext = rsa_encrypt(message=USERS_DCT[sender]['fernetkey'], public_key=USERS_DCT[sender]['pubkey'])
    b64ciphertext = base64.b64encode(ciphertext).decode()
    server.put(sender, "MYFERN%s" % b64ciphertext)  # Sending him the symmetric key


def my_encrypted_ipaddr(sender):
    cipher_suite = Fernet(USERS_DCT[sender]['fernetkey'])
    ipaddr_str = MY_IP_ADDRESS
    cipher_text = cipher_suite.encrypt(ipaddr_str.encode())
    return cipher_text.decode()


def _myfern(server, sender, stem):
    global USERS_DCT
    new_fernetkey = rsa_decrypt(base64.b64decode(stem))
    if USERS_DCT[sender]['fernetkey'] is None:
        print("%s has sent me a new fernet: %s ... and it's our first from him. So, we'll accept it." % (sender, new_fernetkey))
        USERS_DCT[sender]['fernetkey'] = new_fernetkey
    elif base64.b64encode(USERS_DCT[sender]['fernetkey']) < base64.b64encode(new_fernetkey):
        print("%s has sent me a new fernet: %s ... and it's replacing a lower-ascii'd one." % (sender, new_fernetkey))
        USERS_DCT[sender]['fernetkey'] = new_fernetkey
    else:
        print("%s's new fernet is ignored;  %s will be kept instead, as it's higher-ascii'd" % (sender, new_fernetkey))
    server.put(sender, "ALI_IP%s" % my_encrypted_ipaddr(sender))


def _either_ali_or_bob_ip(server, sender, stem):
    global USERS_DCT
    print("I have received an IP address block from %s" % sender)
    assert(USERS_DCT[sender]['fernetkey'] is not None)
    cipher_suite = Fernet(USERS_DCT[sender]['fernetkey'])
    try:
        decoded_msg = cipher_suite.decrypt(stem)
    except InvalidToken:
        return "Warning - failed to decode %s's message. " % sender
    ipaddr = decoded_msg.decode()
#    quid_pro_quo = True if USERS_DCT[sender]['ipaddr'] is None else False
    USERS_DCT[sender]['ipaddr'] = ipaddr
    print("Received IP address (%s) for %s" % (ipaddr, sender))


def _ali_ip(server, sender, stem):
    _either_ali_or_bob_ip(server, sender, stem)
    server.put(sender, "BOB_IP%s" % my_encrypted_ipaddr(sender))


def _bob_ip(server, sender, stem):
    _either_ali_or_bob_ip(server, sender, stem)
#    print("Oi, oi! That's yet lot!")


def act_on_msg_from_irc(connection, server, event):
    global USERS_DCT
    sender = event.source.split('@')[0].split('!')[0]
    if sender not in USERS_DCT:
        USERS_DCT[sender] = {'pubkey':None, 'ipaddr':None, 'fernetkey':None}
    txt = event.arguments[0]
    cmd = txt[:6]
    stem = txt[6:]
    assert(sender != server.nickname)
    retval_dct = {'event':event, 'sender':sender, 'cmd':cmd, 'stem':stem}
#    print("Received command:", cmd)
    if cmd == "PUBKEY":  # He introduced himself to me (and sent me his public key).
        _pubkey(server, sender, stem)  # Also sends MYFERN
    elif cmd == "MYFERN":  # He sent me his fernet key.
        _myfern(server, sender, stem)  # Also sends ALI_IP
    elif cmd == "ALI_IP":
        _ali_ip(server, sender, stem)  # Also sends BOB_IP
    elif cmd == "BOB_IP":
        _bob_ip(server, sender, stem)
    elif cmd == 'TXTXTX':
        try:
            cipher_suite = Fernet(USERS_DCT[sender]['fernetkey'])
            decoded_msg = cipher_suite.decrypt(stem).decode()
        except InvalidToken:
            return "Warning - failed to decode %s's message. " % sender
        else:
            print("From %s: %s" % (sender, str(decoded_msg)))
            retval_dct['decoded'] = decoded_msg
    # else:
    #     raise ValueError("What is private message %s for? " % cmd)
    return retval_dct


def introduce_myself_to_the_new_people(server, channel):
    all_users = server.channels[channel].users()
    for user in [r for r in all_users if r != server.nickname]:
        if user not in USERS_DCT or USERS_DCT[user]['ipaddr'] is None:
            print("Introducing myself to %s" % user)
            server.put(user, "PUBKEY%s" % skinny_key(MY_PUBLIC_KEY))

##########################################################################################################


if __name__ == "__main__":
    if len(sys.argv) != 3:
#        print("Usage: %s <channel> <nickname>" % sys.argv[0])
#        sys.exit(1)
        my_channel = "#prate"
        my_nickname = "mchobbit"
        print("Assuming my_channel is", my_channel, "and nickname is", my_nickname)
    else:
        my_channel = sys.argv[1]
        my_nickname = sys.argv[2]
    my_irc_server = 'cinqcent.local'
    my_port = 6667
    svr = MyGroovyTestBot(my_channel, my_nickname, my_irc_server, my_port)
    wait_until_connected_and_joined(svr, my_channel)
    pubkeys_dct = {}
    introduce_myself_to_the_new_people(svr, my_channel)
    while True:
        if datetime.datetime.now().second % 30 == 0:
            show_users_dct_info()
            introduce_myself_to_the_new_people(svr, my_channel)
            sleep(1)
        while not svr.empty:
            sleep(.1)
            res_dct = process_incoming_message(svr)
            if 'decoded' in res_dct:
                print("From %s: '%s'" % (res_dct['sender'], res_dct['decoded']))

        # for user in [k for k in USERS_DCT.keys() if k != svr.nickname]:
        #     if USERS_DCT[user]['pubkey'] is None:
        #         print("We still need the pubkey of %s" % user)
        #     if USERS_DCT[user]['ipaddr'] is None:
        #         print("We still need the ip address of %s" % user)
        # keys_and_ip_addresses = [(USERS_DCT[k]['pubkey'], USERS_DCT[k]['ipaddr']) for k in USERS_DCT.keys()]
        # for a_key, a_ipaddr in keys_and_ip_addresses:
        #     try:
        #         a_nickname = [k for k in USERS_DCT if USERS_DCT[k]['pubkey'] == a_key][0]
        #     except IndexError:
        #         pass
        #     else:
        #         svr.put(a_nickname, "")
