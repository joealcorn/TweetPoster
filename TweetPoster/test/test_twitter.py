from os import path

import httpretty

from TweetPoster import config
from TweetPoster.twitter import Twitter

json_dir = path.dirname(path.realpath(__file__)) + '/json/'
tweet_url = 'https://api.twitter.com/1.1/statuses/show.json'
config.update({
    'twitter': {
        'consumer_key': 'consumer_key',
        'consumer_secret': 'consumer_secret',
        'access_token': 'access_token',
        'access_secret': 'access_secret',
    }
})


def mock_tweet():
    f = open(json_dir + 'tweet.json')
    body = f.read()
    f.close()

    httpretty.register_uri(
        httpretty.GET,
        tweet_url,
        body=body,
        content_type='application/json'
    )


@httpretty.activate
def test_oauth():
    mock_tweet()
    Twitter().get_tweet('347087814833344512')
    req = httpretty.last_request()
    assert 'Authorization' in req.headers
    assert 'oauth_token="access_token"' in req.headers['Authorization']
    assert 'oauth_consumer_key="consumer_key"' in req.headers['Authorization']
