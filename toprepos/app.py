import sqlite3
import requests as req
import json
import os
import asyncio
import aiohttp
import time
from toprepos import sql
from flask import Flask, jsonify, request, make_response
from functools import reduce
from urllib.parse import urlparse
from urllib.parse import parse_qs
from dotenv import load_dotenv
from datetime import datetime


load_dotenv()


LOGIN = os.environ.get('LOGIN')
TOKEN = os.environ.get('TOKEN')
KEYS = ('id', 'name', "stargazers_count", 'html_url')
LAST_PAGE_DEFAULT = 1
LIMIT_DEFAULT = 10


app = Flask(__name__)
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = True


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


async def get_page_response(url, params):
    async with aiohttp.ClientSession() as session:
        if not LOGIN or not TOKEN:
            async with session.get(
                url, params=params,
            ) as response:
                return await response.json()

        auth = aiohttp.BasicAuth(
                LOGIN, TOKEN, encoding='utf-8'
        )
        async with session.get(
            url, params=params, auth=auth,
        ) as response:
            return await response.json()


async def get_full_response(url, i, full_response):
    params = {'page': i}
    response = await get_page_response(url, params)
    full_response.append(response)


def get_from_cache(username, updated_at):

    cached_repos = sql.get_repos(username, updated_at)

    if cached_repos:
        sorted_repos = sorted(
            json.loads(cached_repos.replace("'", "\"")),
            key=lambda repo: (-repo['stars'], repo['name']),
        )
        return sorted_repos


def get_from_github(url, response, full_response, last_page):
    if response.links.get('last'):
        last_url = response.links['last']['url']
        parsed_url = urlparse(last_url)
        last_page = int(parse_qs(parsed_url.query)['page'][0])

    requests = [
        get_full_response(
            url, i, full_response
        ) for i in range(1, last_page + 1)
    ]

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    loop.run_until_complete(
        asyncio.gather(*requests, return_exceptions=True)
    )

    flat_full_response = reduce(lambda a, b: a+b, full_response)
    repos = [format_repo(repo) for repo in flat_full_response]
    sorted_repos = sorted(
        repos, key=lambda repo: (-repo['stars'], repo['name'])
    )
    return sorted_repos


def save_to_cache(username, repos):
    try:
        sql.cache(username, repos)
    except sqlite3.Error as e:
        return jsonify('SQLite3 error:', str(e))


def get_first_page(url):
    first_page_params = {'per_page': 1, 'page': 1, 'sort': 'updated'}
    if not LOGIN or not TOKEN:
        return req.get(
            url, params=first_page_params,
        )
    return req.get(
            url, params=first_page_params, auth=(LOGIN, TOKEN),
        )


@app.route('/api/top/<username>', methods=['GET'])
def get_top_repos(username):
    try:
        return get_top_repos_internal(username)
    except req.HTTPError as e:
        response = make_response(
            {
                'status_code': e.response.status_code,
                'name': 'URL not found',
                'description': str(e),
            },
            e.response.status_code
        )
        response.content_type = "application/json"
        return response
    except BaseException as e:
        response = make_response(
            {
                'status_code': 500,
                'name': 'internal server error',
                'description': str(e),
            },
            500
        )
        response.content_type = "application/json"
        return response


def get_top_repos_internal(username):
    start = datetime.now()

    sql.create_tables()

    last_page = LAST_PAGE_DEFAULT
    full_response = []
    url = f'https://api.github.com/users/{username}/repos'
    limit = request.args.get('limit')

    if not limit:
        limit = LIMIT_DEFAULT
    limit = int(limit)

    first_page_response = get_first_page(url)
    first_page_response.raise_for_status()

    content = json.loads(first_page_response.content)
    if not content:
        return jsonify([])

    updated_at = content[0]['updated_at']

    cached_top_repos = get_from_cache(
        username, format_to_unix_time(updated_at)
    )
    if cached_top_repos:

        print('pulled from cache')
        finish = datetime.now()
        res = finish - start

        return jsonify(cached_top_repos[:limit], str(res))

    top_repos = get_from_github(
        url, first_page_response, full_response, last_page,
    )

    save_to_cache(username, top_repos)

    print('cached')
    finish = datetime.now()
    res = finish - start

    return jsonify(top_repos[:limit], str(res))
