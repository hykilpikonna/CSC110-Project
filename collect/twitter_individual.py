import os

import json5
import tweepy
from tweepy.models import Status

from collect.utils import *


if __name__ == '__main__':
    conf = load_config()
    api = tweepy_login(conf)

    tweets: list[Status] = api.user_timeline(screen_name='voxdotcom', count=200, tweet_mode = 'extended')

    for tweet in tweets:
        print(tweet._json)

