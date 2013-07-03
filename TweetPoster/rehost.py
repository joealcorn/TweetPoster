import requests
from bs4 import BeautifulSoup

import TweetPoster


class ImageHost(object):

    url_re = None

    def extract(self, url):
        """
        Takes a URL, rehosts an image and returns a new URL.
        """
        raise NotImplementedError

    @classmethod
    def rehost(self, image_url):
        try:
            r = requests.post(
                'http://api.imgur.com/2/upload.json',
                params={
                    'key': TweetPoster.config['imgur']['key'],
                    'image': image_url
                }
            )
            return r.json()['upload']['links']['original']
        except (ValueError, requests.exceptions.RequestException):
            return None


class PicTwitterCom(object):

    @classmethod
    def extract(self, url):
        if not url.endswith(':large'):
            url = url + ':large'

        return ImageHost.rehost(url)


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
