

def get_followings_chain(start_point: str, n: int) -> tuple[list[str], list[str]]:
    """
    This function obtains twitter users through a followings chain.

    1. This function tries to obtain a semi-random list of accounts from twitter.

    Since there isn't a database with all twitter users, we can't obtain a strictly random list of
    twitter users. Therefore, we use the method of follows chaining: we start from a specific
    individual, obtain their followers, and pick 6 random individuals from the followings list.
    Then, we repeat the process for the selected followings: we pick 6 random followings of the 6
    random followings that we picked.

    In reality, this method will be biased toward individuals that are worthy of following since
    we are picking random followings.

    2. This function tries to obtain a list of most popular accounts from twitter.

    Again, since there isn't a database with all twitter users and their popularity, we can't
    obtain a definite list of most popular accounts. So, we obtain our best approximation of a
    list of most popular accounts by obtaining

    :param start_point: The starting user of the search
    :param n: How many random individuals in total?
    :return: 1. A list of semi-random individuals, and 2. a list of most popular individuals.
    """



if __name__ == '__main__':
    pass
