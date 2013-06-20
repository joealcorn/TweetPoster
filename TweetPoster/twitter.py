from requests_oauthlib import OAuth1

from TweetPoster import User, config


class Twitter(User):

    def __init__(self, *a, **kw):
        super(Twitter, self).__init__(*a, **kw)

        self.session.auth = OAuth1(
            config['twitter']['consumer_key'],
            config['twitter']['consumer_secret'],
            config['twitter']['access_token'],
            config['twitter']['access_secret'],
            signature_type='auth_header'
        )
