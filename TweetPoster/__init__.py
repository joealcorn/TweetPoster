import json
import time
import sqlite3
from os import path, environ

import requests
from raven import Client

from TweetPoster import utils
from TweetPoster.signals import pre_request


def load_config():
    config = json.loads(open('config.json').read())
    for key in config['twitter'].keys():
        if environ.get(key):
            config['twitter'][key] = environ[key]

    return config

config = load_config()
sentry = Client(config['sentry'].get('dsn', ''), processors=(
    'TweetPoster.utils.SanitizeCredentialsProcessor',
))
template_path = path.dirname(path.realpath(__file__)) + '/templates/'


class Database(object):
    @property
    def conn(self):
        if not hasattr(self, '_connection'):
            self._connection = sqlite3.connect(config['database'])
        return self._connection

    def cursor(self):
        return self.conn.cursor()

    def init(self, clean=False):
        cur = self.cursor()
        if clean:
            cur.execute('DROP TABLE IF EXISTS posts')

        cur.execute(
            'CREATE TABLE IF NOT EXISTS posts (id INTEGER PRIMARY KEY ASC, thing_id TEXT UNIQUE)'
        )
        self.conn.commit()

    def has_processed(self, thing_id):
        c = self.cursor()
        c.execute('SELECT thing_id FROM posts WHERE thing_id = ?', (thing_id,))
        return c.fetchone() is not None

    def mark_as_processed(self, thing_id):
        c = self.cursor()
        c.execute('INSERT INTO posts (thing_id) VALUES (?)', (thing_id,))
        self.conn.commit()


class User(object):
    """
    Base user object that takes care of making requests
    """

    timeout = 3
    headers = {
        'User-Agent': 'https://github.com/buttscicles/TweetPoster'
    }

    def __init__(self):
        self.session = requests.session()

    def get(self, url, **kw):
        """
        Shortcut function to make a GET request as authed user.
        """
        return self.request(url, 'GET', **kw)

    def post(self, url, data, **kw):
        """
        Shortcut function to make a POST request as authed user.
        """
        return self.request(url, 'POST', data=data)

    def request(self, url, method, **kw):
        """
        Makes a request as the authenticated user.
        All keyword arguments are passed directly to requests

        """
        assert method in ('POST', 'GET'), 'Unsupported HTTP Method'

        kw['timeout'] = self.timeout
        if 'headers' in kw:
            # Merge self.headers with headers passed in
            # The passed in headers take preference
            kw['headers'] = dict(self.headers.items() + kw['headers'].items())
        else:
            kw['headers'] = self.headers

        # Send a pre-request signal.
        # This allows us to abide by different
        # ratelimits for different user accounts.
        pre_request.send(self)

        if method == 'POST':
            return self.session.post(url, **kw)
        elif method == 'GET':
            return self.session.get(url, **kw)


def main():
    from TweetPoster.reddit import Redditor
    from TweetPoster.twitter import Twitter

    db = Database()
    db.init()
    twitter = Twitter()
    reddit = Redditor().login(
        config['reddit']['username'],
        config['reddit']['password']
    )

    while True:
        try:
            posts = reddit.get_new_posts(db)
            for post in posts:
                handle_submission(post, twitter, reddit)
        except KeyboardInterrupt:
            import sys
            sys.exit(0)
        except requests.exceptions.Timeout:
            # These are exceptions we don't
            # want to tell sentry about
            pass
        except:
            sentry.captureException()
        finally:
            print 'sleeping'
            time.sleep(90)


def handle_submission(post, twitter, reddit):
    url = twitter.tweet_re.match(post.url)
    if not url:
        # This post links to the twitter domain
        # but not to a tweet or picture
        post.mark_as_processed()
        return

    tweet_id = url.group(1)
    try:
        tweet = twitter.get_tweet(tweet_id)
    except AssertionError as e:
        code = e.args[0]
        if code == 429:
            # We've hit Twitter's ratelimit
            print 'Ratelimited by Twitter, sleeping for 15 minutes'
            time.sleep(60 * 15)

        elif code == 404:
            post.mark_as_processed()
        return

    if utils.tweet_in_title(tweet, post):
        print 'Tweet in title, skipping'
        post.mark_as_processed()
        return

    with open(template_path + 'footer.txt') as f:
        footer_markdown = f.read().format(**post.__dict__)

    tweets = []
    while True:
        tweets.append(tweet.markdown)
        if tweet.reply_to is None:
            break
        else:
            tweet = tweet.reply_to

    tweets_markdown = '\n'.join(tweets)

    full_comment = tweets_markdown + footer_markdown
    reddit.comment(post.fullname, full_comment)
    post.mark_as_processed()
