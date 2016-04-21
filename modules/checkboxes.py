import re
from core import base
from truerandom import truerandomClass
from random import randint

checkboxes = re.compile('^(\[ \] .+ )+(\[ \] .+)')

class checkboxesClass(base.baseClass):
	def isReal(self, txt):
		try:
			int(txt)
			return True
		except ValueError:
			return False

	def on_privmsg(self, address, target, text):
		if checkboxes.match(text) != None:
			chkbox_rand = truerandomClass.truerandom(1, len(text[3:].split('[ ]')), 10, 1)
			if 'error' in chkbox_rand or self.isReal(chkbox_rand['result']) == False:
				chkbox_rand = randint(1, len(text[3:].split('[ ]')))
			else:
				chkbox_rand = int(chkbox_rand['result'])
			self.irc.msg(target, text.replace('[ ]', '[+]', chkbox_rand).replace('[+]', '[ ]', chkbox_rand-1))
