# -*- coding: utf-8 -*-
"""Audio tools for Prate.

Created on Jan 30, 2025

@author: mchobbit


https://www.codespeedy.com/record-voice-from-the-microphone-in-python-with-few-lines-of-code/
https://stackoverflow.com/questions/62618934/pyaudio-how-to-access-stream-read-data-in-callback-non-blocking-mode
https://stackoverflow.com/questions/19070290/pyaudio-listen-until-voice-is-detected-and-then-record-to-a-wav-file

Todo:
    * Better docs

.. _Google Python Style Guide:
   http://google.github.io/styleguide/pyguide.html

.. _Napoleon Style Guide:
   https://sphinxcontrib-napoleon.readthedocs.io/en/latest/example_google.html

"""

import pyaudio
from pydub import AudioSegment
from queue import Queue, Empty
from io import BytesIO
# import wave
from threading import Thread
import os
from my.classes.readwritelock import ReadWriteLock
from time import sleep
from my.globals import ENDTHREAD_TIMEOUT

SAMPLE_WIDTH = 2  # ...because paInt16 is 2x8
DESIRED_AUDIO_FORMAT = pyaudio.paInt16
NOOF_CHANS = 1
FRAME_RATE = 8000  # 11025 22050 44100


def raw_to_ogg(raw_data):
    io = BytesIO()
    seg = AudioSegment(raw_data, sample_width=SAMPLE_WIDTH, frame_rate=FRAME_RATE, channels=NOOF_CHANS)
    seg.export(io, format='ogg')
    retval = io.read()
    io.close()
    return retval


class MyMic:

    def __init__(self, audio_queue, squelch=100):
        self.__audio_queue = audio_queue
        self.__ready = False
        self.__paused = False
        self.__paused_lock = ReadWriteLock()
        self.__squelch = squelch
        self.__squelch_lock = ReadWriteLock()
        self.__should_we_quit = False
        self.__my_main_thread = Thread(target=self.__my_main_loop, daemon=True)
        self.__my_main_thread.start()

    @property
    def paused(self):
        self.__paused_lock.acquire_read()
        try:
            retval = self.__paused
            return retval
        finally:
            self.__paused_lock.release_read()

    @paused.setter
    def paused(self, value):
        self.__paused_lock.acquire_write()
        try:
            self.__paused = value
        finally:
            self.__paused_lock.release_write()

    @property
    def ready(self):
        return self.__ready

    @property
    def should_we_quit(self):
        return self.__should_we_quit

    @property
    def squelch(self):
        self.__squelch_lock.acquire_read()
        try:
            retval = self.__squelch
            return retval
        finally:
            self.__squelch_lock.release_read()

    @squelch.setter
    def squelch(self, value):
        self.__squelch_lock.acquire_write()
        try:
            self.__squelch = value
        finally:
            self.__squelch_lock.release_write()

    @property
    def audio_queue(self):
        return self.__audio_queue

    def __my_main_loop(self):
        p = pyaudio.PyAudio()
        stream = p.open(format=DESIRED_AUDIO_FORMAT, channels=NOOF_CHANS, rate=FRAME_RATE, input=True, frames_per_buffer=1024)
        self.__ready = True
        alldata = bytearray()
        while not self.should_we_quit:
            try:
                while True:
                    data = stream.read(1024, exception_on_overflow=False)
                    if self.paused:
                        pass
                    elif max(data) >= self.squelch:  # Loud enough
                        alldata += bytearray(data)
                    elif len(alldata) > 0:
                        print("MOAR")
                        self.audio_queue.put(bytes(alldata))
                        alldata = bytearray()
                    else:
                        sleep(.01)
            except Exception as ex:
                print(str(ex))
        if len(alldata) > 0:
            self.audio_queue.put(bytes(alldata))
        stream.stop_stream()
        stream.close()
        p.terminate()

    def quit(self):
        self.__should_we_quit = True
        self.__my_main_thread.join(timeout=ENDTHREAD_TIMEOUT)


def __main__():
    q = Queue()
    mic = MyMic(q, squelch=100)
    while not mic.ready:
        sleep(0.1)
    print("Okay. Speak... or don't. I don't care. In ten seconds, I'll stop listening.")
    while True:
        try:
            audio_data = bytes(q.get_nowait())
        except Empty:
            sleep(.1)
        else:
            fname = "/tmp/simple.ogg"
            with open(fname, "wb") as f:
                f.write(audio_data)
            print("ogg: %d KB" % (os.path.getsize(fname) // 1024))
            os.system("/opt/homebrew/bin/mpv %s &" % fname)
    print("Fin.")

