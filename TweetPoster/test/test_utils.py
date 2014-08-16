import httpretty

from TweetPoster.utils import (
    canonical_url,
    replace_entities,
    sanitize_markdown,
)


class FakeTweet(object):

    def __init__(self, **kw):
        self.entities = {
            'hashtags': [],
            'symbols': [],
            'user_mentions': [],
            'urls': [],
        }

        for key, val in kw.items():
            setattr(self, key, val)

        if 'text' in kw:
            for word in kw['text'].split(' '):
                if word[0] == '#':
                    self.entities['hashtags'].append(dict(text=word[1:]))

                elif word[0] == '@':
                    self.entities['user_mentions'].append(dict(screen_name=word[1:]))

                elif word.startswith('http'):
                    self.entities['urls'].append({
                        'url': word,
                        'expanded_url': 'https://github.com/buttscicles/TweetPoster'
                    })


def mock_redirect():
    httpretty.register_uri(
        httpretty.HEAD,
        'https://github.com/buttscicles/TweetPoster',
        location='http://yl.io',
        status=301,
    )

    httpretty.register_uri(
        httpretty.HEAD,
        'http://yl.io',
    )


@httpretty.activate
def test_replace_entities():
    t = replace_entities(FakeTweet(text='#hashtag'))
    assert t.text == '[#hashtag](https://twitter.com/search?q=%23hashtag)'

    t = replace_entities(FakeTweet(text='@username'))
    print t.text
    assert t.text == '[@username](https://twitter.com/username)'

    httpretty.register_uri(
        httpretty.HEAD,
        'https://github.com/buttscicles/TweetPoster',
    )

    t = replace_entities(FakeTweet(text='https://t.co/1'))
    assert t.text == '[*github.com*](https://github.com/buttscicles/TweetPoster)'

    mock_redirect()

    t = replace_entities(FakeTweet(text='http'))
    assert t.text == '[*yl.io*](http://yl.io)'


def test_canonical():
    u = canonical_url('https://github.com.')
    assert u == 'github.com'

    u = canonical_url('https://www.github.com/')
    assert u == 'github.com'

    u = canonical_url('github.com/buttscicles')
    assert u == 'github.com'

    u = canonical_url('http://example.com')
    assert u == 'example.com'


def test_sanitize_markdown():
    s = sanitize_markdown('[link](http://believe.in)')
    assert s == '\[link\]\(http://believe\.in\)'

    s = sanitize_markdown('>some quote')
    assert s == '\>some quote'

    s = sanitize_markdown('*bold*')
    assert s == '\*bold\*'

    s = sanitize_markdown('_bold_')
    assert s == '\_bold\_'

