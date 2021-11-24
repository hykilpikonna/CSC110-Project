from tabulate import tabulate

from process.twitter_process import *
from raw_collect.twitter import *
from utils import *


if __name__ == '__main__':
    # Load config and create API
    conf = load_config('config.json5')
    api = tweepy_login(conf)

    #####################
    # Data collection - Step C1.1
    # Download a wide range of users from Twitter using follow-chaining starting from a single user.
    # download_users_start(api, 'voxdotcom')

    # This task will run for a very very long time to obtain a large dataset of twitter users. If
    # you want to stop the process, you can resume it later using the following line:
    # download_users_resume_progress(api)

    ####################
    # Data collection - Step C1.2
    # Download all tweets from twitternews
    download_all_tweets(api, 'twitternews')

    #####################
    # Data processing - Step P1
    # (After step C1) Process the downloaded twitter users, extract screen name, popularity, and
    # number of tweets data.
    # process_users()

    #####################
    # Data processing - Step P2
    # (After step P1) Select 500 most popular users and 500 random users who meet a particular
    # criteria as our sample, also find news channels
    # select_user_sample()

    # Just curious, who are the 20 most popular individuals on twitter?
    # print(tabulate(((u.username, u.popularity) for u in load_user_sample().most_popular[:20]),
    #                headers=['Name', 'Followers']))

    #####################
    # Data collection - Step C2.1
    # (After step P2) Load the downloaded twitter users by popularity, and start downloading all
    # tweets from 500 of the most popular users. Takes around 2 hours.
    # for u in load_user_sample().most_popular:
    #     download_all_tweets(api, u.username)

    #####################
    # Data collection - Step C2.2
    # (After step P2) Download all tweets from the 500 randomly selected users, takes around 2 hours
    # for u in load_user_sample().random:
    #     download_all_tweets(api, u.username)

    #####################
    # Data processing - Step P3
    # (After step C2) Process the downloaded tweets, determine whether they are covid-related
    # process_tweets()

    ####################
    # Data Visualization - Step V1
    # Meta-data visualization: Let's see some data about the sample

    # Who posted the most covid tweets? (covid vs non-covid ratio)
    # - Graph histogram of this ratio

    # Who has the most covid tweet popularity (popularity of covid vs non-covid tweets ratio)
    # - Graph histogram of this ratio

    ####################
    # Finalize the program for submission.
    # Pack processed and unprocessed data:
    # pack_data()
