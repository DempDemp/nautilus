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

import re
prefix = re.compile("^[\`\~\!\@\#\$\%\^\&\*\(\)\_\-\+\=\[\]\;\:\'\"\\\|\,\<\.\>\/\?]") # bot commands prefix

class baseClass:
    """ base class for modules """
    def __init__(self, irc):
        self.irc = irc
        pass

    def __del__(self):
        pass

    """ following functions handle triggers """
    def onPRIVMSG(self, address, target, text):
        pass

    def onNOTICE(self, address, target, text):
        pass

    def onJOIN(self, address, target):
        pass

    def onPART(self, address, target, text):
        pass

    def onQUIT(self, address, text):
        pass

    def onNICK(self, address, newnick):
        pass

    def onINVITE(self, address, nickname, channel):
        pass

    def onSIGNEDON(self):
        pass

    def onRAW(self, line):
        pass


class utilsClass(baseClass):

    def onPRIVMSG(self, address, target, text):
        if target == self.irc.nickname:
            if text.startswith('rehash'):
                flags = self.irc.users.getFlags(hostmask=address)
                if flags is None or 'n' not in flags[1]:
                    self.irc.notice(address.split('!')[0], 'Insufficient privileges')
                    self.irc.logger.warning('Unauthorised rehash attempt from %s', address)
                    return
                self.irc.factory.setFromJSON()
                self.irc.factory.reload_modules()
                self.irc.notice(address.split('!')[0], 'Done')
            elif text.startswith('sendline'):
                flags = self.irc.users.getFlags(hostmask=address)
                if flags is None or 'n' not in flags[1]:
                    self.irc.notice(address.split('!')[0], 'Insufficient privileges')
                    self.irc.logger.warning('Unauthorised sendline attempt from %s', address)
                    return
                self.irc.sendLine(' '.join(text.split(' ')[1:]))

MODCLASSES = [utilsClass]