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

class dfeojmClass(botutils.baseClass):
	def downforeveryoneorjustme(self, site):
		site = site.strip()
		if len(site) == 0:
			return {"error": "error"}
		req  = urllib2.Request('http://www.downforeveryoneorjustme.com/' + urllib.quote_plus(site))
		try:
			response = urllib2.urlopen(req)
		except urllib2.HTTPError:
			return {'error': 'error'}
		data = response.read()
		soup = BeautifulSoup(data)
		isup = soup.find("div", {"id": "container"}).findAll(text=True)
		up = True
		if isup[0].strip() == "It's not just you!":
			up = False
		elif isup[0].strip().split(" ")[0] == "Huh?":
			return {"error": "error"}
		return {'site': site, 'up': up}

	def privmsg_format(self, result):
		if "error" in result:
			print "Error occured - downforeveryoneorjustme"
			msg = ""
		else:
			if len(result['site']) > 40:
				result['site'] = result['site'][0:37] + '...'
			if result['up']:
				msg = 'It\'s just you. ' + result['site'] + ' is up.'
			else:
				msg = 'It\'s not just you! ' + result['site'] + ' looks down from here.'
		return msg
	
	def onPRIVMSG(self, address, target, text):
		first_word = text.strip().split(' ')[0]
		if botutils.prefix.match(first_word[0]) != None and (first_word[1:] == "downforeveryoneorjustme" or first_word[1:] == "down" or first_word[1:] == "isdown" or first_word[1:] == "isup") and len(text.split(" ")) >= 2:
			down = self.downforeveryoneorjustme(" ".join(text.split(" ")[1:]))
			self.irc.msg(target, self.privmsg_format(down))
		
MODCLASSES = [dfeojmClass]