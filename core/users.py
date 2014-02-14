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

import botutils
import sqlite3
import hashlib

class usersClass(botutils.baseClass):

    def __init__(self, irc):
        botutils.baseClass.__init__(self, irc)
        self.db = self.irc.dbfile

    def onPRIVMSG(self, address, target, text):
        if target == self.irc.nickname:
            if text.startswith('auth'):
                params = text.split(' ')
                if len(params) < 3:
                    self.irc.notice(address.split('!')[0], 'Usage: auth <username> <password>')
                    return
                else:
                    userdata = self.irc.users.authenticate(params[1], params[2])
                    if not userdata:
                        self.irc.notice(address.split('!')[0], 'Incorrect username or password')
                    else:
                        self.irc.users.setHostmask(userdata[0], address)
                        self.irc.notice(address.split('!')[0], 'Successfully logged in. User flags: %s' % userdata[1])
            elif text.startswith('users'):
                params = text.split(' ')
                if params[0] != 'users':
                    return
                flags = self.irc.users.getFlags(hostmask=address)
                if flags is None:
                    self.irc.notice(address.split('!')[0], 'Insufficient privileges')
                    return
                if len(params) == 1:
                    self.irc.notice(address.split('!')[0], 'Available commands: whoami changepass add delete list setflags')
                    return
                if params[1] == 'whoami':
                    userdata = self.irc.users.getFlags(hostmask=address)
                    self.irc.notice(address.split('!')[0], 'Username: %s, flags: %s' % userdata)
                elif params[1] == 'changepass':
                    if len(params) < 4:
                        if 'n' in flags[1]:
                            self.irc.notice(address.split('!')[0], 'Usage: users changepass [username] <oldpass> <newpass>')
                        else:
                            self.irc.notice(address.split('!')[0], 'Usage: users changepass <oldpass> <newpass>')
                    elif len(params) == 4:
                        try:
                            self.irc.users.changePass(username=flags[0], password=params[3])
                            self.irc.notice(address.split('!')[0], 'Done')
                        except ValueError as e:
                            self.irc.notice(address.split('!')[0], e.message)
                        return
                    elif len(params) == 5:
                        if 'n' in flags[1]:
                            try:
                                self.irc.users.changePass(username=params[2], password=params[3])
                                self.irc.notice(address.split('!')[0], 'Done')
                            except ValueError as e:
                                self.irc.notice(address.split('!')[0], e.message)
                elif params[1] == 'add':
                    if 'n' not in flags[1]:
                        self.irc.notice(address.split('!')[0], 'Insufficient privileges')
                        return
                    if len(params) < 4:
                        self.irc.notice(address.split('!')[0], 'Usage: users add <username> <password> <flags>')
                    else:
                        try:
                            self.irc.users.addUser(params[1], params[2], params[3])
                            self.irc.notice(address.split('!')[0], 'Done')
                        except ValueError as e:
                            self.irc.notice(address.split('!')[0], e.message)
                elif params[1] == 'delete':
                    if 'n' not in flags[1]:
                        self.irc.notice(address.split('!')[0], 'Insufficient privileges')
                        return
                    if len(params) < 3:
                        self.irc.notice(address.split('!')[0], 'Usage: users delete <username>')
                    else:
                        try:
                            self.irc.users.delUser(params[2])
                            self.irc.notice(address.split('!')[0], 'Done')
                        except ValueError as e:
                            self.irc.notice(address.split('!')[0], e.message)
                elif params[1] == 'list':
                    if 'n' not in flags[1]:
                        self.irc.notice(address.split('!')[0], 'Insufficient privileges')
                        return
                    users = self.irc.users.listUsers()
                    self.irc.notice(address.split('!')[0], 'Username Hostmask Flags')
                    for x in users:
                        self.irc.notice(address.split('!')[0], '%s %s %s' % x)
                elif params[1] == 'setflags':
                    if 'n' not in flags[1]:
                        self.irc.notice(address.split('!')[0], 'Insufficient privileges')
                        return
                    if len(params) < 4:
                        self.irc.notice(address.split('!')[0], 'Usage: users setflags <username> <flags>')
                        return
                    else:
                        try:
                            self.irc.users.changeFlags(params[2], params[3])
                            self.irc.notice(address.split('!')[0], 'Done')
                        except ValueError as e:
                            self.irc.notice(address.split('!')[0], e.message)


