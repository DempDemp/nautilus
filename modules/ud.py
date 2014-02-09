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

import urllib, re, urllib2
from core import botutils
from BeautifulSoup import BeautifulSoup

class udClass(botutils.baseClass):
	def urbandictionary(self, term, defnum=1):
		if defnum < 1 or len(term) < 1:
			return {'error': 'error'}
		defnum -= 1
		page = defnum/7+1
		params = {'term': term}
		if page > 1:
			params = dict(params.items() + {'page': page}.items())
		req  = urllib2.Request('http://www.urbandictionary.com/define.php?' + urllib.urlencode(params))
		try:
			response = urllib2.urlopen(req)
		except urllib2.HTTPError:
			return {'error': 'error'}
		data = response.read()
		soup = BeautifulSoup(data)
		defidx = defnum%7
		defregex = re.compile('entry*')
		definitions = soup.findAll('td', {'class': 'text', 'id': defregex})
		if definitions != None and len(definitions) > defidx:
			definition = definitions[defidx].find('div', {'class': 'definition'}).findAll(text=True)
			example = definitions[defidx].find('div', {'class': 'example'}).findAll(text=True)
			if len(example) > 0:
				example[0] = '(' + example[0]
				example[-1] = example[-1] + ')'
				definition += example
			for idx, def_text in enumerate(definition):
				definition[idx] = def_text.strip()
			definition = ' '.join(' '.join(definition).split())
			pages = soup.find('div', {'class': 'pagination'})
			if pages != None:
				pages = pages.findAll('a')[-2].find(text=True)
				params = dict(params.items() + {'page': pages}.items())
				req  = urllib2.Request('http://www.urbandictionary.com/define.php?' + urllib.urlencode(params))
				try:
					response = urllib2.urlopen(req)
				except urllib2.HTTPError:
					return {'error': 'error'}
				data = response.read()
				soup = BeautifulSoup(data)
				numdefs = ((int(pages)*7)-7) + len(soup.findAll('td', {'class': 'text'}))        
			else:
				numdefs = len(definitions)+7*(page-1)
		else:
			definition = 'Nothing found'
			numdefs = 0
		definition = str(BeautifulSoup(definition.replace('\n', '').replace('\r', ''), convertEntities=BeautifulSoup.HTML_ENTITIES))
		return {'term': term, 'defnum': defnum+1, 'numdefs': numdefs, 'definition': definition}

	def privmsg_format(self, result):
		if 'error' in result:
			msg = ['[ud] an error occurred']
		else:
			ud_prefix = '[' + str(result['defnum']) + '/' + str(result['numdefs']) + ']'
			ud_maxlength = 430 - len(ud_prefix)
			ud_list = []
			i = 0
			ud_def = result['definition'].split(' ')
			while len(ud_def) > 0:
				ud_word = ' ' + ud_def.pop(0)
				if i >= len(ud_list):
					ud_list.append('')
				if len(ud_list[i] + ud_word) > ud_maxlength:
					ud_list[i] = ud_prefix + ud_list[i]
					i+=1
					ud_list.append(ud_word)
				elif len(ud_word) > ud_maxlength:
					ud_list[i] += ud_word[0:len(ud_list[i])-1]
					ud_list[i] = ud_prefix + ud_list[i]
					ud_def = [ud_word[len(ud_list[i]):]] + ud_def
					i+=1
				else:
					ud_list[i] += ud_word
			ud_list[i] = ud_prefix + ud_list[i]
			msg = ud_list
		return msg
	
	def onPRIVMSG(self, address, target, text):
		first_word = text.strip().split(' ')[0]
		if botutils.prefix.match(first_word[0]) != None and first_word[1:] == 'ud' and len(text.split(' ')) >= 2:
			if text.split(' ')[1].isdigit():
				num = text.split(' ')[1]
				term = ' '.join(text.split(' ')[2:])
			else:
				num = 1
				term = ' '.join(text.split(' ')[1:])
			udterm = self.urbandictionary(term, int(num))
			res = self.privmsg_format(udterm)
			for x in res:
				self.irc.msg(target, res)

MODCLASSES = [udClass]