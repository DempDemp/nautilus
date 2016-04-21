import time
from core import base
from core.utils import split_address

class Network(object):
    name = None
    options = None
    prefix = None
    my_modes = ''

    def __init__(self, bot_id):
        self.channels = []
        self.users = []
        self.bot_id = bot_id

    def get_channel(self, name):
        for channel in self.channels:
            if channel.name == name:
                return channel
        return None

    def get_user_by_nickname(self, nickname):
        for user in self.users:
            if user.nickname == nickname:
                return user
        return None

class Channel(object):
    topic = None
    my_modes = ''
    who_time = 0
    who_users_increased = True

    def __init__(self, network, name):
        self.users_attr = []
        self.modes = {}
        self.network = network
        self.name = name
        network.channels.append(self)

    def get_user_attr(self, nickname):
        for channeluser in self.users_attr:
            if channeluser.user.nickname == nickname:
                return channeluser
        return None

    def delete(self):
        self.network.channels.remove(self)

    def delete_user_attr(self, channeluser):
        self.users_attr.remove(channeluser)

    def __repr__(self):
        return u'<Channel: {}>'.format(self.name)

class User(object):
    username = None
    host = None
    realname = None
    networkauth = None

    def __init__(self, network, nickname):
        self.channels_attr = []
        self.network = network
        self.nickname = nickname
        network.users.append(self)

    def get_channel_attr(self, channelname):
        for chanattr in self.channels_attr:
            if chanattr.channel.name == channelname:
                return chanattr
        return None

    def delete_channel_attr(self, channeluser):
        self.channels_attr.remove(channeluser)
        if not len(self.channels_attr):
            self.delete()

    def delete(self):
        for chanattr in self.channels_attr:
            chanattr.channel.delete_user_attr(chanattr)
        self.network.users.remove(self)

    def __repr__(self):
        return u'<User: {}>'.format(self.nickname)

class ChannelUser(object):
    def __init__(self, user, channel, modes):
        self.user = user
        self.channel = channel
        self.modes = modes
        self.joined_time = time.time()
        user.channels_attr.append(self)
        channel.users_attr.append(self)
        channel.who_users_increased = True

    def __repr__(self):
        return u'<ChannelUser: {}>'.format(self.user.nickname)

class Tracker(base.baseClass):
    defer_to_thread = False

    def __init__(self, *args, **kwargs):
        super(Tracker, self).__init__(*args, **kwargs)
        if hasattr(self.irc, 'network'):
            self.network = self.irc.network
        else:
            self.network = Network(self.irc.id)
            self.irc.network = self.network

    def update_channel(self, chan):
        if time.time() - chan.who_time > 5*60 and chan.who_users_increased:
            self.irc.sendLine('who {} n%nar'.format(chan.name))
            chan.who_time = time.time()
            chan.who_users_increased = False

    def on_privmsg(self, address, target, text):
        if target[0] == '#':
            chan = self.network.get_channel(target)
            self.update_channel(chan)

    def on_network_supports(self, options):
        for option in options:
            if '=' in option:
                option, value = option.split('=', 1)
            else:
                value = None
            if option == 'NETWORK':
                self.network.name = value
            elif option == 'PREFIX':
                s = value[1:].split(')', 1)
                self.network.prefix = dict(zip(s[0], s[1]))

    def on_self_join(self, channel):
        chan = self.network.get_channel(channel)
        if chan is None:
            chan = Channel(self.network, channel)
            self.update_channel(chan)

    def on_self_part(self, channel):
        chan = self.network.get_channel(channel)
        if chan is not None:
            chan.delete()

    def on_self_kick(self, channel, kicker, message):
        chan = self.network.get_channel(channel)
        if chan is not None:
            chan.delete()

    def on_names(self, channel, nicknames):
        chan = self.network.get_channel(channel)
        if chan is not None:
            prefix = self.network.prefix.values()
            for nickname in nicknames:
                modes = ''.join(set(nickname) & set(prefix))
                for s in prefix:
                    nickname = nickname.replace(s, '')
                user = self.network.get_user_by_nickname(nickname)
                if user is None:
                    user = User(self.network, nickname)
                channeluser = user.get_channel_attr(channel)
                if channeluser is None:
                    channeluser = ChannelUser(user, chan, modes)

    def on_join(self, address, channel):
        chan = self.network.get_channel(channel)
        if chan is not None:
            nickname, username, hostname = split_address(address)
            user = self.network.get_user_by_nickname(nickname)
            if user is None:
                user = User(self.network, nickname)
            user.username = username
            user.hostname = hostname
            if hostname.startswith('unaffiliated/'):
                # freenode auth
                user.networkauth = hostname.split('/')[1]
            channeluser = ChannelUser(user, chan, '')

    def on_part(self, address, channel):
        chan = self.network.get_channel(channel)
        if chan is not None:
            nickname, username, hostname = split_address(address)
            user = self.network.get_user_by_nickname(nickname)
            channeluser = user.get_channel_attr(channel)
            chan.delete_user_attr(channeluser)
            user.delete_channel_attr(channeluser)

    def on_kick(self, kickee, channel, kicker, message):
        chan = self.network.get_channel(channel)
        if chan is not None:
            user = self.network.get_user_by_nickname(kickee)
            channeluser = user.get_channel_attr(channel)
            chan.delete_user_attr(channeluser)
            user.delete_channel_attr(channeluser)

    def on_quit(self, address, reason):
        nickname, username, hostname = split_address(address)
        user = self.network.get_user_by_nickname(nickname)
        user.delete()

    def on_nick(self, nickname, newnick):
        user = self.network.get_user_by_nickname(nickname)
        user.nickname = newnick

    def on_topic(self, nickname, channel, newtopic):
        chan = self.network.get_channel(channel)
        if chan is not None:
            chan.topic = newtopic

    def on_mode(self, nickname, channel, mode_set, modes, args):
        if channel == self.irc.nickname:
            for mode in modes:
                if mode_set and mode not in self.network.my_modes:
                    self.network.my_modes += mode
                elif not mode_set and mode in self.network.my_modes:
                    self.network.my_modes.replace(mode, '')
        else:
            chan = self.network.get_channel(channel)
            if chan is not None:
                prefix = self.network.prefix.values()
                for mode, arg in zip(list(modes), args):
                    if mode in prefix:
                        if arg == self.irc.nickname:
                            if mode_set and mode not in chan.my_modes:
                                chan.my_modes += mode
                            elif not mode_set and mode in chan.my_modes:
                                chan.my_modes.replace(mode, '')
                        else:
                            channeluser = chan.get_user_attr(arg)
                            if mode_set and mode not in channeluser.modes:
                                channeluser.modes += mode
                            elif not mode_set and mode in channeluser.modes:
                                channeluser.modes.replace(mode, '')
                    if mode not in 'bqeI':
                        if mode_set:
                            chan.modes[mode] = arg
                        else:
                            chan.modes.pop(mode, None)

    def on_who_special(self, prefix, params):
        if len(params) == 4:
            _, nickname, authname, realname = params
            user = self.network.get_user_by_nickname(nickname)
            user.realname = realname
            if authname != '0':
                user.networkauth = authname
