import sys
import time
import logging
import settings
import core.conf
from core.base import baseClass
from threading import Lock
from twisted.internet import ssl, reactor, protocol
from twisted.words.protocols import irc
from twisted.internet.threads import deferToThread

class nautilusBot(irc.IRCClient):
    versionName = 'nautilus'
    versionNum = '3.0'
    class_instances = []
    loaded_modules = []
    _flood_buffer = 1024
    _flood_queue = []
    _flood_last = 0
    _flood_current_buffer = 0
    _flood_wait_invalid = False
    _flood_lock = Lock()

    @classmethod
    def add_func(cls, name, mappedname):
        def inner_func(self, *args, **kwargs):
            for instance in self.class_instances:
                if instance.defer_to_thread:
                    deferToThread(getattr(instance, mappedname), *args, **kwargs)
                else:
                    getattr(instance, mappedname)(*args, **kwargs)
        inner_func.__name__ = name
        setattr(cls, name, inner_func)

    def set_params_factory(self):
        self._flood_buffer = self.factory._flood_buffer
        self.nickname = self.factory.nickname
        self.realname = self.factory.realname
        self.id = self.factory.botid
        self.logger = self.factory.logger

    def connectionMade(self):
        irc.IRCClient.connectionMade(self)

    def sendLine(self, line, queue=True):
        ''' normal sendLine with flood protection '''
        if type(line) == unicode:
            try:
                line = line.encode('utf-8')
            except UnicodeDecodeError:
                pass
        if line.startswith(('PRIVMSG', 'NOTICE')):
            length = sys.getsizeof(line) - sys.getsizeof(type(line)()) + 2
            if length <= self._flood_buffer - self._flood_current_buffer:
                # buffer isn't full, send
                self.update_flood_buffer(length)
                irc.IRCClient.sendLine(self, line)
                return True
            else:
                # send an invalid command
                if queue:
                    with self._flood_lock:
                        self._flood_queue.append(line)
                if not self._flood_wait_invalid:
                    irc.IRCClient.sendLine(self, '_!')
                    self._flood_wait_invalid = True
                return False
        else:
            irc.IRCClient.sendLine(self, line)
            return True

    def update_flood_buffer(self, length):
        if time.time() - self._flood_last >= 90:
            # reset flood buffer
            self._flood_current_buffer = length
        else:
            self._flood_current_buffer += length
        self._flood_last = time.time()

    def irc_unknown(self, prefix, command, params):
        if command == 'ERR_UNKNOWNCOMMAND':
            with self._flood_lock:
                self._flood_current_buffer = 0
                self._flood_wait_invalid = False
                while self._flood_queue:
                    line = self._flood_queue[0]
                    if self.sendLine(line, queue=False):
                        self._flood_queue.pop(0)
                    else:
                        break

    def lineReceived(self, line):
        if self.factory.debug:
            self.logger.debug(line)
        irc.IRCClient.lineReceived(self, line)

    def _reallySendLine(self, line):
        if self.factory.debug:
            self.logger.debug(line)
        irc.IRCClient._reallySendLine(self, line)

    def irc_JOIN(self, prefix, params):
        nick = prefix.split('!', 1)[0]
        channel = params[-1]
        if nick == self.nickname:
            self.joined(channel)
        else:
            self.userJoined(prefix, channel)

    def irc_PART(self, prefix, params):
        channel = params[0]
        reason = None
        if len(params) == 2:
            reason = params[1]
        if prefix.split('!', 1)[0] == self.nickname:
            self.left(channel)
        else:
            self.userLeft(prefix, channel, reason)

    def irc_QUIT(self, prefix, params):
        self.userQuit(prefix, params[0])

    def irc_RPL_NAMREPLY(self, prefix, params):
        self.on_names(params[-2], params[-1].split())

