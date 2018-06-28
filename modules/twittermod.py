import re
from core import base
from time import sleep
from twitter import Api, TwitterError
from core.db import Base, session_scope
from core.auth import Auth
from core.conf import settings
from threading import Thread
from core.utils import KeyValue, Whitelist, split_address, paragraphy_string
from sqlalchemy import Column, Integer, String
from six.moves.html_parser import HTMLParser

html_parser = HTMLParser()

class Tweet(Base):
    __tablename__ = 'twitter_tweets'

    id = Column(Integer, primary_key=True)
    tweet_id = Column(String)
    networkauth = Column(String)

    @classmethod
    def get_auth_by_tweet(cls, tweet_id):
        with session_scope() as session:
            return session.query(cls.networkauth).filter(cls.tweet_id == tweet_id).scalar()

    @classmethod
    def add(cls, tweet_id, networkauth):
        with session_scope() as session:
            tweet = cls(tweet_id=tweet_id, networkauth=networkauth)
            session.add(tweet)

class Twitter(base.baseClass):
    '''
    Settings:
        TWITTER_CONSUMER_KEY <key>
        TWITTER_CONSUMER_SECRET <key>
        TWITTER_ACCESS_TOKEN_KEY <key>
        TWITTER_ACCESS_TOKEN_SECRET <key>
        TWITTER_TWEET_CHANNEL <channel> -- to enable in-channel tweeting
        TWITTER_INTERVAL <seconds> -- interval for checking mentions

    User flag required: t
    '''
    thread = None
    thread_mentions = None
    interval = settings.TWITTER_INTERVAL
    tweet_channel = settings.TWITTER_TWEET_CHANNEL
    tweet_regex = re.compile(r'(?:http(?:s)?://)?(?:www\.)?twitter\.com\/[\w\-]+\/status\/(\d+)')

    def __init__(self, *args, **kwargs):
        super(Twitter, self).__init__(*args, **kwargs)
        self.api = self.get_api()
        self.follow_mentions()

    def __del__(self):
        self.api = None

    def get_api(self):
        try:
            apio = Api(consumer_key=settings.TWITTER_CONSUMER_KEY,
                        consumer_secret=settings.TWITTER_CONSUMER_SECRET,
                        access_token_key=settings.TWITTER_ACCESS_TOKEN_KEY,
                        access_token_secret=settings.TWITTER_ACCESS_TOKEN_SECRET)
            return apio
        except (AttributeError, TwitterError) as e:
            self.irc.logger.error('Twitter error: %s' % e.message)
            return False

    def follow_mentions_thread(self):
        while self.api and self.tweet_channel and self.interval:
            self.irc.logger.debug('Twitter: checking for new mentions')
            lastId = KeyValue.get_value(self.irc.id, 'TWITTER_LAST_MENTION_ID')
            statuses = self.api.GetMentions(since_id=lastId, count=5)
            for i, status in enumerate(statuses):
                self.irc.logger.info('New mention: %s', status.id)
                if i == 0:
                    KeyValue.set(self.irc.id, 'TWITTER_LAST_MENTION_ID', status.id)
                self.irc.msg(self.tweet_channel, u'Twitter @{}: {}'.format(status.user.screen_name, status.text.replace('\n', '').replace('\r', '')))
            sleep(self.interval)

    def follow_mentions(self):
        if self.api:
            if not self.thread_mentions or not self.thread_mentions.isAlive():
                self.thread_mentions = Thread(target=self.follow_mentions_thread)
                self.thread_mentions.daemon = False
                self.thread_mentions.start()

    def tweet(self, message, reply_to=None, media=None, networkauth=None):
        if self.api:
            try:
                if media:
                    status = self.api.PostMedia(message, media=media, in_reply_to_status_id=reply_to)
                else:
                    status = self.api.PostUpdate(message, in_reply_to_status_id=reply_to)
            except TwitterError as e:
                r = e.message
                if isinstance(e.message, list) and 'message' in e.message[0]:
                    r = e.message[0]['message']
                if r == 'Status is over 140 characters.':
                    r = '{} Length (approx.) - {}'.format(r, len(message))
                return r
            else:
                if networkauth:
                    Tweet.add(status.id, networkauth)
                return 'https://twitter.com/{}/status/{}'.format(status.user.screen_name, status.id)
        else:
            return 'No api defined'

    def tweet_delete(self, tweetid):
        if self.api:
            try:
                self.api.DestroyStatus(tweetid)
            except TwitterError as e:
                if isinstance(e.message, list) and 'message' in e.message[0]:
                    return e.message[0]['message']
                return e.message
            else:
                return 'Deleted'
        else:
            return 'No api defined'

    def get_status(self, status_id):
        if self.api:
            url = '%s/statuses/show.json' % (self.api.base_url)
            parameters = {
                'id': int(status_id),
                'trim_user': False,
                'include_my_retweet': True,
                'include_entities': True,
                'include_ext_alt_text': True,
                'tweet_mode': 'extended'
            }
            resp = self.api._RequestUrl(url, 'GET', data=parameters)
            return self.api._ParseAndCheckTwitter(resp.content.decode('utf-8'))

    def on_signedon(self):
        sleep(15)
        self.follow_mentions()

    def on_privmsg(self, address, target, text):
        if target.startswith('#') and 'http' in text and self.api:
            status_search = self.tweet_regex.search(text)
            if status_search is not None:
                status_id = status_search.groups()[0]
                try:
                    tweet = self.get_status(status_id)
                except TwitterError:
                    pass
                else:
                    message = u''
                    if tweet['user']['verified']:
                        message += u'{bold}\u2713{bold}'.format(bold=chr(2))
                    message += u'{bold}@{screen_name}{bold} {italics}({name}){italics}: {full_text}'.format(bold=chr(2), italics=chr(29), screen_name=tweet['user']['screen_name'], name=tweet['user']['name'], full_text=paragraphy_string(html_parser.unescape(tweet['full_text'])))
                    self.irc.msg(target, message)
        if target == self.tweet_channel:
            if text[0] not in base.prefix:
                return
            nickname, username, hostname = split_address(address)
            command = text.strip().split(' ', 1)[0][1:]
            if 'tweet' not in command:
                return
            params = text.split()[1:]
            user = self.irc.network.get_user_by_nickname(nickname)
            if not user or not user.networkauth or not Whitelist.has_permission(self.irc.id, user.networkauth, 'twitter'):
                return
            if command == 'tweet' and len(params):
                r = self.tweet(' '.join(params), networkauth=user.networkauth)
                self.irc.msg(target, r)
            if command == 'tweetreply' and len(params) > 1:
                r = self.tweet(' '.join(params[1:]), reply_to=params[0], networkauth=user.networkauth)
                self.irc.msg(target, r)
            if command == 'tweetmedia' and len(params) > 1:
                r = self.tweet(' '.join(params[1:]), media=params[0], networkauth=user.networkauth)
                self.irc.msg(target, r)
            if command == 'tweetmediareply' and len(params) > 1:
                r = self.tweet(' '.join(params[2:]), reply_to=params[0], media=params[0], networkauth=user.networkauth)
                self.irc.msg(target, r)
            elif command == 'deltweet' and len(params):
                tweetid = params[0]
                tweetauth = Tweet.get_auth_by_tweet(tweetid)
                user = Auth.get_user_by_hostmask(self.irc.id, address)
                if tweetauth or user is not None and 't' in user.flags:
                    if tweetauth == user.networkauth or flags is not None and 't' in flags[1]:
                        r = self.tweet_delete(tweetid)
                        self.irc.msg(target, r)
                    else:
                        self.irc.msg(target, 'You are not the tweet author (author: {})'.format(tweetauth))
                else:
                    self.irc.msg(target, 'No such tweet on record')
            elif command == 'whotweeted' and len(params):
                tweetid = params[0]
                tweetauth = Tweet.get_auth_by_tweet(tweetid)
                if tweetauth:
                    self.irc.msg(target, 'Author: {}'.format(tweetauth))
                else:
                    self.irc.msg(target, 'No such tweet on record')
        elif target == self.irc.nickname and text.split(' ', 1)[0] == 'twitter':
            try:
                command = text.split()[1]
                params = text.split()[2:]
            except IndexError:
                command = None
                params = []
            nickname, username, hostname = split_address(address)
            user = Auth.get_user_by_hostmask(self.irc.id, address)
            if user is None or 't' not in user.flags:
                self.irc.notice(nickname, 'Insufficient privileges')
            elif not command:
                self.irc.notice(nickname, 'Available commands: tweet deltweet whotweeted')
            elif command == 'tweet':
                if len(params):
                    r = self.tweet(' '.join(params))
                    self.irc.notice(nickname, r)
                else:
                    self.irc.notice(nickname, 'No text provided')
            elif command == 'whotweeted':
                if len(params):
                    tweetauth = Tweet.get_auth_by_tweet(params[0])
                    if tweetauth:
                        self.irc.notice(nickname, 'Author: {}'.format(tweetauth))
                    else:
                        self.irc.notice(nickname, 'No such tweet on record')
                else:
                    self.irc.notice(nickname, 'No tweet id provided')
            if command == 'deltweet':
                if len(params):
                    r = self.deleteTweet(params[0])
                    self.irc.notice(nickname, r)
                else:
                    self.irc.notice(nickname, 'No tweet id provided')
