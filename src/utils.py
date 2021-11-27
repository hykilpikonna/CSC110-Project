import dataclasses
import inspect
import json
import os
import statistics
from dataclasses import dataclass
from datetime import datetime, date, timedelta
from pathlib import Path
from typing import Union, NamedTuple, Any, Generator

import json5
import numpy as np
from tabulate import tabulate

from constants import REPORT_DIR


@dataclass
class Config:
    """
    Secrets configuration for this program.

    Attributes:
      - consumer_key: The consumer key from the Twitter application portal
      - consumer_secret: The consumer secret from the Twitter application portal
      - access_token: The access token of an app from the Twitter application portal
      - access_secret: The access secret of an app from the Twitter application portal

    Representation Invariants:
      - self.consumer_key != ''
      - self.consumer_secret != ''
      - self.access_token != ''
      - self.access_secret != ''
    """
    # Twitter's official API v1 keys
    consumer_key: str
    consumer_secret: str
    access_token: str
    access_secret: str


def load_config(path: str = 'config.json5') -> Config:
    """
    Load config using JSON5, from either the local file ~/config.json5 or from the environment variable named config.

    :param path: Path of the config file (Default: config.json5)
    :return: Config object
    """
    if os.path.isfile(path):
        with open(path, 'r', encoding='utf-8') as f:
            conf = json5.load(f)
    else:
        conf = json5.loads(os.getenv('config'))

    return Config(**conf)


def debug(msg: object) -> None:
    """
    Output a debug message

    :param msg: Message
    """
    caller = inspect.stack()[1].function
    print(f'[DEBUG] {caller}: {msg}')


def calculate_rate_delay(rate_limit: float) -> float:
    """
    Calculate the rate delay for each request given rate limit in request per minute

    :param rate_limit: Rate limit in requests per minute
    :return: Rate delay in seconds per request (added one second just to be safe)
    """
    return 1 / rate_limit * 60


def write(file: str, text: str) -> None:
    """
    Write text to a file

    :param file: File path (will be converted to lowercase)
    :param text: Text
    :return: None
    """
    file = file.lower().replace('\\', '/')

    if '/' in file:
        Path(file).parent.mkdir(parents=True, exist_ok=True)

    with open(file, 'w', encoding='utf-8') as f:
        f.write(text)


def read(file: str) -> str:
    """
    Read file content

    :param file: File path (will be converted to lowercase)
    :return: None
    """
    with open(file.lower(), 'r', encoding='utf-8') as f:
        return f.read()


class Reporter:
    """
    Report file creator

    Attributes:
      - report: The string of the report
      - file: Where the report is stored
    """
    report: str
    file: str

    def __init__(self, file: str) -> None:
        self.report = ''
        self.file = os.path.join(REPORT_DIR, file)

    def print(self, line: str = '', arg: Any = None, autosave: bool = True) -> None:
        """
        Add a line to the report

        :param line: Line content
        :param arg: Additional argument
        :param autosave: Save automatically
        :return: self (this is for call chaining, this way you can call Reporter.print().save()
        """
        self.report += line
        if arg is not None:
            self.report += str(arg)
        self.report += '\n'
        if autosave:
            self.save()

    def save(self) -> None:
        write(self.file, self.report)

    def table(self, table: list[list[str]], headers: list[str], header_code: bool = False) -> None:
        """
        Report a table

        :param table: Table data
        :param headers: Headers
        :param header_code: Whether the headers should be code-formatted
        :return: None
        """
        if header_code:
            headers = [f'`{s}`' for s in headers]
        self.print(tabulate(table, headers, tablefmt='github'))


def remove_outliers(points: list[float], z_threshold: float = 3.5) -> list[float]:
    """
    Create list with outliers removed for graphing

    Credit to: https://stackoverflow.com/a/11886564/7346633

    :param points: Input points list
    :param z_threshold: Z threshold for identifying whether or not a point is an outlier
    :return: List with outliers removed
    """
    x = np.array(points)
    if len(x.shape) == 1:
        x = x[:, None]
    median = np.median(x, axis=0)
    diff = np.sum((x - median) ** 2, axis=-1)
    diff = np.sqrt(diff)
    med_abs_deviation = np.median(diff)

    modified_z_score = 0.6745 * diff / med_abs_deviation

    is_outlier = modified_z_score > z_threshold

    return [points[v] for v in range(len(x)) if not is_outlier[v]]


@dataclass()
class Stats:
    """
    Data class storing the statistics of a sample

    Attributes:
      - mean: The average of the sample
      - stddev: The standard deviation
      - median: The median value of the sample, or the 50th percentile
      - iqr: The interquartile-range (75th percentile - 25th percentile)
      - q25: The first quartile, or the 25th percentile
      - q75: The third quartile, or the 75th percentile
    """
    mean: float
    stddev: float
    median: float
    iqr: float
    q25: float
    q75: float


def get_statistics(points: list[float]) -> Stats:
    """
    Calculate statistics for a set of points

    :param points: Input points
    :return: Statistics
    """
    q75, q25 = np.percentile(points, [75, 25])
    iqr = q75 - q25
    return Stats(statistics.mean(points), statistics.stdev(points), statistics.median(points),
                 iqr, q25, q75)


