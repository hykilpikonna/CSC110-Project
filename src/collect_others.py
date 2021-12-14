"""CSC110 Fall 2021 Project
This module uses web requests to collect and process other data we are using in our analysis.
"""

from dataclasses import dataclass

import requests
import python_ta
import python_ta.contracts


@dataclass
class CasesData:
    """
    A dataclass that stores a mapping of date to cases on that day and a mapping of date to deaths
    on that day.

    Attributes:
        - cases: cases[date in "YYYY-MM-DD"] = 7-day average of cases around that date
        - deaths: deaths[date in "YYYY-MM-DD"] = 7-day average of deaths around that date

    Representation Invariants:
        - all(x >= 0 for x in self.cases.values())
        - all(x >= 0 for x in self.deaths.values())
    """
    cases: dict[str, float]
    deaths: dict[str, float]


def get_covid_cases_us() -> CasesData:
    """
    Get the US COVID-19 cases data from https://github.com/nytimes/covid-19-data by New York Times

    :return: Cases data
    """
    url = 'https://raw.githubusercontent.com/nytimes/covid-19-data/master/rolling-averages/us.csv'
    csv = requests.get(url).text.replace('\r\n', '\n').split('\n')[1:]
    data = CasesData({}, {})

    # Parse CSV
    for line in csv:
        split = line.split(',')
        day, cases, deaths = split[0], split[2], split[6]
        data.cases[day] = float(cases)
        data.deaths[day] = float(deaths)
    return data


if __name__ == '__main__':
    python_ta.contracts.check_all_contracts()
    python_ta.check_all(config={
        'extra-imports': ['requests', 'dataclasses'],  # the names (strs) of imported modules
        'allowed-io': [],  # the names (strs) of functions that call print/open/input
        'max-line-length': 100,
        'disable': ['R1705', 'C0200']
    })
