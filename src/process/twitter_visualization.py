from matplotlib import pyplot as plt
from tabulate import tabulate

from process.twitter_process import *


def view_covid_tweets_freq(users: list[ProcessedUser],
                           sample_name: str,
                           tweets_dir: str = './data/twitter/user-tweets/') -> None:
    """
    Visualize the frequency that the sampled users post about COVID. For example, someone who
    posted every single tweet about COVID will have a frequency of 1, and someone who doesn't
    post about COVID will have a frequency of 0.

    :param users: Sample users
    :param sample_name: Name of the sample
    :param tweets_dir: Data dir for tweets
    :return: None
    """
    tweets_dir = normalize_directory(tweets_dir)

    # Load tweets, and get the frequency of covid tweets for each user
    user_frequency = []
    for u in users:
        # Load processed tweet
        tweets = load_tweets(tweets_dir, u.username)
        # Get the frequency of COVID-related tweets
        freq = len([1 for t in tweets if t.covid_related]) / len(tweets)
        user_frequency.append((u.username, freq))

    # Sort by frequency
    user_frequency.sort(key=lambda x: x[1], reverse=True)

    # How many people didn't post about COVID?
    print(f"In {sample_name} -")
    print("How many people didn't post about COVID:",
          len([a for a in user_frequency if a[1] == 0]))
    print("How many people have less than 1% of their posts about COVID:",
          len([a for a in user_frequency if a[1] <= 0.01]))
    print()

    # Top 20
    print(f"20 Users of who post COVID-related tweets most frequently:")
    print(tabulate([[u[0], f'{u[1] * 100:.1f}%'] for u in user_frequency[:20]],
                   ['Username', 'Frequency']))

    # Graph histogram
    plt.title(f'COVID-related posting frequency for {sample_name}')
    plt.xticks(rotation=90)
    plt.tight_layout()
    plt.hist([f[1] for f in user_frequency], bins=100, color='#ffcccc')
    plt.show()


if __name__ == '__main__':
    sample = load_user_sample()
    view_covid_tweets_freq(sample.most_popular, '500 most popular Twitter users')
    view_covid_tweets_freq(sample.random, '500 random Twitter users')
