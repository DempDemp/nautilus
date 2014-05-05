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
from core import botutils
from twitter import Api, TwitterError
from time import sleep
from threading import Thread

class twitterClass(botutils.baseClass):
    '''
    To setup an account:
        twitter set TWITTER_CONSUMER_KEY <key>
        twitter set TWITTER_CONSUMER_SECRET <key>
        twitter set TWITTER_ACCESS_TOKEN_KEY <key>
        twitter set TWITTER_ACCESS_TOKEN_SECRET <key>

    Set interval:
        twitter set TWITTER_INTERVAL <seconds>

    User flag required: t
    '''
    def __init__(self, irc):
        botutils.baseClass.__init__(self, irc)
        self.conn = sqlite3.connect(self.irc.users.dbfile, check_same_thread=False)
        self.thread = None
        self.createTables()
        self.setFollow()

    def __del__(self):
        super(twitterClass, self).__del__()
        self.follow = False
        
    def setFollow(self):
        self.api = self.getAPI()
        self.interval = self.getInterval()
        if self.api and len(self.getFollowing()) and self.interval:
            self.follow = True
        else:
            self.follow = False

    def createTables(self):
        cur = self.conn.cursor()
        cur.execute('''CREATE TABLE IF NOT EXISTS twitterFollow (id INTEGER PRIMARY KEY AUTOINCREMENT,
                botid TEXT NOT NULL,
                userid TEXT NOT NULL,
                displayname TEXT NOT NULL,
                channels TEXT NOT NULL,
                lasttweet TEXT NOT NULL)''')
        self.conn.commit()
        cur.close()

    def getAPI(self):
        cur = self.conn.cursor()
        cur.execute('SELECT setting, sval FROM botSettings WHERE botid=? AND setting LIKE ?', (self.irc.id, 'TWITTER_%'))
        res = cur.fetchall()
        cur.close()
        if len(res) == 4:
            try:
                apio = Api(consumer_key=filter(lambda x: x[0] == 'TWITTER_CONSUMER_KEY', res)[0][1],
                    consumer_secret=filter(lambda x: x[0] == 'TWITTER_CONSUMER_SECRET', res)[0][1],
                    access_token_key=filter(lambda x: x[0] == 'TWITTER_ACCESS_TOKEN_KEY', res)[0][1],
                    access_token_secret=filter(lambda x: x[0] == 'TWITTER_ACCESS_TOKEN_SECRET', res)[0][1])
                return apio
            except TwitterError as e:
                self.irc.logger.error('Twitter error: %s' % e.message)
                return False
        return False

    def getFollowing(self):
        cur = self.conn.cursor()
        cur.execute('SELECT id, userid, displayname, channels, lasttweet FROM twitterFollow WHERE botid=?', (self.irc.id,))
        res = cur.fetchall()
        cur.close()
        return res

    def getInterval(self):
        cur = self.conn.cursor()
        cur.execute("SELECT sval FROM botSettings WHERE botid=? AND setting='TWITTER_INTERVAL'", (self.irc.id,))
        res = cur.fetchone()
        cur.close()
        if res is None:
            return False
        else:
            return int(res[0])

    def setVar(self, setting, sval):
        cur = self.conn.cursor()
        if not setting.startswith('TWITTER_'):
            setting = 'TWITTER_%s' % setting
        cur.execute('INSERT OR REPLACE INTO botSettings (botid, setting, sval) VALUES (?, ?, ?)', (self.irc.id, setting, sval))
        self.conn.commit()
        cur.close()

    def delSetting(self, sid):
        cur = self.conn.cursor()
        cur.execute('DELETE FROM botSettings WHERE botid=? AND id=? AND setting LIKE ?', (self.irc.id, sid, 'TWITTER_%'))
        res = cur.rowcount
        self.conn.commit()
        cur.close()
        if res:
            return True
        return False

    def getSettings(self):
        cur = self.conn.cursor()
        cur.execute('SELECT id, setting, sval FROM botSettings WHERE botid=? AND setting LIKE ?', (self.irc.id, 'TWITTER_%'))
        res = cur.fetchall()
        cur.close()
        return res

    def setLastTweet(self, userid, tweetid):
        cur = self.conn.cursor()
        cur.execute('UPDATE twitterFollow SET lasttweet=? WHERE botid=? AND userid=?', (tweetid, self.irc.id, userid))
        self.conn.commit()
        cur.close()

    def addFollow(self, userid, displayname, channels):
        cur = self.conn.cursor()
        cur.execute('INSERT INTO twitterFollow (botid, userid, displayname, channels, lasttweet) VALUES (?, ?, ?, ?, ?)', 
                (self.irc.id, userid, displayname, channels, 0))
        self.conn.commit()
        cur.close()

    def delFollow(self, fid):
        cur = self.conn.cursor()
        cur.execute('DELETE FROM twitterFollow WHERE botid=? AND id=?', (self.irc.id, fid))
        res = cur.rowcount
        self.conn.commit()
        cur.close()
        if res:
            return True
        return False

    def startFollowingThread(self):
        while self.follow:
            following = self.getFollowing()
            for u in following:
                statuses = self.api.GetUserTimeline(u[1])
                lastId = long(u[4])
                if lastId == 0:
                    if len(statuses) > 1:
                        self.setLastTweet(u[1], statuses[1].id)
                        lastId = statuses[1].id
                for i, status in enumerate(statuses):
                    if i == 0:
                        self.setLastTweet(u[1], status.id)
                    if status.id > lastId:
                        self.irc.msg(u[3], 'Twitter @%s: %s' % (u[2], status.text.replace('\n', '').replace('\r', '').encode('utf-8')))
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
        if target == self.irc.nickname and text.startswith('twitter'):
            params = text.split(' ')
            if params[0] != 'twitter':
                return
            flags = self.irc.users.getFlags(hostmask=address)
            if flags is None or 't' not in flags[1]:
                self.irc.notice(address.split('!')[0], 'Insufficient privileges')
                return
            if len(params) == 1:
                self.irc.notice(address.split('!')[0], 'Available commands: set delsetting listsettings follow listfollowing unfollow')
                return
            if params[1] == 'set':
                if len(params) < 4:
                    self.irc.notice(address.split('!')[0], 'Usage: twitter set <key> <value>')
                else:
                    self.setVar(params[2], ' '.join(params[3:]))
                    self.irc.notice(address.split('!')[0], 'Done')
                    self.setFollow()
                    self.startFollowing()
            if params[1] == 'delsetting':
                if len(params) < 3:
                    self.irc.notice(address.split('!')[0], 'Usage: twitter delsetting <id>>')
                else:
                    if self.delSetting(params[2]):
                        self.irc.notice(address.split('!')[0], 'Done')
                    else:
                        self.irc.notice(address.split('!')[0], 'Unable to delete setting')
            elif params[1] == 'listsettings':
                settings = self.getSettings()
                self.irc.notice(address.split('!')[0], 'id key value')
                for s in settings:
                    self.irc.notice(address.split('!')[0], '%s %s %s' % s)
            elif params[1] == 'follow':
                if len(params) != 5:
                    self.irc.notice(address.split('!')[0], 'Usage: twitter follow <userid> <displayname> <channels>')
                else:
                    self.addFollow(params[2], params[3], params[4])
                    self.irc.notice(address.split('!')[0], 'Done')
                    self.setFollow()
                    self.startFollowing()
            elif params[1] == 'listfollowing':
                following = self.getFollowing()
                self.irc.notice(address.split('!')[0], 'id userid displayname channels lasttweet')
                for x in following:
                    self.irc.notice(address.split('!')[0], '%s %s %s %s %s' % x)
            elif params[1] == 'unfollow':
                if len(params) != 3:
                    self.irc.notice(address.split('!')[0], 'Usage: twitter unfollow <id>')
                else:
                    if self.delFollow(params[2]):
                        self.irc.notice(address.split('!')[0], 'Done')
                    else:
                        self.irc.notice(address.split('!')[0], 'Unable to unfollow id')

MODCLASSES = [twitterClass]
