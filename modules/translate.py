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

import urllib, urllib2, re, sys
from core import botutils

try:
	import json
except ImportError:
	import simplejson as json

class translateClass(botutils.baseClass):
	def translate(self, src_lang, dest_lang, text):
		print 'a:', type(text)
		if len(text) < 1:
			return {'error': 'error'}
		params = {'client': 't',
			'text': text,
			'hl': 'en',
			'sl': src_lang,
			'tl': dest_lang,
			'multires': '1',
			'ssel': '0',
			'tsel': '0',
			'sc': '1'
		}
		headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/536.11 (KHTML, like Gecko) Chrome/20.0.1132.57 Safari/536.11'}
		req  = urllib2.Request('http://translate.google.com/translate_a/t?' + urllib.urlencode(params), '', headers)
		try:
			response = urllib2.urlopen(req)
		except urllib2.HTTPError, e:
			return {'error': 'error'}
		data = re.sub(',{1,}', ',', response.read())
		try:
			data = json.loads(unicode(data, 'latin-1'))
		except ValueError:
			return {'error': 'error'}
		return {'text': text, 'translation': data[0][0][0], 'src_lang': src_lang, 'dest_lang': dest_lang}

	def privmsg_format(self, result):
		if 'error' in result:
			msg = ['[translate] an error occurred']
		else:
			prefix = '[' + result['src_lang'] + '-' + result['dest_lang'] + '] '
			maxlength = 430 - len(prefix)
			tlist = []
			i = 0
			text = result['translation'].split(' ')
			while len(text) > 0:
				word = ' ' + text.pop(0)
				if i >= len(tlist):
					tlist.append('')
				if len(tlist[i] + word) > maxlength:
					tlist[i] = prefix + tlist[i]
					i+=1
					tlist.append(word)
				elif len(word) > maxlength:
					tlist[i] += word[0:len(tlist[i])-1]
					tlist[i] = prefix + tlist[i]
					text = [word[len(tlist[i]):]] + text
					i+=1
				else:
					tlist[i] += word
			tlist[i] = prefix + tlist[i]
			msg = tlist
		return msg
		
	def onPRIVMSG(self, address, target, text):
		first_word = text.strip().split(' ')[0]
		if botutils.prefix.match(first_word[0]) != None and (first_word[1:] == 'translate' or first_word[1:] == 'trans' or first_word[1:] == 'tr') and len(text.split(' ')) >= 3:
			trans = self.translate(text.split(' ')[1], text.split(' ')[2], ' '.join(text.split(' ')[3:]))
			output = self.privmsg_format(trans)
			self.irc.msg(target, output.encode('utf-8'))
				
MODCLASSES = [translateClass]