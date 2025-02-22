# -*- coding: utf-8 -*-
'''
from my.stringtools import generate_irc_handle
generate_irc_handle()
'''
import requests
from my.classes.exceptions import WebAPITimeoutError, WebAPIOutputError, IrcBadNicknameError, IrcNicknameTooLongError
from bs4 import BeautifulSoup as bs
from random import randint, choice
from my.globals import VANILLA_WORD_SALAD, steg_dct_CLUMPS, MAX_NICKNAME_LENGTH
import base64
from urllib3.connectionpool import HTTPSConnectionPool
import string

from functools import reduce

from typing import Iterable
import datetime

# def get_random_zenquote(timeout:int=10) -> str:
#     """Return an uplifting quote from ZenQuotes.
#
#     Using the API at https://zenquotes.io, I retrieve a random quote --
#     something uplifting -- and return it as a string.
#
#     Args:
#         timeout (optional): Timeout before returning string (or failing).
#
#     Returns:
#         str: Random uplifting message string.
#
#     Raises:
#         WebAPITimeoutError: Unable to access website to get quote.
#         WebAPIOutputError: Website's output was incomprehensible.
#
#     """
#     response = requests.get('https://zenquotes.io/api/random', timeout=timeout)
#     try:
#         data = response.json()[0]
#         quote = data['q'] + ' - ' + data['a']
#     except (TimeoutError, ConnectionError) as e:
#         raise WebAPITimeoutError("The ZenQuotes website timed out") from e
#     except (KeyError, IndexError) as e:
#         raise WebAPIOutputError("The output from the ZenQuotes website was incomprehensible") from e
#     else:
#         return quote


def get_wordrandomizer_phrase(timeout:int=10) -> str:
    """Return a random phrase from https://wordgenerator.co/phrase-generator

    Using https://wordgenerator.co/phrase-generator,
    I retrieve a random phrase and return it as a string.

    Args:
        timeout (optional): Timeout before returning string (or failing).

    Returns:
        str: Random phrase.

    Raises:
        WebAPITimeoutError: Unable to access website to get quote.
        WebAPIOutputError: Website's output was incomprehensible.

    """
    response = requests.get('https://wordgenerator.co/phrase-generator', timeout=timeout)
    # try:
    #     data = response.json()[0]
    #     quote = data['q'] + ' - ' + data['a']
    # except (TimeoutError, ConnectionError) as e:
    #     raise WebAPITimeoutError("The ZenQuotes website timed out") from e
    # except (KeyError, IndexError) as e:
    #     raise WebAPIOutputError("The output from the ZenQuotes website was incomprehensible") from e
    # else:
    soup = bs(response.content)
    phrase = ''
    for row in soup.findAll('div', attrs={'class':'phrase'}):
        phrase = phrase + [r.strip() for r in str(row).split('\n') if '<' not in r][-1] + '. '
    return phrase.strip(' ')


def get_shakespeare_quote(timeout:int=10) -> str:
    """Return a random phrase from https://www.generatormix.com/random-shakespeare-quotes

    Using https://www.generatormix.com/random-shakespeare-quotes,
    I retrieve a random phrase and return it as a string.

    Args:
        timeout (optional): Timeout before returning string (or failing).

    Returns:
        str: Random phrase.

    Raises:
        WebAPITimeoutError: Unable to access website to get quote.
        WebAPIOutputError: Website's output was incomprehensible.

    """
    response = requests.get('https://www.generatormix.com/random-shakespeare-quotes', timeout=timeout)
    # try:
    #     data = response.json()[0]
    #     quote = data['q'] + ' - ' + data['a']
    # except (TimeoutError, ConnectionError) as e:
    #     raise WebAPITimeoutError("The ZenQuotes website timed out") from e
    # except (KeyError, IndexError) as e:
    #     raise WebAPIOutputError("The output from the ZenQuotes website was incomprehensible") from e
    # else:
    soup = bs(response.content)
    phrase = ''
    for row in soup.findAll('blockquote'):
        phrase = phrase + row.text + '. '
    return phrase.strip(' ')


def remove_nonalpha_from_string(incoming_str:str) -> str:
    """Remove nonalpha chars from string.

    Args:
        incoming_str (str): Incoming string.

    Returns:
        str: Result.

    """
    outstr = ''.join([r for r in incoming_str if r.isalpha() or r == ' ']).lower()
    return outstr.strip(' ').replace('  ', ' ').replace('  ', ' ').replace('  ', ' ').replace('  ', ' ')


