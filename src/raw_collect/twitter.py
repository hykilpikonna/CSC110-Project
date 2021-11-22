import json
import math
import random
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Union

import pytz
import tweepy
from tweepy import API

from raw_collect.utils import Config, debug, Posting, json_stringify, load_config


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
        f.write(json_stringify([t._json for t in tweets]))
    with open(dir + screen_name + '.json', 'w') as f:
        f.write(json_stringify(postings))


def download_users(api: API, start_point: str, n: float = math.inf,
                   base_dir: str = './data/twitter/user/',
                   rate_limit: int = 1) -> None:
    """
    This function downloads n twitter users by using a friends-chain.

    Since there isn't an API or a database with all twitter users, we can't obtain a strict list
    of all twitter users, nor can we obtain a list of strictly random or most popular twitter
    users. Therefore, we use the method of follows chaining: we start from a specific individual,
    obtain their followers, and pick 6 random individuals from the friends list. Then, we repeat
    the process for the selected friends: we pick 6 random friends of the 6 random friends
    that we picked.

    In reality, this method will be biased toward individuals that are worthy of following since
    "friends" are the list of users that someone followed.

    We will download all user data to ./data/twitter/user/users/<screen_name>.json

    We will save meta info to ./data/twitter/user/meta/

    Then, we can obtain a list of all users we have downloaded just by obtaining a list of all
    files under this directory.

    :param api: Tweepy's API object
    :param start_point: Starting user's screen name.
    :param n: How many users do you want to download? (Default: math.inf)
    :param base_dir: The downloads folder (Default: "./data/twitter/user/")
    :param rate_limit: The maximum number of requests per minute. (Default: 1)
    :return: None
    """

    # Ensure that basedir doesn't ends with /
    if base_dir == '':
        base_dir = '.'
    if base_dir.endswith('/'):
        base_dir = base_dir[:-1]

    # Ensure directory exists
    Path(f'{base_dir}/users').mkdir(parents=True, exist_ok=True)
    Path(f'{base_dir}/meta').mkdir(parents=True, exist_ok=True)

    # Set of all the downloaded users' screen names
    downloaded = set()

    # The set of starting users that are queried.
    done_set = set()

    # The set of starting users currently looping through
    current_set = {start_point}

    # The next set of starting users
    next_set = set()

    # Loop until there are enough users
    while len(downloaded) < n:
        # Rate limit
        time.sleep(1 / rate_limit * 60 + 0.1)

        # Take a screen name from the current list
        screen_name = current_set.pop()

        # Get a list of friends.
        friends = api.get_friends(screen_name=screen_name, count=200)

        # Save users
        for user in friends:
            # This user was not saved, save the user.
            if user not in downloaded:
                # Save user json
                with open(f'{base_dir}/users/{user.screen_name}.json', 'w', encoding='utf-8') as f:
                    f.write(json_stringify(user._json))

                # Add to set
                downloaded.add(user.screen_name)
                # debug(f'- Downloaded {user.screen_name}')

        # Get users and their popularity that we haven't downloaded
        screen_names = [(user.screen_name, user.followers_count) for user in friends
                        if user.screen_name not in done_set]

        # Sort by followers count, from least popular to most popular
        screen_names.sort(key=lambda x: x[1])

        # Add 3 random users to the next set
        if len(screen_names) > 3:
            samples = {n[0] for n in random.sample(screen_names, 3)}
        else:
            samples = {n[0] for n in screen_names}

        # Add 3 most popular users that we haven't downloaded to the next set
        while len(screen_names) > 0 and len(samples) < 6:
            most_popular = screen_names.pop()[0]
            if most_popular not in done_set and most_popular not in samples:
                samples.add(most_popular)

        # Add the selected users to the next set
        for s in samples:
            next_set.add(s)

        # Change name lists
        if len(current_set) == 0:
            current_set = next_set
            next_set = set()

        # Update meta info so that downloading can be continued
        with open(f'{base_dir}/meta/meta.json', 'w', encoding='utf-8') as f:
            meta = {'downloaded': downloaded, 'done_set': done_set,
                    'current_set': current_set, 'next_set': next_set}
            f.write(json_stringify(meta))

        debug(f'Finished saving friends of {screen_name}')
        debug(f'============= Total {len(downloaded)} saved =============')


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


if __name__ == '__main__':
    conf = load_config('config.json5')
    api = tweepy_login(conf)
    download_users(api, 'sauricat')
