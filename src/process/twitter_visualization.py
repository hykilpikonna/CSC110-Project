"""
TODO: Module Docstring
"""
from datetime import timedelta
from dataclasses import dataclass, field

import scipy.signal
from matplotlib import pyplot as plt, font_manager

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


class Sample:
    name: str
    users: list[str]
    # Total frequencies of all posts for each user across all dates (sorted)
    user_freqs: list[UserFloat]
    # Total popularity ratios of all posts for each user across all dates (sorted)
    user_pops: list[UserFloat]
    # Tweets by all users in a sample (always sorted by date)
    tweets: list[Posting]
    # dates[i] = The i-th day since the first tweet
    dates: list[datetime]
    # date_freqs[i] = Total frequency of all posts from all users in this sample on date[i]
    date_freqs: list[float]
    # date_pops[i] = Average popularity ratio of all posts from all users in this sample on date[i]
    date_pops: list[float]

    def __init__(self, name: str, users: list[str]):
        self.name = name
        self.users = users
        self.calculate_sample_data()

    def calculate_sample_data(self) -> None:
        """
        This function loads and calculates the frequency that a list of user posts about COVID, and
        also calculates their relative popularity of COVID posts.

        This function also creates a combined list of all users in a sample.

        Frequency: the frequency that the sampled users post about COVID. For example, someone who
        posted every single tweet about COVID will have a frequency of 1, and someone who doesn't
        post about COVID will have a frequency of 0.

        Popularity ratio: the relative popularity of the sampled users' posts about COVID. If one
        person posted a COVID post and got 1000 likes, while their other posts (including this
        one) got an average of 1 like, they will have a relative popularity of 1000. If,
        on the other hand, one person posted a COVID post and got 1 like, while their other posts
        (including this one) got an average of 1000 likes, they will have a relative popularity
        of 1/1000.

        To prevent divide-by-zero, we ignored everyone who didn't post about covid and who didn't
        post at all.
        """
        debug(f'Calculating sample tweets data for {self.name}...')
        popularity = []
        frequency = []
        all_tweets: list[Posting] = []
        for i in range(len(self.users)):
            u = self.users[i]

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
        all_tweets.sort(key=lambda x: x.date)

        # Ignore tweets that are earlier than the start of COVID
        all_tweets = [t for t in all_tweets if t.date > '2020-01-01T01:01:01']

        # Assign to sample
        self.user_freqs = frequency
        self.user_pops = popularity
        self.tweets = all_tweets
        debug('- Done.')

    def calculate_change(self) -> None:
        """

        Preconditions:
          - len(self.tweets) > 0
          - self.tweets != None

        :return: None
        """
        # List indicies are days since the first tweet
        covid_count = [0]
        covid_popularity = [0]
        all_count = [0]
        all_popularity = [0]
        current_date = self.tweets[0][:10]
        i = 0

        # Loop through all tweets
        for tweet in self.tweets:
            # Move on to the next date
            tweet_date = tweet.date[:10]
            if tweet_date != current_date:
                current_date = tweet_date
                covid_count.append(0)
                covid_popularity.append(0)
                all_count.append(0)
                all_popularity.append(0)
                i += 1

            # Add current tweet data
            all_count[i] += 1
            all_popularity[i] += tweet.popularity
            if tweet.covid_related:
                covid_count[i] += 1
                covid_popularity[i] += tweet.popularity

        # Calculate frequency and popularity ratio for each date, which will be our y-axis
        self.date_freqs = divide_zeros(covid_count, all_count)
        self.date_pops = divide_zeros(divide_zeros(covid_popularity, covid_count),
                                      divide_zeros(all_popularity, all_count))

        # Convert indicies to dates, which will be our x-axis
        first_date = parse_date(self.tweets[0].date).replace(hour=0, minute=0, second=0)
        dates = [first_date + timedelta(days=j) for j in range(len(all_count))]

        # Find suitable n
        for n in range(1, 20, 3):
            # Reduce noise by averaging results over 7 day frame
            b = [1.0 / n] * n
            a = 1
            f = scipy.signal.lfilter(b, a, self.date_freqs)
            p = scipy.signal.lfilter(b, a, self.date_pops)

            # plt.title(f'COVID-posting frequency over time for {sample.name} with IIR n = {n}')
            # plt.plot(dates, f)
            # plt.show()
            plt.title(f'COVID-posting popularity ratio over time for {self.name} with IIR n = {n}')
            plt.plot(dates, p)
            plt.savefig(f'{REPORT_DIR}/test/{n}.png')
            plt.clf()


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

    return samples


def report_top_20_tables(sample: Sample) -> None:
    """
    Get top-20 most frequent or most relatively popular users and store them in a table.

    :param sample: Sample
    :return: None
    """
    Reporter(f'freq/{sample.name}-top-20.md').table(
        [[u.name, f'{u.data * 100:.1f}%'] for u in sample.user_freqs[:20]],
        ['Username', 'Frequency'])

    Reporter(f'pop/{sample.name}-top-20.md').table(
        [[u.name, f'{u.data * 100:.1f}%'] for u in sample.user_pops[:20]],
        ['Username', 'Popularity Ratio'])


