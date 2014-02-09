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
from local_settings import tinysongapikey

try:
	import json
except ImportError:
	import simplejson as json

class tinysongClass(botutils.baseClass):
	def shorten(self, s, l = 60):
		if len(s) > l:
			s = s[0:l-3] + '...'
		return s

	def findsong(self, search, num = 1):
		if len(search) < 1 or num < 1:
			return {'error': 'error'}
		apikey = tinysongapikey
		req = urllib2.Request('http://tinysong.com/s/' + urllib.quote_plus(search) + '?format=json&key=' + apikey + '&limit=32')
		try:
			response = urllib2.urlopen(req)
		except urllib2.HTTPError:
			pass
		data = response.read()
		try:
			data = json.loads(data)
		except ValueError:
			return {'error': 'error'}
		return {'songs': data, 'num': num}

	def privmsg_format(self, result):
		if 'error' in result:
			msg = ''
		elif 'songs' in result:
			if len(result['songs']) == 0:
				msg = '[Tinysong] Nothing found'
			else:
				if result['num'] > len(result['songs']):
					result['num'] = len(result['songs'])
				result['num'] -= 1
				msg = '[' + str(result['num'] +1) + '/' + str(len(result['songs'])) + '] ' + self.shorten(result['songs'][result['num']]['ArtistName']) + ' - ' + self.shorten(result['songs'][result['num']]['SongName']) + ' [' + self.shorten(result['songs'][result['num']]['AlbumName']) + '] ' + self.shorten(result['songs'][result['num']]['Url'])
		return msg.split('\n')[0].encode('utf-8')

	def onPRIVMSG(self, address, target, text):
		first_word = text.strip().split(' ')[0]
		if botutils.prefix.match(first_word[0]) != None and (first_word[1:] == 'song' or first_word[1:] == 'findsong' or first_word[1:] == 'tinysong') and len(text.split(' ')) >= 2:
			if text.split(' ')[1].isdigit():
				num = text.split(' ')[1]
				search = ' '.join(text.split(' ')[2:])
			else:
				num = 1
				search = ' '.join(text.split(' ')[1:])
			songres = self.findsong(search, int(num))
			self.irc.msg(target, self.privmsg_format(songres))

MODCLASSES = [tinysongClass]