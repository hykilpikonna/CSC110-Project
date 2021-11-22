import os
from dataclasses import dataclass
from datetime import datetime


@dataclass
class GeneralUser:
    # Username
    username: str
    # A measurement of a user's popularity, such as followers count
    popularity: int
    # Which platform is this user from
    platform: str


@dataclass
class Posting:
    # Which platform did the user post on
    platform: str
    # Username on that platform
    username: str
    # Full text of the post's content
    text: str
    # Popularity of the post
    popularity: int
    # Is it a repost
    repost: bool
    # Date
    date: datetime


