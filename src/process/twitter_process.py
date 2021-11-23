import json
import os
import random
from datetime import datetime, time
from typing import NamedTuple

from utils import *


class UserPopularity(NamedTuple):
    """
    User and popularity (we use NamedTuple instead of dataclass because named tuples are easier to
    serialize in JSON and they require much less space in the stored json format because no key info
    is stored).
    """
    # Username
    username: str
    # A measurement of a user's popularity, such as followers count
    popularity: int
    # Number of tweets
    num_postings: int


def process_users_popularity(user_dir: str = './data/twitter/user/') -> None:
    """
    After downloading a wide range of users using download_users_start in raw_collect/twitter.py,
    this function will read the user files and rank the users by popularity.

    The return format will consist of a list of users' screen names and popularity, which will be
    saved to <user_dir>/processed/popularity.json

    :param user_dir: Download directory of users data, should be the same as the downloads dir in
     download_user_start. (Default: "./data/twitter/user/")
    :return: None
    """
    user_dir = normalize_directory(user_dir)
    users = []

    # Loop through all the files
    for filename in os.listdir(f'{user_dir}/users'):
        # Only check json files and ignore macos dot files
        if filename.endswith('.json') and not filename.startswith('.'):
            # Read
            user = json.loads(read(f'{user_dir}/users/{filename}'))
            users.append(UserPopularity(user['screen_name'], user['followers_count'],
                                        user['statuses_count']))

            # Log progress
            if len(users) % 2000 == 0:
                debug(f'Loaded {len(users)} users.')

    # Sort by followers count, descending
    users.sort(key=lambda x: x.popularity, reverse=True)

    # Save data
    write(f'{user_dir}/processed/popularity.json', json_stringify(users))


def load_users_popularity(user_dir: str = './data/twitter/user/') -> list[UserPopularity]:
    """
    Load user popularity data after processing in process_users_popularity

    :param user_dir: Download directory of users data, should be the same as the downloads dir in
     download_user_start. (Default: "./data/twitter/user/")
    :return: List of users' screen names and popularity, sorted descending by popularity.
    """
    user_dir = normalize_directory(user_dir)
    return [UserPopularity(*u) for u in json.loads(read(f'{user_dir}/processed/popularity.json'))]


def get_user_popularity_ranking(user: str, user_dir: str = './data/twitter/user/') -> int:
    """
    Get a user's popularity ranking. This is not used in data analysis, just for curiosity.

    :param user: Username
    :param user_dir: Download directory
    :return: User's popularity ranking
    """
    pop = load_users_popularity(user_dir)
    for i in range(len(pop)):
        if pop[i].username == user:
            return i + 1
    return -1


def select_user_sample(user_dir: str = './data/twitter/user/') -> None:
    """
    Select our sample of 500 most popular users and 500 random users who meet the criteria. The
    criteria we use is that the user must have at least 150 followers, and must have a number of
    postings in between 1000 and 3250. Analyzing someone who don't post or someone who doesn't have
    enough followers for interaction might not reveal useful information.

    The result will be stored in <user_dir>/processed/sample.json

    :param user_dir: Download directory for users
    :return: None
    """
    user_dir = normalize_directory(user_dir)

    # Load users
    users = load_users_popularity(user_dir)

    # Find most popular, and exclude them from the random sample
    most_popular = users[:500]
    users = users[500:]

    # Filter by criteria
    filtered = {u for u in users if 150 < u.popularity and 1000 < u.num_postings < 3250}
    debug(f'There are {len(filtered)} users who meets the criteria.')

    # Sample
    sample = random.sample(filtered, 500)

    # Save
    write(f'{user_dir}/processed/sample.json',
          json_stringify({'most_popular': most_popular, 'random': sample}))

class Posting(NamedTuple):
    """
    Posting data (whether or not a posting is covid-related)
    """
    # Full text of the post's content
    covid_related: bool
    # Popularity of the post
    popularity: int
    # Is it a repost
    repost: bool
    # Date
    date: datetime


def process_tweets(tweets_dir: str = './data/twitter/user-tweets/') -> None:
    """
    Process tweets, reduce the tweets data to only a few fields defined in the Posting class. These
    include whether or not the tweet is covid-related, how popular is the tweet, if it is a repost,
    and its date. The processed tweet does not contain its content.

    If a user's tweets is already processed, this function will skip over that user's data.

    This function will save the processed tweets data to <user_dir>/processed/<username>.json

    :param tweets_dir: Raw tweets directory (Default: './data/twitter/user-tweets/')
    :return:
    """
    tweets_dir = normalize_directory(tweets_dir)

    # Loop through all the files
    for filename in os.listdir(f'{tweets_dir}/user'):
        # Only check json files and ignore macos dot files
        if filename.endswith('.json') and not filename.startswith('.'):
            # Check if already processed
            if os.path.isfile(f'{tweets_dir}/processed/{filename}'):
                continue

            # Read
            tweets = json.loads(read(f'{tweets_dir}/user/{filename}'))
            p = [Posting(is_covid_related(t['full_text']),
                         t['favorite_count'] + t['retweet_count'],
                         'retweeted_status' in t,
                         datetime.strptime(t['created_at'], '%a %b %d %H:%M:%S +0000 %Y'))
                 for t in tweets]

            # Save data
            write(f'{tweets_dir}/processed/{filename}', json_stringify(p))
            debug(f'Processed: {filename}')


def is_covid_related(text: str) -> bool:
    """
    Is a tweet / article covid-related. Currently, this is done through keyword matching. Even
    though we know that not all posts with covid-related words are covid-related posts, this is our
    current best method of classification.

    :param text: Text content
    :return: Whether the text is covid related
    """
    # We cannot include words like "pandemic" or "vaccine" because they might refer to other
    # pandemics or other vaccines. However, I think we need to include "the pandemic" because many
    # posts refer to covid only as "the pandemic".
    keywords = 'covid; the pandemic; lockdown; spikevax; comirnaty; vaxzevria; 疫情'.split('; ')
    return any(k in text.lower() for k in keywords)
