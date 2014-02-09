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

try:
	import json
except ImportError:
	import simplejson as json

class imdbClass(botutils.baseClass):
	def imdb(self, search):
		if len(search) < 1:
			return {'error': 'error'}
		params = {'t': search}
		req  = urllib2.Request('http://www.imdbapi.com/?' + urllib.urlencode(params))
		try:
			response = urllib2.urlopen(req)
		except urllib2.HTTPError:
			return {'error': 'error'}
		data = response.read()
		try:
			data = json.loads(data)
		except ValueError:
			return {'error': 'error'}
		return data

	def privmsg_format(self, result):
		if 'error' in result:
			msg = '[IMDB] an error occurred'
		elif 'Response' in result and result['Response'] == 'False':
			msg = '[IMDB] Nothing found'
		elif 'Response' in result and result['Response'] == 'True':
			msg = '[IMDB] Title: ' + result['Title'] + '. Genre: ' + result['Genre'] + '. Director: ' + result['Director'] + '. Rating: ' + result['imdbRating'] + '. Runtime: ' + result['Runtime'] + '. http://imdb.com/title/' + result['imdbID'] + '/'
		return msg.split('\n')[0].encode('utf-8')
		
	def onPRIVMSG(self, address, target, text):
		first_word = text.strip().split(' ')[0]
		if botutils.prefix.match(first_word[0]) != None and first_word[1:] == 'imdb' and len(text.split(' ')) >= 2:
			if len(' '.join(text.split(' ')[1:])) > 0:
				imdbdata = self.imdb(' '.join(text.split(' ')[1:]))
				self.irc.msg(target, self.privmsg_format(imdbdata))
				
MODCLASSES = [imdbClass]