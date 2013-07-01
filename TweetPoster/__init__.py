import json
import time
import sqlite3
from os import path

import requests
from raven import Client

from TweetPoster import utils
from TweetPoster.signals import pre_request


config = json.loads(open('config.json').read())
sentry = Client(config['sentry'].get('dsn', ''))


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


def run():
    while True:
        try:
            main()
        except KeyboardInterrupt:
            import sys
            sys.exit(0)
        except:
            sentry.captureException()
        finally:
            print 'sleeping'
            time.sleep(90)


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

    posts = reddit.get_new_posts(db)
    for post in posts:
        url = twitter.tweet_re.match(post.url)
        if not url:
            # This post links to the twitter domain
            # but not to a tweet or picture
            post.mark_as_processed()
            continue

        tweet_id = url.group(1)
        # tweet_id = '351794310498357248'
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

            continue

        except Exception as e:
            print 'except'
            if not isinstance(e, KeyboardInterrupt):
                sentry.captureException()
            continue

        if utils.tweet_in_title(tweet, post):
            print 'Tweet in title, skipping'
            post.mark_as_processed()
            continue

        template_path = path.dirname(path.realpath(__file__)) + '/templates/'
        with open(template_path + 'tweet.txt') as f:
            tweet_template = f.read()

        # Link hashtags, expand urls, rehost images etc
        tweet = utils.replace_entities(tweet)

        # This prevents newlines breaking out of a markdown quote
        tweet.text = '\n>'.join(tweet.text.splitlines())
        tweet_markdown = tweet_template.format(**tweet.__dict__)

        with open(template_path + 'footer.txt') as f:
            footer_markdown = f.read().format(**post.__dict__)

        full_comment = tweet_markdown + footer_markdown

        reddit.comment(post.fullname, full_comment)
        post.mark_as_processed()
