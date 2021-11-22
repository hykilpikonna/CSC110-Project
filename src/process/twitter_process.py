import json
import os
from dataclasses import dataclass
from datetime import datetime

from utils import normalize_directory


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


def load_users_popularity(user_dir: str = './data/twitter/user/') -> list[tuple[str, int]]:
    """
    After downloading a wide range of users using download_users_start in raw_collect/twitter.py,
    this function will read the user files and rank the users by popularity.

    The return format will consist of a list of users' screen names and popularity.

    :param user_dir: Download directory of users data, should be the same as the downloads dir in
     download_user_start. (Default: "./data/twitter/user/")
    :return: List of users' screen names and popularity, sorted descending by popularity.
    """
    user_dir = normalize_directory(user_dir)
    users = []

    # Loop through all the files
    for filename in os.listdir(user_dir + ''):
        # Only check json files and ignore macos dot files
        if filename.endswith('.json') and not filename.startswith('.'):
            # Read
            with open(filename, 'r', encoding='utf-8') as f:
                user = json.load(f)
                users.append((user['screen_name'], user['followers_count']))

    # Sort by followers count, descending
    users.sort(key=lambda x: x[1])

    # Return
    return users
