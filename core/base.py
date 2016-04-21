import re

# bot commands prefix
prefix = r'^[`~!@#$%^&*()_-+=[];:\'"\|,<.>/?]'

class baseClass(object):
    ''' base class for modules '''
    defer_to_thread = True # should be changed to False

    def __init__(self, irc):
        self.irc = irc

    ''' following functions handle triggers '''
    def on_signedon(self):
        pass

    def on_network_supports(self, options):
        pass

    def on_names(self, channel, nicknames):
        pass

    def on_who_special(self, prefix, params):
        pass

    def on_privmsg(self, address, target, text):
        pass

    def on_notice(self, address, target, text):
        pass

    def on_action(self, nickname, channel, data):
        pass

    def on_topic(self, nickname, channel, newtopic):
        pass

    def on_mode(self, nickname, channel, mode_set, modes, args):
        pass

    def on_join(self, address, channel):
        pass

    def on_part(self, address, channel, reason):
        pass

    def on_quit(self, address, reason):
        pass

    def on_nick(self, nickname, newnick):
        pass

    def on_kick(self, kickee, channel, kicker, message):
        pass

    def on_raw(self, line):
        pass

    def on_self_join(self, channel):
        pass

    def on_self_part(self, channel):
        pass

    def on_self_nick(self, nick):
        pass

    def on_self_kick(self, channel, kicker, message):
        pass
