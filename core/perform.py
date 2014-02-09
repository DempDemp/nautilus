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

class performClass(botutils.baseClass):
    def __init__(self, irc):
        botutils.baseClass.__init__(self, irc)
        self.conn = sqlite3.connect(self.irc.users.dbfile, check_same_thread=False)
        self.createTables()

    def createTables(self):
        cur = self.conn.cursor()
        cur.execute('''CREATE TABLE IF NOT EXISTS perform (id INTEGER PRIMARY KEY AUTOINCREMENT,
                botid TEXT NOT NULL,
                pline TEXT NOT NULL)''')
        self.conn.commit()
        cur.close()

    def getLines(self):
        cur = self.conn.cursor()
        cur.execute('SELECT id, pline FROM perform WHERE botid=?', (self.irc.id,))
        res = cur.fetchall()
        cur.close()
        return res

    def addPerform(self, line):
        cur = self.conn.cursor()
        cur.execute('INSERT INTO perform (botid, pline) VALUES (?, ?)', (self.irc.id, line))
        self.conn.commit()
        cur.close()
        return True

    def delPerform(self, pid):
        cur = self.conn.cursor()
        cur.execute('DELETE FROM perform WHERE botid=? AND id=?', (self.irc.id, pid))
        affected = cur.rowcount
        self.conn.commit()
        cur.close()
        if affected:
            return True
        return False

    def onSIGNEDON(self):
        lines = self.getLines()
        for l in lines:
            self.irc.sendLine(l[1])

    def onPRIVMSG(self, address, target, text):
        if target == self.irc.nickname:
            if text.startswith('perform'):
                params = text.split(' ')
                if params[0] != 'perform':
                    return
                flags = self.irc.users.getFlags(hostmask=address)
                if flags is None or 'n' not in flags[1]:
                    self.irc.notice(address.split('!')[0], 'Insufficient privileges')
                    return
                if len(params) == 1:
                    self.irc.notice(address.split('!')[0], 'Available commands: list add delete')
                    return
                if params[1] == 'list':
                    lines = self.getLines()
                    self.irc.notice(address.split('!')[0], 'id line')
                    for l in lines:
                        self.irc.notice(address.split('!')[0], '%s %s' % l)
                    return
                elif params[1] == 'add':
                    if len(params) < 3:
                        self.irc.notice(address.split('!')[0], 'Usage: perform add <line>')
                        return
                    else:
                        self.addPerform(' '.join(params[2:]))
                        self.irc.notice(address.split('!')[0], 'Done')
                    return
                elif params[1] == 'delete':
                    if len(params) < 3:
                        self.irc.notice(address.split('!')[0], 'Usage: perform delete <id>')
                        return
                    else:
                        if self.delPerform(params[2]):
                            self.irc.notice(address.split('!')[0], 'Done')
                        else:
                            self.irc.notice(address.split('!')[0], 'Unable to delete line')
                    return

MODCLASSES = [performClass]
