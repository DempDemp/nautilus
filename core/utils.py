from core import base
from core.db import Base, session_scope
from core.auth import Auth
from sqlalchemy import Column, Integer, String

def split_address(address):
    nickname = address.split('!', 1)[0]
    username = address[len(nickname)+1:].split('@', 1)[0]
    hostname = address.split('@', 1)[1]
    return nickname, username, hostname

def paragraphy_string(s):
    ''' converts a string into a single paragraph '''
    paragraph = []
    for sentence in s.splitlines():
        sentence = sentence.strip()
        if sentence:
            if not sentence.endswith('.'):
                sentence += '.'
            paragraph.append(sentence)
    return ' '.join(paragraph)

class KeyValue(Base):
    __tablename__ = 'keyvalue'

    id = Column(Integer, primary_key=True)
    bot_id = Column(String)
    key = Column(String)
    value = Column(String)

    @classmethod
    def get_value(cls, bot_id, key):
        with session_scope() as session:
            return session.query(cls.value).filter(cls.bot_id == bot_id, cls.key == key).scalar()

    @classmethod
    def set(cls, bot_id, key, value):
        with session_scope() as session:
            keyval = session.query(cls).filter(cls.bot_id == bot_id, cls.key == key).first()
            if keyval:
                keyval.value = value
            else:
                keyval = cls(bot_id=bot_id, key=key, value=value)
                session.add(keyval)

    @classmethod
    def delete_key(cls, bot_id, key):
        with session_scope() as session:
            keyval = session.query(cls).filter(cls.bot_id == bot_id, cls.key == key).first()
            if keyval:
                session.delete(keyval)

class Whitelist(Base):
    __tablename__ = 'whitelist'

    id = Column(Integer, primary_key=True)
    bot_id = Column(String)
    networkauth = Column(String)
    permissions = Column(String)

    @classmethod
    def get_permissions(cls, bot_id, networkauth):
        with session_scope() as session:
            permissions = session.query(cls.permissions).filter(cls.bot_id == bot_id, cls.networkauth == networkauth).scalar()
            if permissions:
                return permissions.split(',')
            else:
                return None

    @classmethod
    def has_permission(cls, bot_id, networkauth, permission):
        permissions = cls.get_permissions(bot_id, networkauth)
        return permissions and permission in permissions

    @classmethod
    def add_permission(cls, bot_id, networkauth, permission):
        with session_scope() as session:
            wl = session.query(cls).filter(cls.bot_id == bot_id, cls.networkauth == networkauth).first()
            if wl:
                permissions = wl.permissions.split(',')
                if permission not in permissions:
                    permissions.append(permission)
                wl.permissions = ','.join(permissions)
            else:
                wl = cls(bot_id=bot_id, networkauth=networkauth, permissions=permission)
                session.add(wl)

    @classmethod
    def delete_permission(cls, bot_id, networkauth, permission):
        with session_scope() as session:
            wl = session.query(cls).filter(cls.bot_id == bot_id, cls.networkauth == networkauth).first()
            if wl:
                permissions = wl.permissions.split(',')
                if permission in permissions:
                    permissions.remove(permission)
                wl.permissions = ','.join(permissions)
                return True
            return False

    @classmethod
    def list_auths(cls, bot_id):
        with session_scope() as session:
            return session.query(cls.networkauth).filter(cls.bot_id == bot_id).all()

class Utilities(base.baseClass):
    def on_privmsg(self, address, target, text):
        nickname = address.split('!')[0]
        if target == self.irc.nickname:
            user = Auth.get_user_by_hostmask(self.irc.id, address)
            command = text.strip().split(' ', 1)[0]
            params = text.split()[1:]
            if user is None or 'n' not in user.flags:
                self.irc.notice(nickname, 'Insufficient privileges')
                return
            if command == 'rehash':
                self.irc.factory.reload_modules()
                self.irc.notice(nickname, 'Done')
            elif command == 'sendline':
                self.irc.sendLine(' '.join(params))
            elif command == 'whitelist':
                try:
                    command = text.split()[1]
                    params = text.split()[2:]
                except IndexError:
                    command = None
                    params = []
                if not command:
                    self.irc.notice(nickname, 'Available commands: add delete listauths listpermissions')
                elif command == 'add':
                    if len(params) == 2:
                        Whitelist.add_permission(self.irc.id, params[0], params[1])
                        self.irc.notice(nickname, 'Added permission successfully')
                    else:
                        self.irc.notice(nickname, 'Syntax: whitelist add <network_auth> <permission>')
                elif command == 'delete':
                    if len(params) == 2:
                        if Whitelist.delete_permission(self.irc.id, params[0], params[1]):
                            self.irc.notice(nickname, 'Deleted permission successfully')
                        else:
                            self.irc.notice(nickname, 'This auth name has no permissions')
                    else:
                        self.irc.notice(nickname, 'Syntax: whitelist delete <network_auth> <permission>')
                elif command == 'listauths':
                    auths = Whitelist.list_auths(self.irc.id)
                    if auths:
                        auths = ', '.join([x[0] for x in auths])
                    self.irc.notice(nickname, 'Auths: {}'.format(auths))
                elif command == 'listpermissions':
                    if len(params) == 1:
                        permissions = Whitelist.get_permissions(self.irc.id, params[0])
                        if permissions:
                            permissions = ', '.join(permissions)
                        self.irc.notice(nickname, '{}\'s permissions: {}'.format(params[0], permissions))
                    else:
                        self.irc.notice(nickname, 'Syntax: whitelist listpermissions <network_auth>')
