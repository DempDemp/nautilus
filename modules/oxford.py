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
from BeautifulSoup import BeautifulSoup

class oxfordClass(botutils.baseClass):
	def oxforddictionary(self, word, defnum=1):
		if defnum < 1 or len(word) == 0:
			return {'error': 'error'}
		defnum -= 1
		req  = urllib2.Request('http://oxforddictionaries.com/definition/english/' + urllib.quote_plus(word))
		try:
			response = urllib2.urlopen(req)
		except urllib2.HTTPError, e:
			return {'error': 'error'}
		data = response.read()
		soup = BeautifulSoup(data)
		definitions = soup.findAll('ul', {'class': 'sense-entry'})
		if definitions != None and len(definitions) > defnum:
			definition = definitions[defnum].find('span', {'class': 'definition'}).findAll(text=True)
			example = definitions[defnum].find('em', {'class': 'example'})
			if example != None and len(example) > 0:
				example = example.findAll(text=True)
				example[0] = '(' + example[0].strip()
				example[-1] = example[-1] + ')'
				definition += example
			for idx, def_text in enumerate(definition):
				definition[idx] = def_text.strip()
			definition = ' '.join(' '.join(definition).split())
			numdefs = len(definitions)
		else:
			definition = 'Nothing found'
			numdefs = 0
		definition = str(BeautifulSoup(definition.replace('\n', '').replace('\r', ''), convertEntities=BeautifulSoup.HTML_ENTITIES))
		return {'word': word, 'defnum': defnum+1, 'numdefs': numdefs, 'definition': definition}

	def privmsg_format(self, result):
		if 'error' in result:
			msg = ['[oxford] an error occurred']
		else:
			ox_prefix = '[' + str(result['defnum']) + '/' + str(result['numdefs']) + ']'
			ox_maxlength = 430 - len(ox_prefix)
			ox_list = []
			i = 0
			ox_def = result['definition'].split(' ')
			while len(ox_def) > 0:
				ox_word = ' ' + ox_def.pop(0)
				if i >= len(ox_list):
					ox_list.append('')
				if len(ox_list[i] + ox_word) > ox_maxlength:
					ox_list[i] = ox_prefix + ox_list[i]
					i+=1
					ox_list.append(ox_word)
				elif len(ox_word) > ox_maxlength:
					ox_list[i] += ox_word[0:len(ox_list[i])-1]
					ox_list[i] = ox_prefix + ox_list[i]
					ox_def = [ox_word[len(ox_list[i]):]] + ox_def
					i+=1
				else:
					ox_list[i] += ox_word
			ox_list[i] = ox_prefix + ox_list[i]
			msg = ox_list
		return msg
		
	def onPRIVMSG(self, address, target, text):
		first_word = text.strip().split(' ')[0]
		if botutils.prefix.match(first_word[0]) != None and (first_word[1:] == 'oxford' or first_word[1:] == 'ox' or first_word[1:] == 'oxf') and len(text.split(' ')) >= 2:
			if text.split(' ')[1].isdigit():
				num = text.split(' ')[1]
				word = ' '.join(text.split(' ')[2:])
			else:
				num = 1
				word = ' '.join(text.split(' ')[1:])
			oxterm = self.oxforddictionary(word, int(num))
			res = self.privmsg_format(oxterm)
			for x in res:
				self.irc.msg(target, x)
				
MODCLASSES = [oxfordClass]