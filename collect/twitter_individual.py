from collect.twitter import tweepy_login, get_user_tweets
from collect.utils import *


if __name__ == '__main__':
    conf = load_config()
    api = tweepy_login(conf)

    tweets = get_user_tweets(api, 'voxdotcom')

    print(len(tweets))

