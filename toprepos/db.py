import sqlite3
import time
from flask import current_app


LIFETIME = 3600


def create_con():
    return sqlite3.connect(
            current_app.config["DATABASE"]
        )


def create_tables():
    con = create_con()

    with con:
        cur = con.cursor()
        cur.execute(
            '''
            CREATE TABLE IF NOT EXISTS repos (
                username varchar PRIMARY KEY,
                cached_repos text,
                updated_at timestamp
            );'''
        )
    con.close()


def get_user(con, username):
    cur = con.cursor()
    cur.execute(
        '''
        SELECT *
        FROM repos
        WHERE username = (?);
        ''',
        (username,)
    )
    result = cur.fetchall()
    if not result:
        return None
    (user,) = result
    return user


def get_record(con, username):
    cur = con.cursor()
    cur.execute(
        '''
        SELECT cached_repos, updated_at
        FROM repos WHERE username = (?);
        ''',
        (username,)
    )
    record = cur.fetchone()
    return record


def insert_record(con, repos, username):
    cur = con.cursor()
    cur.execute(
        '''
        INSERT INTO repos (username, cached_repos, updated_at)
        VALUES (?, ?, ?);
        ''',
        (username, str(repos), time.time())
    )


def update_record(con, repos, username):
    cur = con.cursor()
    cur.execute(
        '''
        UPDATE repos
        SET cached_repos = (?), updated_at = (?)
        WHERE username = (?);
        ''',
        (str(repos), time.time(), username)
    )


def save_to_cache(username, repos):
    con = create_con()

    with con:
        user = get_user(con, username)

        if user:
            update_record(con, repos, username)
        else:
            insert_record(con, repos, username)

    con.close()


def get_repos(username, repo_updated_at):
    con = create_con()

    record = get_record(con, username)
    if not record:
        con.close()
        return None

    (cached_repos, cache_updated_at) = record

    if repo_updated_at > cache_updated_at\
            or time.time() - cache_updated_at > LIFETIME:
        con.close()
        return None

    con.close()
    return cached_repos
