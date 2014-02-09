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

import urllib, urllib2
from core import botutils

class truerandomClass(botutils.baseClass):
	def isReal(self, txt):
		try:
			int(txt)
			return True
		except ValueError:
			return False
	
	def truerandom(self, low, high, base = 10, num = 1):
		if low < -1000000000 or high > 1000000000 or high <= low or (base != 2 and base != 8 and base != 10 and base != 16) or num < 1 or num > 10000:
			return {'error': 'error'}
		params = {
			'num': num,
			'min': low,
			'max': high,
			'col': 1,
			'base': base,
			'format': 'plain',
			'rnd': 'new'
		}
		req  = urllib2.Request('http://www.random.org/integers/?' + urllib.urlencode(params))
		try:
			response = urllib2.urlopen(req)
		except:
			return {'error': 'error'}
		data = response.read()
		return {'result': ' '.join(data.split('\n'))}

	def privmsg_format(self, result):
		if 'error' in result:
			msg = ['[Random] an error occurred']
		elif 'result' in result:
			result['result'] = result['result'].split('\n')[0]
			prefix = '[Random] '
			maxlength = 430 - len(prefix)
			if (len(result['result']) > maxlength):
				result['result'] = result['result'][0:maxlength-1]
			msg = '[Random] ' + result['result']
		return msg.strip()
		
	def onPRIVMSG(self, address, target, text):
		first_word = text.strip().split(' ')[0]
		if botutils.prefix.match(first_word[0]) != None and (first_word[1:] == 'random' or first_word[1:] == 'rand' or first_word[1:] == 'rnd') and len(text.split(' ')) >= 2:
			length = len(text.split(' '))
			rnd_low=0
			rnd_high=100000
			rnd_base=10
			rnd_num=1
			if length >=2 and self.isReal(text.split(' ')[1]):
				rnd_low = 0
				rnd_high = int(text.split(' ')[1])
			if length >= 3 and self.isReal(text.split(' ')[1]) and self.isReal(text.split(' ')[2]):
				rnd_low = int(text.split(' ')[1])
				rnd_high = int(text.split(' ')[2])
			if length >= 4 and self.isReal(text.split(' ')[3]):
				rnd_base = int(text.split(' ')[3])
			if length == 5 and self.isReal(text.split(' ')[4]) and int(text.split(' ')[4]) <= 20:
				rnd_num = int(text.split(' ')[4])
			self.irc.msg(target, self.privmsg_format(self.truerandom(rnd_low, rnd_high, rnd_base, rnd_num)))
			
MODCLASSES = [truerandomClass]