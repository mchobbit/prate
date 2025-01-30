#!/usr/bin/env python3

"""

TO DO

Detect if users' nicknames change
Make the users' dictionary threadsafe
Make the entire class threadsafe
Use the public keys' fingerprints, not the users' nicknames, as the key for the dictionary
Turn the users' dictionary into a class
Auto-check the nicknames whenever using a dictionary entry

WRITE UNIT TESTS!


"""
import sys
import queue
import datetime
from time import sleep
from my.irctools import MyGroovyTestBot, rsa_encrypt, rsa_decrypt, pubkey_to_b64, b64_to_pubkey  # skinny_key, unskin_key
from threading import Thread
from _queue import Empty

from cryptography.fernet import Fernet, InvalidToken
import base64
from my.globals import MY_IP_ADDRESS, MY_RSAKEY
# Generate RSA keys

# pip3 install pycryptodome

# https://medium.com/@info_82002/a-beginners-guide-to-encryption-and-decryption-in-python-12d81f6a9eac


class MyObject(object):
    pass


class MyWrapperForTheGroovyTestBot:

    def __init__(self, channel, nickname, public_key, irc_server, port):
        self.users_dct = {}  # FIXME: add __ and setters and getters
        self.channel = channel  # FIXME: add __ and setters and getters
        self.nickname = nickname  # FIXME: add __ and setters and getters
        self.public_key = public_key
        self.svr_url = irc_server  # FIXME: add __ and setters and getters
        self.port = port  # FIXME: add __ and setters and getters
        self.rx_queue = queue.LifoQueue()  # TODO: Is this threadsafe?
        self.tx_queue = queue.LifoQueue()  # TODO: Is this threadsafe?
        self.ircbot = MyGroovyTestBot(self.channel, self.nickname, pubkey_to_b64(self.public_key), self.svr_url, self.port)
        self.channel = channel
        self.input_queue = queue.LifoQueue()
        self.output_queue = queue.LifoQueue()
        self.keep_broadcasting = True
        self.__time_to_quit = False
        self.__my_worker_thread = Thread(target=self._worker_loop, daemon=True)
        self.__the_previous_time_i_said_what_was_going_on = None
        self.__ready = False
        self._start()

    @property
    def ready(self):
        return self.__ready

    def _start(self):
        self.wait_until_connected_and_joined(self.channel)
        self.introduce_myself_to_the_new_people(self.channel)
        self.__my_worker_thread.start()
        self.__ready = True

    def quit(self):
        self.__time_to_quit = True
        self.__my_worker_thread.join()  # print("Joining server thread")
        self.ircbot.quit()

    def _worker_loop(self):
        while not self.__time_to_quit:
            try:
                (a_user, msg_txt) = self.tx_queue.get_nowait()
                print("Send to %s (encrypted): %s" % (a_user, msg_txt))
