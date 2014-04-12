import re
import sys
import traceback

from fuzzywuzzy import fuzz
import requests

import TweetPoster
from TweetPoster import rehost

from raven.processors import SanitizePasswordsProcessor


class SanitizeCredentialsProcessor(SanitizePasswordsProcessor):
    FIELDS = frozenset([
        'authorization',
        'password',
        'secret',
        'passwd',
        'token',
        'key',
        'dsn',
    ])


def tweet_in_title(tweet, submission):
    similarity = fuzz.ratio(tweet.text, submission.title)
    if (similarity >= 85 or
            tweet.text.lower() in submission.title.lower()):
        return True
    return False


def canonical_url(url):
    url = url.lower()

    if url.startswith('http://'):
        url = url[7:]
    if url.startswith('https://'):
        url = url[8:]
    if url.startswith('www.'):
        url = url[4:]
    if url.endswith('/'):
        url = url[:-1]
    if url.endswith('.'):
        url = url[:-1]

    url = url.split('/', 1)[0]
    return url


def replace_entities(tweet):
    """
    Rehosts images, expands urls and links
    hashtags and @mentions
    """

    # Link hashtags
    for tag in tweet.entities['hashtags']:
        replacement = u'[#{tag}](https://twitter.com/search?q=%23{tag})'.format(tag=tag['text'])
        tweet.text = tweet.text.replace('#' + tag['text'], replacement)

    # Link mentions
    for mention in tweet.entities['user_mentions']:
        replacement = u'[@{name}](https://twitter.com/{name})'.format(name=mention['screen_name'])
        tweet.text = re.sub('(?i)\@{0}'.format(mention['screen_name']), replacement, tweet.text)

    # Rehost pic.twitter.com images
    if 'media' in tweet.entities:
        # Photos using Twitter's own image sharing
        # will be in here. We need to match an re
        # against urls to grab the rest of them
        for media in tweet.entities['media']:
            if media['type'] != 'photo':
                continue

            imgur = rehost.PicTwitterCom.extract(media['media_url'])
            if not imgur:
                # We still want to unshorten the t.co link
                replacement = '[*pic.twitter.com*]({0})'.format(media['url'])
            else:
                replacement = u'[*pic.twitter.com*]({url}) [^[Imgur]]({imgur})'
                replacement = replacement.format(url=media['media_url'], imgur=imgur)

            tweet.text = tweet.text.replace(media['url'], replacement)

    # Replace t.co with actual urls, unshorten any
    # other urls shorteners and rehost other images
    for url in tweet.entities['urls']:
        # check for redirects
        try:
            # requests will follow any redirects
            # and allow us to check for them
            r = requests.head(url['expanded_url'], allow_redirects=True)
        except requests.exceptions.RequestException:
            sys.stderr.write('Exception when checking url: {0}\n'.format(
                url['expanded_url']
            ))
            traceback.print_exc()
        else:
            if r.history != []:
                url['expanded_url'] = r.url

        replacement = u'[*{canonical}*]({url})'.format(
            canonical=canonical_url(url['expanded_url']),
            url=url['expanded_url']
        )

        # Check if this link is to an image we can rehost
        for host in rehost.ImageHost.__subclasses__():
            if re.match(host.url_re, url['expanded_url']):
                imgur = host().extract(url['expanded_url'])
                if imgur:
                    replacement = replacement + ' [^[Imgur]]({0})'.format(
                        imgur
                    )

        tweet.text = tweet.text.replace(url['url'], replacement)

    return tweet

def sanitize_markdown(unescaped):
    # This prevents newlines breaking out of a markdown quote
    # and also escapes markdown's special characters
    return re.sub(r'([\\`*_{}[\]()#+-.!])', r'\\\\1',
                  '\n>'.join(unescaped.splitlines()))


def tweet_to_markdown(tweet):
    with open(TweetPoster.template_path + 'tweet.txt') as f:
        tweet_template = f.read().decode('utf8')

    # Link hashtags, expand urls, rehost images etc
    tweet = replace_entities(tweet)

    tweet.text = sanitize_markdown(tweet.text)

    return tweet_template.format(**tweet.__dict__)
