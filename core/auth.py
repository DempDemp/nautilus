import hashlib
from core import base
from core.db import Base, session_scope
from sqlalchemy import Column, Integer, String
from sqlalchemy.sql import func

class Auth(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    bot_id = Column(String)
    username = Column(String)
    password = Column(String)
    hostmask = Column(String)
    flags = Column(String)

    class Auth(object):
        def __init__(self, user):
            for k, v in user.__dict__.iteritems():
                if not k.startswith('_'):
                    setattr(self, k, v)

        def get_instance(self, session):
            return session.query(Auth).filter(Auth.id == self.id).first()

        def delete(self):
            with session_scope() as session:
                user = self.get_instance(session)
                if user:
                    session.delete(user)

        def change_password(self, newpass):
            with session_scope() as session:
                user = self.get_instance(session)
                hashed = hashlib.sha512(str(self.bot_id) + newpass).hexdigest()
                user.password = hashed

        def change_flags(self, flags):
            with session_scope() as session:
                user = self.get_instance(session)
                user.flags = flags

    @classmethod
    def create_defaults(cls, bot_id):
        with session_scope() as session:
            if not session.query(func.count(cls.id)).filter(cls.bot_id == bot_id).scalar():
                password = hashlib.sha512(str(bot_id) + '12345').hexdigest()
                user = cls(bot_id=bot_id, username='admin', password=password, hostmask='', flags='n')
                session.add(user)

    @classmethod
    def authenticate(cls, bot_id, username, password, hostmask=None):
        with session_scope() as session:
            hashed = hashlib.sha512(str(bot_id) + password).hexdigest()
            user = session.query(cls).filter(cls.bot_id == bot_id, cls.username == username, cls.password == hashed).first()
            if user:
                if hostmask:
                    user.hostmask = hostmask
                return cls.Auth(user)
            return False


    @classmethod
    def get_user_by_username(cls, bot_id, username):
        with session_scope() as session:
            user = session.query(cls).filter(cls.bot_id == bot_id, cls.username == username).first()
            if user:
                return cls.Auth(user)
            return None

    @classmethod
    def get_user_by_hostmask(cls, bot_id, hostmask):
        with session_scope() as session:
            user = session.query(cls).filter(cls.bot_id == bot_id, cls.hostmask == hostmask).first()
            if user:
                return cls.Auth(user)
            return None

    @classmethod
    def add(cls, bot_id, username, password, flags):
        with session_scope() as session:
            hashed = hashlib.sha512(str(bot_id) + password).hexdigest()
            user = cls(bot_id=bot_id, username=username, password=hashed, hostmask='', flags=flags)
            session.add(user)
            return cls.Auth(user)

    @classmethod
    def list_users(cls, bot_id):
        with session_scope() as session:
            return session.query(cls.username, cls.hostmask, cls.flags).filter(cls.bot_id == bot_id).all()

class AuthClass(base.baseClass):
    def __init__(self, *args, **kwargs):
        super(AuthClass, self).__init__(*args, **kwargs)
        Auth.create_defaults(self.irc.id)

    def on_privmsg(self, address, target, text):
        nickname = address.split('!')[0]
        if target == self.irc.nickname:
            if text.startswith('auth'):
                params = text.split(' ')
                if len(params) < 3:
                    self.irc.notice(nickname, 'Usage: auth <username> <password>')
                else:
                    user = Auth.authenticate(self.irc.id, params[1], params[2], address)
                    if user:
                        self.irc.notice(nickname, 'Successfully logged in. User flags: %s' % user.flags)
                    else:
                        self.irc.notice(nickname, 'Incorrect username or password')
            elif text.startswith('users'):
                params = text.split(' ')
                if params[0] != 'users':
                    return
                user = Auth.get_user_by_hostmask(self.irc.id, address)
                if user is None:
                    self.irc.notice(nickname, 'Insufficient privileges')
                elif len(params) == 1:
                    self.irc.notice(nickname, 'Available commands: whoami changepass add delete list setflags')
                elif params[1] == 'whoami':
                    self.irc.notice(nickname, 'Username: {}, flags: {}'.format(user.username, user.flags))
                elif params[1] == 'changepass':
                    if len(params) < 4:
                        if 'n' in user.flags:
                            self.irc.notice(nickname, 'Usage: users changepass [username] <oldpass> <newpass>')
                        else:
                            self.irc.notice(nickname, 'Usage: users changepass <oldpass> <newpass>')
                    elif len(params) == 4:
                        user.change_password(params[3])
                        self.irc.notice(nickname, 'Done')
                    elif len(params) == 5:
                        if 'n' in user.flags:
                            tuser = Auth.get_user_by_username(self.irc.id, params[2])
                            if tuser:
                                user.change_password(params[3])
                                self.irc.notice(nickname, 'Done')
                            else:
                                self.irc.notice(nickname, 'No such username')
                elif params[1] == 'add':
                    if 'n' not in user.flags:
                        self.irc.notice(nickname, 'Insufficient privileges')
                    elif len(params) < 4:
                        self.irc.notice(nickname, 'Usage: users add <username> <password> <flags>')
                    else:
                        if Auth.get_user_by_username(self.irc.id, params[2]) is None:
                            Auth.add(self.irc.id, params[2], params[3], params[4])
                            self.irc.notice(nickname, 'Done')
                        else:
                            self.irc.notice(nickname, 'Username already taken')
                elif params[1] == 'delete':
                    if 'n' not in user.flags:
                        self.irc.notice(nickname, 'Insufficient privileges')
                    elif len(params) < 3:
                        self.irc.notice(nickname, 'Usage: users delete <username>')
                    else:
                        tuser = Auth.get_user_by_username(self.irc.id, params[2])
                        if tuser:
                            tuser.delete()
                            self.irc.notice(nickname, 'Done')
                        else:
                            self.irc.notice(nickname, 'No such username')
                elif params[1] == 'list':
                    if 'n' not in user.flags:
                        self.irc.notice(nickname, 'Insufficient privileges')
                    else:
                        users = Auth.list_users(self.irc.id)
                        self.irc.notice(nickname, 'Username Hostmask Flags')
                        for x in users:
                            self.irc.notice(nickname, '%s %s %s' % x)
                elif params[1] == 'setflags':
                    if 'n' not in user.flags:
                        self.irc.notice(nickname, 'Insufficient privileges')
                    elif len(params) < 4:
                        self.irc.notice(nickname, 'Usage: users setflags <username> <flags>')
                    else:
                        tuser = Auth.get_user_by_username(self.irc.id, params[2])
                        if tuser:
                            tuser.change_flags(params[3])
                            self.irc.notice(nickname, 'Done')
                        else:
                            self.irc.notice(nickname, 'No such username')
