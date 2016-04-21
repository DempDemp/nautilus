import urllib
import urllib2
from core import base
try:
    import json
except ImportError:
    import simplejson as json

class IMDB(base.baseClass):
    @classmethod
    def imdb(cls, search):
        data = urllib2.urlopen('http://www.imdbapi.com/?' + urllib.urlencode({'t': search})).read()
        return json.loads(data)

    def on_privmsg(self, address, target, text):
        if text[0] in base.prefix and text.strip().split(' ', 1)[0][1:] == 'imdb' and len(text.split()) >= 2:
            search = ' '.join(text.split()[1:])
            if len(search) > 0:
                try:
                    imdbdata = self.imdb(search)
                except (urllib2.HTTPError, ValueError) as e:
                    self.irc.msg(target, 'Unable to retrieve IMDB information')
                else:
                    if 'Response' in result and result['Response'] == 'False':
                        msg = '[IMDB] Nothing found'
                    elif 'Response' in result and result['Response'] == 'True':
                        msg = '[IMDB] {Title} ({Year}). Genre: {Genre}. Director: {Director}. Rating: {imdbRating}. Runtime: {Runtime}. http://imdb.com/title/{imdbID}/'.format(**result)
                    self.irc.msg(target, msg.split('\n')[0])
