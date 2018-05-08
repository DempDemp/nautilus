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
        r = requests.get('https://od-api.oxforddictionaries.com:443/api/v1/entries/en/{}/regions=gb'.format(urllib.quote_plus(text)), headers={'app_id': settings.OXFORD_APP_ID, 'app_key': settings.OXFORD_APP_KEY})
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
                            i += 1
                            if i == num:
                                message = u'[{num}/{max_num}] {bold}' + '{}'.format(lexentry.get('text')) + '{bold}'
                                if lexentry.get('lexicalCategory'):
                                    message += u' ({})'.format(lexentry.get('lexicalCategory'))
                                message += u': '
                                if sense.get('registers'):
                                    message += u'{italics}' + '{}'.format(sense.get('registers')[0]) + '{italics} '
                                if sense.get('domains'):
                                    message += u'{italics}' + '{}'.format(sense.get('domains')[0]) + '{italics} '
                                if sense.get('notes'):
                                    for note in sense.get('notes'):
                                        if note.get('type') == 'grammaticalNote':
                                            message += u'{italics}[' + '{}'.format(note.get('text')) + ']{italics} '
                                        if note.get('type') == 'wordFormNote':
                                            message += u'{bold}' + '{}'.format(note.get('text')) + '{bold} '
                                message += u'{}'.format(sense.get('definitions', [])[0])
            if message:
                message = message.format(bold=chr(2), italics=chr(29), num=num, max_num=i)
            else:
                self.irc.msg(target, 'OxfordDictionary: No results found')
            self.irc.msg(target, message)
