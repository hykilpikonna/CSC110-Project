from collect.twitter import tweepy_login, download_user_tweets
from collect.utils import *


if __name__ == '__main__':
    conf = load_config()
    api = tweepy_login(conf)

    download_user_tweets(api, 'voxdotcom')

