"""
TODO: Module Docstring
"""
import random
from typing import NamedTuple
from dataclasses import dataclass

from py7zr import SevenZipFile

from main import DATA_DIR, TWEETS_DIR, USER_DIR
from utils import *


class ProcessedUser(NamedTuple):
    """
    User and popularity.

    We use NamedTuple instead of dataclass because named tuples are easier to serialize in JSON and
    they require much less space in the stored json format because no key info is stored. For
    example, using dataclass, the json for one UserPopularity object will be:
    {"username": "a", "popularity": 1, "num_postings": 1}, while using NamedTuple, the json will be:
    ["a", 1, 1], which saves an entire 42 bytes for each user.
    """
    # Username
    username: str
    # A measurement of a user's popularity, such as followers count
    popularity: int
    # Number of tweets
    num_postings: int
    # Language
    lang: str


def process_users() -> None:
    """
    After downloading a wide range of users using download_users_start in raw_collect/twitter.py,
    this function will read the user files, extract only relevant information defined in the
    ProcessedUser class, and rank the users by popularity.

    This function will save the processed user data to <user_dir>/processed/users.json

    :return: None
    """
    users = []

    # Loop through all the files
    for filename in os.listdir(f'{USER_DIR}/users'):
        # Only check json files and ignore macos dot files
        if filename.endswith('.json') and not filename.startswith('.'):
            # Read
            user = json.loads(read(f'{USER_DIR}/users/{filename}'))

            # Get user language (The problem is, most people's lang field are null, so we have to
            # look at the language of their latest status as well, while they might not have a
            # status field as well!)
            lang = user['lang']
            status_lang = user['status']['lang'] if 'status' in user else None
            if lang is None:
                lang = status_lang

            users.append(ProcessedUser(user['screen_name'], user['followers_count'],
                                       user['statuses_count'], lang))

            # Log progress
            if len(users) % 2000 == 0:
                debug(f'Loaded {len(users)} users.')

    # Sort by followers count, descending
    users.sort(key=lambda x: x.popularity, reverse=True)

    # Save data
    write(f'{USER_DIR}/processed/users.json', json_stringify(users))


def load_users() -> list[ProcessedUser]:
    """
    Load processed user data after process_users

    :return: List of processed users, sorted descending by popularity.
    """
    return [ProcessedUser(*u) for u in json.loads(read(f'{USER_DIR}/processed/users.json'))]


def get_user_popularity_ranking(user: str) -> int:
    """
    Get a user's popularity ranking. This is not used in data analysis, just for curiosity.

    :param user: Username
    :return: User's popularity ranking
    """
    pop = load_users()
    for i in range(len(pop)):
        if pop[i].username == user:
            return i + 1
    return -1


@dataclass()
class Sample:
    """
    This is a data class storing our different samples.
    """
    most_popular: list[ProcessedUser]
    random: list[ProcessedUser]


def select_user_sample() -> None:
    """
    Select our sample of 500 most popular users and 500 random users who meet the criteria. The
    criteria we use is that the user must have at least 150 followers, and must have a number of
    postings in between 1000 and 3250. Analyzing someone who don't post or someone who doesn't have
    enough followers for interaction might not reveal useful information. We also filter based on
    language, because we only know how to identify COVID-related posts in a few languages.

    The result will be stored in <user_dir>/processed/sample.json

    :return: None
    """
    file = f'{USER_DIR}/processed/sample.json'

    # Exists
    if os.path.isfile(file):
        debug(f'There is already a sample generated at {file}. If you want to reselect the'
              f'sample, please delete the existing sample file.')
        return

    # Load users
    users = load_users()

    # Filter by language first
    users = [u for u in users if u.lang is not None and
             any(lang in u.lang for lang in {'en', 'zh', 'ja'})]

    # Find most popular, and exclude them from the random sample
    most_popular = users[:500]
    users = users[500:]

    # Filter by criteria
    filtered = {u for u in users if 150 < u.popularity and 1000 < u.num_postings < 3250}
    debug(f'There are {len(filtered)} users who meets the criteria.')

    # Sample
    sample = random.sample(filtered, 500)

    # Save
    write(file, json_stringify(Sample(most_popular, sample)))


