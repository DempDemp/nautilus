import re
from collections import defaultdict

# bot commands prefix
prefix = r'^[`~!@#$%^&*()_-+=[];:\'"\|,<.>/?]'

class CommandArguments(object):
    def __init__(self, command, events, min_params, prefix):
        self.command = command if isinstance(command, list) else [command]
        self.events = events if isinstance(events, list) else [events]
        self.min_params = min_params
        self.prefix = prefix


def command(command, events='on_privmsg', min_params=0, prefix=prefix):
    def _decorator(func):
        args = CommandArguments(command, events, min_params, prefix)
        def __decorator(*args, **kwargs):
            return func(*args, **kwargs)
        __decorator._cmd_args = args
        return __decorator
    return _decorator

class baseClass(object):
    ''' base class for modules '''
    defer_to_thread = True # should be changed to False
    _commands = None

    def __init__(self, irc):
        self.irc = irc
        commands = defaultdict(list)
        for attr in dir(self):
            obj = getattr(self, attr)
            if hasattr(obj, '_cmd_args'):
                cmd_args = getattr(obj, '_cmd_args')
                for event in cmd_args.events:
                    commands[event].append(obj)
        self._commands = commands

    def _process_event(self, event, address, target, text):
        for func in self._commands[event]:
            cmd_args = func._cmd_args
            cmd = text.strip().split(' ', 1)[0][1:]
            if text[0] in cmd_args.prefix and cmd in cmd_args.command and len(text.split()) >= cmd_args.min_params + 1:
                params = text.strip().split()[1:]
                func(event=event, address=address, target=target, text=text, cmd=cmd, params=params)

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
        if self._commands['on_privmsg']:
            self._process_event('on_privmsg', address, target, text)

    def on_notice(self, address, target, text):
        if self._commands['on_notice']:
            self._process_event('on_notice', address, target, text)

    def on_action(self, nickname, channel, data):
        if self._commands['on_action']:
            self._process_event('on_action', nickname, channel, data)

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
