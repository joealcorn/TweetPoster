import os
import json
import sys

import TweetPoster

default_conf = {
    'database': 'tp.db',
    'sentry': {
        'dsn': ''
    },
    'reddit': {
        'username': '',
        'password': '',
    },
    'twitter': {
        'consumer_key': '',
        'consumer_secret': '',
        'access_token': '',
        'access_secret': '',
    },
}


def write_conf(conf):
    config = json.dumps(conf, indent=4, sort_keys=True)
    with open('config.json', 'w') as f:
        f.write(config)


if __name__ == '__main__':
    if not os.path.isfile('config.json'):
        write_conf(default_conf)
        print 'Created default config in config.json, please edit'

    elif 'updateconf' in sys.argv:
        with open('config.json', 'r') as f:
            config = json.loads(f.read())

        default_conf.update(config)
        write_conf(default_conf)

    else:
        TweetPoster.run()