def get_word_salad(the_incoming_phrase=VANILLA_WORD_SALAD):
# def get_word_salad(use_internet:bool=False, timeout:int=3, source_txt) -> str:
#     """Return a string of lowercase words, separated by spaces, with no numbers, punctuation, or non-alpha characters
#
#     Get random words & phrases, create a mishmash of words, and return them.
#
#     Args:
#         use_internet (optional): Should we use an Internet-based quotation source instead of our local one?
#         timeout (optional): Timeout before returning string (or failing).
#
#     Returns:
#         str: Random phrase.
#
#     """
#     funcs = (get_shakespeare_quote, get_wordrandomizer_phrase)  # get_shakespeare_quote,
#     if use_internet:
#         try:
#             the_incoming_phrase = funcs[randint(0, len(funcs) - 1)](timeout=timeout)
#         except Exception as e:  # (WebAPITimeoutError, WebAPIOutputError) as e:
#             print("Unable to obtain random phrase:", e, "...So, I shall do it manually instead.")
#             the_incoming_phrase = VANILLA_WORD_SALAD
#     else:
#         the_incoming_phrase = VANILLA_WORD_SALAD
    if the_incoming_phrase[-1] not in ('\n', '.'):
        the_incoming_phrase += '.'
    if the_incoming_phrase[-1] == '.':
        the_incoming_phrase += ' '
    for d in steg_dct_CLUMPS:
        for v in steg_dct_CLUMPS[d]:
            the_incoming_phrase = the_incoming_phrase.replace(v, '_')
    return ''.join([c for c in the_incoming_phrase if 32 <= ord(c) <= 127])


def generate_random_alphanumeric_string(length):
    return ''.join(choice(string.ascii_uppercase + string.ascii_lowercase + string.digits) for _ in range(length))


def generate_irc_handle(minimum_desired_length:int=MAX_NICKNAME_LENGTH - 2, maximum_desired_length:int=MAX_NICKNAME_LENGTH, salad_txt=VANILLA_WORD_SALAD) -> str:
    """Generate a random IRC handle of at least N characters.

    Args:
        minimum_desired_length: The minimum length of the handle.
        maximum_desired_length: The maximum length of the handle.
        word_salad_generator: Name of function that spits out the word salad that we use for generating the IRC handle.

    Returns:
        The handle.

    """
    if maximum_desired_length > MAX_NICKNAME_LENGTH:
        raise IrcNicknameTooLongError("I dare not create an IRC handle longer than %d, lest it be incompatible with the IRC server." % MAX_NICKNAME_LENGTH)
    substs_dct = {'The':'D', 'Are':'R', 'Of':'', 'To':'2', 'Two':'2', 'One':'1', 'Won':'1', 'Too':'2',
                  'Three':'3', 'Four':'4', 'Five':'5', 'Six':'6', 'Seven':'7', 'Eight':'8',
                  'Nine':'9', 'Ten':'10', 'Eleven':'11', 'Twelve':'12', 'Thirteen':'13', 'Fourteen':'14',
                  'Fifteen':'15', 'Sixteen':'16', 'Seventeen':'17', 'Eighteen':'18', 'Nineteen':'19',
                  'Twenty':'20', 'Hate':'H8', 'Hating':'H8g', 'Fore':'4'}  # , 'ing':'g', 'o':'0', 'e':'3', 't':'7', 'l':'1', 'I':'1', 'a':'4', 'O':'0'}
    salad = remove_nonalpha_from_string(salad_txt)
    salad_lst = salad.split(' ')
    total_noof_words = len(salad_lst)
    word_no = randint(0, total_noof_words - 1)
    our_overblown_handle = ""
    while len(our_overblown_handle) < minimum_desired_length:
        word_no = (word_no + 1) % total_noof_words
        this_word = salad_lst[word_no].title()
        if our_overblown_handle == '' and this_word in substs_dct:
            continue  # we don't want the nick to start with a dictionary word, in case that word starts with a digit
        for k in substs_dct:
            this_word = this_word.replace(k, substs_dct[k])
        our_overblown_handle += this_word
    if not our_overblown_handle[0].isalpha():
        our_overblown_handle = 'Z' + our_overblown_handle
    return our_overblown_handle[:maximum_desired_length]


