import requests

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
        except requests.exceptions.RequestException:
            return None

        return r.json()['upload']['links']['original']


class PicTwitterCom(object):

    @classmethod
    def extract(self, url):
        if not url.endswith(':large'):
            url = url + ':large'

        return ImageHost.rehost(url)
