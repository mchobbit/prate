from irc_class import *
import os
import random

## IRC Config
server = "irc.darkmyst.org" # Provide a valid server IP/Hostname
port = 6697
channel = "#prate"
botnick = "wibble69"
botnickpass = None # "guido"
botpass = "<%= @guido_password %>"
irc = IRC()
irc.connect(server, port, channel, botnick, botpass, botnickpass)

while True:
    text = irc.get_response()
    print(text)
 
    if "PRIVMSG" in text and channel in text and "hello" in text:
        irc.send(channel, "Hello!")