def generate_9char_signature_for_this_string(key, irc_handle):
#    FORMAT: (letter / special) * 8(letter / digit / special / "-")
    signed_irc_handle_binary = key.sign_ssh_data(str.encode(irc_handle))
    b = base64.b64encode(signed_irc_handle_binary.asbytes())
    t = b.decode('utf-8').strip(' =- ')
    return('=' + t[-8:])


def get_bits_to_be_encoded(the_raw_text):
    """Turn the supplied string of alphanumeric characters into a string of bits.

    Args:
        the_raw_text: The incoming raw text.

    Returns:
        The resultant string of bits (e.g. "0101101001011101")

    """
    for c in the_raw_text:
        number_to_encode = ord(c) if type(the_raw_text) is str else c
        for _rots in range(0, 8):
            bit_to_encode = number_to_encode % 2
            number_to_encode = number_to_encode // 2
            yield bit_to_encode


def decode_bits(string_of_bits:str, output_in_bytes=False) -> str:
    """Turn the supplied string of bits into a string of alphanumeric characters.

    Args:
        string_of_bits: The incoming string of bits (e.g. "0101101001011101")

    Returns:
        The string of characters deduced from the string of bits.

    """
    outstr = bytearray(b'') if output_in_bytes else ''
#    assert(len(string_of_bits) % 8 == 0)
    for y in range(0, len(string_of_bits) // 8):
        v = 0
        for x in range(7, -1, -1):
            v = v * 2 + int(string_of_bits[y * 8 + x])
        if output_in_bytes:
            outstr.append(v)  # pylint: disable=no-member
        else:
            outstr += chr(v)
    if len(string_of_bits) % 8 != 0:
        print("WARNING --- %d bits left over" % (len(string_of_bits) % 8))
    return bytes(outstr) if output_in_bytes else outstr


def encode_via_steg(the_plaintext_message, salad_txt, random_offset=True, laziness=0, max_out_len=9999999, clumps_dct=None) -> str:
    """Encode a hidden message steganographically in the supplied text.

    Args:
        the_plaintext_message: The text to be hidden.
        salad_txt: Word salad in which the plaintext will be hidden.
        laziness: if 0, flip 100% of available letters for steg message. If 1, 50%; if 2, 33%; and so on.
            The selection is random-ish.
        max_out_len: How big should the output text be allowed to grow?

    Returns:
        The text, hiding the hidden message.

    """

    def ourwordsalad(salad_txt, random_offset):
        ourtxt = get_word_salad(salad_txt)
        assert('. ' in ourtxt or '\n' in ourtxt)
        if random_offset:
            i = randint(0, len(ourtxt) - 1)
            while ourtxt[i] != '\n' and ourtxt[i:i + 2] != '. ':
                i = (i + 1) % len(ourtxt)
        else:
            i = 0
        i -= 1
        while True:
            i += 1
            if i >= len(ourtxt):
                i = 0
            if not (32 <= ord(ourtxt[i]) <= 126):
                i += 1
            else:
                yield ourtxt[i]

    if clumps_dct is None:
        clumps_dct = steg_dct_CLUMPS
    if the_plaintext_message == '':
        return ''
    assert(laziness >= 0)
    all_bits = ''.join([str(r) for r  in get_bits_to_be_encoded(the_plaintext_message)])
    outstr = ''
    current_bit_index = 0
    for ch in ourwordsalad(salad_txt, random_offset):
        assert(len(outstr) < max_out_len)
        assert(current_bit_index <= len(all_bits))
        if current_bit_index == len(all_bits) and ch in ("!?;:,.\n"):
            outstr += ch
            break
        elif current_bit_index == len(all_bits):
            outstr += ch
        elif ch not in clumps_dct or all_bits[current_bit_index] not in clumps_dct[ch].values() or randint(0, laziness) != 0:
            outstr += ch
        else:
            assert(32 <= ord(ch) <= 126)
            all_available_binary_clumps_for_this_letter = list(clumps_dct[ch].values())
            all_available_binary_clumps_for_this_letter.reverse()  # sort by length, longest first
            for clump in all_available_binary_clumps_for_this_letter:
                if all_bits[current_bit_index:].startswith(clump):
                    outstr += list(clumps_dct[ch].keys())[list(clumps_dct[ch].values()).index(clump)]
                    current_bit_index += len(clump)
                    break
            else:
                outstr += ch
    return outstr


def decode_via_steg(the_ciphertext_message:str, output_in_bytes=False, clumps_dct=None) -> str:
    """Extract the steganographically hidden message from the supplied text.

    Args:
        the_ciphertext_message: The incoming text to be de-stagg-ified.

    Returns:
        The hidden message.

    """
    if clumps_dct is None:
        clumps_dct = steg_dct_CLUMPS
    if the_ciphertext_message == '':
        return ''
    binaryvals_extracted = ''
    for ch in the_ciphertext_message:
        for k in clumps_dct:
            for v in clumps_dct[k]:
                if v == ch:
                    binaryvals_extracted += clumps_dct[k][v]
    return decode_bits(binaryvals_extracted, output_in_bytes=output_in_bytes)


def generate_channel_name():

    return generate_irc_handle(salad_txt="Few things are more distressing to a well-regulated mind than to see a boy who ought to know better disporting himself at improper moments.",
                               minimum_desired_length=7)


def generate_all_possible_channel_names():
    lst = []
    for _ in range(0, 1000):
        nam = generate_channel_name()
        if nam not in lst:
            lst.insert(0, nam)
    return lst


def strict_encode_via_steg_SUB(the_plaintext_message, salad_txt, laziness=0, max_out_len=9999999):
    # Same as encode_via_steg BUT we DO NOT LOOP THE WORD SALAD.
    noof_useful_chars = 0
    our_word_salad = ''
    for ch in salad_txt:
        our_word_salad += ch  # QQQ Inefficient. Don't care.
        if ch in steg_dct_CLUMPS:
            noof_useful_chars += 1
    endmarker = '#' * 10
    while endmarker in our_word_salad:
        endmarker = ''.join(choice(string.ascii_uppercase + string.ascii_lowercase + string.digits) for _ in range(64))  # '#' * 10 + 'F@R$*RE*EH@!AT>'
    assert(endmarker not in our_word_salad)
    our_word_salad += endmarker
    assert(noof_useful_chars >= len(the_plaintext_message))
    retval = encode_via_steg(the_plaintext_message=the_plaintext_message, salad_txt=salad_txt, laziness=laziness, max_out_len=max_out_len).strip(endmarker)
    assert(endmarker not in retval)
    return retval.strip(endmarker)


def strict_encode_via_steg(the_plaintext_message, salad_txt, max_laziness=0, clumps_dct=None):
    if clumps_dct is None:
        clumps_dct = steg_dct_CLUMPS
    for laziness in range(max_laziness, -1, -1):
        try:
            res = strict_encode_via_steg_SUB(the_plaintext_message, salad_txt=salad_txt[randint(0, len(salad_txt) // 2):], laziness=laziness)
            break
        except AssertionError:
            try:
                res = strict_encode_via_steg_SUB(the_plaintext_message, salad_txt=salad_txt[randint(0, len(salad_txt) // 3):], laziness=laziness)
                break
            except AssertionError:
                try:
                    res = strict_encode_via_steg_SUB(the_plaintext_message, salad_txt=salad_txt, laziness=laziness)
                    break
                except AssertionError:
                    pass
    return res


# lst = multiline_encode_via_steg(plaintext, salad_txt=VANILLA_WORD_SALAD, random_offset=True, maxlen=120)
def multiline_encode_via_steg(plaintext, salad_txt=VANILLA_WORD_SALAD, random_offset=False, maxlen=500):
    ciphertext = encode_via_steg(plaintext, salad_txt=salad_txt, random_offset=random_offset)
    i = 0
    outlines = []
    while i < len(ciphertext):
        j = min(i + maxlen, len(ciphertext))
        while j < len(ciphertext) and j > i + 5 and ciphertext[j] not in '\n.?!;:,':
            j -= 1
        this_line = ciphertext[i:j].strip().strip('\n')
        outlines += [this_line]
        i = j + 1
    return outlines


def chop_up_string_into_substrings_of_N_characters(s, n):
    return [(s[i:i + n]) for i in range(0, len(s), n)]

# from collections import Iterable                            # < py38


def flatten(items):
    """Yield items from any nested iterable; see Reference."""
    for x in items:
        if isinstance(x, Iterable) and not isinstance(x, (str, bytes)):
            for sub_x in flatten(x):
                yield sub_x
        else:
            yield x


def s_now():
    """Now, as HH:MM:SS str."""
    return datetime.datetime.fromtimestamp(datetime.datetime.timestamp(datetime.datetime.now())).strftime("%H:%M:%S")
