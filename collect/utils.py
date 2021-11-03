import os
from dataclasses import dataclass

import json5
import tweepy


@dataclass
class Config:
    # Twitter's official API v1 keys
    consumer_key: str
    consumer_secret: str
    access_token: str
    access_secret: str

    # Twitter's Web API keys
    # Twitter web authentication token, you can get this by inspecting XHR requests
    twitter_web_bearer: str
    # Twitter web cookies file path, you can export cookies using EditThisCookie plugin
    twitter_web_cookies: str
    # Twitter request rate: How many requests per second
    twitter_rate_limit: int

    # Telegram config
    # Telegram bot token
    telegram_token: str
    # Telegram update user id (Who should the bot send updates to?)
    telegram_userid: int



def load_config() -> Config:
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
