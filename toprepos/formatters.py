from datetime import datetime
import time


KEYS = ('id', 'name', "stargazers_count", 'html_url')


def format_to_unix_time(date):
    format_date = datetime.strptime(date, '%Y-%m-%dT%H:%M:%SZ')
    unix_time = time.mktime(format_date.timetuple())
    return unix_time


def format_repo(repo):
    dict_ = {}
    for key in KEYS:
        if key == 'stargazers_count':
            dict_['stars'] = repo['stargazers_count']
            continue
        dict_[key] = repo[key]
    return dict_
