import urllib
import urllib2
import HTMLParser
from bs4 import BeautifulSoup
from core.base import baseClass, command
from core.utils import paragraphy_string

h = HTMLParser.HTMLParser()

class EmptyResult(Exception):
    pass

class UrbanDictionary(baseClass):
    def get_definitions(self, term):
        soup = BeautifulSoup(urllib2.urlopen('https://www.urbandictionary.com/define.php?term=' + urllib.quote_plus(term)))
        definitions = []
        for definition in soup.findAll('div', {'data-defid': True}, class_='def-panel'):
            word = ' '.join(h.unescape(definition.find(class_='word').text).splitlines())
            meaning = ' '.join(h.unescape(definition.find(class_='meaning').text.strip()).splitlines())
            example = ' '.join(h.unescape(definition.find(class_='example').text.strip()).splitlines())
            definitions.append({'word': word, 'meaning': meaning, 'example': example})
        if not definitions:
            raise EmptyResult
        return definitions

    @command(['ud', 'urbandictionary'], min_params=1)
    def get_definition(self, target, params, **kwargs):
        if len(params) >= 2 and params[0].isdigit():
            num = int(params.pop(0))
        else:
            num = 1
        term = ' '.join(params)
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
