import os

# Constants (The instructors said that we can use global constants here:
# https://piazza.com/class/ksovzjrlsye72f?cid=1664
# They should not end with "/"
from pathlib import Path

DATA_DIR = './data'
TWEETS_DIR = f'{DATA_DIR}/twitter/user-tweets'
USER_DIR = f'{DATA_DIR}/twitter/user'
REPORT_DIR = './report'
# Sources directory. This may be different from the data directory if the running
SRC_DIR = str(Path(os.path.realpath(__file__)).parent)
