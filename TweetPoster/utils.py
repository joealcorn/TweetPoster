import re

from fuzzywuzzy import fuzz


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

    # Replace t.co with actual urls
    for url in tweet.entities['urls']:
        replacement = u'[*{canonical}*]({url})'.format(
            canonical=canonical_url(url['expanded_url']),
            url=url['expanded_url']
        )
        tweet.text = tweet.text.replace(url['url'], replacement)

    return tweet
