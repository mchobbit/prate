# -*- coding: utf-8 -*-
'''
Created on Jan 22, 2025

@author: mchobbit
'''
import os
import paramiko
import sys
from my.stringtools import generate_irc_handle, get_word_salad, get_bits_to_be_encoded, encode_via_steg, decode_via_steg, \
    generate_all_possible_channel_names, strict_encode_via_steg
import base64
from my.globals import HAMLET, CICERO
from random import randint, choice, shuffle
import string
import time
from time import mktime
import pytz
import datetime

