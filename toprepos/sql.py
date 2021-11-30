import sqlite3
from datetime import datetime


def create_tables():
    con = sqlite3.connect('cache.db')
    
    with con:
        cur = con.cursor()
        cur.execute('''CREATE TABLE IF NOT EXISTS users (
                id bigint PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
                username varchar UNIQUE,
                updated_at timestamp
            );''')

    with con:
        cur = con.cursor()
        cur.execute('''CREATE TABLE IF NOT EXISTS repos (
                id bigint PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
                user_id bigint REFERENCES users(id),
                repo_id integer,
                name varchar,
                stars integer,
                html_url varchar,
            );''')

    con.close()

def get_user_id(cur, username):
    cur.execute('''SELECT id FROM users WHERE username = (?);''', username)
    return cur.fetchone()


def cache(username, repos):
    con = sqlite3.connect('cache.db')

    with con:
        cur = con.cursor()
        user_id = get_user_id(cur, username)
    
    if user_id:
        with con:
            cur = con.cursor()
            cur.execute('''DELETE FROM repos WHERE user_id = (?);''', user_id)
            cur.execute('''UPDATE users SET updated_at = (?) 
            WHERE username = (?);''', (datetime.now(), username))
    else:
        with con:
            cur = con.cursor()
            cur.execute('''INSERT INTO users
                VALUES (?, ?);''', (username, datetime.now()))
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
        cur.execute('''SELECT updated_at FROM users WHERE username = (?);''', username)
        updated_date = cur.fetchone()
    
    if not updated_date or date > updated_date:
        con.close()
        return None
    
    with con:
        cur = con.cursor()
        cur.execute('''SELECT repo_id, name, stars, html_url FROM users 
            JOIN repos ON users.id = user_id 
            WHERE username=(?);''', username
        )
        repos = cur.fetchall()
        print('repos:\n', repos)
    con.close()
    return repos
