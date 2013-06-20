import os
import json

default_conf = {
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


if __name__ == '__main__':
    if not os.path.isfile('config.json'):
        config = json.dumps(default_conf, indent=4, sort_keys=True)
        with open('config.json', 'w') as f:
            f.write(config)

        print 'Created default config in config.json, please edit'
