import urllib2
from core import base
from core.auth import Auth

class IRCPaint(base.baseClass):
    @classmethod
    def get_drawing(cls, sid):
        return urllib2.urlopen('http://ircpaint.randomlab.info/rawirc.php?q={}'.format(sid)).read()

    def on_privmsg(self, address, target, text):
        if target == self.irc.nickname and text.startswith('ircpaint'):
            params = text.split()
            if params[0] != 'ircpaint':
                return
            nickname = address.split('!')[0]
            user = Auth.get_user_by_hostmask(self.irc.id, address)
            if user is None or 'n' not in user.flags:
                self.irc.notice(nickname, 'Insufficient privileges')
            elif len(params) < 3:
                self.irc.notice(nickname, 'Usage: ircpaint <target> <id>')
            else:
                try:
                    drawing = self.get_drawing(params[2])
                except urllib2.HTTPError as e:
                    self.irc.notice(nickname, 'Unable to get drawing: {}'.format(e))
                else:
                    drawing = drawing.split()
                    for line in drawing:
                        self.irc.msg(params[1], line.strip())
