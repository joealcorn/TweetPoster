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

    def get_tweet(self, tweet_id):
        url = 'https://api.twitter.com/1.1/statuses/show.json'
        params = {
            'id': tweet_id,
            'include_entities': 1,
        }

        r = self.get(url, params=params)
        assert r.status_code == 200, r.status_code

        return r.json()
