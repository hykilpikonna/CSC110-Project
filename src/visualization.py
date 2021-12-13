"""
This module uses matplotlib to visualize processed data as graphs. The results are stored in report directory.
The graphs are created after processing the data, for example with filtering and removing outliers.
"""
import os.path
from typing import Optional

import matplotlib.ticker
import scipy.signal
from matplotlib import pyplot as plt, font_manager
import matplotlib.dates as mdates

from constants import RES_DIR
from processing import *
from collect_others import get_covid_cases_us


@dataclass()
class UserFloat:
    """
    Model for which a floating point data is assigned to each user

    This is used for both COVID tweet frequency and popularity ratio data, because both of these
    are floating point data.

    Representation Invariants:
        - self.name != ''

    """
    name: str
    data: float


class Sample:
    """
    A sample of many users, containing statistical data that will be used in graphs.

    Representation Invariants:
        - self.name != ''
        - all(name != '' for name in self.users)

    """
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
        self.date_pops = []

        # Average popularity ratio results over 7 days
        seven_days_user_prs = []

        # Loop through all dates from the start of COVID to when the data is obtained
        for (ds, dt) in daterange('2020-01-01', '2021-11-25'):
            self.dates.append(dt)

            # Calculate date covid popularity ratio
            users_posted_today = [u for u in self.users if u in self.user_date_covid_pop_avg and
                                  ds in self.user_date_covid_pop_avg[u]]
            if len(users_posted_today) == 0:
                seven_days_user_prs.append([])
            else:
                user_prs = [self.user_date_covid_pop_avg[u][ds] / self.user_all_pop_avg[u]
                            for u in users_posted_today if self.user_all_pop_avg[u] != 0]
                seven_days_user_prs.append(user_prs)

            # Average over seven days
            seven_days_count = sum(len(user_prs) for user_prs in seven_days_user_prs)
            if seven_days_count == 0:
                pops_i = 1
            else:
                user_pop_ratio_sum = sum(sum(user_prs) for user_prs in seven_days_user_prs)
                pops_i = user_pop_ratio_sum / seven_days_count

            # More than seven days, remove one
            if len(seven_days_user_prs) > 7:
                seven_days_user_prs.pop(0)

            self.date_pops.append(pops_i)

        # Date frequencies
        self.date_freqs = map_to_dates(self.date_covid_freq,
                                       [x.isoformat()[:10] for x in self.dates])
        self.date_freqs = filter_days_avg(self.date_freqs, 3)


def load_samples() -> list[Sample]:
    """
    Load samples, and report demographics

    :return: Samples
    """
    # Load sample, convert format
    users = load_user_sample()
    samples = [Sample('500-pop', [u.username for u in users.most_popular]),
               Sample('500-rand', [u.username for u in users.random]),
               Sample('eng-news', list(users.english_news))]

    # Report demographics
    keys = ['en', 'zh', 'ja']
    pop_lang = [u.lang for u in users.most_popular]
    rand_lang = [u.lang for u in users.random]
    Reporter('sample-demographics.md')\
        .table([['`500-pop`'] + [str(len(pop_lang))] + [str(pop_lang.count(k)) for k in keys],
                ['`500-rand`'] + [str(len(rand_lang))] + [str(rand_lang.count(k)) for k in keys]],
               ['Total', 'English', 'Chinese', 'Japanese'], False)

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
    font = os.path.join(RES_DIR, 'iosevka-ss04-regular.ttf')
    fe = font_manager.FontEntry(font, 'iosevka')
    font_manager.fontManager.ttflist.insert(0, fe)
    plt.rcParams["font.family"] = "iosevka"


