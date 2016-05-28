import urllib
import urllib2
from bs4 import BeautifulSoup
from core import base
from core.utils import paragraphy_string

class EmptyResult(Exception):
    pass

class UrbanDictionary(base.baseClass):
    def get_definitions(self, term):
        soup = BeautifulSoup(urllib2.urlopen('https://www.urbandictionary.com/define.php?term=' + urllib.quote_plus(term)))
        definitions = []
        for definition in soup.findAll('div', {'data-defid': True}, class_='def-panel'):
            word = definition.find(class_='word').text
            meaning = definition.find(class_='meaning').text.strip()
            example = definition.find(class_='example').text.strip()
            definitions.append({'word': word, 'meaning': meaning, 'example': example})
        if not definitions:
            raise EmptyResult
        return definitions

    def on_privmsg(self, address, target, text):
        if text[0] in base.prefix and text.strip().split(' ', 1)[0][1:] in ('ud', 'urbandictionary') and len(text.split()) >= 2:
            term = text.split()[1:]
            if len(term) >= 2 and term[0].isdigit():
                num = int(term.pop(0))
            else:
                num = 1
            term = ' '.join(term)
            definition = None
            try:
                definitions = self.get_definitions(term)
                definition = definitions[num - 1]
            except IndexError:
                definition = definitions[-1]
                num = len(definitions)
            except EmptyResult:
                self.irc.msg(target, 'UrbanDictionary: No results found')
            except urllib2.HTTPError:
                self.irc.msg(target, 'UrbanDictionary: Unable to retrieve definition')
            if definition:
                max_len = 500
                meaning = paragraphy_string(definition['meaning'])
                example = paragraphy_string(definition['example'])
                message = u'[{num}/{max_num}] {italics}{bold}{word}{bold}{italics}: '.format(bold=chr(2), italics=chr(29), num=num, max_num=len(definitions), word=definition['word'])
                max_len -= len(message)
                message += meaning[:max_len - 3] + u'...' if len(meaning) > max_len else meaning
                max_len -= len(message)
                if max_len > 15:
                    example_text = example[:max_len - 3] + u'...' if len(example) > max_len else example
                    message += u' {italics}{example}{italics}'.format(italics=chr(29), example=example_text)
                self.irc.msg(target, message)
