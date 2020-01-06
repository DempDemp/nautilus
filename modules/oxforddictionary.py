import urllib
import urllib2
import requests
from core.base import baseClass, command
from core.conf import settings
from core.utils import split_address

class EmptyResult(Exception):
    pass

class OxfordDictionary(baseClass):
    def get_definitions(self, text):
        r = requests.get('https://od-api.oxforddictionaries.com/api/v2/entries/en-gb/{}'.format(urllib.quote_plus('_'.join(text.split()))), headers={'app_id': settings.OXFORD_APP_ID, 'app_key': settings.OXFORD_APP_KEY})
        if r.status_code == 404:
            raise EmptyResult
        return r.json()['results']

    @command(['oxford', 'ox', 'def'], min_params=1)
    def define_word(self, target, address, params, **kwargs):
        nickname, username, hostname = split_address(address)
        if len(params) >= 2 and params[0].isdigit():
            num = int(params.pop(0))
        else:
            num = 1
        word = ' '.join(params)
        try:
            results = self.get_definitions(word)
        except (urllib2.HTTPError, AttributeError):
            self.irc.msg(target, 'OxfordDictionary: Error retrieving list')
        except EmptyResult:
            self.irc.msg(target, 'OxfordDictionary: No results found')
        else:
            i = 0
            message = ''
            for result in results:
                for lexentry in result['lexicalEntries']:
                    for entry in lexentry['entries']:
                        senses = []
                        for sense in entry['senses']:
                            senses.append(sense)
                            if sense.get('subsenses'):
                                senses += sense.get('subsenses')
                        for sense in senses:
                            definitions = sense.get('definitions', sense.get('shortDefinitions'))
                            if definitions:
                                i += 1
                                if i == num:
                                    message = u'[{num}/{max_num}] {bold}' + '{}'.format(lexentry.get('text')) + '{bold}'
                                    if lexentry.get('lexicalCategory'):
                                        message += u' ({})'.format(lexentry['lexicalCategory']['text'])
                                    message += u': '
                                    if sense.get('registers'):
                                        message += u'{italics}' + '{}'.format(sense['registers'][0]['text']) + '{italics} '
                                    if sense.get('domains'):
                                        message += u'{italics}' + '{}'.format(sense['domains'][0]['text']) + '{italics} '
                                    if sense.get('notes'):
                                        for note in sense.get('notes'):
                                            if note.get('type') == 'grammaticalNote':
                                                message += u'{italics}[' + '{}'.format(note.get('text')) + ']{italics} '
                                            if note.get('type') == 'wordFormNote':
                                                message += u'{bold}' + '{}'.format(note.get('text')) + '{bold} '
                                    message += u'{}'.format(definitions[0])
            if not message and results and results[0]['lexicalEntries'] and results[0]['lexicalEntries'][0].get('derivativeOf'):
                message += u'[1/1] {bold}{term}{bold}: See {see}'.format(bold=chr(2), term=results[0]['lexicalEntries'][0]['text'], see=results[0]['lexicalEntries'][0]['derivativeOf'][0]['text'])
            if message:
                message = message.format(bold=chr(2), italics=chr(29), num=num, max_num=i)
            else:
                self.irc.msg(target, 'OxfordDictionary: No results found')
            self.irc.msg(target, message)
