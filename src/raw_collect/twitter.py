import json
import math
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Union

import pytz
import tweepy
from collect.utils import Config, debug, Posting, json_stringify, load_config
from tweepy import API


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
    user: User

    is_quote_status: bool

    retweeted_status: Union[dict, None]
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
    tweets = api.user_timeline(screen_name=screen_name, count=200, tweet_mode='extended',
                               trim_user=True)
    postings = [convert_to_generic(screen_name, t) for t in tweets]

    # Get additional tweets
    while True:
        debug(f'- Got {len(tweets)} tweets, getting additional tweets...')
        additional_tweets = api.user_timeline(screen_name=screen_name, count=200,
                                              tweet_mode='extended', trim_user=True,
                                              max_id=int(tweets[-1].id_str) - 1)
        if len(additional_tweets) == 0:
            debug(f'- Got {len(tweets)} tweets, finished because no more tweets are available.')
            break

        if additional_tweets[-1].created_at < start_date:
            debug(
                f'- Got {len(tweets)} tweets, finished because the earliest tweet in the dataset goes before 2020-01-01.')
            break

        tweets.extend(additional_tweets)
        postings.extend([convert_to_generic(screen_name, t) for t in additional_tweets])

    # Make directory
    dir_raw = './data/twitter_users_raw/'
    dir = './data/twitter_users/'
    Path(dir_raw).mkdir(parents=True, exist_ok=True)
    Path(dir).mkdir(parents=True, exist_ok=True)

    # Store in file
    with open(dir_raw + screen_name + '.json', 'w') as f:
        f.write(json.dumps([t._json for t in tweets], indent=1, ensure_ascii=False))
    with open(dir + screen_name + '.json', 'w') as f:
        f.write(json_stringify(postings))


def download_users(start_point: str, n: float = math.inf, rate_limit: int = 10) -> None:
    """
    This function downloads n twitter users by using a followings-chain.

    Since there isn't an API or a database with all twitter users, we can't obtain a strict list
    of all twitter users, nor can we obtain a list of strictly random or most popular twitter
    users. Therefore, we use the method of follows chaining: we start from a specific individual,
    obtain their followers, and pick 6 random individuals from the followings list. Then, we repeat
    the process for the selected followings: we pick 6 random followings of the 6 random followings
    that we picked.

    In reality, this method will be biased toward individuals that are worthy of following since we
    are picking random followings.

    We will download all user data to /data/twitter/user/<screen_name>.json

    Then, we can obtain a list of all users we have downloaded just by obtaining a list of all
    files under this directory.

    :param start_point: Starting user's screen name.
    :param n: How many users do you want to download? (Set to infinity if you want all the data)
    :param rate_limit: The maximum number of requests per minute.
    :return: None
    """


def convert_to_generic(username: str, tweet: Tweet) -> Posting:
    """
    Convert a twitter's tweet to a generic posting

    :param username: Username (for optimization, because including a user object in every tweet slows computation significantly.)
    :param tweet: Tweet data
    :return: Generic posting
    """
    return Posting('twitter', username,
                   text=tweet.full_text,
                   popularity=tweet.favorite_count + tweet.retweet_count,
                   repost=hasattr(tweet, 'retweeted_status'),
                   date=tweet.created_at)


def get_user_followings_data(api: API, screen_name: str) -> list[str]:
    """
    Get a user's followings - a list of user that a specific user follows.

    We limited the result to 5000 entries because that is the maximum entries per query that the
    twitter API allows. And we think 5000 entries is an enough sample size.

    :param api: Tweepy API
    :param screen_name: The user's screen name
    :return: List of users that the user follows.
    """
    return api.get_friends(screen_name=screen_name, count=5000)


if __name__ == '__main__':
    conf = load_config()
    api = tweepy_login(conf)
    print(json.dumps(get_user_followings(api, "sauricat")))
