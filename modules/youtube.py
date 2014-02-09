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

import re, urllib, urllib2
from core import botutils
from BeautifulSoup import BeautifulSoup

youtubere = re.compile("youtu(?:\.be|be\.com)/(?:.*v(?:/|=)|(?:.*/)?)([a-zA-Z0-9-_]+)")

class youtubeClass(botutils.baseClass):
	def purify(self, s):
		if type(s) == "str" or type(s) == "unicode":
			return str(BeautifulSoup(s.replace('\n', '').replace('\r', ''), convertEntities=BeautifulSoup.HTML_ENTITIES))
		else:
			return s

	def intWithCommas(self, x):
		if type(x) not in [type(0), type(0L)]:
			raise TypeError("Parameter must be an integer.")
		if x < 0:
			return '-' + self.intWithCommas(-x)
		result = ''
		while x >= 1000:
			x, r = divmod(x, 1000)
			result = ",%03d%s" % (r, result)
		return "%d%s" % (x, result)

	def get_info(self, video):
		if len(video) < 1:
			return {"error": "error"}
		req  = urllib2.Request('http://gdata.youtube.com/feeds/api/videos/' + urllib.quote_plus(video))
		try:
			response = urllib2.urlopen(req)
		except urllib2.HTTPError:
			return {'error': 'error'}
		data = response.read()
		if data == "Invalid id":
			return {"error": "error"}
		soup = BeautifulSoup(data)
		title = self.purify(soup.find("title").find(text=True))
		views = self.purify(soup.find("yt:statistics")['viewcount'])
		try:
			views = self.intWithCommas(int(views))
		except ValueError:
			views = "-"
		return {"video": video, "title": title, "views": views}

	def privmsg_format(self, result):
		if "error" in result:
			msg = "[YouTube] an error occurred"
		else:
			msg = "[YouTube] Title: " + chr(2) + result['title'] + chr(2) + ". Views: " + chr(2) + result['views'] + chr(2)
		return msg.split("\n")[0].encode('utf-8')
	
	def onPRIVMSG(self, address, target, text):
		if 'youtu' in text:
			youtubesearch = youtubere.search(text)
			if youtubesearch != None:
				youtubeid = youtubesearch.group(1)
				result = self.get_info(youtubeid)
				if not "error" in result:
					self.irc.msg(target, self.privmsg_format(result))
				
MODCLASSES = [youtubeClass]