def report_ignored(samples: list[Sample]) -> None:
    """
    Report how many people didn't post about covid or posted less than 1% about COVID across
    different samples.

    And for popularity ratios, report how many people are ignored because they didn't post.

    :param samples: Samples
    :return: None
    """
    # For frequencies, report who didn't post
    table = [["Total users"] + [str(len(s.user_freqs)) for s in samples],
             ["Users who didn't post at all"] +
             [str(len([1 for a in s.user_freqs if a.data == 0])) for s in samples],
             ["Users who posted less than 1%"] +
             [str(len([1 for a in s.user_freqs if a.data < 0.01])) for s in samples]]

    Reporter('freq/didnt-post.md').table(table, [s.name for s in samples], True)

    # For popularity ratio, report ignored
    table = [["Ignored"] + [str(len(s.users) - len(s.user_pops)) for s in samples]]
    Reporter('pop/ignored.md').table(table, [s.name for s in samples], True)


def load_font() -> None:
    """
    Load iosevka font for matplotlib
    """
    font = Path(os.path.realpath(__file__)).absolute().parent.joinpath('iosevka-ss04-regular.ttf')
    fe = font_manager.FontEntry(font, 'iosevka')
    font_manager.fontManager.ttflist.insert(0, fe)
    plt.rcParams["font.family"] = "iosevka"


def report_histogram(x: list[float], path: str, title: str, clear_outliers: bool = False,
                     bins: int = 20, axvline: Union[list[int], None] = None) -> None:
    """
    Plot a histogram

    :param x: X axis data
    :param path: Output image path (should end in .png)
    :param title: Title
    :param clear_outliers: Remove outliers or not
    :param bins: Number of bins
    :param axvline: Vertical line
    :return: None
    """
    if clear_outliers:
        title = title + ' - No Outliers'
        x = remove_outliers(x)

    border_color = '#5b3300'

    # Create fig ax
    fig: plt.Figure
    ax: plt.Axes
    fig, ax = plt.subplots()
    ax.margins(x=0, y=0)

    # Plot
    ax.set_title(title, color=border_color)
    ax.hist(x, bins=bins, color='#ffcccc')

    # Plot lines
    if axvline:
        for line in axvline:
            ax.axvline(line, color='#DACAA9')

    # Colors
    ax.tick_params(color=border_color, labelcolor=border_color)
    for spine in ax.spines.values():
        spine.set_edgecolor(border_color)

    # Save
    fig.savefig(os.path.join(REPORT_DIR, path))


def report_histograms(sample: Sample) -> None:
    """
    Report histograms of COVID posting frequencies and popularity ratios

    :param sample: Sample
    :return: None
    """
    x = [f.data for f in sample.user_freqs]
    title = f'COVID-related posting frequency for {sample.name}'
    report_histogram(x, f'freq/{sample.name}-hist-outliers.png', title, False, 100)
    x = [p for p in x if p > 0.001]
    report_histogram(x, f'freq/{sample.name}-hist.png', title, True)

    x = [f.data for f in sample.user_pops]
    title = f'Popularity ratio of COVID posts for {sample.name}'
    report_histogram(x, f'pop/{sample.name}-hist-outliers.png', title, False, 100, axvline=[1])
    report_histogram(x, f'pop/{sample.name}-hist.png', title, True, axvline=[1])


def report_stats(samples: list[Sample]) -> None:
    """
    Report frequencies and popularity ratios' statistics

    :param samples: Samples
    :return: None
    """
    xs = [[d.data for d in s.user_pops] for s in samples]

    table = tabulate_stats([get_statistics(x) for x in xs])
    Reporter('pop/stats-with-outliers.md').table(table, [s.name for s in samples], True)

    table = tabulate_stats([get_statistics(remove_outliers(x)) for x in xs])
    Reporter('pop/stats.md').table(table, [s.name for s in samples], True)

    xs = [[d.data for d in s.user_freqs if d.data > 0.0005] for s in samples]
    table = tabulate_stats([get_statistics(x) for x in xs], percent=True)
    Reporter('freq/stats.md').table(table, [s.name for s in samples], True)


def view_covid_tweets_date(tweets: list[Posting]):
    # Graph histogram
    plt.title(f'COVID posting dates')
    plt.xticks(rotation=45)
    plt.yticks(rotation=45)
    plt.tight_layout()
    plt.hist([parse_date(t.date) for t in tweets if t.covid_related], bins=40, color='#ffcccc')
    plt.show()


def report_all() -> None:
    """
    Generate all reports
    """
    load_font()

    Path(f'{REPORT_DIR}/freq').mkdir(parents=True, exist_ok=True)
    Path(f'{REPORT_DIR}/pop').mkdir(parents=True, exist_ok=True)

    debug('Loading samples...')
    samples = load_samples()

    print()
    debug('Creating reports...')

    report_ignored(samples)
    report_stats(samples)
    for s in samples:
        report_top_20_tables(s)
        report_histograms(s)


if __name__ == '__main__':
    report_all()
    # samples = load_user_sample()
    # combine_tweets_for_sample([u.username for u in samples.most_popular], '500-pop')
    # combine_tweets_for_sample([u.username for u in samples.random], '500-rand')
    # combine_tweets_for_sample(samples.english_news, 'eng-news')

    # tweets = load_combined_tweets('500-pop')
    # print(len(tweets))
    # view_covid_tweets_date(tweets)