def load_user_sample() -> Sample:
    """
    Load the selected sample

    :return: None
    """
    j = json.loads(read(f'{USER_DIR}/processed/sample.json'))
    return Sample([ProcessedUser(*u) for u in j['most_popular']],
                  [ProcessedUser(*u) for u in j['random']])


class Posting(NamedTuple):
    """
    Posting data stores the processed tweets data, and it contains info such as whether or not a
    tweet is covid-related
    """
    # Full text of the post's content
    covid_related: bool
    # Popularity of the post
    popularity: int
    # Is it a repost
    repost: bool
    # Date
    date: datetime


def process_tweets() -> None:
    """
    Process tweets, reduce the tweets data to only a few fields defined in the Posting class. These
    include whether or not the tweet is covid-related, how popular is the tweet, if it is a repost,
    and its date. The processed tweet does not contain its content.

    If a user's tweets is already processed, this function will skip over that user's data.

    This function will save the processed tweets data to <tweets_dir>/processed/<username>.json

    :return: None
    """
    # Loop through all the files
    for filename in os.listdir(f'{TWEETS_DIR}/user'):
        # Only check json files and ignore macos dot files
        if filename.endswith('.json') and not filename.startswith('.'):
            # Check if already processed
            if os.path.isfile(f'{TWEETS_DIR}/processed/{filename}'):
                continue

            # Read
            tweets = json.loads(read(f'{TWEETS_DIR}/user/{filename}'))
            p = [Posting(is_covid_related(t['full_text']),
                         t['favorite_count'] + t['retweet_count'],
                         'retweeted_status' in t,
                         datetime.strptime(t['created_at'], '%a %b %d %H:%M:%S +0000 %Y'))
                 for t in tweets]

            # Save data
            write(f'{TWEETS_DIR}/processed/{filename}', json_stringify(p))
            debug(f'Processed: {filename}')


def load_tweets(username: str) -> list[Posting]:
    """
    Load tweets for a specific user

    :param username: User's screen name
    :return: User's processed tweets
    """
    return [Posting(*p) for p in json.loads(read(
        os.path.join(TWEETS_DIR, f'processed/{username}.json')))]


def is_covid_related(text: str) -> bool:
    """
    Is a tweet / article covid-related. Currently, this is done through keyword matching. Even
    though we know that not all posts with covid-related words are covid-related posts, this is our
    current best method of classification.

    :param text: Text content
    :return: Whether the text is covid related
    """
    # English
    # We're hesitate to include words like "pandemic" or "vaccine" because they might refer to other
    # pandemics or other vaccines. However, I think we need to include "the pandemic" because many
    # posts refer to covid only as "the pandemic."
    keywords = ['covid', 'the pandemic', 'lockdown', 'spikevax', 'comirnaty', 'vaxzevria',
                'coronavirus', 'moderna', 'pfizer', 'quarantine', 'vaccine', 'social distancing',
                'booster shot']

    # Chinese
    keywords += ['新冠', '疫情', '感染', '疫苗', '隔离']

    # Japanese
    keywords += ['コロナ', '検疫', '三密']

    return any(k in text.lower() for k in keywords)


def pack_data() -> None:
    """
    This function packs processed data and raw data separately.

    :return: None
    """
    packed_dir = f'{DATA_DIR}/packed'
    Path(packed_dir).mkdir(parents=True, exist_ok=True)

    # Pack data for processed.
    debug('Packing data...')
    processed_dirs = ['/twitter/user/meta', '/twitter/user/processed',
                      '/twitter/user-tweets/processed']
    with SevenZipFile(f'{packed_dir}/processed.7z', 'w') as z:
        z: SevenZipFile = z
        for p in processed_dirs:
            debug(f'- Packing {p}')
            z.writeall(DATA_DIR + p)
