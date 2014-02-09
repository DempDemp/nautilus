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

import urllib, urllib2, time
from core import botutils
from BeautifulSoup import BeautifulSoup

class tvrageClass(botutils.baseClass):
	def purify(self, s):
		if type(s) == 'str' or type(s) == 'unicode':
			return str(BeautifulSoup(s.replace('\n', '').replace('\r', ''), convertEntities=BeautifulSoup.HTML_ENTITIES))
		else:
			return s

	def get_show_id(self, name, num = 1):
		if num < 1 or len(name) == 0:
			return False
		num = num -1
		req  = urllib2.Request('http://services.tvrage.com/feeds/search.php?show=' + urllib.quote_plus(name))
		try:
			response = urllib2.urlopen(req)
		except urllib2.HTTPError:
			return False
		data = response.read()
		soup = BeautifulSoup(data)
		shows = soup.findAll('show')
		if shows != None and len(shows) > num:
			showid = shows[num].find('showid').findAll(text=True)
			for idx, text in enumerate(showid):
				showid[idx] = text.strip()
			showid = ' '.join(' '.join(showid).split())
		else:
			showid = False
		return self.purify(showid)
		
	def get_show_episodes(self, showid):
		req  = urllib2.Request('http://services.tvrage.com/feeds/episode_list.php?sid=' + urllib.quote_plus(showid))
		try:
			response = urllib2.urlopen(req)
		except urllib2.HTTPError:
			return False
		data = response.read()
		soup = BeautifulSoup(data)
		episodes = soup.findAll('episode')
		lastep = False
		nextep = False
		
		if episodes != None and len(episodes) > 0:
			today = time.mktime(time.strptime(time.strftime('%Y-%m-%d'), '%Y-%m-%d'))
			found = False
			for idx, episode in enumerate(episodes):
				airdate = ''.join(episode.find('airdate').findAll(text=True))
				try:
					airdatetime = time.strptime(airdate, '%Y-%m-%d')
				except ValueError:
					airdatetime = time.strptime('1990-01-01', '%Y-%m-%d')
				if today <= time.mktime(airdatetime): # didn't air yet
					found = True
					epnum = ''.join(episode.find('seasonnum').findAll(text=True))
					season = episode.parent['no']
					title = ''.join(episode.find('title').findAll(text=True))
					nextep = {'epnum': self.purify(epnum), 'season': self.purify(season), 'airdate': self.purify(airdate), 'title': self.purify(title)}
					if idx >= 1:
						epnum = ''.join(episodes[idx-1].find('seasonnum').findAll(text=True))
						season = episodes[idx-1].parent['no']
						title = ''.join(episodes[idx-1].find('title').findAll(text=True))
						airdate = ''.join(episodes[idx-1].find('airdate').findAll(text=True))
						lastep = {'epnum': self.purify(epnum), 'season': self.purify(season), 'airdate': self.purify(airdate), 'title': self.purify(title)}
					break
			if not found:
				epnum = ''.join(episodes[idx].find('seasonnum').findAll(text=True))
				season = episodes[idx].parent['no']
				title = ''.join(episodes[idx].find('title').findAll(text=True))
				airdate = ''.join(episodes[idx].find('airdate').findAll(text=True))
				lastep = {'epnum': self.purify(epnum), 'season': self.purify(season), 'airdate': self.purify(airdate), 'title': self.purify(title)}
		name = ''.join(soup.find('name').findAll(text=True))
		return {'show': self.purify(name), 'lastep': lastep, 'nextep': nextep}

	def privmsg_format(self, info):
		if not info or not info['show'] or len(info['show']) == 0:
			msg = '[TVRage] Couldn\'t find episode information for that show'
		else:
			if not info['lastep']:
				lastep = 'No details'
			else:
				lastep = chr(2) + info['lastep']['season'] + 'x' + info['lastep']['epnum'] + ' - ' + info['lastep']['title'] + chr(2) + ' aired on ' + info['lastep']['airdate']
			if not info['nextep']:
				nextep = 'Not scheduled'
			else:
				nextep = chr(2) + info['nextep']['season'] + 'x' + info['nextep']['epnum'] + ' - ' + info['nextep']['title'] + chr(2) + ' will air on ' + info['nextep']['airdate']
			msg = '[TVRage] ' + chr(2) + info['show'] + chr(2) + ' - Last episode: ' + lastep + '. Next episode: ' + nextep + '.'
		return msg
	
	def onPRIVMSG(self, address, target, text):
		first_word = text.strip().split(' ')[0]
		if botutils.prefix.match(first_word[0]) != None and (first_word[1:] == 'tvrage' or first_word[1:] == 'epinfo') and len(text.split(' ')) >= 2:
			showid = self.get_show_id(' '.join(text.split(' ')[1:]))
			showinfo = False
			if showid:
				showinfo = self.get_show_episodes(showid)
			self.irc.msg(target, self.privmsg_format(showinfo))
				
MODCLASSES = [tvrageClass]