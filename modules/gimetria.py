import random
import urllib
import urllib2
from bs4 import BeautifulSoup
from core import base
from truerandom import truerandomClass

class Gimetria(base.baseClass):
    def gimetria(self, text):
        soup = BeautifulSoup(urllib2.urlopen('http://www.c2kb.com/gematria/?showcurse=on&word=' + urllib.quote_plus(text)))
        definitions = []
        for row in soup.find('table', class_='gematria-table').find('tbody').findChildren('tr'):
            tds = row.findAll('td')
            if len(tds) == 7:
                definitions.append(row.findAll('td')[1].text)
        if definitions:
            rand = truerandomClass.truerandom(0, len(definitions), 10, 1)
            if 'error' in rand or not rand['result'].is_digit():
                num = random.randint(0, len(definitions))
            else:
                num = int(rand['result'])
        return definitions[num]

    def on_privmsg(self, address, target, text):
        if text[0] in base.prefix and text.strip().split(' ', 1)[0][1:] in ('gimetria', 'gi', 'ask') and len(text.split()) >= 2:
            nickname = address.split('!', 1)[0]
            q = ' '.join(text.split()[1:])
            try:
                definition = self.gimetria(q)
            except (urllib2.HTTPError, AttributeError):
                self.irc.msg(target, 'gimetria: error retrieving list')
            else:
                self.irc.msg(target, u'{}: {}'.format(nickname, definition))
