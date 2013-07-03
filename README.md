TweetPoster
======

TweetPoster is a reddit bot that posts the contents of the submitted tweet (and any parents)
as a comment on the submission itself, as well as rehosts any images.  
It is a replacement for the now-defunct [/u/tweet_poster](http://www.reddit.com/user/tweet_poster).


## Adding an image host

All image hosts must subclass `TweetPoster.rehost.ImageHost`, this allows them to
be automatically picked up when it comes time to rehost an image.

Each image host has two prerequisites:

 1. a `url_re` attribute which will be used to match against a url
 2. an `extract` method that recieves a url

`extract` should return an imgur.com url (obtained using `ImageHost.rehost`) or `None`

An example can be found below, and further examples can be found in [rehost.py](https://github.com/buttscicles/TweetPoster/blob/master/TweetPoster/rehost.py)

```python
class Instagram(ImageHost):

    url_re = 'https?://instagram.com/p/\w+/'

    def extract(self, url):
        try:
            r = requests.get(url)
        except requests.exceptions.RequestException:
            return None

        soup = BeautifulSoup(r.content)
        photo = soup.find("img", class_="photo")['src']
        return self.rehost(photo)
```

## Links
 - [reddit](http://www.reddit.com/user/TweetPoster)
 - [code](https://github.com/buttscicles/TweetPoster)
 - [issues](https://github.com/buttscicles/TweetPoster/issues)
 - [faq](http://www.reddit.com/r/TweetPoster/comments/13relk/faq/)
