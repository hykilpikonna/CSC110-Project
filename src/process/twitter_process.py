import json
import os
from datetime import datetime
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


def process_users_popularity(user_dir: str = './data/twitter/user/') -> None:
    """
    After downloading a wide range of users using download_users_start in raw_collect/twitter.py,
    this function will read the user files and rank the users by popularity.

    The return format will consist of a list of users' screen names and popularity, which will be
    saved to <user_dir>/processed_popularity.json

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
            users.append(UserPopularity(user['screen_name'], user['followers_count']))

            # Log progress
            if len(users) % 2000 == 0:
                debug(f'Loaded {len(users)} users.')

    # Sort by followers count, descending
    users.sort(key=lambda x: x.popularity, reverse=True)

    # Save data
    write(f'{user_dir}/processed/popularity.json', json_stringify(users, indent=None))


def load_users_popularity(user_dir: str = './data/twitter/user/') -> list[UserPopularity]:
    """
    Load user popularity data after processing in process_users_popularity

    :param user_dir: Download directory of users data, should be the same as the downloads dir in
     download_user_start. (Default: "./data/twitter/user/")
    :return: List of users' screen names and popularity, sorted descending by popularity.
    """
    user_dir = normalize_directory(user_dir)
    with open(f'{user_dir}/processed_popularity.json', 'r', encoding='utf-8') as f:
        return [UserPopularity(*u) for u in json.load(f)]
