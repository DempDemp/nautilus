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

import sqlite3
import feedparser
import requests
from operator import itemgetter
from core import botutils
from time import sleep, mktime
from threading import Thread
from datetime import datetime

def tinyurl(s):
    r = requests.get('http://tinyurl.com/api-create.php', params={'url': s})
    if r.status_code == 200:
        return r.text
    return False

class rssClass(botutils.baseClass):
    '''

    Set interval:
        twitter set RSS_INTERVAL <seconds>

    User flag required: r
    '''
    def __init__(self, irc):
        botutils.baseClass.__init__(self, irc)
        self.conn = sqlite3.connect(self.irc.users.dbfile, check_same_thread=False,
                detect_types=sqlite3.PARSE_DECLTYPES)
        self.thread = None
        self.createTables()
        self.setFollow()

    def __del__(self):
        super(rssClass, self).__del__()
        self.follow = False
        
    def setFollow(self):
        self.interval = self.getInterval()
        if len(self.getFeeds()) and self.interval:
            self.follow = True
        else:
            self.follow = False

    def createTables(self):
        cur = self.conn.cursor()
        cur.execute('''CREATE TABLE IF NOT EXISTS rssFeeds (id INTEGER PRIMARY KEY AUTOINCREMENT,
                botid TEXT NOT NULL,
                name TEXT NOT NULL,
                url TEXT NOT NULL,
                channels TEXT NOT NULL,
                lastitem TIMESTAMP)''')
        self.conn.commit()
        cur.close()

    def getFeeds(self):
        cur = self.conn.cursor()
        cur.execute('SELECT id, name, url, channels, lastitem FROM rssFeeds WHERE botid=?', (self.irc.id,))
        res = cur.fetchall()
        cur.close()
        return res

    def getInterval(self):
        cur = self.conn.cursor()
        cur.execute("SELECT sval FROM botSettings WHERE botid=? AND setting='RSS_INTERVAL'", (self.irc.id,))
        res = cur.fetchone()
        cur.close()
        if res is None:
            return False
        else:
            return int(res[0])

    def setInterval(self, sval):
        cur = self.conn.cursor()
        cur.execute('INSERT OR REPLACE INTO botSettings (botid, setting, sval) VALUES (?, ?, ?)', (self.irc.id, 'RSS_INTERVAL', sval))
        self.conn.commit()
        cur.close()
        self.interval = int(sval)

    def setLastItem(self, feedid, d):
        cur = self.conn.cursor()
        cur.execute('UPDATE rssFeeds SET lastitem=? WHERE botid=? AND id=?', (d, self.irc.id, feedid))
        self.conn.commit()
        cur.close()

    def addFeed(self, name, url, channels):
        cur = self.conn.cursor()
        cur.execute('INSERT INTO rssFeeds (botid, name, url, channels) VALUES (?, ?, ?, ?)', 
                (self.irc.id, name, url, channels))
        self.conn.commit()
        cur.close()

    def delFeed(self, fid):
        cur = self.conn.cursor()
        cur.execute('DELETE FROM rssFeeds WHERE botid=? AND id=?', (self.irc.id, fid))
        res = cur.rowcount
        self.conn.commit()
        cur.close()
        if res:
            return True
        return False

    def startFollowingThread(self):
        while self.follow:
            feeds = self.getFeeds()
            for feedid, name, url, channels, lastitem in feeds:
                feed = feedparser.parse(url)
                entries = sorted(feed.entries, key=itemgetter('published_parsed'), reverse=True)
                if lastitem is None:
                    if len(feed.entries) > 1:
                        lastitem = datetime.fromtimestamp(mktime(entries[1].published_parsed))
                        self.setLastItem(feedid, lastitem)
                for i, entry in enumerate(entries):
                    published = datetime.fromtimestamp(mktime(entry.published_parsed))
                    if i == 0:
                        self.setLastItem(feedid, published)
                    if published > lastitem:
                        turl = tinyurl(entry.link)
                        self.irc.msg(channels, '%s: %s %s' % (name,
                                entry.title.replace('\n', '').replace('\r', ''), turl))
            sleep(self.interval)

    def startFollowing(self):
        if self.follow:
            if not self.thread or not self.thread.isAlive():
                self.thread = Thread(target=self.startFollowingThread)
                self.thread.daemon = False
                self.thread.start()

    def onSIGNEDON(self):
        sleep(15)
        self.startFollowing()

    def onPRIVMSG(self, address, target, text):
        if target == self.irc.nickname and text.startswith('rss'):
            params = text.split(' ')
            if params[0] != 'rss':
                return
            flags = self.irc.users.getFlags(hostmask=address)
            if flags is None or 'r' not in flags[1]:
                self.irc.notice(address.split('!')[0], 'Insufficient privileges')
                return
            if len(params) == 1:
                self.irc.notice(address.split('!')[0], 'Available commands: interval add list delete')
                return
            if params[1] == 'interval':
                if len(params) < 3:
                    i = self.getInterval() or 'None'
                    self.irc.notice(address.split('!')[0], 'Usage: rss interval <seconds>. Current interval: %s' % i)
                else:
                    self.setInterval(params[2])
                    self.irc.notice(address.split('!')[0], 'Done')
                    self.setFollow()
                    self.startFollowing()
            elif params[1] == 'add':
                if len(params) != 5:
                    self.irc.notice(address.split('!')[0], 'Usage: rss add <name> <url> <channels>')
                else:
                    self.addFeed(params[2], params[3], params[4])
                    self.irc.notice(address.split('!')[0], 'Done')
                    self.setFollow()
                    self.startFollowing()
            elif params[1] == 'list':
                following = self.getFeeds()
                self.irc.notice(address.split('!')[0], 'id name url channels lastitem')
                for x in following:
                    self.irc.notice(address.split('!')[0], '%s %s %s %s %s' % x)
            elif params[1] == 'delete':
                if len(params) != 3:
                    self.irc.notice(address.split('!')[0], 'Usage: rss delete <id>')
                else:
                    if self.delFeed(params[2]):
                        self.irc.notice(address.split('!')[0], 'Done')
                    else:
                        self.irc.notice(address.split('!')[0], 'Unable to delete id')

MODCLASSES = [rssClass]
