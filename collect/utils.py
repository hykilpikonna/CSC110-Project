import os
from dataclasses import dataclass
from datetime import datetime

import json5


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


@dataclass
class GeneralUser:
    # Username
    username: str
    # A measurement of a user's popularity, such as followers count
    popularity: int
    # Which platform is this user from
    platform: str


@dataclass
class Posting:
    # Which platform did the user post on
    platform: str
    # Username on that platform
    username: str
    # Full text of the post's content
    text: str
    # Popularity of the post
    popularity: int
    # Is it a repost
    repost: bool
    # Date
    date: datetime


def load_config() -> Config:
    """
    Load config using JSON5, from either the local file ~/config.json5 or from the environment variable named config.

    :return: Config object
    """
    if os.path.isfile('config.json5'):
        with open('config.json5', 'r') as f:
            conf = json5.load(f)
    else:
        conf = json5.loads(os.getenv('config'))

    return Config(**conf)


def debug(msg: object) -> None:
    """
    Output a debug message

    :param msg: Message
    """
    print('[DEBUG] ' + str(msg))