#                self._send_encrypted_data(a_user, msg_txt)
#                sleep(randint(16, 20) // 10.)  # Do not send more than 20 messages in 30 seconds! => 30/(((20+16)/2)/10)=16.7 messages per 30 seconds.
            except Empty:
                pass
            if datetime.datetime.now().second % 30 == 0 and self.keep_broadcasting:
                self.show_users_dct_info()
                self.introduce_myself_to_the_new_people(self.channel)
                sleep(1)
            while not self.ircbot.empty:
                sleep(.1)
                res_dct = self.process_incoming_message()
                if 'decoded' in res_dct:
                    print("From %s: '%s'" % (res_dct['sender'], res_dct['decoded']))

    def show_users_dct_info(self):
        outstr = ""
        for k in self.users_dct:
            if self.users_dct[k] is None:
                pass
            elif self.users_dct[k]['ipaddr'] is not None:
                outstr += "\n%-20s pubkey OK, fernetkey OK, IP=%s" % (k, self.users_dct[k]['ipaddr'])
            elif self.users_dct[k]['ipaddr'] is None:
                outstr += "\n%-20s pubkey OK, fernetkey OK" % k
            elif self.users_dct[k]['fernetkey'] is None:
                outstr += "\n%-20s pubkey OK" % k
            elif self.users_dct[k]['pubkey'] is None:
                outstr += "\n%-20s ?" % k
            else:
                outstr += "\n%-20s ????" % k
        if self.__the_previous_time_i_said_what_was_going_on != outstr:
            self.__the_previous_time_i_said_what_was_going_on = outstr
            print(outstr)

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
        if event is None:
            raise AttributeError("act_on_msg_from_irc() has an event of None")
        if event.source:
            sender = event.source.split('@')[0].split('!')[0]
            if sender not in self.users_dct:
                self.users_dct[sender] = {'pubkey':None, 'ipaddr':None, 'fernetkey':None}
        else:
            sender = None
        txt = event.arguments[0]
        cmd = txt[:6]
        stem = txt[6:]
        assert(sender != self.ircbot.nickname)
        retval_dct = {'event':event, 'sender':sender, 'cmd':cmd, 'stem':stem}
        if event.type == 'foo':
            print("event type is foo for %s; this is a foo-tile attempt at a test." % event.target)
        elif event.type == 'whois':
            print("event type is whois for %s; result is unknown, as my bot's code didn't handle it properly." % event.target)
        elif cmd == "PUBKEY":  # He introduced himself to me (and sent me his public key).
            self._pubkey(sender, stem)  # Also sends MYFERN
        elif cmd == "MYFERN":  # He sent me his fernet key.
            self._myfern(sender, stem)  # Also sends ALI_IP
        elif cmd == "ALI_IP":
            self._ali_ip(sender, stem)  # Also sends BOB_IP
        elif cmd == "BOB_IP":
            self._bob_ip(sender, stem)
        elif cmd == 'TXTXTX':  # This means that some data was TX'd to us.
            try:
                cipher_suite = Fernet(self.users_dct[sender]['fernetkey'])
                decoded_msg = cipher_suite.decrypt(stem).decode()
            except InvalidToken:
                retval_dct['error'] = "Warning - failed to decode %s's message. " % sender
            else:
                print("From %s: %s" % (sender, str(decoded_msg)))
                self.rx_queue.put([sender, decoded_msg])
                retval_dct['decoded'] = decoded_msg
        else:
            print("Probably a private message from %s: %s" % (sender, txt))
            retval_dct['error'] = "What is private message %s for? " % cmd
        return retval_dct

    @property
    def crypto_empty(self):
        return self.rx_queue.empty()

    def crypto_get(self):
        return self.rx_queue.get()

    def crypto_get_nowait(self):
        return self.rx_queue.get_nowait()

    def crypto_put(self, user, byteblock):
        assert(user in self.users_dct)
        assert(type(byteblock) is bytes)
        cipher_suite = Fernet(self.users_dct[user]['fernetkey'])
        cipher_text = cipher_suite.encrypt(byteblock)
        self.ircbot.put(user, "TXTXTX%s" % cipher_text.decode())

    def _pubkey(self, sender, stem):
        self.users_dct[sender]['pubkey'] = b64_to_pubkey(stem)
        self.users_dct[sender]['fernetkey'] = Fernet.generate_key()
        print("I have received %s's pubkey. Yay." % sender)
        print("Sending %s his fernet key:   %s" % (sender, str(self.users_dct[sender]['fernetkey'])))
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
        if channel not in self.ircbot.channels:
            print("I cannot introduce myself to %s: I am not in that channel." % channel)
        else:
            all_users = self.ircbot.channels[channel].users()
            for user in [r for r in all_users if r != self.ircbot.nickname]:
                if user not in self.users_dct or self.users_dct[user]['ipaddr'] is None:
#                    print("Introducing myself to %s" % user)
                    self.ircbot.put(user, "PUBKEY%s" % pubkey_to_b64(MY_RSAKEY.public_key()))

##########################################################################################################

'''
from random import randint
from testbot8 import *
nickname = "clyde" # nickname='mac' + str(randint(100,999)
svr = MyWrapperForTheGroovyTestBot(channel="#prate", nickname=nickname, public_key=MY_RSAKEY.public_key(), irc_server='cinqcent.local', port=6667)
svr.keep_broadcasting = False
svr.ircbot.connection.whois('clyde')
svr.ircbot.connection.whois('mchobbit')

svr.ircbot.connection.send_items('PRIVMSG', 'mchobbit', 'HIII')
sender = getattr(svr.ircbot.connection.socket, 'write', svr.ircbot.connection.socket.send)
_msg = svr.ircbot.connection._prep_message("PRIVMSG mchobbit HELLOTHERE")
sender(_msg)

# reassign_handleother_subroutine(svr, my_handle_other)
# svr.ircbot.connection._process_line("foo clyde")
# svr.ircbot.reactor.add_global_handler("all_events", foo, -10)
while not svr.ready:
    sleep(1)

while len(svr.users_dct) < 1:
    sleep(1)

my_buddy = list(svr.users_dct.keys())[0]
svr.crypto_put(my_buddy, b"HI THERE.")
'''

if __name__ == "__main__":
    if len(sys.argv) != 3:
#        print("Usage: %s <channel> <nickname>" % sys.argv[0])
#        sys.exit(1)
        my_channel = "#prate"
        my_nickname = "macgyver"
        my_realname = "iammcgyv"
        print("Assuming my_channel is", my_channel, "and nickname is", my_nickname)
    else:
        my_channel = sys.argv[1]
        my_nickname = sys.argv[2]
        my_realname = my_nickname[::-1] * 3
    my_irc_server = 'cinqcent.local'
    my_port = 6667
    svr = MyWrapperForTheGroovyTestBot(channel=my_channel, nickname=my_nickname,
                                       public_key=MY_RSAKEY.public_key(),
                                       irc_server=my_irc_server, port=my_port)
    while not svr.ready:
        sleep(1)
    print("Press CTRL-C to quit.")
    svr.keep_broadcasting = False
    while True:
        sleep(1)
        all_users = list(svr.ircbot.channels[my_channel].users())
        for user in all_users:
            whois_user = svr.ircbot.connection.whois(user)  # pylint: disable=not-callable
#            print(user, '=>', whois_user)
