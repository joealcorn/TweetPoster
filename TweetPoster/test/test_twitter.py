from os import path

import httpretty
from nose.plugins.attrib import attr

from TweetPoster.twitter import Twitter

json_dir = path.dirname(path.realpath(__file__)) + '/json/'
tweet_url = 'https://api.twitter.com/1.1/statuses/show.json'


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
    assert 'oauth_token="' in req.headers['Authorization']
    assert 'oauth_consumer_key="' in req.headers['Authorization']


@attr('network')
def test_get_tweet():
    t = Twitter().get_tweet('352056725160988672')
    assert t.id == 352056725160988672
    assert isinstance(t.markdown, unicode)


@attr('network')
def test_unicode_tweet():
    Twitter().get_tweet('351969339991277568')
