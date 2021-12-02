import sqlite3
from datetime import datetime, timedelta


LIFETIME = timedelta(hours=1)


def format_date(date):
    format_date = datetime.strptime(date, '%Y-%m-%dT%H:%M:%SZ')
    return format_date


def format_timestamp(timestamp):
    format_date = datetime.strptime(timestamp[:19], '%Y-%m-%d %H:%M:%S')
    return format_date


def create_tables():
    con = sqlite3.connect('cache.db')

    with con:
        cur = con.cursor()
        cur.execute('''CREATE TABLE IF NOT EXISTS repos (
                username varchar PRIMARY KEY,
                cached_repos text,
                updated_at timestamp
            );''')


    con.close()


def get_user(cur, username):
    cur.execute(
        '''SELECT * FROM repos WHERE username = (?);''', (username,)
    )
    result = cur.fetchall()
    if not result:
        return None
    (user,) = result
    return user


def cache(username, repos):
    con = sqlite3.connect('cache.db')

    with con:
        cur = con.cursor()
        user = get_user(cur, username)

    if user:
        with con:
            cur = con.cursor()
            cur.execute('''UPDATE repos SET cached_repos = (?), updated_at = (?)
            WHERE username = (?);''', (repos, datetime.utcnow(), username))
    else:
        with con:
            cur = con.cursor()
            cur.execute('''INSERT INTO repos (username, cached_repos, updated_at)
                VALUES (?, ?, ?);''', (username, str(repos), datetime.utcnow()))

    con.close()


def get_repos(username, date):
    con = sqlite3.connect('cache.db')

    with con:
        cur = con.cursor()
        cur.execute(
            '''SELECT updated_at FROM repos WHERE username = (?);''',
            (username,)
        )
        result = cur.fetchone()
        if not result:
            updated_at = None
        else:
            (updated_at,) = result

    repo_updated_at = format_date(date)
    if updated_at:
        cache_updated_at = format_timestamp(updated_at)

    if not updated_at or repo_updated_at > cache_updated_at\
            or datetime.utcnow() - cache_updated_at > LIFETIME:
        con.close()
        return None

    with con:
        cur = con.cursor()
        cur.execute(
            '''SELECT cached_repos FROM repos
            WHERE username=(?);''', (username,)
        )
        (repos,) = cur.fetchone()

    con.close()
    return repos
