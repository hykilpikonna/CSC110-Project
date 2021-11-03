import json
from dataclasses import dataclass
from datetime import datetime
from typing import Union

import demjson as demjson
import json5
import tweepy
from tweepy import API
from tweepy.models import Status

from collect.utils import Config, Posting, debug


@dataclass
class User:
    id: int
    id_str: str
    name: str
    screen_name: str
    location: str
    description: str
    url: str
    entities: dict
    protected: bool
    followers_count: int
    friends_count: int
    listed_count: int
    created_at: datetime
    favourites_count: int
    verified: bool
    statuses_count: int


@dataclass
class Tweet:
    created_at: datetime
    id: int
    id_str: str
    full_text: str
    truncated: bool
    display_text_range: list[int]
    entities: dict[str: list]
    source: str

    in_reply_to_status_id: int
    in_reply_to_status_id_str: str
    in_reply_to_user_id: int
    in_reply_to_user_id_str: str
    in_reply_to_screen_name: str

    geo: str
    coordinates: str

    is_quote_status: bool

    retweet_status: Union[dict, None]
    retweet_count: int
    favorite_count: int


def tweepy_login(conf: Config) -> tweepy.API:
    """
    Login to tweepy

    :param conf: Config from load_config()
    :return: Tweepy API object
    """
    auth = tweepy.OAuthHandler(conf.consumer_key, conf.consumer_secret)
    auth.set_access_token(conf.access_token, conf.access_secret)
    api: tweepy.API = tweepy.API(auth)
    return api


def get_user_tweets(api: API, screen_name: str) -> list[Tweet]:
    """
    Get all tweets from a specific individual

    :param api: Tweepy API object
    :param screen_name: Screen name of that individual
    :return: All tweets
    """
    debug(f'Getting user tweets for {screen_name}')

    tweets: list[Tweet] = api.user_timeline(screen_name=screen_name, count=200, tweet_mode='extended')
    while True:
        debug(f'- Got {len(tweets)} tweets, getting additional tweets...')
        additional_tweets = api.user_timeline(screen_name=screen_name, count=200, tweet_mode='extended', max_id=tweets[-1].id)
        if len(additional_tweets) == 0:
            break
        tweets.extend(additional_tweets)

    debug(f'- Got {len(tweets)} tweets, finished.')
    return tweets