def tabulate_stats(stats: list[Stats], percent: bool = False) -> list[list[str]]:
    """
    Create a table structure from statistics for tabulate

    :param stats: Statistics
    :param percent: Whether the numbers are percentages
    :return: Table for tabulate
    """
    def num(n: float) -> str:
        return f'{n:.2f}' if not percent else f'{n * 100:.1f}%'

    return [['Mean'] + [num(s.mean) for s in stats],
            ['StdDev'] + [num(s.stddev) for s in stats],
            ['Median'] + [num(s.median) for s in stats],
            ['IQR'] + [num(s.iqr) for s in stats],
            ['Q1 (25%)'] + [num(s.q25) for s in stats],
            ['Q3 (75%)'] + [num(s.q75) for s in stats],
            ]


def parse_date_time(iso: str) -> datetime:
    """
    Parse date faster. Running 1,000,000 trials, this parse_date function is 4.03 times faster than
    python's built-in dateutil.parser.isoparse() function.

    Preconditions:
      - iso is the output of datetime.isoformat() (In a format like "2021-10-20T23:50:14")
      - iso is a valid date (this function does not check for the validity of the input)

    :param iso: Input date
    :return: Datetime object
    """
    return datetime(int(iso[:4]), int(iso[5:7]), int(iso[8:10]),
                    int(iso[11:13]), int(iso[14:16]), int(iso[17:19]))


def parse_date_only(iso: str) -> datetime:
    """
    Parse date faster.

    Preconditions:
      - iso is in the format of "YYYY-MM-DD" (e.g. "2021-10-20")
      - iso is a valid date (this function does not check for the validity of the input)

    :param iso: Input date
    :return: Datetime object
    """
    return datetime(int(iso[:4]), int(iso[5:7]), int(iso[8:10]))


def daterange(start_date: str, end_date: str) -> Generator[tuple[str, datetime], None, None]:
    """
    Date range for looping

    :param start_date: Start date in "YYYY-MM-DD" format
    :param end_date: End date in "YYYY-MM-DD" format
    :return: Generator for looping through the dates one day at a time.
    """
    start = parse_date_only(start_date)
    for n in range(int((parse_date_only(end_date) - start).days)):
        dt = start + timedelta(n)
        yield dt.strftime('%Y-%m-%d'), dt


def map_to_dates(y: dict[str, Union[int, float]], dates: list[str],
                 default: float = 0) -> list[float]:
    """
    Map y axis to date

    Preconditions:
      - The date in dates must be in the same format as the dates in the keys of y

    :param y: Y axis data (in the format y[date] = value)
    :param dates: Dates
    :param default: Default data if y doesn't exist on that date
    :return: A list of y data, one over each day in dates
    """
    return [y[d] if d in y else default for d in dates]


def filter_days_avg(y: list[float], n: int) -> list[float]:
    """
    Filter y by taking an average over a n-days window. If n = 0, then return y without processing.

    Precondition:
      - n % 2 == 1
      - len(y) > 0

    :param y: Values
    :param n: Number of days, must be odd
    :return: Averaged data
    """
    if n <= 1:
        return y
    if n % 2 != 1:
        ValueError(f'n must be odd (you entered {n})')

    # Calculate
    results = []
    buffer = [y[0] * n // 2]

    for i in range(len(y)):
        buffer.append(y[i])
        results.append(sum(buffer) / len(buffer))

        # Queue longer than n days, remove first
        if len(buffer) > n:
            buffer.pop(0)
    return results


def divide_zeros(numerator: list[float], denominator: list[float]) -> list[float]:
    """
    Divide two lists of floats, ignoring zeros (anything dividing by zero will produce zero)

    Preconditions:
      - len(numerator) == len(denominator)

    :param numerator: Numerator
    :param denominator: Denominator
    :return: A list where list[i] = numerator[i] / denominator[i]
    """
    output = np.zeros(len(numerator), float)
    for i in range(len(numerator)):
        if denominator[i] == 0:
            output[i] = 0
        else:
            output[i] = numerator[i] / denominator[i]
    # This marks it as incorrect type but it's actually not incorrect type, just because numpy
    # doesn't specify its return types
    return output.tolist()


class EnhancedJSONEncoder(json.JSONEncoder):
    def default(self, o):

        # Support encoding dataclasses
        # https://stackoverflow.com/a/51286749/7346633
        if dataclasses.is_dataclass(o):
            return dataclasses.asdict(o)

        # Support encoding datetime
        if isinstance(o, (datetime, date)):
            return o.isoformat()

        # Support for sets
        # https://stackoverflow.com/a/8230505/7346633
        if isinstance(o, set):
            return list(o)

        return super().default(o)


def json_stringify(obj, indent: Union[int, None] = None) -> str:
    """
    Serialize json string with support for dataclasses and datetime and sets and with custom
    configuration.

    :param obj: Objects
    :param indent: Indent size or none
    :return: Json strings
    """
    return json.dumps(obj, indent=indent, cls=EnhancedJSONEncoder, ensure_ascii=False)
