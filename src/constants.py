# Constants (The instructors said that we can use global constants here:
# https://piazza.com/class/ksovzjrlsye72f?cid=1664
# They should not end with "/"
DATA_DIR = '../data'
TWEETS_DIR = f'{DATA_DIR}/twitter/user-tweets'
USER_DIR = f'{DATA_DIR}/twitter/user'
REPORT_DIR = './report'

# Debug mode, or developer mode. This affects two things:
# 1. Whether debug messages are outputted
# 2. Whether the web server regenerates the HTML page for every request
DEBUG = True
