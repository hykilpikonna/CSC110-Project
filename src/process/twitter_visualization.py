"""
TODO: Module Docstring
"""
from datetime import timedelta
from dataclasses import dataclass, field

import numpy as np
import scipy.signal
from matplotlib import pyplot as plt, font_manager
import matplotlib.dates as mdates
from matplotlib import cm

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
    # Average popularity of all u's posts
    user_all_pop_avg: dict[str, float]
    # Average popularity of COVID tweets by a specific user on a specific date
    # user_covid_tweets_pop[user][date] = Average popularity of COVID-posts by {user} on {date}
    user_date_covid_pop_avg: dict[str, dict[str, float]]
    # Total COVID-tweets frequency on a specific date for all users.
    date_covid_freq: dict[str, float]
    # dates[i] = The i-th day since the first tweet
    dates: list[datetime]
    # date_freqs[i] = COVID frequency of all posts from all users in this sample on date[i]
    date_freqs: list[float]
    # date_pops[i] = Average popularity ratio of all posts from all users in this sample on date[i]
    date_pops: list[float]

    def __init__(self, name: str, users: list[str]):
        self.name = name
        self.users = users
        self.calculate_sample_data()
        self.calculate_change_data()

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

        Precondition:
          - Downloaded tweets data are sorted by date
        """
        debug(f'Calculating sample tweets data for {self.name}...')
        popularity = []
        frequency = []
        date_covid_count = dict()
        date_all_count = dict()
        self.user_all_pop_avg = dict()
        self.user_date_covid_pop_avg = dict()
        for i in range(len(self.users)):
            u = self.users[i]

            # Show progress
            if i != 0 and i % 100 == 0:
                debug(f'- Calculated {i} users.')

            # Load processed tweet
            tweets = load_tweets(u)
            # Ignore retweets, and ignore tweets that are earlier than the start of COVID
            tweets = [t for t in tweets if not t.repost and t.date > '2020-01-01T01:01:01']
            # Filter covid tweets
            covid = [t for t in tweets if t.covid_related]

            # To prevent divide by zero, ignore people who didn't post at all
            if len(tweets) == 0:
                frequency.append(UserFloat(u, 0))
                continue
            # Calculate the frequency of COVID-related tweets
            freq = len(covid) / len(tweets)
            frequency.append(UserFloat(u, freq))

            # Calculate date fields
            # Assume tweets are sorted
            # tweets.sort(key=lambda x: x.date)
            # Calculate popularity by date
            date_cp_sum = dict()
            date_cp_count = dict()
            for t in tweets:
                d = t.date[:10]

                # For covid popularity on date
                if t.covid_related:
                    if d not in date_cp_sum:
                        date_cp_sum[d] = 0
                        date_cp_count[d] = 0
                    date_cp_sum[d] += t.popularity
                    date_cp_count[d] += 1

                # For frequency on date
                if d not in date_covid_count:
                    date_covid_count[d] = 0
                    date_all_count[d] = 0
                if t.covid_related:
                    date_covid_count[d] += 1
                date_all_count[d] += 1

            self.user_date_covid_pop_avg[u] = \
                {d: date_cp_sum[d] / date_cp_count[d] for d in date_cp_sum}

            # Calculate total popularity ratio for a user
            # To prevent divide by zero, ignore everyone who didn't post about covid
            if len(covid) == 0:
                continue
            # Get the average popularity for COVID-related tweets
            covid_pop_avg = sum(t.popularity for t in covid) / len(covid)
            all_pop_avg = sum(t.popularity for t in tweets) / len(tweets)
            # Save global_avg
            self.user_all_pop_avg[u] = all_pop_avg
            # To prevent divide by zero, ignore everyone who literally have no likes on any post
            if all_pop_avg == 0:
                continue
            # Get the relative popularity
            popularity.append(UserFloat(u, covid_pop_avg / all_pop_avg))

        # Calculate frequency on date
        self.date_covid_freq = {d: date_covid_count[d] / date_all_count[d] for d in date_covid_count}

        # Sort by relative popularity or frequency
        popularity.sort(key=lambda x: x.data, reverse=True)
        frequency.sort(key=lambda x: x.data, reverse=True)

        # Assign to sample
        self.user_freqs = frequency
        self.user_pops = popularity
        debug('- Done.')

    def calculate_change_data(self) -> None:
        """
        This function calculates self.date_freqs and self.date_pops, which are lists that stores the
        frequencies and popularity ratios on each date since the first tweet. This calculation
        ignores users, but instead combines the tweets of the entire sample in the calculation.

        More details about the calculations can be found in the report, or report_document.md

        Preconditions:
          - len(self.tweets) > 0
          - self.tweets != None

        :return: None
        """
        self.dates = []
        self.date_freqs = []
        self.date_pops = []

        # Loop through all dates from the start of COVID to when the data is obtained
        for (ds, dt) in daterange('2020-01-01', '2021-11-25'):
            self.dates.append(dt)

            # Convert date covid freq format
            if ds in self.date_covid_freq:
                self.date_freqs.append(self.date_covid_freq[ds])
            else:
                self.date_freqs.append(0)

            # Calculate date covid popularity ratio
            users_posted_today = [u for u in self.users if u in self.user_date_covid_pop_avg and
                                  ds in self.user_date_covid_pop_avg[u]]
            if len(users_posted_today) != 0:
                user_pop_ratio_sum = sum(self.user_date_covid_pop_avg[u][ds] /
                                         self.user_all_pop_avg[u] for u in users_posted_today
                                         if self.user_all_pop_avg[u] != 0)
                pops_i = user_pop_ratio_sum / len(users_posted_today)

                if pops_i > 20:
                    print('Date: ', ds)
                    for u in users_posted_today:
                        if self.user_all_pop_avg[u] != 0:
                            print('-', u, self.user_date_covid_pop_avg[u][ds] /
                                  self.user_all_pop_avg[u])
            else:
                pops_i = 1
            self.date_pops.append(pops_i)


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
    table = [["Total users"] + [str(len(s.users)) for s in samples],
             ["Users who didn't post at all"] +
             [str(len([1 for a in s.user_freqs if a.data == 0])) for s in samples],
             ["Users who posted less than 1%"] +
             [str(len([1 for a in s.user_freqs if a.data < 0.01])) for s in samples]]

    Reporter('freq/didnt-post.md').table(table, [s.name for s in samples], True)

    # For popularity ratio, report ignored
    table = [["Ignored"] + [str(len(s.users) - len(s.user_pops)) for s in samples]]
    Reporter('pop/ignored.md').table(table, [s.name for s in samples], True)


def graph_load_font() -> None:
    """
    Load iosevka font for matplotlib
    """
    font = Path(os.path.realpath(__file__)).absolute().parent.joinpath('iosevka-ss04-regular.ttf')
    fe = font_manager.FontEntry(font, 'iosevka')
    font_manager.fontManager.ttflist.insert(0, fe)
    plt.rcParams["font.family"] = "iosevka"


def graph_histogram(x: list[float], path: str, title: str, clear_outliers: bool = False,
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
    fig.clf()
    plt.close(fig)


def graph_line_plot(x: list[datetime], y: list[float], path: str, title: str, freq: bool,
                    n: int = 0) -> None:
    """
    Plot a line plot, and reduce noise using an IIR filter

    :param x: X axis data
    :param y: Y axis data
    :param n: IIR filter parameter (Ignored if n <= 0)
    :param path: Output image path (should end in .png)
    :param freq: Whether you are graphing frequencies data instead of popularity ratios
    :param title: Title
    :return: None
    """
    # Filter
    if n > 0:
        b = [1.0 / n] * n
        a = 1
        y = scipy.signal.lfilter(b, a, y)

    border_color = '#5b3300'

    # Create fig ax
    fig: plt.Figure
    ax: plt.Axes
    fig, ax = plt.subplots()
    ax.margins(x=0, y=0)

    # Date format
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d\n%Y'))

    # Plot
    ax.set_title(title, color=border_color)
    ax.plot(x, y, color='#d4b595')

    if freq:
        # Color below curve
        ax.fill_between(x, y, color='#d4b595')

    else:
        ax.axhline(1, color=border_color)

        # # Color by y-value
        # upper = 1.5
        # lower = 0.5
        #
        # y = np.array(y)
        # y_up = np.ma.masked_where(y < upper, y)
        # y_low = np.ma.masked_where(y > lower, y)
        # y_middle = np.ma.masked_where((y < lower) | (y > upper), y)
        #
        # ax.plot(x, y_up, color='green')
        # ax.plot(x, y_middle, color='yellow')
        # ax.plot(x, y_low, color='red')

    # Colors
    ax.tick_params(color=border_color, labelcolor=border_color)
    for spine in ax.spines.values():
        spine.set_edgecolor(border_color)

    # Save
    path = Path(os.path.join(REPORT_DIR, path))
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(str(path))
    fig.clf()
    plt.close(fig)


def report_histograms(sample: Sample) -> None:
    """
    Report histograms of COVID posting frequencies and popularity ratios

    :param sample: Sample
    :return: None
    """
    x = [f.data for f in sample.user_freqs]
    title = f'COVID-related posting frequency for {sample.name}'
    graph_histogram(x, f'freq/{sample.name}-hist-outliers.png', title, False, 100)
    x = [p for p in x if p > 0.001]
    graph_histogram(x, f'freq/{sample.name}-hist.png', title, True)

    x = [f.data for f in sample.user_pops]
    title = f'Popularity ratio of COVID posts for {sample.name}'
    graph_histogram(x, f'pop/{sample.name}-hist-outliers.png', title, False, 100, axvline=[1])
    graph_histogram(x, f'pop/{sample.name}-hist.png', title, True, axvline=[1])


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


def report_change_different_n(sample: Sample) -> None:
    """
    Experiment wth different n values for IIR filter

    :param sample: Sample
    :return: None
    """
    for n in range(1, 15, 3):
        graph_line_plot(sample.dates, sample.date_pops, f'change/n/{n}.png',
                        f'COVID-posting popularity ratio over time for {sample.name} IIR(n={n})',
                        False, n)


def report_change_graphs(sample: Sample) -> None:
    graph_line_plot(sample.dates, sample.date_pops, f'change/pop/{sample.name}.png',
                    f'COVID-posting popularity ratio over time for {sample.name} IIR(10)',
                    False, 10)
    graph_line_plot(sample.dates, sample.date_freqs, f'change/freq/{sample.name}.png',
                    f'COVID-posting frequency over time for {sample.name} IIR(10)',
                    True, 10)
    print(sum(sample.date_pops) / len(sample.dates))


def report_all() -> None:
    """
    Generate all reports
    """
    graph_load_font()

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
        report_change_graphs(s)
    report_change_different_n(samples[0])


if __name__ == '__main__':
    report_all()
    # samples = load_user_sample()
    # combine_tweets_for_sample([u.username for u in samples.most_popular], '500-pop')
    # combine_tweets_for_sample([u.username for u in samples.random], '500-rand')
    # combine_tweets_for_sample(samples.english_news, 'eng-news')

    # tweets = load_combined_tweets('500-pop')
    # print(len(tweets))
    # view_covid_tweets_date(tweets)
