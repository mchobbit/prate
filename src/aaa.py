
import irc.bot
from time import sleep


class GroovyWhoisTestBot(irc.bot.SingleServerIRCBot):

    def __init__(self, channel, nickname, server, port=6667):
        irc.bot.SingleServerIRCBot.__init__(self, [(server, port)], nickname, nickname)
        self.channel = channel

    def on_nicknameinuse(self, c, e):
        c.nick(c.get_nickname() + "_")

    def on_welcome(self, c, e):
        c.join(self.channel)

    def on_privmsg(self, c, e):
        self.do_command(e, e.arguments[0])

    def do_command(self, e, cmd):
        nick = e.source.nick
        c = self.connection
        if cmd == "disconnect":
            self.disconnect()
        elif cmd == "die":
            self.die()
        elif cmd.startswith("whois"):
            i = cmd.find(' ')
            if i < 0:
                found = None
            else:
                user = cmd[i + 1:]
                c.whois(user)
                for _ in range(0, 50):
                    sleep(.1)
                    self.reactor.process_once()
                    found = c.whois(interrogate=user)
                    if found:
                        c.notice(nick, found)
                        return
                c.notice(nick, "I don't know. Ask me again in a few seconds.")
        else:
            c.notice(nick, "What? => " + cmd)


def rejig_ircbot(ircbot):
    _orig_whois = ircbot.connection.whois

    def my_whois(targets=None, *args, interrogate=False):
        if interrogate:
            dct = _on_whoisuser(c=interrogate, interrogate=True)
            return None if interrogate not in dct else dct[interrogate]
        else:
            return _orig_whois(targets, *args)

    def _on_whoisuser(c=None, e=None, interrogate=None):
        if not hasattr(_on_whoisuser, "dct"):
            _on_whoisuser.dct = {}
        if interrogate:
            return _on_whoisuser.dct
        nick = e.arguments[0]
        channel = e.target
        _on_whoisuser.dct[nick] = ' '.join(r for r in e.arguments)

    ircbot.connection.add_global_handler('whoisuser', _on_whoisuser, -1)  # svr.nickname
    ircbot.connection.whois = my_whois


if __name__ == "__main__":

    def _on_whoisuser(c=None, e=None, interrogate=None):
        if not hasattr(_on_whoisuser, "dct"):
            _on_whoisuser.dct = {}
        if interrogate:
            return _on_whoisuser.dct[interrogate]
        else:
            _on_whoisuser.dct[e.arguments[0]] = ' '.join([str(r) for r in e.arguments])

    ircbot = GroovyWhoisTestBot(channel="#prate", nickname='clyde', server='cinqcent.local', port=6667)
    ircbot.connect("cinqcent.local", 6667, "clyde")
    rejig_ircbot(ircbot)
    ircbot.start()

