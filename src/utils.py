import dataclasses
import inspect
import json
import os
import statistics
from dataclasses import dataclass
from datetime import datetime, date
from pathlib import Path
from typing import Union, NamedTuple

import json5
import numpy as np


@dataclass
class Config:
    # Twitter's official API v1 keys
    consumer_key: str
    consumer_secret: str
    access_token: str
    access_secret: str

    # Twitter's Web API keys
    # Twitter web authentication token, you can get this by inspecting XHR requests
    twitter_web_bearer: str
    # Twitter web cookies file path, you can export cookies using EditThisCookie plugin
    twitter_web_cookies: str
    # Twitter request rate: How many requests per second
    twitter_rate_limit: int

    # Telegram config
    # Telegram bot token
    telegram_token: str
    # Telegram update user id (Who should the bot send updates to?)
    telegram_userid: int


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
        path = '/'.join(file.split('/')[:-1])
        Path(path).mkdir(parents=True, exist_ok=True)

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


class Stats(NamedTuple):
    mean: float
    median: float
    stddev: float


def get_statistics(points: list[float]) -> Stats:
    """
    Calculate statistics for a set of points

    :param points: Input points
    :return: Statistics
    """
    return Stats(statistics.mean(points), statistics.median(points), statistics.stdev(points))


def parse_date(iso: str) -> datetime:
    """
    Parse date faster

    Preconditions:
      - iso is the output of datetime.isoformat() (In a format like "2021-10-20T23:50:14")

    :param iso: Input date
    :return: Datetime object
    """
    params = [iso[:4], iso[5:7], iso[8:10], iso[11:13], iso[14:16], iso[17:19]]
    params = [int(i) for i in params]
    return datetime(*params)


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
