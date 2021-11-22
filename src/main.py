from tabulate import tabulate

from process.twitter_process import load_users_popularity, process_users_popularity
from raw_collect.twitter import tweepy_login
from utils import load_config

if __name__ == '__main__':
    # Load config and create API
    conf = load_config('config.json5')
    api = tweepy_login(conf)

    #####################
    # Data collection - Step C1
    # Download a wide range of users from Twitter using follow-chaining starting from a single user.
    # download_users_start(api, 'sauricat')

    # This task will run for a very very long time to obtain a large dataset of twitter users. If
    # you want to stop the process, you can resume it later using the following line:
    # download_users_resume_progress(api)

    #####################
    # Data processing - Step P1
    # (After step C1) Process the downloaded twitter users by popularity
    users = process_users_popularity()



    # Just curious, who are the 20 most popular individuals on twitter?
    print(tabulate(((u.username, u.popularity) for u in users[:20]), headers=['Name', 'Followers']))

    #####################
    # Data collection - Step C2
    # Download as many posts of the most popular individuals as possible.


