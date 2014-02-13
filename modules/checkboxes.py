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
from core import botutils
from truerandom import truerandomClass
from random import randint
checkboxes = re.compile('^(\[ \] .+ )+(\[ \] .+)')

class checkboxesClass(botutils.baseClass):
	def isReal(self, txt):
		try:
			int(txt)
			return True
		except ValueError:
			return False

	def onPRIVMSG(self, address, target, text):
		if checkboxes.match(text) != None:
			chkbox_rand = truerandomClass.truerandom(1, len(text[3:].split('[ ]')), 10, 1)
			if 'error' in chkbox_rand or self.isReal(chkbox_rand['result']) == False:
				chkbox_rand = randint(1, len(text[3:].split('[ ]')))
			else:
				chkbox_rand = int(chkbox_rand['result'])
			self.irc.msg(target, text.replace('[ ]', '[+]', chkbox_rand).replace('[+]', '[ ]', chkbox_rand-1))

MODCLASSES = [checkboxesClass]