class nautilusBotFactory(protocol.ClientFactory):
    protocol = nautilusBot
    default_modules = ['core.auth', 'core.perform', 'core.utils', 'core.tracker']
    mapped_funcs = (
        ('signedOn', 'on_signedon'),
        ('isupport', 'on_network_supports'),
        ('on_names', 'on_names'),
        ('irc_354', 'on_who_special'),
        ('privmsg', 'on_privmsg'),
        ('noticed', 'on_notice'),
        ('action', 'on_action'),
        ('topicUpdated', 'on_topic'),
        ('modeChanged', 'on_mode'),
        ('userJoined', 'on_join'),
        ('userLeft', 'on_part'),
        ('userQuit', 'on_quit'),
        ('userRenamed', 'on_nick'),
        ('userKicked', 'on_kick'),
        ('joined', 'on_self_join'),
        ('left', 'on_self_part'),
        ('nickChanged', 'on_self_nick'),
        ('kickedFrom', 'on_self_kick'),
    )

    def __init__(self, botid, factories):
        for name, mappedname in self.mapped_funcs:
            nautilusBot.add_func(name, mappedname)
        self.factories = factories
        self.botid = botid
        self.debug = core.conf.settings.DEBUG
        self.load_settings()
        self.logger = logging.getLogger(self.botid)
        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(logging.DEBUG)
        self.logger.addHandler(ch)
        fh = logging.FileHandler('{}.log'.format(self.botid))
        fh.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        fh.setFormatter(formatter)
        self.logger.addHandler(fh)
        if self.debug:
            self.logger.setLevel(logging.DEBUG)
        else:
            self.logger.setLevel(logging.INFO)

    def load_settings(self):
        for bot in core.conf.settings.BOTS:
            if bot['id'] == self.botid:
                self.nickname = bot['nickname']
                self.realname = bot['realname']
                self.modules = bot['modules']
                self._flood_buffer = bot['flood_buffer']
                break

    def initialize_modules(self):
        from core.db import Base, engine
        self.logger.info('Loading modules')
        loaded_modules = []
        loaded_modules_names = []
        cls_list = []
        modules = self.default_modules + self.modules
        for modulename in modules:
            if not modulename.startswith('core.'):
                modulename = 'modules.%s' % modulename
            try:
                self.logger.info('Loading {}'.format(modulename))
                module = __import__(modulename, globals(), locals(), [], -1)
                if module in self.bot.loaded_modules:
                    print 'trying to reload %s' % modulename
                    reload(module)
            except ImportError as e:
                self.logger.warn('Unable to load {}. {}'.format(modulename, e))
            else:
                loaded_modules.append(module)
                loaded_modules_names.append(modulename)
        self.bot.loaded_modules = loaded_modules
        Base.metadata.create_all(engine)
        print baseClass.__subclasses__()
        for cls in baseClass.__subclasses__():
            if cls.__module__ in loaded_modules_names:
                instance = cls(self.bot)
                self.bot.class_instances.append(instance)

    def reload_all_modules(self):
        for class_instance in self.bot.class_instances:
            # explicitly call __del__ for each class instance in case it's running a thread
            if hasattr(class_instance, '__del__'):
                class_instance.__del__()
        self.bot.class_instances = []

    def reload_modules(self):
        from core.db import Base
        reload(settings)
        core.conf.settings.setup(settings)
        self.load_settings()
        Base.metadata.clear()
        for factory in self.factories:
            factory.reload_all_modules()
        for factory in self.factories:
            factory.initialize_modules()

    def buildProtocol(self, addr):
        self.bot = nautilusBot()
        self.bot.factory = self
        self.bot.set_params_factory()
        self.reload_all_modules()
        self.initialize_modules()
        return self.bot

    def clientConnectionLost(self, connector, reason):
        self.logger.error('Connection lost: %s', reason)
        connector.connect()

    def clientConnectionFailed(self, connector, reason):
        self.logger.error('Connection failed: %s', reason)
        reactor.stop()

if __name__ == '__main__':
    core.conf.settings.setup(settings)
    factories = []
    for bot in core.conf.settings.BOTS:
        botFactory = nautilusBotFactory(bot['id'], factories)
        factories.append(botFactory)
        if bot['ssl']:
            reactor.connectSSL(bot['server'], bot['port'], botFactory, ssl.CertificateOptions())
        else:
            reactor.connectTCP(bot['server'], bot['port'], botFactory)
    reactor.run()
