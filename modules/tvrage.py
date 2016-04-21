import time
import urllib
import urllib2
from core import base
from BeautifulSoup import BeautifulSoup

class TVRage(base.baseClass):
    def purify(self, s):
        if type(s) == 'str' or type(s) == 'unicode':
            return str(BeautifulSoup(s.replace('\n', '').replace('\r', ''), convertEntities=BeautifulSoup.HTML_ENTITIES))
        else:
            return s

    def get_show_id(self, name, num = 1):
        num -= 1
        soup = BeautifulSoup(urllib2.urlopen('http://services.tvrage.com/feeds/search.php?show=' + urllib.quote_plus(name)))
        shows = soup.findAll('show')
        if shows != None and len(shows) > num:
            showid = shows[num].find('showid').findAll(text=True)
            for idx, text in enumerate(showid):
                showid[idx] = text.strip()
            showid = ' '.join(' '.join(showid).split())
        else:
            showid = False
        return showid

    def get_show_episodes(self, showid):
        soup = BeautifulSoup(urllib2.urlopen('http://services.tvrage.com/feeds/episode_list.php?sid=' + urllib.quote_plus(showid)))
        episodes = soup.findAll('episode')
        lastep = nextep = False
        if episodes is not None and len(episodes):
            today = time.mktime(time.strptime(time.strftime('%Y-%m-%d'), '%Y-%m-%d'))
            found = False
            for idx, episode in enumerate(episodes):
                airdate = ''.join(episode.find('airdate').findAll(text=True))
                try:
                    airdatetime = time.strptime(airdate, '%Y-%m-%d')
                except ValueError:
                    airdatetime = time.strptime('1990-01-01', '%Y-%m-%d')
                if today <= time.mktime(airdatetime): # didn't air yet
                    found = True
                    epnum = ''.join(episode.find('seasonnum').findAll(text=True))
                    season = episode.parent['no']
                    title = ''.join(episode.find('title').findAll(text=True))
                    nextep = {'epnum': epnum, 'season': season, 'airdate': airdate, 'title': title}
                    if idx >= 1:
                        epnum = ''.join(episodes[idx-1].find('seasonnum').findAll(text=True))
                        season = episodes[idx-1].parent['no']
                        title = ''.join(episodes[idx-1].find('title').findAll(text=True))
                        airdate = ''.join(episodes[idx-1].find('airdate').findAll(text=True))
                        lastep = {'epnum': epnum, 'season': season, 'airdate': airdate, 'title': title}
                    break
            if not found:
                epnum = ''.join(episodes[idx].find('seasonnum').findAll(text=True))
                season = episodes[idx].parent['no']
                title = ''.join(episodes[idx].find('title').findAll(text=True))
                airdate = ''.join(episodes[idx].find('airdate').findAll(text=True))
                lastep = {'epnum': epnum, 'season': season, 'airdate': airdate, 'title': title}
        name = ''.join(soup.find('name').findAll(text=True))
        return name, lastep, nextep

    def on_privmsg(self, address, target, text):
        if text[0] in base.prefix and text.strip().split(' ', 1)[0][1:] in ('tvrage', 'epinfo') and len(text.split()) >= 2:
            try:
                showid = self.get_show_id(' '.join(text.split()[1:]))
                if showid:
                    name, lastep, nextep = self.get_show_episodes(showid)
                    if lastep:
                        slastep = '{bold}{season}x{epnum} - {title}{bold} aired on {airdate}'.format(bold=chr(2), **lastep)
                    else:
                        slastep = 'No details'
                    if nextep:
                        snextep = '{bold}{season}x{epnum} - {title}{bold} will air on {airdate}'.format(bold=chr(2), **nextep)
                    else:
                        snextep = 'Not scheduled'
                    self.irc.msg(target, '[TVRage] {bold}{name}{bold} - Last episode: {lastep}. Next episode: {nextep}.'.format(bold=chr(2), name=name, lastep=slastep, nextep=snextep))
            except urllib2.HTTPError as e:
                self.irc.logger.exception(e)
                self.irc.msg(target, 'Unable to retrieve information from tvrage')
