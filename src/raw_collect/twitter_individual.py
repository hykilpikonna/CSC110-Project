from raw_collect.twitter import tweepy_login, download_user_tweets
from raw_collect.utils import *


if __name__ == '__main__':
    conf = load_config()
    api = tweepy_login(conf)

    download_user_tweets(api, 'sauricat')

