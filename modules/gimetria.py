import random
import urllib
import urllib2
from bs4 import BeautifulSoup
from core.base import baseClass, command
from core.utils import split_address
from truerandom import truerandomClass

class Gimetria(baseClass):
    def get_random_term(self, text):
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

    @command(['gimetria', 'gi', 'ask'], min_params=1)
    def gimetria(self, target, address, params, **kwargs):
        nickname, username, hostname = split_address(address)
        q = ' '.join(params)
        try:
            definition = self.get_random_term(q)
        except (urllib2.HTTPError, AttributeError):
            self.irc.msg(target, 'gimetria: error retrieving list')
        else:
            self.irc.msg(target, u'{}: {}'.format(nickname, definition))
