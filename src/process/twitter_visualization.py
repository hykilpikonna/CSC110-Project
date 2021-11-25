"""
TODO: Module Docstring
"""
import os
import statistics
from typing import Any
from dataclasses import dataclass, field

from matplotlib import pyplot as plt, font_manager
from tabulate import tabulate

from constants import REPORT_DIR
from process.twitter_process import *


@dataclass()
class UserFloat:
    """
    Model for which a floating point data is assigned to each user

    This is used for both COVID tweet frequency and popularity ratio data, because both of these
    are floating point data.
    """
    name: str
    data: float


@dataclass()
class Sample:
    name: str
    users: list[str]
    frequencies: list[UserFloat] = field(default_factory=list)
    popularity_ratios: list[UserFloat] = field(default_factory=list)
    # Tweets by all users in a sample
    tweets: list[Posting] = field(default_factory=list)


def load_samples() -> list[Sample]:
    """
    Load samples and calculate their data

    :return: Samples
    """
    # Load sample, convert format
    samples = load_user_sample()
    samples = [Sample('500-pop', [u.username for u in samples.most_popular]),
               Sample('500-rand', [u.username for u in samples.random]),
               Sample('eng-news', list(samples.english_news))]

    # Calculate frequencies and popularity ratios
    for s in samples:
        calculate_sample_data(s)

    return samples


def calculate_sample_data(sample: Sample) -> None:
    """
    This function loads and calculates the frequency that a list of user posts about COVID, and
    also calculates their relative popularity of COVID posts.

    This function also creates a combined list of all users in a sample.

    Frequency: the frequency that the sampled users post about COVID. For example, someone who
    posted every single tweet about COVID will have a frequency of 1, and someone who doesn't
    post about COVID will have a frequency of 0.

    Popularity ratio: the relative popularity of the sampled users' posts about COVID. If one
    person posted a COVID post and got 1000 likes, while their other posts (including this one) got
    an average of 1 like, they will have a relative popularity of 1000. If, on the other hand, one
    person posted a COVID post and got 1 like, while their other posts (including this one) got an
    average of 1000 likes, they will have a relative popularity of 1/1000.

    To prevent divide-by-zero, we ignored everyone who didn't post about covid and who didn't post
    at all.

    :param sample: Sample
    """
    debug(f'Calculating sample tweets data for {sample.name}...')
    popularity = []
    frequency = []
    all_tweets: list[Posting] = []
    for i in range(len(sample.users)):
        u = sample.users[i]

        # Show progress
        if i != 0 and i % 100 == 0:
            debug(f'- Calculated {i} users.')

        # Load processed tweet
        tweets = load_tweets(u)
        # Ignore retweets
        tweets = [t for t in tweets if not t.repost]
        all_tweets += tweets
        # Filter covid tweets
        covid = [t for t in tweets if t.covid_related]

        # To prevent divide by zero, ignore people who didn't post at all
        if len(tweets) == 0:
            continue
        # Calculate the frequency of COVID-related tweets
        freq = len(covid) / len(tweets)
        frequency.append(UserFloat(u, freq))

        # To prevent divide by zero, ignore everyone who didn't post about covid
        if len(covid) == 0:
            continue
        # Get the average popularity for COVID-related tweets
        covid_avg = sum(t.popularity for t in covid) / len(covid)
        global_avg = sum(t.popularity for t in tweets) / len(tweets)
        # To prevent divide by zero, ignore everyone who literally have no likes on any post
        if global_avg == 0:
            continue
        # Get the relative popularity
        popularity.append(UserFloat(u, covid_avg / global_avg))

    # Sort by relative popularity or frequency
    popularity.sort(key=lambda x: x.data, reverse=True)
    frequency.sort(key=lambda x: x.data, reverse=True)

    # Sort by date, latest first
    all_tweets.sort(key=lambda x: x.date, reverse=True)

    # Ignore tweets that are earlier than the start of COVID
    all_tweets = [t for t in all_tweets if t.date > '2020-01-01T01:01:01']

    # Assign to sample
    sample.frequencies = frequency
    sample.popularity_ratios = popularity
    sample.tweets = all_tweets
    debug('- Done.')


def report_top_20_tables(sample: Sample) -> None:
    """
    Get top-20 most frequent or most relatively popular users and store them in a table.

    :param sample: Sample
    :return: None
    """
    r = Reporter(f'freq/{sample.name}-top-20.md')
    r.print(tabulate([[u.name, f'{u.data * 100:.1f}%'] for u in sample.frequencies[:20]],
                     ['Username', 'Frequency'], tablefmt="github"))

    r = Reporter(f'pop/{sample.name}-top-20.md')
    r.print(tabulate([[u.name, f'{u.data * 100:.1f}%'] for u in sample.popularity_ratios[:20]],
                     ['Username', 'Popularity Ratio'], tablefmt="github"))