class UserAccess:
    def __init__(self, irc):
        self.irc = irc
        self.dbfile = irc.dbfile
        self.conn = sqlite3.connect(self.dbfile, check_same_thread=False)
        self.createTables()

    def createTables(self):
        cur = self.conn.cursor()
        cur.execute('''CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT,
                botid TEXT NOT NULL,
                username TEXT NOT NULL,
                password TEXT NOT NULL,
                hostmask TEXT NOT NULL,
                flags TEXT NOT NULL)''')
        cur.execute('SELECT COUNT(*) FROM users WHERE botid=?', (self.irc.id,))
        if not cur.fetchone()[0]:
            cur.execute('INSERT INTO users (botid, username, password, hostmask, flags) VALUES (?, ?, ?, ?, ?)', (self.irc.id,
                    'admin',
                    hashlib.sha512(str(self.irc.id) + '12345').hexdigest(),
                    '*',
                    'n'))
        self.conn.commit()
        cur.close()

    def authenticate(self, username, password):
        hashed = hashlib.sha512(str(self.irc.id) + password).hexdigest()
        cur = self.conn.cursor()
        cur.execute('SELECT id, flags FROM users WHERE botid=? AND username=? AND password=?', (self.irc.id, 
                username,
                hashlib.sha512(str(self.irc.id) + password).hexdigest()))
        res = cur.fetchone()
        cur.close()
        if res is not None:
            return res
        return False

    def setHostmask(self, userid, hostmask):
        cur = self.conn.cursor()
        cur.execute('UPDATE users SET hostmask=? WHERE id=?', (hostmask, userid))
        self.conn.commit()
        cur.close()

    def userExists(self, username=None, userid=None):
        if username is None and userid is None:
            return False
        cur = self.conn.cursor()
        if username is not None:
            cur.execute('SELECT COUNT(*) FROM users WHERE botid=? AND username=?', (self.irc.id, username))
        else:
            cur.execute('SELECT COUNT(*) FROM users WHERE botid=? AND id=?', (self.irc.id, userid))
        res = cur.fetchone()
        cur.close()
        if res[0]:
            return True
        return False

    def getFlags(self, username=None, hostmask=None):
        ''' returns (username, flags) if user exists, or None '''
        cur = self.conn.cursor()
        if username is not None and hostmask is not None:
            cur.execute('SELECT username, flags FROM users WHERE username=? AND hostmask=?', (username, hostmask))
        elif username is not None:
            cur.execute('SELECT username, flags FROM users WHERE username=?', (username,))
        elif hostmask is not None:
            cur.execute('SELECT username, flags FROM users WHERE hostmask=?', (hostmask,))
        else:
            cur.close()
            return None
        res = cur.fetchone()
        cur.close()
        return res

    def addUser(self, username, password, flags):
        if self.userExists(username):
            raise ValueError('Username already exists')
        else:
            cur = self.conn.cursor()
            cur.execute('INSERT INTO users (botid, username, password, hostmask, flags) VALUES (?, ?, ?, ?, ?)', (self.irc.id,
                    username,
                    hashlib.sha512(str(self.irc.id) + password).hexdigest(),
                    '*',
                    flags))
            self.conn.commit()
            cur.close()

    def delUser(self, username):
        if not self.userExists(username):
            raise ValueError('Username does not exist')
        else:
            cur = self.conn.cursor()
            cur.execute('DELETE FROM users WHERE botid=? AND username=?', (self.irc.id, username))
            self.conn.commit()
            cur.close()

    def changePass(self, password, userid=None, username=None):
        if not self.userExists(username=username, userid=userid):
            raise ValueError('Username does not exist')
        else:
            cur = self.conn.cursor()
            if userid is None:
                v = ('username', username)
            else:
                v = ('id', userid)
            cur.execute('UPDATE users SET password=? WHERE botid=? AND %s=?' % (v[0]), (hashlib.sha512(str(self.irc.id) + password).hexdigest(),
                    self.irc.id,
                    v[1]))
            self.conn.commit()
            cur.close()

    def changeFlags(self, username, flags):
        if not self.userExists(username=username):
            raise ValueError('Username does not exist')
        else:
            cur = self.conn.cursor()
            cur.execute('UPDATE users SET flags=? WHERE botid=? AND username=?', (flags,
                    self.irc.id,
                    username))
            self.conn.commit()
            cur.close()

    def listUsers(self):
        cur = self.conn.cursor()
        cur.execute('SELECT username, hostmask, flags FROM users')
        users = cur.fetchall()
        cur.close()
        return users

MODCLASSES = [usersClass]