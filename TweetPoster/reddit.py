import time

from TweetPoster import User
from TweetPoster.signals import pre_request


class Redditor(User):

    authenticated = False
    last_request = None

    def __init__(self, *a, **kw):
        super(Redditor, self).__init__(*a, **kw)
        pre_request.connect(self.ratelimit, sender=self)

    def login(self, password):
        """
        Logs a user in, stores modhash in Redditor.modhash

        """
        login_url = 'https://ssl.reddit.com/api/login'
        params = {
            'passwd': password,
            'rem': False,
            'user': self.username,
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

    def ratelimit(self, sender):
        """
        Helps us abide by reddit's API usage limitations.
        https://github.com/reddit/reddit/wiki/API#rules
        """
        if self.last_request is not None:
            diff = time.time() - self.last_request
            if diff < 2:
                time.sleep(2 - diff)

        self.last_request = time.time()
