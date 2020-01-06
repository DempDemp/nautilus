import urllib2
import requests
from core.base import baseClass, command
from core.utils import split_address

class EmptyResult(Exception):
    pass

class Wikipedia(baseClass):
    def get_definitions(self, text):
        r = requests.get('https://en.wikipedia.org/w/api.php', params={
            'action': 'opensearch',
            'search': text,
            'limit': 500,
            'format': 'json',
        })
        data = r.json()
        results = []
        for i in range(len(data[1])):
            if data[2][i] and not data[2][i].endswith(' may refer to:'):
                results.append((data[1][i], data[2][i]))
        if not results:
            raise EmptyResult
        return results

    def get_random_definition(self):
        r = requests.get('https://en.wikipedia.org/w/api.php', params={
            'action': 'query',
            'format': 'json',
            'generator': 'random',
            'grnlimit': 1,
            'grnnamespace': 0,
            'prop': 'extracts',
            'exsentences': 1,
            'explaintext': 1,
        })
        result = r.json()['query']['pages'].values()[0]
        return [(result['title'], result['extract'])]

    @command(['wiki', 'wikipedia'], min_params=1)
    def query(self, target, address, params, **kwargs):
        nickname, username, hostname = split_address(address)
        if len(params) >= 2 and params[0].isdigit():
            num = int(params.pop(0))
        else:
            num = 1
        term = ' '.join(params)
        try:
            if term == 'random':
                results = self.get_random_definition()
            else:
                results = self.get_definitions(term)
            if num > len(results):
                num = len(results)
        except (urllib2.HTTPError, AttributeError):
            self.irc.msg(target, 'Wikipedia: Error retrieving list')
        except EmptyResult:
            self.irc.msg(target, 'Wikipedia: No results found')
        else:
            self.irc.msg(target, u'[{num}/{max_num}] {bold}{term}{bold}: {definition}'.format(
                bold=chr(2),
                num=num,
                max_num=len(results),
                term=results[num - 1][0],
                definition=results[num - 1][1],
            ))
