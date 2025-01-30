# -*- coding: utf-8 -*-
'''
Created on Jan 21, 2025

@author: mchobbit
'''
import unittest
from my.stringtools import  generate_irc_handle, encode_via_steg, decode_via_steg, get_word_salad
import paramiko
from my.globals.poetry import CICERO, HAMLET
from my.globals import VANILLA_WORD_SALAD


class Test(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def testName(self):
        pass

    # def testWordSalad(self):
    #     for _ in range(10):
    #         saladstr = get_word_salad()
    #         for c in saladstr:
    #             self.assertTrue(c.isalpha() or c == ' ')

    def testIrcNickGenerator(self):
        for _ in range(10):
            for minval in range(5, 10):
                nick = generate_irc_handle(minval)
                self.assertTrue(minval <= len(nick))
                for maxval in range(minval, 20):
                    nick = generate_irc_handle(minval, maxval)
                    self.assertTrue(minval <= len(nick) <= maxval)

    def testYesWeWantCollisions(self):
        keyspace_lst = []
        for _ in range(0, 20):
            all_nicks = []
            nick = 'wibblywobblywoo'
            while nick not in all_nicks:
                all_nicks += [nick]
                nick = generate_irc_handle(minimum_desired_length=6)
                self.assertTrue(len(all_nicks) < 300)
            keyspace_lst += [len(all_nicks)]
#        print("Average of %d keyspace" % (sum(keyspace_lst) / len(keyspace_lst)))

    def testStegEncoderAndDecoder(self):
        for _ in range(0, 5):
            key = paramiko.RSAKey.generate(4096)
            for the_plaintext_message in ("Hello world", "This is fun.", "", "0", "WibbleWobbleWoo",
                                          key.fingerprint, key.get_base64()):
                the_ciphertext_message = encode_via_steg(the_plaintext_message=the_plaintext_message,
                                                         salad_txt=get_word_salad())
                the_decoded_text = decode_via_steg(the_ciphertext_message)
                self.assertEqual(the_plaintext_message, the_decoded_text)

    def testLaziness(self):
        for laziness in range(0, 10):
            key = paramiko.RSAKey.generate(4096)
            for the_plaintext_message in ("Hello world", "This is fun.", "", "0", "WibbleWobbleWoo",
                                          key.fingerprint, key.get_base64()):
                the_ciphertext_message = encode_via_steg(the_plaintext_message=the_plaintext_message,
                                                         salad_txt=get_word_salad(), laziness=laziness)
                the_decoded_text = decode_via_steg(the_ciphertext_message)
                self.assertEqual(the_plaintext_message, the_decoded_text)
                # try:
                #     print("With laziness==%d, crypto length is %f x plain" % (laziness, len(the_ciphertext_message) / len(the_plaintext_message)))
                # except ZeroDivisionError:
                #     pass

    def testSimpleStegger(self):
        key = paramiko.RSAKey.generate(4096)
        irc_nickname = generate_irc_handle(salad_txt="Few things are more distressing to a well-regulated mind than to see a boy who ought to know better disporting himself at improper moments.")
        # word_salad_str = '''Do you hear the people sing? Singing a song of angry men? It is the music of a people Who will not be slaves again! When the beating of your heart Echoes the beating of the drums There is a life about to start When tomorrow comes!'''
        # ws_generator = lambda: word_salad_str
        plaintext = key.get_base64()  # "Hello, world."
        ciphertext = encode_via_steg(plaintext, get_word_salad())
        destegged = decode_via_steg(ciphertext, output_in_bytes=False)
        self.assertEqual(destegged, plaintext)

    def testBytesStegger(self):
        key = paramiko.RSAKey.generate(4096)
        irc_nickname = generate_irc_handle(salad_txt="Few things are more distressing to a well-regulated mind than to see a boy who ought to know better disporting himself at improper moments.")
        # word_salad_str = '''Do you hear the people sing? Singing a song of angry men? It is the music of a people Who will not be slaves again! When the beating of your heart Echoes the beating of the drums There is a life about to start When tomorrow comes!'''
        # ws_generator = lambda: word_salad_str
        plaintext = key.asbytes()
        ciphertext = encode_via_steg(plaintext, get_word_salad())
        destegged = decode_via_steg(ciphertext, output_in_bytes=True)
        self.assertEqual(destegged, plaintext)

    def testCicero(self):
        key = paramiko.RSAKey.generate(4096)
        plaintext = key.asbytes()
        ciphertext = encode_via_steg(plaintext, CICERO)
        destegged = decode_via_steg(ciphertext, output_in_bytes=True)
        self.assertEqual(destegged, plaintext)

    def testHamlet(self):
        key = paramiko.RSAKey.generate(4096)
        plaintext = key.asbytes()
        ciphertext = encode_via_steg(plaintext, HAMLET)
        destegged = decode_via_steg(ciphertext, output_in_bytes=True)
        self.assertEqual(destegged, plaintext)

    def testRandomOffset(self):
        key = paramiko.RSAKey.generate(4096)
        plaintext = key.asbytes()
        ciphertext = encode_via_steg(plaintext, VANILLA_WORD_SALAD, random_offset=True)
        destegged = decode_via_steg(ciphertext, output_in_bytes=True)
        self.assertEqual(destegged, plaintext)
        plaintext = CICERO
        ciphertext = encode_via_steg(plaintext, VANILLA_WORD_SALAD, random_offset=True)
        destegged = decode_via_steg(ciphertext, output_in_bytes=False)
        self.assertEqual(destegged, plaintext)


if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