def report_ignored(samples: list[Sample]) -> None:
    """
    Report how many people didn't post about covid or posted less than 1% about COVID across
    different samples.

    And for popularity ratios, report how many people are ignored because they didn't post.

    :param samples: Samples
    :return: None
    """
    # For frequencies, report who didn't post
    table = [["Didn't post at all"] +
             [str(len([1 for a in s.frequencies if a.data == 0])) for s in samples],
             ["Posted less than 1%"] +
             [str(len([1 for a in s.frequencies if a.data < 0.01])) for s in samples]]

    r = Reporter(f'freq/didnt-post.md')
    r.print(tabulate(table, [s.name for s in samples], tablefmt="github"))

    # For popularity ratio, report ignored
    table = [["Ignored"] + [str(len(s.users) - len(s.popularity_ratios)) for s in samples]]
    r = Reporter(f'pop/ignored.md')
    r.print(tabulate(table, [s.name for s in samples], tablefmt="github"))


def load_font() -> None:
    """
    Load iosevka font for matplotlib
    """
    font = Path(os.path.realpath(__file__)).absolute().parent.joinpath('iosevka-ss04-regular.ttf')
    fe = font_manager.FontEntry(font, 'iosevka')
    font_manager.fontManager.ttflist.insert(0, fe)


def report_histogram(x: list[float], path: str, title: str, clear_outliers: bool = False,
                     bins: int = 40):
    if clear_outliers:
        title = title + ' - No Outliers'
        x = remove_outliers(x)

    border_color = '#5b3300'
    plt.rcParams["font.family"] = "iosevka"
    plt.xticks(rotation=45)
    plt.yticks(rotation=45)
    plt.tight_layout()

    # Create fig ax
    fig: plt.Figure
    ax: plt.Axes
    fig, ax = plt.subplots()

    ax.set_title(title, color=border_color)
    ax.hist(x, bins=bins, color='#ffcccc')

    # Colors
    ax.tick_params(color=border_color, labelcolor=border_color)
    for spine in ax.spines.values():
        spine.set_edgecolor(border_color)

    # Save
    plt.savefig(os.path.join(REPORT_DIR, path))


def report_freq_histogram(sample: Sample) -> None:
    """
    Report histogram of COVID posting frequencies

    :param sample: Sample
    :return: None
    """
    x = [f.data for f in sample.frequencies]
    title = f'COVID-related posting frequency for {sample.name}'
    report_histogram(x, f'freq/{sample.name}-hist-with-outliers.png', title, False, 100)
    report_histogram(x, f'freq/{sample.name}-hist.png', title)


def view_covid_tweets_pop(sample: Sample) -> None:
    """
    :param sample: Sample
    :return: None
    """
    # Init reporter
    r = Reporter(f'{REPORT_DIR}/pop/{sample.name}.md')

    # Calculate statistics
    x_list = [f.data for f in sample.popularity_ratios]
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
    plt.title(f'COVID-related popularity ratios for {sample.name}')
    plt.xticks(rotation=90)
    plt.tight_layout()
    plt.hist(x_list, bins=40, color='#ffcccc')
    plt.axvline([1], color='lightgray')
    plt.savefig(f'{REPORT_DIR}/pop/{sample.name}.png')


def view_covid_tweets_date(tweets: list[Posting]):
    # Graph histogram
    plt.title(f'COVID posting dates')
    plt.xticks(rotation=45)
    plt.yticks(rotation=45)
    plt.tight_layout()
    plt.hist([parse_date(t.date) for t in tweets if t.covid_related], bins=40, color='#ffcccc')
    plt.show()


if __name__ == '__main__':
    load_font()

    Path(f'{REPORT_DIR}/freq').mkdir(parents=True, exist_ok=True)
    Path(f'{REPORT_DIR}/pop').mkdir(parents=True, exist_ok=True)

    debug('Loading samples...')
    samples = load_samples()

    print()
    debug('Creating histograms...')
    for s in samples:
        report_freq_histogram(s)
    # samples = load_user_sample()
    # combine_tweets_for_sample([u.username for u in samples.most_popular], '500-pop')
    # combine_tweets_for_sample([u.username for u in samples.random], '500-rand')
    # combine_tweets_for_sample(samples.english_news, 'eng-news')

    # tweets = load_combined_tweets('500-pop')
    # print(len(tweets))
    # view_covid_tweets_date(tweets)
