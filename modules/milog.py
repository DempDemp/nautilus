import urllib
import urllib2
import requests
import HTMLParser
from bs4 import BeautifulSoup
from core.base import baseClass, command

class EmptyResult(Exception):
    pass

class Milog(baseClass):
    def get_definitions(self, term):
        r = requests.get('https://milog.co.il/{}'.format(urllib.quote(term)))
        soup = BeautifulSoup(r.content)
        definitions = []
        for entry in soup.findAll(class_='sr_e'):
            term, _, term_extra = entry.find(class_='sr_e_t').text.partition(' - ')
            for paragraph in entry.find_all(class_='sr_e_para'):
                definition_e = paragraph.find(class_='sr_e_txt')
                if not definition_e or definition_e.find_all('a'):
                    continue
                definition = {'definition': definition_e.text, 'term': term, 'term_extra': term_extra, 'trans': None}
                if paragraph.find(class_='sr_e_trans'):
                    definition['trans'] = paragraph.find(class_='sr_e_trans').text
                definitions.append(definition)
        if not definitions:
            raise EmptyResult
        return definitions

    @command(['mi', 'milog', 'he'], min_params=1)
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
            self.irc.msg(target, 'Milog: No results found')
        except urllib2.HTTPError:
            self.irc.msg(target, 'Milog: Unable to retrieve definition')
        if definition:
            max_len = 500
            message = u'[{num}/{max_num}] {bold}{term}{bold}'
            if definition['term_extra']:
                message += u' {italics}({term_extra}){italics}'
            if definition['trans']:
                message += u' {italics}{bold}{trans}{bold}{italics}'
            message += ': {definition}'
            message = message.format(bold=chr(2), italics=chr(29), num=num, max_num=len(definitions), **definition)
            self.irc.msg(target, message)
