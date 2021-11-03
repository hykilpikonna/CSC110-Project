import os

import json5


def load_config() -> dict:
    """
    Load config using JSON5, from either the local file ~/config.json5 or from the environment variable named config.

    :return: Config dictionary object
    """
    if os.path.isfile('config.json5'):
        with open('config.json5', 'r') as f:
            return json5.load(f)
    else:
        return json5.loads(os.getenv('config'))
