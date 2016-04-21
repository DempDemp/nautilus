from core import base
from core.db import Base, session_scope
from core.auth import Auth
from sqlalchemy import Column, Integer, String

class Perform(Base):
    __tablename__ = 'perform'

    id = Column(Integer, primary_key=True)
    bot_id = Column(String)
    pline = Column(String)

    @classmethod
    def list_lines(cls, bot_id):
        with session_scope() as session:
            return session.query(cls.id, cls.pline).filter(cls.bot_id == bot_id).all()

    @classmethod
    def add(cls, bot_id, pline):
        with session_scope() as session:
            perform = cls(bot_id=bot_id, pline=pline)
            session.add(perform)
            session.commit()
            return perform.id

    @classmethod
    def delete(cls, bot_id, id):
        with session_scope() as session:
            perform = session.query(cls).filter(cls.bot_id == bot_id, cls.id == id).first()
            if perform:
                session.delete(perform)
                return True
            return False

class PerformClass(base.baseClass):
    def on_signedon(self):
        lines = Perform.list_lines(self.irc.id)
        for _, line in lines:
            self.irc.sendLine(line)

    def on_privmsg(self, address, target, text):
        nickname = address.split('!')[0]
        if target == self.irc.nickname:
            if text.startswith('perform'):
                params = text.split()
                if params[0] != 'perform':
                    return
                user = Auth.get_user_by_hostmask(self.irc.id, address)
                if user is None or 'n' not in user.flags:
                    self.irc.notice(nickname, 'Insufficient privileges')
                elif len(params) == 1:
                    self.irc.notice(nickname, 'Available commands: list add delete')
                elif params[1] == 'list':
                    lines = Perform.list_lines(self.irc.id)
                    self.irc.notice(nickname, 'Id Line')
                    for l in lines:
                        self.irc.notice(nickname, '%s %s' % l)
                    self.irc.notice(nickname, 'End of list')
                elif params[1] == 'add':
                    if len(params) < 3:
                        self.irc.notice(nickname, 'Usage: perform add <line>')
                    else:
                        pid = Perform.add(self.irc.id, ' '.join(params[2:]))
                        self.irc.notice(nickname, 'Done. Id: {}'.format(pid))
                elif params[1] == 'delete':
                    if len(params) < 3:
                        self.irc.notice(nickname, 'Usage: perform delete <id>')
                    else:
                        if Perform.delete(self.irc.id, params[2]):
                            self.irc.notice(nickname, 'Done')
                        else:
                            self.irc.notice(nickname, 'Unable to delete line')
