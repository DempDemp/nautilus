'''
Copyright 2014 Demp <lidor.demp@gmail.com>
This file is part of nautilus.

nautilus is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

nautilus is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with nautilus. If not, see <http://www.gnu.org/licenses/>.
'''

import json
import time
import sys
import logging
from twisted.words.protocols import irc
from twisted.internet import reactor, protocol
from twisted.internet.threads import deferToThread
from core.users import UserAccess
from threading import Lock


class nautilusBot(irc.IRCClient):
    versionName = 'nautilus'
    versionNum = '2.0'
    class_instances = []
    loaded_modules = []
    _floodQueue = []
    _floodLast = 0
    _floodCurrentBuffer = 0
    _floodWaitInvalid = False
    _floodLock = Lock()

    def setParamsFromFactory(self):
        self.nickname = self.factory.nickname
        self.realname = self.factory.realname
        self.floodBuffer = self.factory.floodBuffer
        self.dbfile = self.factory.dbfile
        self.id = self.factory.botid
        self.logger = self.factory.logger

    def connectionMade(self):
        irc.IRCClient.connectionMade(self)

    def signedOn(self):
        for instance in self.class_instances:
            deferToThread(instance.onSIGNEDON)

    def privmsg(self, user, channel, msg):
        for instance in self.class_instances:
            deferToThread(instance.onPRIVMSG, user, channel, msg)

    def noticed(self, user, channel, message):
        for instance in self.class_instances:
            deferToThread(instance.onNOTICE, user, channel, message)

    def userJoined(self, user, channel):
        for instance in self.class_instances:
            deferToThread(instance.onJOIN, user, channel)

    def userLeft(self, user, channel):
        for instance in self.class_instances:
            deferToThread(instance.onPART, user, channel)

    def userQuit(self, user, quitMessage):
        for instance in self.class_instances:
            deferToThread(instance.onQUIT, user, quitMessage)

    def userRenamed(self, oldname, newname):
        for instance in self.class_instances:
            deferToThread(instance.onNICK, oldname, newname)

    def sendLine(self, line):
        ''' normal sendLine with flood protection '''
        if type(line) == unicode:
            try:
                line = line.encode('utf-8')
            except UnicodeDecodeError:
                pass
        if line.startswith(('PRIVMSG', 'NOTICE')):
            length = sys.getsizeof(line) - sys.getsizeof(type(line)()) + 2
            if length <= self.floodBuffer - self._floodCurrentBuffer:
                # buffer isn't full, send
                irc.IRCClient.sendLine(self, line)
                self.updateFloodBuffer(length)
            else:
                # send an invalid command
                with self._floodLock:
                    self._floodQueue.append(line)
                    if not self._floodWaitInvalid:
                        irc.IRCClient.sendLine(self, '_!')
                        self._floodWaitInvalid = True
        else:
            irc.IRCClient.sendLine(self, line)

    def updateFloodBuffer(self, length):
        with self._floodLock:
            if time.time() - self._floodLast >= 30:
                # reset flood buffer
                self._floodCurrentBuffer = length
            else:
                self._floodCurrentBuffer += length
            self._floodLast = time.time()

    def irc_unknown(self, prefix, command, params):
        with self._floodLock:
            self._floodCurrentBuffer = 0
            self._floodWaitInvalid = False
            while self._floodQueue:
                self.sendLine(self._floodQueue.pop(0))

    def lineReceived(self, line):
        if self.factory.debug:
            self.logger.debug(line)
        irc.IRCClient.lineReceived(self, line)

    def _reallySendLine(self, line):
        if self.factory.debug:
            self.logger.debug(line)
        irc.IRCClient._reallySendLine(self, line)


class nautilusBotFactory(protocol.ClientFactory):
    protocol = nautilusBot
    defaultmodules = ['core.users', 'core.perform']

    def __init__(self, botid, configfile='config.json'):
        self.configfile = configfile
        self.botid = botid
        self.setFromJSON()
        self.logger = logging.getLogger('rotter')
        if self.debug:
            self.logger.setLevel(logging.DEBUG)
        else:
            self.logger.setLevel(logging.WARN)
        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(logging.DEBUG)
        self.logger.addHandler(ch)
        fh = logging.FileHandler('%s.log' % self.botid, encoding='utf-8')
        fh.setLevel(logging.WARN)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        fh.setFormatter(formatter)
        self.logger.addHandler(fh)

    def setFromJSON(self):
        with open(self.configfile) as f:
            j = json.load(f)
        for b in j['bots']:
            if b['id'] == self.botid:
                self.nickname = b['nickname']
                self.realname = b['realname']
                self.modules = b['modules']
                self.floodBuffer = b['floodBuffer']
                self.dbfile = b['dbfile']
                self.debug = b['debug']
                return

    def buildProtocol(self, addr):
        self.bot = nautilusBot()
        self.bot.factory = self
        self.bot.setParamsFromFactory()
        self.bot.users = UserAccess(self.bot)
        if len(self.bot.loaded_modules):
            self.unload_all_modules()
        self.initialize_modules()
        return self.bot

    def clientConnectionLost(self, connector, reason):
        """If we get disconnected, reconnect to server."""
        print 'connection lost:', reason
        connector.connect()

    def clientConnectionFailed(self, connector, reason):
        print 'connection failed:', reason
        reactor.stop()

    def initialize_modules(self):
        self.bot.loaded_modules = []
        mlist = self.defaultmodules + self.modules
        for m in mlist:
            loaded = True
            if not m.startswith('core.'):
                m = 'modules.%s' % m
            try:
                mo = __import__(m, globals(), locals(), ['MODCLASSES'], -1)
                for c in mo.MODCLASSES:
                    ci = c(self.bot)
                    self.bot.class_instances.append(ci)
            except ImportError as e:
                loaded = False # could not load module
            if loaded:
                self.bot.loaded_modules.append(m)

    def delete_module(self, modname):
        try:
            thismod = sys.modules[modname]
        except KeyError:
            raise ValueError(modname)
        these_symbols = dir(thismod)
        del sys.modules[modname]
        for mod in sys.modules.values():
            try:
                delattr(mod, modname)
            except AttributeError:
                pass

    def unload_all_modules(self):
        self.bot.class_instances = []
        for loaded_module in self.bot.loaded_modules:
            self.delete_module(loaded_module)

if __name__ == '__main__':
    with open('config.json') as f:
        j = json.load(f)
    for b in j['bots']:
        # create factory protocol and application
        factory = nautilusBotFactory(b['id'])
        # connect factory to this host and port
        if b['ssl']:
            reactor.connectSSL(b['server'], b['port'], factory)
        else:
            reactor.connectTCP(b['server'], b['port'], factory)

    # run bot
    reactor.run()
