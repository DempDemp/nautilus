import datetime
from random import randint
from core.db import Base, session_scope
from core.auth import Auth
from core.base import baseClass, command, TARGET_CHANNEL, TARGET_SELF
from core.utils import split_address
from sqlalchemy import Column, Integer, String, DateTime, Boolean, UniqueConstraint
from sqlalchemy.sql import func

class Quote(Base):
    __tablename__ = 'quotes_quotes'
    __table_args__ = (UniqueConstraint('bot_id', 'channel', 'quote_id', name='_bot_channel_quote_uc'),)

    id = Column(Integer, primary_key=True)
    bot_id = Column(String)
    channel = Column(String)
    quote_id = Column(Integer)
    added_by = Column(String)
    added_by_auth = Column(String)
    added_date = Column(DateTime, default=datetime.datetime.utcnow)
    quote = Column(String)
    deleted = Column(Boolean, default=False)

    @classmethod
    def get_last_quote_id(cls, bot_id, channel):
        with session_scope() as session:
            return session.query(func.max(cls.quote_id)).filter(cls.bot_id == bot_id, cls.channel == channel).scalar()

    @classmethod
    def get_quotes(cls, bot_id, channel, quote_id=None, text=None):
        with session_scope() as session:
            query = session.query(cls.quote_id, cls.added_by_auth, cls.added_date, cls.quote).filter(cls.bot_id == bot_id, cls.channel == channel, cls.deleted == False)
            if quote_id:
                query = query.filter(cls.quote_id == quote_id)
            elif text:
                for s in text.split():
                    query = query.filter(cls.quote.like('%{}%'.format(s)))
            return query.all()

    @classmethod
    def add(cls, bot_id, channel, address, auth, quote):
        last_quote_id = cls.get_last_quote_id(bot_id, channel)
        if last_quote_id is None:
            last_quote_id = 0
        quote_id = last_quote_id + 1
        with session_scope() as session:
            quote = cls(bot_id=bot_id, quote_id=quote_id, channel=channel, added_by=address, added_by_auth=auth, quote=quote)
            session.add(quote)
            session.commit()
            return quote.quote_id

    @classmethod
    def delete(cls, bot_id, channel, quote_id):
        with session_scope() as session:
            num = session.query(cls).filter(cls.bot_id == bot_id, cls.channel == channel, cls.quote_id == quote_id).update({'deleted': True})
            session.commit()
            return num

class Quotes(baseClass):
    @command('addquote', min_params=2, target=TARGET_CHANNEL)
    def add_quote(self, target, address, params, **kwargs):
        nickname, username, hostname = split_address(address)
        user = self.irc.network.get_user_by_nickname(nickname)
        if not user or not user.networkauth or not target.startswith('#'):
            return
        quote_id = Quote.add(self.irc.id, target, address, user.networkauth, ' '.join(params))
        self.irc.msg(target, 'Quote #{} added'.format(quote_id))

    @command('quote', target=TARGET_CHANNEL)
    def quote(self, target, params, **kwargs):
        if not params:
            quotes = Quote.get_quotes(self.irc.id, target)
            if len(quotes):
                quotes = [quotes[randint(0, len(quotes) -1)]]
            else:
                quotes = []
        else:
            quote_id = None
            if len(params) == 1:
                try:
                    quote_id = int(params[0])
                except ValueError:
                    pass
            if quote_id:
                quotes = Quote.get_quotes(self.irc.id, target, quote_id=quote_id)
                if not quotes:
                    return self.irc.msg(target, 'Invalid quote id')
            else:
                quotes = Quote.get_quotes(self.irc.id, target, text=' '.join(params))
        if not quotes:
            return self.irc.msg(target, 'No quotes found')
        more = []
        for idx, row in enumerate(quotes):
            quote_id, auth, date, quote = row
            if idx < 3:
                self.irc.msg(target, 'Quote #{} by {} ({}): {}'.format(quote_id, auth, date.strftime('%Y-%m-%d'), quote))
            else:
                more.append(quote_id)
        if more:
            self.irc.msg(target, 'Additional quotes: {}'.format(', '.join(['#{}'.format(quote_id) for quote_id in more])))

    @command('delquote', prefix='', target=TARGET_SELF)
    def del_quote(self, target, address, params, **kwargs):
        nickname, username, hostname = split_address(address)
        user = Auth.get_user_by_hostmask(self.irc.id, address)
        if user is None or 'q' not in user.flags:
            return self.irc.notice(nickname, 'Insufficient privileges')
        if len(params) < 2:
            return self.irc.notice(nickname, 'delquote <channel> <quote_id>')
        channel = params[0]
        try:
            quote_id = int(params[1])
        except ValueError:
            return self.irc.notice(nickname, 'Invalid quote id')
        deleted = Quote.delete(self.irc.id, channel, quote_id)
        if deleted:
            self.irc.notice(nickname, 'Quote #{} deleted successfully'.format(quote_id))
        else:
            self.irc.notice(nickname, 'Invalid quote id')
