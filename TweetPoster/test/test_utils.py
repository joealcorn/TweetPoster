from TweetPoster.utils import (
    canonical_url,
    replace_entities,
)


class FakeTweet(object):
    entities = {
        'hashtags': [],
        'symbols': [],
        'user_mentions': [],
        'urls': [],
    }

    def __init__(self, **kw):
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


def test_replace_entities():
    t = replace_entities(FakeTweet(text='#hashtag'))
    assert t.text == '[#hashtag](https://twitter.com/search?q=%23hashtag)'

    t = replace_entities(FakeTweet(text='@username'))
    print t.text
    assert t.text == '[@username](https://twitter.com/username)'

    t = replace_entities(FakeTweet(text='https://t.co/1'))
    assert t.text == '[*github.com*](https://github.com/buttscicles/TweetPoster)'


def test_canonical():
    u = canonical_url('https://github.com.')
    assert u == 'github.com'

    u = canonical_url('https://www.github.com/')
    assert u == 'github.com'

    u = canonical_url('github.com/buttscicles')
    assert u == 'github.com'

    u = canonical_url('http://example.com')
    assert u == 'example.com'