def graph_histogram(x: list[float], path: str, title: str, freq: bool, clear_outliers: bool = False,
                    bins: int = 20) -> None:
    """
    Plot a histogram

    :param x: X axis data
    :param path: Output image path (should end in .png)
    :param title: Title
    :param freq: Whether we are graphing frequencies data instead of popularity ratios
    :param clear_outliers: Remove outliers or not
    :param bins: Number of bins
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

    if freq:
        ax.xaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1))
    else:
        ax.axvline(1, color='#DACAA9')

    # Colors
    ax.tick_params(color=border_color, labelcolor=border_color)
    for spine in ax.spines.values():
        spine.set_edgecolor(border_color)

    # Grid
    ax.grid(visible=True, axis='both')

    # Save
    fig.savefig(os.path.join(REPORT_DIR, path))
    fig.clf()
    plt.close(fig)


def graph_line_plot(x: list[datetime], y: Union[list[float], list[list[float]]], path: str,
                    title: str, freq: bool, n: int = 0, labels: Optional[list[str]] = None) -> None:
    """
    Plot a line plot, and reduce noise using an IIR filter

    :param x: X axis data
    :param y: Y axis data (or Y axis data lines)
    :param n: IIR filter parameter (Ignored if n <= 0)
    :param path: Output image path (should end in .png)
    :param freq: Whether you are graphing frequencies data instead of popularity ratios
    :param title: Title
    :param labels: Labels or none
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
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%m\n%Y'))
    ax.xaxis.set_minor_locator(mdates.MonthLocator(interval=1))
    ax.xaxis.set_minor_formatter(mdates.DateFormatter('%m'))

    if freq:
        # Y axis percent format
        ax.yaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1))

    # Plot
    ax.set_title(title, color=border_color)

    # Plotting single data line
    if isinstance(y[0], float):
        ax.plot(x, y, color='#d4b595')

        if freq:
            # Color below curve
            ax.fill_between(x, y, color='#d4b595')

        else:
            ax.axhline(1, color=border_color)
            ax.set_ylim(0, 2)

    # Plotting multiple data lines
    else:
        fig.set_size_inches(16, 9)
        plt.tight_layout()
        for i in range(len(y)):
            line, = ax.plot(x, y[i])
            if len(labels) > i:
                line.set_label(labels[i])
                ax.legend()

        # Plotting frequency, add in the COVID cases data
        if freq:
            cases = get_covid_cases_us()
            c = map_to_dates(cases.cases, [d.isoformat()[:10] for d in x])
            # c = scipy.signal.savgol_filter(c, 45, 2)
            c = filter_days_avg(c, 7)
            c = scipy.signal.lfilter([1.0 / n] * n, 1, c)

            twin: plt.Axes = ax.twinx()
            twin.plot(x, c, color='#d4b595', label='US COVID-19 Cases')
            twin.set_ylim(bottom=0)

        # Plotting popularity
        else:
            ax.axhline(1, color=border_color)
            ax.set_ylim(0, 2)

    # Colors
    ax.tick_params(color=border_color, labelcolor=border_color)
    ax.tick_params(which='minor', colors='#e1ad6b', labelcolor='#e1ad6b')
    for spine in ax.spines.values():
        spine.set_edgecolor(border_color)

    # Grid
    ax.grid(visible=True, axis='both')

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
    graph_histogram(x, f'freq/{sample.name}-hist-outliers.png', title, True, False, 100)
    x = [p for p in x if p > 0.001]
    graph_histogram(x, f'freq/{sample.name}-hist.png', title, True, True)

    x = [f.data for f in sample.user_pops]
    title = f'Popularity ratio of COVID posts for {sample.name}'
    graph_histogram(x, f'pop/{sample.name}-hist.png', title, False, True)


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
    for n in range(5, 16, 5):
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

    graph_line_plot(samples[0].dates, [s.date_pops for s in samples], 'change/comb/pop.png',
                    'COVID-posting popularity ratio over time for all samples - IIR(10)', False, 10,
                    labels=[s.name for s in samples])
    graph_line_plot(samples[0].dates, [s.date_freqs for s in samples], 'change/comb/freq.png',
                    'COVID-posting frequency over time for all samples - IIR(10)', True, 10,
                    labels=[s.name for s in samples])


if __name__ == '__main__':
    report_all()
    # samples = load_user_sample()
    # combine_tweets_for_sample([u.username for u in samples.most_popular], '500-pop')
    # combine_tweets_for_sample([u.username for u in samples.random], '500-rand')
    # combine_tweets_for_sample(samples.english_news, 'eng-news')

    # tweets = load_combined_tweets('500-pop')
    # print(len(tweets))
    # view_covid_tweets_date(tweets)
