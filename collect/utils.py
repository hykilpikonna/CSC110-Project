import os

import json5
import tweepy


def load_config() -> dict:
    """
    Load config using JSON5, from either the local file ~/config.json5 or from the environment variable named config.

    :return: Config dictionary object
    """
    if os.path.isfile('config.json5'):
        with open('config.json5', 'r') as f:
            return json5.load(f)
    else:
        return json5.loads(os.getenv('config'))


def tweepy_login(conf: dict) -> tweepy.API:
    """
    Login to tweepy

    :param conf: Config from load_config()
    :return: Tweepy API object
    """
    auth = tweepy.OAuthHandler(conf['consumer_key'], conf['consumer_secret'])
    auth.set_access_token(conf['access_token'], conf['access_secret'])
    api: tweepy.API = tweepy.API(auth)
    return api
