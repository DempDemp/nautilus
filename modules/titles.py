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

import urllib
import urllib2
import re
from core import botutils
from urlparse import urlparse
from BeautifulSoup import BeautifulSoup

webre = [
    re.compile('((http(s)?://)?www\.(m)?ynet\.co\.il/articles/0,7340,L-\d+,00.html)'),
    re.compile('((http(s)?://)?www\.calcalist\.co\.il/\w+/\w+/0,7340,L-\d+,00.html)'),
    re.compile('((http(s)?://)?www\.amazon\.com(?:/dp/|/gp/product/)(?:[A-Z0-9]){10})'),
    re.compile('((http(s)?://)?rotter\.net\/forum\/scoops1\/(\d)+\.shtml)'),
    re.compile('((http(s)?://)?www\.nrg\.co\.il/online/\d+/\w+/\d+/\d+.html)'),
    re.compile('((http(s)?://)?www\.themarker\.com/\w+/\d\.\d+)'),
    re.compile('((http(s)?:\/\/)?[\w\-]+\.walla\.co\.il\/((\?w\=(\/|\%2F)\d+(\/|\%2F)\d+)|item\/\d+))'),
    re.compile('((http(s)?://)?www\.haaretz\.co(\.il|m)/(([\w-]+/)+(\.premium-)?)?\d\.\d+)'),
    re.compile('((http(s)?://)?www\.globes\.co\.il\/(news\/article\.aspx|serveen\/globes\/docview\.asp)\?did=\d+)'),
    re.compile('((http(s)?://)?[a-zA-Z\-]+\.nana10\.co\.il/Article/\?ArticleID\=\d+)'),
    re.compile('((http(s)?://)?(www\.)?the7eye\.org\.il/\d+)'),
    re.compile('((http(s)?://)?imgur\.com\/gallery\/\w+)'),
    re.compile('((http(s)?://)?(www\.)?bbc\.co(\.uk|m)\/news\/[\w\-]+)'),
    re.compile('((http(s)?://)?(www\.)?reuters\.co(\.uk|m)\/article\/[\w\-\/]+)'),
    re.compile('((http(s)?://)?(www\.)?twitter\.com\/[\w\-]+\/status\/\d+)')
]

titleregex = re.compile('<title(?:[a-zA-Z\= \'\"]*)>(.*)</title>', re.DOTALL | re.MULTILINE | re.IGNORECASE)
charsetregex = re.compile('charset=([\w\-]+)', re.DOTALL | re.MULTILINE | re.IGNORECASE)


class titleClass(botutils.baseClass):
    def purify(self, s):
        if isinstance(s, str) or isinstance(s, unicode):
            return unicode(BeautifulSoup(s.replace("\n", '').replace("\r", '').replace("\t", ''), convertEntities=BeautifulSoup.HTML_ENTITIES))
        else:
            return s

    def getTitle(self, url):
        if len(url) == 0:
            return {'error': 'error'}
        host = urlparse(url)
        host = host.netloc
        req = urllib2.Request(url)
        try:
            response = urllib2.urlopen(req)
        except urllib2.HTTPError, e:
            return {'error': 'error'}
        data = response.read()

        title = titleregex.search(data)
        if title is not None:
            title = title.group(1)
        else:
            return {'error': 'error'}
        charset = charsetregex.search(data)
        if charset is not None:
            charset = charset.group(1)
            if charset.lower() != 'utf-8':
                title = title.decode(charset)
        return {'url': url, 'title': self.purify(title)}

    def privmsg_format(self, result):
        if 'error' in result:
            msg = ''
        else:
            if len(result['title']) > 200:
                result['title'] = result['title'][0:197] + '...'
            msg = 'Title: ' + result['title'] + '.'
        return msg

    def onPRIVMSG(self, address, target, text):
        if 'http' in text:
            for tre in webre:
                titlesearch = tre.search(text)
                if titlesearch is not None:
                    link = titlesearch.group(1)
                    result = self.getTitle(link)
                    if not 'error' in result:
                        self.irc.msg(target, self.privmsg_format(result))
                    break

MODCLASSES = [titleClass]
