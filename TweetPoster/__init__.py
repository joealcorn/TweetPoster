import json
import sqlite3

import requests

from TweetPoster.signals import pre_request


config = json.loads(open('config.json').read())


class Database(object):
    @property
    def conn(self):
        if not hasattr(self, '_connection'):
            self._connection = sqlite3.connect(config['database'])
        return self._connection

    def cursor(self):
        return self.conn.cursor()

    def init(self):
        self.cursor().execute(
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
