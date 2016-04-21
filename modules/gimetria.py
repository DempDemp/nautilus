import random
import urllib
import urllib2
from core import base
from truerandom import truerandomClass
from BeautifulSoup import BeautifulSoup

class Gimetria(base.baseClass):
    def isReal(self, txt):
        try:
            int(txt)
            return True
        except ValueError:
            return False

    def gimetria(self, text, defnum=1):
        defnum -= 1
        soup = BeautifulSoup(urllib2.urlopen('http://www.c2kb.com/gematria/?x=0&y=0&showcurse=on&word=' + urllib.quote_plus(text)))
        definitions = soup.find('table', {'class': 'gematria-table'}).find('tbody').findAll('td', colspan=None)
        if definitions is not None and (len(definitions) / 7) > defnum:
            if defnum < 0:
                rand = truerandomClass.truerandom(0, len(definitions) / 7, 10, 1)
                if 'error' in rand or not rand['result'].is_digit():
                    defnum = random.randint(0, len(definitions)/7)*7+1
                else:
                    defnum = int(rand['result']) * 7 + 1
            definition = definitions[defnum].find('a').findAll(text=True)
            for idx, def_text in enumerate(definition):
                definition[idx] = def_text.strip()
            definition = ' '.join(' '.join(definition).split())
            numdefs = len(definitions) / 7
        else:
            definition = 'Nothing found'
            numdefs = 0
        definition = str(BeautifulSoup(definition.replace('\n', '').replace('\r', ''), convertEntities=BeautifulSoup.HTML_ENTITIES))
        return {'word': text, 'defnum': defnum + 1, 'numdefs': numdefs, 'definition': definition}

    def on_privmsg(self, address, target, text):
        if text[0] in base.prefix and text.strip().split(' ', 1)[0][1:] in ('gimetria', 'gi', 'ask') and len(text.split()) >= 2:
            nickname = address.split('!', 1)[0]
            num = -1
            q = ' '.join(text.split()[1:])
            try:
                result = self.gimetria(q, int(num))
            except (urllib2.HTTPError, AttributeError):
                self.irc.msg(target, 'gimetria: error retrieving list')
            else:
                self.irc.msg(target, u'{}: {}'.format(nickname, result['definition'].decode('utf8')))
