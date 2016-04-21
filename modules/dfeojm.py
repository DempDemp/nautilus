import urllib
import urllib2
from core import base
from BeautifulSoup import BeautifulSoup

class DownForMe(base.baseClass):
    @classmethod
    def check(cls, site):
        site = site.strip()
        soup = BeautifulSoup(urllib2.urlopen('http://www.downforeveryoneorjustme.com/' + urllib.quote_plus(site)))
        isup = soup.find('div', {'id': 'container'}).findAll(text=True)
        up = True
        if isup[0].strip() == "It's not just you!":
            up = False
        elif isup[0].strip().split()[0] == 'Huh?':
            raise StandardError('Huh?')
        return site, up

    def on_privmsg(self, address, target, text):
        if text[0] in base.prefix and text.strip().split(' ', 1)[0][1:] in ('downforeveryoneorjustme', 'down', 'isdown', 'isup') and len(text.split()) >= 2:
            try:
                site, up = self.check(' '.join(text.split()[1:]))
            except (urllib2.HTTPError, StandardError) as e:
                self.irc.logger.exception(e)
                self.irc.msg(target, 'dfeojm - error occured')
            else:
                if len(site) > 40:
                    site = site[0:37] + '...'
                if up:
                    msg = 'It\'s just you. {} is up.'.format(site)
                else:
                    msg = 'It\'s not just you! {} looks down from here.'.format(site)
                self.irc.msg(target, msg)
