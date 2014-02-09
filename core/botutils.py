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