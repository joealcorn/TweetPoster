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

        login_url = 'https://www.reddit.com/api/login'
        about_url = 'http://www.reddit.com/api/me.json'

        params = {
            'passwd': password,
            'rem': False,
            'user': self.username,
            'api_type': 'json',
        }

        self.post(login_url, params)
        r = self.get(about_url)
        self.modhash = r.json()['data']['modhash']
        self.authenticated = True

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
        print 'signal received'
        now = time.time()
        if self.last_request is None:
            self.last_request = now
        else:
            tts = min(2, now, self.last_request)
            time.sleep(tts)
