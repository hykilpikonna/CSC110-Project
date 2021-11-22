"""
TODO: Module docstring
"""
import json
import math
import random
import time
from pathlib import Path
from typing import Union, List

import tweepy
from tweepy import API, TooManyRequests, User, Tweet

from process.twitter_process import Posting
from utils import Config, debug, json_stringify, load_config, normalize_directory, \
    calculate_rate_delay


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


def get_tweets(api: API, name: str, rate_delay: float, max_id: Union[int, None]) -> List[Tweet]:
    """
    Get tweets and wait for delay

    :param api: Tweepy API object
    :param name: Screen name
    :param rate_delay: Seconds of delay per request
    :param max_id: Max id of the tweet or none
    :return: Tweets list
    """
    tweets = api.user_timeline(screen_name=name, count=200, tweet_mode='extended', trim_user=True,
                               max_id=max_id)
    time.sleep(rate_delay)
    return tweets


def download_all_tweets(api: API, screen_name: str,
                        base_dir: str = './data/twitter/user-tweets/') -> None:
    """
    Download all tweets from a specific individual to a local folder.

    Data Directory
    --------
    It will download all tweets to ./data/twitter/user-tweets/user/<screen_name>.json

    Twitter API Reference
    --------
    It will be using the API endpoint api.twitter.com/statuses/user_timeline (Documentation:
    https://developer.twitter.com/en/docs/twitter-api/v1/tweets/timelines/api-reference/get-statuses-user_timeline)
    This endpoint has a rate limit of 900 requests / 15-minutes = 60 rpm for user auth, and it has a
    limit of 100,000 requests / 24 hours = 69.44 rpm independent of authentication method. To be
    safe, this function uses a rate limit of 60 rpm.

    :param api: Tweepy API object
    :param screen_name: Screen name of that individual
    :param base_dir: The downloads folder (Default: "./data/twitter/user-tweets/")
    :return: None
    """
    debug(f'Downloading user tweets for {screen_name}')

    # Ensure directories exist
    base_dir = normalize_directory(base_dir) + '/user'
    Path(base_dir).mkdir(parents=True, exist_ok=True)

    # Rate limit for this endpoint is 60 rpm for user auth and 69.44 rpm for app auth.
    rate_delay = calculate_rate_delay(60)

    # Get initial 200 tweets
    tweets = get_tweets(api, screen_name, rate_delay, None)

    # Get additional tweets
    while True:
        # Try to get more tweets
        debug(f'- {screen_name}: {len(tweets)} tweets, downloading additional tweets...')
        additional_tweets = get_tweets(api, screen_name, rate_delay, int(tweets[-1].id_str) - 1)

        # No more tweets
        if len(additional_tweets) == 0:
            debug(f'- {screen_name}: {len(tweets)} tweets, no more tweets are available.')
            break

        # Add tweets to the list
        tweets.extend(additional_tweets)

    # Store in file
    with open(f'{base_dir}/{screen_name}.json', 'w', encoding='utf-8') as f:
        # Even though we are not supposed to use internal fields, there aren't any efficient way of
        # obtaining the json without the field. Using t.__dict__ will include the API object, which
        # is not serializable.
        f.write(json_stringify([t._json for t in tweets]))


def download_users_start(api: API, start_point: str, n: float = math.inf,
                         base_dir: str = './data/twitter/user/') -> None:
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
    It will download all user data to ./data/twitter/user/users/<screen_name>.json
    It will save meta info to ./data/twitter/user/meta/

    Twitter API Reference
    --------
    It will be using the API endpoint api.twitter.com/friends/list (Documentation:
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
    download_users_execute(api, n, base_dir, downloaded,
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
    download_users_execute(api, meta['n'], base_dir,
                           set(meta['downloaded']), set(meta['done_set']),
                           set(meta['current_set']), set(meta['next_set']))


def download_users_execute(api: API, n: float, base_dir: str,
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

    # Rate limit for this API endpoint is 1 request per minute, and rate delay defines how many
    # seconds to sleep for each request.
    rate_delay = calculate_rate_delay(1) + 1

    print("Executing friends-chain download:")
    print(f"- n: {n}")
    print(f"- Requests per minute: 1")
    print(f"- Directory: {base_dir}")
    print(f"- Downloaded: {len(downloaded)}")
    print(f"- Current search set: {len(current_set)}")
    print(f"- Next search set: {len(next_set)}")
    print()

    # Loop until there are enough users
    while len(downloaded) < n:
        # Take a screen name from the current list
        screen_name = current_set.pop()

        try:
            # Get a list of friends.
            friends: List[User] = api.get_friends(screen_name=screen_name, count=200)
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
        screen_names = [(u.screen_name, u.followers_count) for u in friends
                        if u.screen_name not in done_set and not u.protected]

        # Sort by followers count, from least popular to most popular
        screen_names.sort(key=lambda x: x[1])

        # Add 3 random users to the next set
        if len(screen_names) > 3:
            samples = {u[0] for u in random.sample(screen_names, 3)}
        else:
            samples = {u[0] for u in screen_names}

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
                    'current_set': current_set, 'next_set': next_set, 'n': n}
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
    # python_ta.check_all(config={
    #     'max-line-length': 100,
    #     'disable': ['R1705', 'C0200', 'E9998', 'E9999']
    # })

    config = load_config('config.json5')
    tweepy_api = tweepy_login(config)
    # download_users_start(tweepy_api, 'sauricat')
    download_users_resume_progress(tweepy_api)
