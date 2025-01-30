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


def show_users_dct_info(dct):
    for k in dct:
        if dct[k] is None:
            pass
        elif dct[k]['ipaddr'] is not None:
            print("%-20s pubkey OK, fernetkey OK, IP=%s" % (k, dct[k]['ipaddr']))
        elif dct[k]['ipaddr'] is None:
            print("%-20s pubkey OK, fernetkey OK" % k)
        elif dct[k]['fernetkey'] is None:
            print("%-20s pubkey OK" % k)
        elif dct[k]['pubkey'] is None:
            print("%-20s ?" % k)
        else:
            print("%-20s ????" % k)


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


class MyWrapperForTheGroovyTestBot:

    def __init__(self, channel, nickname, irc_server, port):
        self.users_dct = {}  # FIXME: add __ and setters and getters
        self.channel = channel  # FIXME: add __ and setters and getters
        self.nickname = nickname  # FIXME: add __ and setters and getters
        self.irc_server = irc_server  # FIXME: add __ and setters and getters
        self.port = port  # FIXME: add __ and setters and getters
        self.rx_queue = queue.LifoQueue()
        self.tx_queue = queue.LifoQueue()
        self.ircbot = MyGroovyTestBot(self.channel, self.nickname, self.irc_server, self.port)
        self.wait_until_connected_and_joined(self.channel)
        self.introduce_myself_to_the_new_people(self.channel)

    def start(self):
        while True:
            self.run_loop_once()

    def run_loop_once(self):
        if datetime.datetime.now().second % 30 == 0:
            show_users_dct_info(self.users_dct)
            self.introduce_myself_to_the_new_people(self.channel)
            sleep(1)
        while not self.ircbot.empty:
            sleep(.1)
            res_dct = self.process_incoming_message()
            if 'decoded' in res_dct:
                print("From %s: '%s'" % (res_dct['sender'], res_dct['decoded']))

    def process_incoming_message(self, wait=True):
        (connection, event) = self.get_from_irc(wait)
        return self.act_on_msg_from_irc(connection, event)

    def _ali_ip(self, sender, stem):
        self._either_ali_or_bob_ip(sender, stem)
        self.ircbot.put(sender, "BOB_IP%s" % self.my_encrypted_ipaddr(sender))

    def _bob_ip(self, sender, stem):
        self._either_ali_or_bob_ip(sender, stem)
    #    print("Oi, oi! That's yet lot!")

    def my_encrypted_ipaddr(self, sender):
        cipher_suite = Fernet(self.users_dct[sender]['fernetkey'])
        ipaddr_str = MY_IP_ADDRESS
        cipher_text = cipher_suite.encrypt(ipaddr_str.encode())
        return cipher_text.decode()

    def wait_until_connected_and_joined(self, the_channel):
        print("Waiting for connection")
        while not self.ircbot.connected:
            sleep(1)
        print("Connected. Waiting to join channel")
        while the_channel not in self.ircbot.channels:
            sleep(1)
        print("*** MY NAME IS %s ***" % self.ircbot.nickname)
        print("Joined. Waiting for incoming messages")

    def get_from_irc(self, wait=True):
        return self.ircbot.get() if wait else self.ircbot.get_nowait()

    def act_on_msg_from_irc(self, connection, event):

        sender = event.source.split('@')[0].split('!')[0]
        if sender not in self.users_dct:
            self.users_dct[sender] = {'pubkey':None, 'ipaddr':None, 'fernetkey':None}
        txt = event.arguments[0]
        cmd = txt[:6]
        stem = txt[6:]
        assert(sender != self.ircbot.nickname)
        retval_dct = {'event':event, 'sender':sender, 'cmd':cmd, 'stem':stem}
    #    print("Received command:", cmd)
        if cmd == "PUBKEY":  # He introduced himself to me (and sent me his public key).
            self._pubkey(sender, stem)  # Also sends MYFERN
        elif cmd == "MYFERN":  # He sent me his fernet key.
            self._myfern(sender, stem)  # Also sends ALI_IP
        elif cmd == "ALI_IP":
            self._ali_ip(sender, stem)  # Also sends BOB_IP
        elif cmd == "BOB_IP":
            self._bob_ip(sender, stem)
        elif cmd == 'TXTXTX':
            try:
                cipher_suite = Fernet(self.users_dct[sender]['fernetkey'])
                decoded_msg = cipher_suite.decrypt(stem).decode()
            except InvalidToken:
                return "Warning - failed to decode %s's message. " % sender
            else:
                print("From %s: %s" % (sender, str(decoded_msg)))
                retval_dct['decoded'] = decoded_msg
        # else:
        #     raise ValueError("What is private message %s for? " % cmd)
        return retval_dct

    def _pubkey(self, sender, stem):
        self.users_dct[sender]['pubkey'] = unskin_key(stem)
        self.users_dct[sender]['fernetkey'] = Fernet.generate_key()
        print("I have received %s's pubkey. Yay." % sender)
        print("Sending %s my fernet key:    %s" % (sender, str(self.users_dct[sender]['fernetkey'])))
        ciphertext = rsa_encrypt(message=self.users_dct[sender]['fernetkey'], public_key=self.users_dct[sender]['pubkey'])
        b64ciphertext = base64.b64encode(ciphertext).decode()
        self.ircbot.put(sender, "MYFERN%s" % b64ciphertext)  # Sending him the symmetric key

    def _myfern(self, sender, stem):

        new_fernetkey = rsa_decrypt(base64.b64decode(stem))
        if self.users_dct[sender]['fernetkey'] is None:
            print("%s has sent me a new fernet: %s ... and it's our first from him. So, we'll accept it." % (sender, new_fernetkey))
            self.users_dct[sender]['fernetkey'] = new_fernetkey
        elif base64.b64encode(self.users_dct[sender]['fernetkey']) < base64.b64encode(new_fernetkey):
            print("%s has sent me a new fernet: %s ... and it's replacing a lower-ascii'd one." % (sender, new_fernetkey))
            self.users_dct[sender]['fernetkey'] = new_fernetkey
        else:
            print("%s's new fernet is ignored;  %s will be kept instead, as it's higher-ascii'd" % (sender, new_fernetkey))
        self.ircbot.put(sender, "ALI_IP%s" % self.my_encrypted_ipaddr(sender))

    def _either_ali_or_bob_ip(self, sender, stem):
        print("I have received an IP address block from %s" % sender)
        assert(self.users_dct[sender]['fernetkey'] is not None)
        cipher_suite = Fernet(self.users_dct[sender]['fernetkey'])
        try:
            decoded_msg = cipher_suite.decrypt(stem)
        except InvalidToken:
            return "Warning - failed to decode %s's message. " % sender
        ipaddr = decoded_msg.decode()
    #    quid_pro_quo = True if self.users_dct[sender]['ipaddr'] is None else False
        self.users_dct[sender]['ipaddr'] = ipaddr
        print("Received IP address (%s) for %s" % (ipaddr, sender))

    def introduce_myself_to_the_new_people(self, channel):
        all_users = self.ircbot.channels[channel].users()
        for user in [r for r in all_users if r != self.ircbot.nickname]:
            if user not in self.users_dct or self.users_dct[user]['ipaddr'] is None:
                print("Introducing myself to %s" % user)
                self.ircbot.put(user, "PUBKEY%s" % skinny_key(MY_PUBLIC_KEY))

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

##########################################################################################################

# def send_encrypted_byteblock(server, dest, byteblock):
#     assert(type(byteblock) is bytes)
#     cipher_suite = Fernet(USERS_DCT[dest]['fernetkey'])
#     cipher_text = cipher_suite.encrypt(byteblock)
#     server.put(dest, "TXTXTX%s" % cipher_text.decode(), encrypted=False)


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
    server = MyWrapperForTheGroovyTestBot(channel=my_channel, nickname=my_nickname, irc_server=my_irc_server, port=my_port)
    server.start()

