import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Union

import pytz
import tweepy
from tweepy import API
from tweepy.models import Status

from collect.utils import Config, debug


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


def download_user_tweets(api: API, screen_name: str) -> None:
    """
    Download all tweets from a specific individual to a local folder

    :param api: Tweepy API object
    :param screen_name: Screen name of that individual
    :return: None
    """
    debug(f'Getting user tweets for {screen_name}')
    start_date = pytz.UTC.localize(datetime(2020, 1, 1))

    # Get initial 200 tweets
    tweets: list[Status] = api.user_timeline(screen_name=screen_name, count=200, tweet_mode='extended', trim_user=True)

    # Get additional tweets
    while True:
        debug(f'- Got {len(tweets)} tweets, getting additional tweets...')
        additional_tweets: list[Status] = api.user_timeline(screen_name=screen_name, count=200, tweet_mode='extended', trim_user=True,
                                                            max_id=int(tweets[-1].id_str) - 1)
        if len(additional_tweets) == 0:
            debug(f'- Got {len(tweets)} tweets, finished because no more tweets are available.')
            break

        if additional_tweets[-1].created_at < start_date:
            debug(f'- Got {len(tweets)} tweets, finished because the earliest tweet in the dataset goes before 2020-01-01.')
            break

        tweets.extend(additional_tweets)


    # Make directory
    dir = './data/raw_twitter_users/'
    Path(dir).mkdir(parents=True, exist_ok=True)

    # Encode json
    json_output = json.dumps([t._json for t in tweets], indent=4)

    # Store in file
    with open(dir + screen_name + '.json', 'w') as f:
        f.write(json_output)
