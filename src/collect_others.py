from dataclasses import dataclass

import requests


@dataclass
class CasesData:
    # cases[date in "YYYY-MM-DD"] = 7-day average of cases around that date
    cases: dict[str, float]
    deaths: dict[str, float]


def get_covid_cases_us() -> CasesData:
    """
    Get the US COVID-19 cases data from https://github.com/nytimes/covid-19-data by New York Times

    :return: Cases data
    """
    url = 'https://raw.githubusercontent.com/nytimes/covid-19-data/master/rolling-averages/us.csv'
    csv = requests.get(url).text.replace('\r\n', '\n').split('\n')[1:]
    data = CasesData(dict(), dict())

    # Parse CSV
    for line in csv:
        split = line.split(',')
        day, cases, deaths = split[0], split[2], split[6]
        data.cases[day] = float(cases)
        data.deaths[day] = float(deaths)
    return data
