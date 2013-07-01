import time

from TweetPoster import User
from TweetPoster.signals import pre_request


class Redditor(User):

    authenticated = False
    last_request = None

    def __init__(self, bypass_ratelimit=False, *a, **kw):
        super(Redditor, self).__init__(*a, **kw)

        if not bypass_ratelimit:
            pre_request.connect(self._ratelimit, sender=self)

    def login(self, username, password):
        """
        Logs a user in, stores modhash in Redditor.modhash

        """
        login_url = 'https://ssl.reddit.com/api/login'
        params = {
            'passwd': password,
            'rem': False,
            'user': username,
            'api_type': 'json',
        }

        r = self.post(login_url, params)
        if 'data' not in r.json()['json']:
            raise Exception('login failed')

        self.modhash = r.json()['json']['data']['modhash']
        self.authenticated = True
        return self

    def comment(self, thing_id, comment):
        """
        Replies to :thing_id: with :comment:

        """
        url = 'http://www.reddit.com/api/comment'

        params = {
            'uh': self.modhash,
            'thing_id': thing_id,
            'comment': comment,
            'api_type': 'json',
        }

        return self.post(url, params)

    def get_new_posts(self, db):
        """
        Returns a list of posts that haven't already
        been processed
        """
        url = 'http://www.reddit.com/domain/twitter.com/new.json'
        r = self.get(url, params=dict(limit=100))
        all_posts = r.json()['data']['children']
        posts = [p for p in all_posts if not db.has_processed(p['data']['name'])]
        return posts

    def _ratelimit(self, sender):
        """
        Helps us abide by reddit's API usage limitations.
        https://github.com/reddit/reddit/wiki/API#rules
        """
        if self.last_request is not None:
            diff = time.time() - self.last_request
            if diff < 2:
                time.sleep(2 - diff)

        self.last_request = time.time()
