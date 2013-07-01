import time
from os import path

import httpretty

from TweetPoster import Database, config
from TweetPoster.reddit import Redditor

json_dir = path.dirname(path.realpath(__file__)) + '/json/'
config.update({
    'database': ':memory:'
})

login_url = 'https://ssl.reddit.com/api/login'
comment_url = 'http://www.reddit.com/api/comment'
twitter_posts_url = 'http://www.reddit.com/domain/twitter.com/new.json'


def mock_login():
    f = open(json_dir + 'reddit_login.json')
    body = f.read()
    f.close()

    httpretty.register_uri(
        httpretty.POST,
        login_url,
        body=body,
        content_type='application/json',
        set_cookie='reddit_session=nom; Domain=reddit.com; Path=/; HttpOnly',
    )


def mock_comment():
    f = open(json_dir + 'reddit_comment.json')
    body = f.read()
    f.close()

    httpretty.register_uri(
        httpretty.POST,
        comment_url,
        body=body,
        content_type='application/json'
    )


def mock_index():
    httpretty.register_uri(
        httpretty.GET,
        'http://www.reddit.com'
    )


def mock_posts():
    f = open(json_dir + 'reddit_twitter_posts.json')
    body = f.read()
    f.close()

    httpretty.register_uri(
        httpretty.GET,
        twitter_posts_url,
        body=body,
        content_type='application/json'
    )


@httpretty.activate
def test_ratelimit():
    mock_index()
    url = 'http://www.reddit.com/'
    r = Redditor()
    start = time.time()
    r.get(url)
    r.get(url)
    end = time.time()
    assert end - start > 2


@httpretty.activate
def test_login():
    mock_login()
    r = Redditor(bypass_ratelimit=True)
    r.login('TweetPoster', 'hunter2')
    req = httpretty.last_request()

    assert r.authenticated
    assert 'api_type=json' in req.body
    assert 'passwd=hunter2' in req.body
    assert 'user=TweetPoster' in req.body
    assert 'nom' == r.session.cookies['reddit_session']


@httpretty.activate
def test_comment():
    mock_login()
    mock_comment()

    thing_id = 't3_1hb15l'
    comment = 'test comment'

    r = Redditor(bypass_ratelimit=True).login('tp', 'hunter2')
    c = r.comment(thing_id, comment)

    thing = c.json()['json']['data']['things'][0]
    assert comment == thing['data']['contentText']
    assert thing_id == thing['data']['parent']


@httpretty.activate
def test_useragent():
    mock_index()
    r = Redditor(bypass_ratelimit=True)
    r.get('http://www.reddit.com')
    h = httpretty.last_request().headers
    assert r.headers['User-Agent'] == h['User-Agent']


@httpretty.activate
def test_get_new():
    mock_posts()
    db = Database()
    db.init(clean=True)
    r = Redditor(bypass_ratelimit=True)
    all_posts = r.get_new_posts(db)
    assert len(all_posts) == 15

    # Mark some as processed
    for i, p in enumerate(all_posts):
        if i % 5 == 0:
            p.mark_as_processed(db)

    # Now check if only returns new ones
    posts = r.get_new_posts(db)
    assert len(posts) == 12
