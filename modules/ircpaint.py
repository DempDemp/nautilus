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

import urllib2
from core import botutils

class ircpaintClass(botutils.baseClass):

    @staticmethod
    def getDrawing(sid):
        req = urllib2.Request('http://ircpaint.randomlab.info/rawirc.php?q=%s' % sid)
        try:
            response = urllib2.urlopen(req)
        except urllib2.HTTPError as e:
            raise e
        return response.read()

    def onPRIVMSG(self, address, target, text):
        if target == self.irc.nickname and text.startswith('ircpaint'):
            params = text.split(' ')
            if params[0] != 'ircpaint':
                return
            flags = self.irc.users.getFlags(hostmask=address)
            if flags is None or 'n' not in flags[1]:
                self.irc.notice(address.split('!')[0], 'Insufficient privileges')
                return
            if len(params) < 3:
                self.irc.notice(address.split('!')[0], 'Usage: ircpaint <target> <id>')
            else:
                try:
                    drawing = self.getDrawing(params[2])
                except urllib2.HTTPError as e:
                    self.irc.notice(address.split('!')[0], 'Unable to get drawing: %s' % e.message)
                    return
                drawing = drawing.split()
                for line in drawing:
                    self.irc.msg(params[1], line.strip())
                

MODCLASSES = [ircpaintClass]
