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

import urllib
import urllib2
import sqlite3
import re
from core import botutils
from urlparse import urlparse
from BeautifulSoup import BeautifulSoup

titleregex = re.compile('<title(?:[a-zA-Z\= \'\"]*)>([^<]*)</title>', re.DOTALL | re.MULTILINE | re.IGNORECASE)
charsetregex = re.compile('charset=([\w\-]+)', re.DOTALL | re.MULTILINE | re.IGNORECASE)


class titleClass(botutils.baseClass):
    def __init__(self, irc):
        botutils.baseClass.__init__(self, irc)
        self.conn = sqlite3.connect(self.irc.users.dbfile, check_same_thread=False)
        self.createTables()
        self.regexes = []
        self.setRegexes()

    def createTables(self):
        cur = self.conn.cursor()
        cur.execute('''CREATE TABLE IF NOT EXISTS title_regex (id INTEGER PRIMARY KEY AUTOINCREMENT,
                botid TEXT NOT NULL,
                regex TEXT NOT NULL)''')
        self.conn.commit()
        cur.close()

    def getRegexes(self):
        cur = self.conn.cursor()
        cur.execute('SELECT id, regex FROM title_regex WHERE botid=?', (self.irc.id,))
        res = cur.fetchall()
        cur.close()
        return res

    def addRegex(self, regex):
        cur = self.conn.cursor()
        cur.execute('INSERT INTO title_regex (botid, regex) VALUES (?, ?)', (self.irc.id, regex))
        self.conn.commit()
        cur.close()

    def delRegex(self, rid):
        cur = self.conn.cursor()
        cur.execute('DELETE FROM title_regex WHERE botid=? AND id=?', (self.irc.id, rid))
        res = cur.rowcount
        self.conn.commit()
        cur.close()
        if res:
            return True
        return False

    def setRegexes(self):
        regexes = self.getRegexes()
        for rid, regex in regexes:
            self.regexes.append(re.compile(regex))

    def purify(self, s):
        if isinstance(s, str) or isinstance(s, unicode):
            return unicode(BeautifulSoup(s.replace("\n", '').replace("\r", '').replace("\t", ''), convertEntities=BeautifulSoup.HTML_ENTITIES))
        else:
            return s

    def getTitle(self, url):
        if len(url) == 0:
            return {'error': 'error'}
        host = urlparse(url)
        host = host.netloc
        req = urllib2.Request(url)
        try:
            response = urllib2.urlopen(req)
        except urllib2.HTTPError, e:
            return {'error': 'error'}
        data = response.read()

        title = titleregex.search(data)
        if title is not None:
            title = title.group(1)
        else:
            return {'error': 'error'}
        charset = charsetregex.search(data)
        if charset is not None:
            charset = charset.group(1)
            if charset.lower() != 'utf-8':
                title = title.decode(charset)
        return {'url': url, 'title': self.purify(title)}

    def privmsg_format(self, result):
        if 'error' in result:
            msg = ''
        else:
            if len(result['title']) > 200:
                result['title'] = result['title'][0:197] + '...'
            msg = 'Title: ' + result['title'] + '.'
        return msg

    def onPRIVMSG(self, address, target, text):
        if target[0] == '#' and 'http' in text:
            for regex in self.regexes:
                titlesearch = regex.search(text)
                if titlesearch is not None:
                    link = titlesearch.group(1)
                    result = self.getTitle(link)
                    if not 'error' in result:
                        self.irc.msg(target, self.privmsg_format(result))
                    break
        elif target == self.irc.nickname and text.startswith('titles'):
            params = text.split(' ')
            if params[0] != 'titles':
                return
            flags = self.irc.users.getFlags(hostmask=address)
            if flags is None or 'w' not in flags[1]:
                self.irc.notice(address.split('!')[0], 'Insufficient privileges')
                return
            if len(params) == 1:
                self.irc.notice(address.split('!')[0], 'Available commands: add del list')
                return
            elif params[1] == 'add':
                if len(params) != 3:
                    self.irc.notice(address.split('!')[0], 'Usage: titles add <regex>')
                else:
                    self.addRegex(' '.join(params[2:]))
                    self.irc.notice(address.split('!')[0], 'Done')
                    self.setRegexes()
            elif params[1] == 'del':
                if len(params) != 3:
                    self.irc.notice(address.split('!')[0], 'Usage: twitter del <id>')
                else:
                    if self.delRegex(params[2]):
                        self.irc.notice(address.split('!')[0], 'Done')
                    else:
                        self.irc.notice(address.split('!')[0], 'Unable to delete regex')
            elif params[1] == 'list':
                regexes = self.getRegexes()
                self.irc.notice(address.split('!')[0], 'id regex')
                for x in regexes:
                    self.irc.notice(address.split('!')[0], '%s %s' % x)

MODCLASSES = [titleClass]
