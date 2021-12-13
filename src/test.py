from process.twitter_process import *
from raw_collect.twitter import *
from utils import *

if __name__ == '__main__':
    # conf = load_config('config.json5')
    # api = tweepy_login(conf)
    # print(json_stringify(api.get_user(screen_name="sauricat")._json, indent=2))

    # keywords = '⚧; mtf; ftm; transgender; 药娘; 🍥; they/them'.split('; ')
    #
    # base_dir = './data/twitter/user'
    #
    # users = []
    #
    # # for f in ['NASAspaceplace.json']:
    # for f in os.listdir(f'{base_dir}/users'):
    #     s = read(f'{base_dir}/users/{f}')
    #     j = json.loads(s)
    #     s = ''.join(j[k] for k in ['name', 'description'])
    #     if any(k in s.lower() for k in keywords):
    #         # print([k in s.lower() for k in keywords])
    #         print(f)
    #         users.append((j['screen_name'], j['name'], j['description'], j['followers_count']))
    #
    # write('trans.json', json_stringify(users, 2))
    # print(len(users))
    # time.sleep(5)

    # print(get_user_popularity_ranking('danieltosh'))

    # for f in os.listdir(f'{USER_DIR}/users'):
    #     os.rename(f, f.lower())

    # combine_tweets_for_sample(['abc', 'wsj'], 'test')

    start = time.time()
    for i in range(1000000):
        dateutil.parser.isoparse('2020-01-01T01:01:01')
    print(f'dateutil.parser.isoparse took {time.time() - start:.2f} seconds')

    start = time.time()
    for i in range(1000000):
        parse_date('2020-01-01T01:01:01')
    print(f'parse_date took {time.time() - start:.2f} seconds')
