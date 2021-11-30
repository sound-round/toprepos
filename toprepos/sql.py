import sqlite3
from datetime import datetime


def format_date(date):
    # date = '2021-11-30T15:52:49Z'
    format_date = datetime.strptime(date, '%Y-%m-%dT%H:%M:%SZ')
    return format_date


def format_timestamp(timestamp):
    format_date = datetime.strptime(timestamp[:19], '%Y-%m-%d %H:%M:%S')
    return format_date


def create_tables():
    con = sqlite3.connect('cache.db')
    
    with con:
        cur = con.cursor()
        cur.execute('''CREATE TABLE IF NOT EXISTS users (
                id integer PRIMARY KEY AUTOINCREMENT,
                username varchar UNIQUE,
                updated_at timestamp
            );''')

    with con:
        cur = con.cursor()
        cur.execute('''CREATE TABLE IF NOT EXISTS repos (
                id integer PRIMARY KEY AUTOINCREMENT,
                user_id integer REFERENCES users(id),
                repo_id integer,
                name varchar,
                stars integer,
                html_url varchar
            );''')

    con.close()

def get_user_id(cur, username):
    cur.execute('''SELECT id FROM users WHERE username = (?);''', (username,))
    result = cur.fetchone()
    if not result:
        return None
    (user_id,) = result
    return user_id

def cache(username, repos):
    con = sqlite3.connect('cache.db')

    with con:
        cur = con.cursor()
        user_id = get_user_id(cur, username)
    
    if user_id:
        with con:
            cur = con.cursor()
            cur.execute('''DELETE FROM repos WHERE user_id = (?);''', (user_id,))
            cur.execute('''UPDATE users SET updated_at = (?) 
            WHERE username = (?);''', (datetime.utcnow(), username))
    else:
        with con:
            cur = con.cursor()
            cur.execute('''INSERT INTO users (username, updated_at)
                VALUES (?, ?);''', (username, datetime.utcnow()))
            user_id = get_user_id(cur, username)

    with con:
        cur = con.cursor()
        
        for repo in repos:
            values = (
                user_id, repo['id'], repo['name'],
                repo['stars'], repo['html_url'],
            )
            cur.execute('''INSERT INTO repos 
                (user_id, repo_id, name, stars, html_url) 
                VALUES (?, ?, ?, ?, ?);''',  values)

    con.close()


def get_repos(username, date):
    con = sqlite3.connect('cache.db')

    with con:
        cur = con.cursor()
        cur.execute('''SELECT updated_at FROM users WHERE username = (?);''', (username,))
        result = cur.fetchone()
        if not result:
            updated_at = None
        else:
            (updated_at,) = result

    if not updated_at or format_date(date) >= format_timestamp(updated_at):
        con.close()
        return None
    
    with con:
        cur = con.cursor()
        cur.execute('''SELECT repo_id, name, stars, html_url FROM users 
            JOIN repos ON users.id = user_id 
            WHERE username=(?);''', (username,)
        )
        repos = cur.fetchall()

    con.close()
    return repos
