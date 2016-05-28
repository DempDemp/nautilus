import urllib2
import re
import HTMLParser
from bs4 import BeautifulSoup
from core import base
from core.db import Base, session_scope
from core.auth import Auth
from sqlalchemy import Column, Integer, String

class TitleRegex(Base):
    __tablename__ = 'title_regex'

    id = Column(Integer, primary_key=True)
    bot_id = Column(String)
    regex = Column(String)

    @classmethod
    def list_regexes(cls, bot_id):
        with session_scope() as session:
            return session.query(cls.id, cls.regex).filter(cls.bot_id == bot_id).all()

    @classmethod
    def add(cls, bot_id, regex):
        re.compile(regex)
        with session_scope() as session:
            treg = cls(bot_id=bot_id, regex=regex)
            session.add(treg)
            session.commit()
            return treg.id

    @classmethod
    def delete(cls, bot_id, id):
        with session_scope() as session:
            treg = session.query(cls).filter(cls.bot_id == bot_id, cls.id == id).first()
            if treg:
                session.delete(treg)
                return True
            return False

h = HTMLParser.HTMLParser()

class Titles(base.baseClass):
    test = 2
    def __init__(self, *args, **kwargs):
        super(Titles, self).__init__(*args, **kwargs)
        self.set_regex_list()

    def set_regex_list(self):
        self.regexps = []
        for _, regex in TitleRegex.list_regexes(self.irc.id):
            self.regexps.append(re.compile(regex))

    def get_title(self, url):
        soup = BeautifulSoup(urllib2.urlopen(url))
        title = h.unescape(soup.title.string)
        title = ' '.join(title.replace('\r', '').replace('\n', '').split())
        return url, title

    def on_privmsg(self, address, target, text):
        if target.startswith('#') and 'http' in text:
            for regex in self.regexps:
                titlesearch = regex.search(text)
                if titlesearch is not None:
                    link = titlesearch.group(1)
                    try:
                        url, title = self.get_title(link)
                    except (urllib2.HTTPError, AttributeError) as e:
                        self.irc.logger.exception(e)
                        self.irc.msg(target, 'Unable to retrieve title')
                    else:
                        if len(title) > 200:
                            title = title[0:197] + '...'
                        self.irc.msg(target, u'Title: {}'.format(title))
                    break
        elif target == self.irc.nickname and text.startswith('titles'):
            nickname = address.split('!')[0]
            params = text.split()
            if params[0] != 'titles':
                return
            user = Auth.get_user_by_hostmask(self.irc.id, address)
            if user is None or 'w' not in user.flags:
                self.irc.notice(nickname, 'Insufficient privileges')
            elif len(params) == 1:
                self.irc.notice(nickname, 'Available commands: add del list')
            elif params[1] == 'add':
                if len(params) != 3:
                    self.irc.notice(nickname, 'Usage: titles add <regex>')
                else:
                    try:
                        rid = TitleRegex.add(self.irc.id, ' '.join(params[2:]))
                    except re.error as e:
                        self.irc.notice(nickname, 'Invalid regexp: {}'.format(e))
                    else:
                        self.irc.notice(nickname, 'Done. Regex id: {}'.format(rid))
                    self.set_regex_list()
            elif params[1] == 'del':
                if len(params) != 3:
                    self.irc.notice(nickname, 'Usage: titles del <id>')
                else:
                    if TitleRegex.delete(self.irc.id, params[2]):
                        self.irc.notice(nickname, 'Done')
                    else:
                        self.irc.notice(nickname, 'Unable to delete regex')
            elif params[1] == 'list':
                regexps = TitleRegex.list_regexes(self.irc.id)
                self.irc.notice(nickname, 'Id Regex')
                for x in regexes:
                    self.irc.notice(nickname, '%s %s' % x)
                self.irc.notice(nickname, 'End of list')
