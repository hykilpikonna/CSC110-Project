from tabulate import tabulate

from process.twitter_process import *
from raw_collect.twitter import *
from utils import *

if __name__ == '__main__':
    # Load config and create API
    conf = load_config('config.json5')
    api = tweepy_login(conf)

    #####################
    # Data collection - Step C1
    # Download a wide range of users from Twitter using follow-chaining starting from a single user.
    # download_users_start(api, 'voxdotcom')

    # This task will run for a very very long time to obtain a large dataset of twitter users. If
    # you want to stop the process, you can resume it later using the following line:
    # download_users_resume_progress(api)

    #####################
    # Data processing - Step P1
    # (After step C1) Process the downloaded twitter users by popularity
    # process_users_popularity()

    #####################
    # Data collection - Step C2
    # (After step P1) Load the downloaded twitter users by popularity, and start downloading as many
    # tweets from these users as possible.
    # users = load_users_popularity()

    # Just curious, who are the 20 most popular individuals on twitter?
    # print(tabulate(((u.username, u.popularity) for u in users[:20]),
    #                headers=['Name', 'Followers']))

    # Start download
    # for u in users:
    #     download_all_tweets(api, u.username)

    #####################
    # Data processing - Step P2
    # (After step C2) Process the downloaded tweets, determine whether they are covid-related
    process_tweets()
