"""
TODO: Module docstring
"""
import json
import math
import random
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Union

import python_ta
import pytz
import tweepy
from tweepy import API, TooManyRequests, User

from process.twitter_process import Posting
from utils import Config, debug, json_stringify, load_config, normalize_directory


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


def download_users_start(api: API, start_point: str, n: float = math.inf,
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

    Data Directory
    --------
    We will download all user data to ./data/twitter/user/users/<screen_name>.json
    We will save meta info to ./data/twitter/user/meta/

    Twitter API Reference
    --------
    We will be using the API endpoint api.twitter.com/friends/list (Documentation:
    https://developer.twitter.com/en/docs/twitter-api/v1/accounts-and-users/follow-search-get-users/api-reference/get-friends-list)
    This will limit the rate of requests to 15 requests in a 15-minute window, which is one request
    per minute. But it is actually the fastest method of downloading a wide range of users on
    twitter because it can download a maximum of 200 users at a time while the API for downloading
    a single user is limited to only 900 queries per 15, which is only 60 users per minute.

    There is another API endpoint that might do the job, which is api.twitter.com/friends/ids (Doc:
    https://developer.twitter.com/en/docs/twitter-api/v1/accounts-and-users/follow-search-get-users/api-reference/get-friends-ids)
    However, even though this endpoint has a much higher request rate limit, it only returns user
    ids and not full user info.

    Parameters
    --------
    :param api: Tweepy's API object
    :param start_point: Starting user's screen name.
    :param n: How many users do you want to download? (Default: math.inf)
    :param base_dir: The downloads folder (Default: "./data/twitter/user/")
    :param rate_limit: The maximum number of requests per minute. (Default: 1)
    :return: None
    """

    # Set of all the downloaded users' screen names
    downloaded = set()

    # The set of starting users that are queried.
    done_set = set()

    # The set of starting users currently looping through
    current_set = {start_point}

    # The next set of starting users
    next_set = set()

    # Start download
    download_users_execute(api, n, base_dir, rate_limit, downloaded,
                           done_set, current_set, next_set)


def download_users_resume_progress(api: API, base_dir: str = './data/twitter/user/') -> None:
    """
    Resume from started progress

    :param api: Tweepy's API object
    :param base_dir: The downloads folder
    :return: None
    """
    # Open file and read
    with open(f'{base_dir}/meta/meta.json', 'r', encoding='utf-8') as f:
        meta = json.load(f)

    # Resume
    download_users_execute(api, meta['n'], base_dir, meta['rate_limit'],
                           set(meta['downloaded']), set(meta['done_set']),
                           set(meta['current_set']), set(meta['next_set']))


def download_users_execute(api: API, n: float, base_dir: str, rate_limit: int,
                           downloaded: set[str], done_set: set[str],
                           current_set: set[str], next_set: set[str]) -> None:
    """
    Execute download from the given parameters. The download method is defined in the document for
    the download_users function.

    Resume functionality is necessary because twitter limits the rate of get friends list to 15
    requests in a 15-minute window, which is 1 request per minute, so it will take a long time to
    gather enough data, so we don't want to have to start over from the beginning once something
    goes wrong.

    :param api: Tweepy's API object
    :param n: How many users do you want to download?
    :param base_dir: The downloads folder
    :param rate_limit: The maximum number of requests per minute
    :param downloaded: Set of all the downloaded users' screen names
    :param done_set: The set of starting users that are queried
    :param current_set: The set of starting users currently looping through
    :param next_set: The next set of starting users
    :return: None
    """
    base_dir = normalize_directory(base_dir)

    # Ensure directory exists
    Path(f'{base_dir}/users').mkdir(parents=True, exist_ok=True)
    Path(f'{base_dir}/meta').mkdir(parents=True, exist_ok=True)

    # Rate limit delay
    rate_delay = 1 / rate_limit * 60 + 1

    print(f"Executing friends-chain download:")
    print(f"- n: {n}")
    print(f"- Requests per minute: {rate_limit}")
    print(f"- Directory: {base_dir}")
    print(f"- Downloaded: {len(downloaded)}")
    print(f"- Current search set: {current_set}")
    print(f"- Next search set: {len(next_set)}")
    print()

    # Loop until there are enough users
    while len(downloaded) < n:
        # Take a screen name from the current list
        screen_name = current_set.pop()

        try:
            # Get a list of friends.
            friends = api.get_friends(screen_name=screen_name, count=200)
        except TooManyRequests:
            # Rate limited, sleep and try again
            debug('Caught TooManyRequests exception: Rate limited, sleep and try again.')
            time.sleep(rate_delay)
            current_set.add(screen_name)
            continue

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
                        if user.screen_name not in done_set and not user.protected]

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

        # This one is done
        done_set.add(screen_name)

        # Update meta info so that downloading can be continued
        with open(f'{base_dir}/meta/meta.json', 'w', encoding='utf-8') as f:
            meta = {'downloaded': downloaded, 'done_set': done_set,
                    'current_set': current_set, 'next_set': next_set,
                    'n': n, 'rate_limit': rate_limit}
            f.write(json_stringify(meta, indent=None))

        debug(f'Finished saving friends of {screen_name}')
        debug(f'============= Total {len(downloaded)} saved =============')

        # Rate limit
        time.sleep(rate_delay)


def convert_to_generic(username: str, tweet: Tweet) -> Posting:
    """
    Convert a twitter's tweet to a generic posting

    :param username: Username (for optimization, because including a user object in every tweet
    slows computation significantly.)
    :param tweet: Tweet data
    :return: Generic posting
    """
    return Posting('twitter', username,
                   text=tweet.full_text,
                   popularity=tweet.favorite_count + tweet.retweet_count,
                   repost=hasattr(tweet, 'retweeted_status'),
                   date=tweet.created_at)


if __name__ == '__main__':
    python_ta.check_all(config={
        'extra-imports': [],  # the names (strs) of imported modules
        'allowed-io': [],     # the names (strs) of functions that call print/open/input
        'max-line-length': 100,
        'disable': ['R1705', 'C0200']
    })

    # conf = load_config('config.json5')
    # api = tweepy_login(conf)
    # # download_users_start(api, 'sauricat')
    # download_users_resume_progress(api)
