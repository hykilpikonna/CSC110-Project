from tabulate import tabulate

from process.twitter_process import *
from raw_collect.twitter import *
from utils import *


if __name__ == '__main__':
    conf = load_config()
    api = tweepy_login(conf)

    users = load_users()[:500]

    # Just curious, who are the 20 most popular individuals on twitter?
    print(tabulate(((u.username, u.popularity) for u in users[:20]), headers=['Name', 'Followers']))

    # Start download
    for u in users:
        download_all_tweets(api, u.username)
