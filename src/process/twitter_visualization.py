"""
TODO: Module Docstring
"""
import statistics
from typing import Any

from matplotlib import pyplot as plt
from tabulate import tabulate

from constants import REPORT_DIR
from process.twitter_process import *


class Reporter:
    """
    Report file creator
    """
    report: str
    file: str

    def __init__(self, file: str) -> None:
        self.report = ''
        self.file = file

    def print(self, line: str = '', arg: Any = None) -> None:
        """
        Add a line to the report

        :param line: Line content
        :param arg: Additional argument
        :return: None
        """
        self.report += line
        if arg is not None:
            self.report += str(arg)
        self.report += '\n'

    def save(self) -> None:
        write(self.file, self.report)


def view_covid_tweets_freq(users: list[str],
                           sample_name: str) -> None:
    """
    Visualize the frequency that the sampled users post about COVID. For example, someone who
    posted every single tweet about COVID will have a frequency of 1, and someone who doesn't
    post about COVID will have a frequency of 0.

    :param users: Sample users
    :param sample_name: Name of the sample
    :return: None
    """
    # Load tweets, and get the frequency of covid tweets for each user
    user_frequency = []
    for u in users:
        # Load processed tweet
        tweets = load_tweets(u)
        # Get the frequency of COVID-related tweets
        freq = len([1 for t in tweets if t.covid_related]) / len(tweets)
        user_frequency.append((u, freq))

    # Sort by frequency
    user_frequency.sort(key=lambda x: x[1], reverse=True)

    # Init reporter
    r = Reporter(f'{REPORT_DIR}/1-covid-tweet-frequency/{sample_name}.md')
    r.print(f"In {sample_name} -")

    # How many people didn't post about COVID?
    r.print("How many people didn't post about COVID:",
            len([a for a in user_frequency if a[1] == 0]))
    r.print("How many people have less than 1% of their posts about COVID:",
          len([a for a in user_frequency if a[1] <= 0.01]))
    r.print()

    # Top 20
    r.print(f"20 Users of who post COVID-related tweets most frequently:")
    r.print(tabulate([[u[0], f'{u[1] * 100:.1f}%'] for u in user_frequency[:20]],
                   ['Username', 'Frequency']))

    # Save report
    r.save()

    # Graph histogram
    plt.title(f'COVID-related posting frequency for {sample_name}')
    plt.xticks(rotation=90)
    plt.tight_layout()
    plt.hist([f[1] for f in user_frequency], bins=100, color='#ffcccc')
    plt.savefig(f'{REPORT_DIR}/1-covid-tweet-frequency/{sample_name}.png')


def view_covid_tweets_pop(users: list[str],
                          sample_name: str) -> None:
    """
    Visualize the relative popularity of the sampled users' posts about COVID. For example, if one
    person posted a COVID post and got 1000 likes, while their other posts (including this one) got
    an average of 1 like, they will have a relative popularity of 1000. If, on the other hand, one
    person posted a COVID post and got 1 like, while their other posts (including this one) got an
    average of 1000 likes, they will have a relative popularity of 1/1000.

    To prevent divide-by-zero, we ignored everyone who didn't post about covid and who didn't post
    at all.

    :param users: Sample users
    :param sample_name: Name of the sample
    :return: None
    """
    user_popularity = load_covid_tweets_pop(users)

    # Init reporter
    r = Reporter(f'{REPORT_DIR}/2-covid-tweet-popularity/{sample_name}.md')
    r.print(f"In {sample_name} -")

    # How many people are ignored
    r.print("To prevent division by zero, we ignored people who didn't post about COVID or didn't "
          f"post at all. We ignored {len(users) - len(user_popularity)} people in this list.")
    r.print()

    # Top 20
    r.print(f"20 Users of whose COVID-related posts are the most popular:")
    r.print(tabulate([[u[0], f'{u[1]:.2f}'] for u in user_popularity[:20]],
                   ['Username', 'Popularity Ratio']))
    r.print()

    # Calculate statistics
    x_list = [f[1] for f in user_popularity]
    s = get_statistics(x_list)
    r.print(f'With outliers, ')
    r.print(f'- mean: {s.mean:.2f}, median: {s.median:.2f}, stddev: {s.stddev:.2f}')
    r.print()

    # Remove outliers
    r.print('As there are many outliers in the popularity ratio, they are removed in graphing.')
    r.print()
    x_list = remove_outliers(x_list)

    # Calculate statistics without outliers
    s = get_statistics(x_list)
    r.print(f'Without outliers, ')
    r.print(f'- mean: {s.mean:.2f}, median: {s.median:.2f}, stddev: {s.stddev:.2f}')
    r.print()

    # Save report
    r.save()

    # Graph histogram
    plt.title(f'COVID-related popularity ratios for {sample_name}')
    plt.xticks(rotation=90)
    plt.tight_layout()
    plt.hist(x_list, bins=40, color='#ffcccc')
    plt.axvline([1], color='lightgray')
    plt.savefig(f'{REPORT_DIR}/2-covid-tweet-popularity/{sample_name}.png')


def load_covid_tweets_pop(users: list[str]):
    """
    Helper function for view_covid_tweets_pop. This function loads and calculates relative
    popularity of COVID posts by a list of users

    :param users: Users in a sample
    :return: List of users and their relative popularity for COVID posts
    """
    user_popularity = []
    for u in users:
        # Load processed tweet
        tweets = load_tweets(u)
        # Ignore retweets
        tweets = [t for t in tweets if not t.repost]
        # Filter covid tweets
        covid = [t for t in tweets if t.covid_related]
        # To prevent divide by zero, ignore everyone who didn't post about covid or who didn't post
        # at all.
        if len(covid) == 0 or len(tweets) == 0:
            continue
        # Get the average popularity for COVID-related tweets
        covid_avg = statistics.mean(t.popularity for t in covid)
        global_avg = statistics.mean(t.popularity for t in tweets)
        # Get the relative popularity
        user_popularity.append((u, covid_avg / global_avg))

    # Sort by relative popularity
    user_popularity.sort(key=lambda x: x[1], reverse=True)
    return user_popularity


def view_covid_tweets_date(tweets: list[Posting]):

    # Graph histogram
    plt.title(f'COVID posting dates')
    plt.xticks(rotation=45)
    plt.yticks(rotation=45)
    plt.tight_layout()
    plt.hist([parse_date(t.date) for t in tweets if t.covid_related], bins=40, color='#ffcccc')
    plt.show()


if __name__ == '__main__':
    sample = load_user_sample()
    view_covid_tweets_freq([u.username for u in sample.most_popular], '500-pop')
    # view_covid_tweets_freq(sample.random, '500-rand')
    # view_covid_tweets_pop(sample.most_popular, '500-pop')
    # view_covid_tweets_pop(sample.random, '500-rand')

    # samples = load_user_sample()
    # combine_tweets_for_sample([u.username for u in samples.most_popular], '500-pop')
    # combine_tweets_for_sample([u.username for u in samples.random], '500-rand')
    # combine_tweets_for_sample(samples.english_news, 'eng-news')

    # tweets = load_combined_tweets('500-pop')
    # print(len(tweets))
    # view_covid_tweets_date(tweets)
