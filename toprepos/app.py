import sqlite3
import requests as req
import json
import os
import asyncio
import aiohttp
from toprepos import sql
from flask import Flask, jsonify, request
from functools import reduce
from urllib.parse import urlparse
from urllib.parse import parse_qs
from dotenv import load_dotenv
from datetime import datetime


load_dotenv()


LOGIN = os.environ.get('LOGIN')  # TODO delete
TOKEN = os.environ.get('TOKEN')   # TODO delete
KEYS = ('id', 'name', "stargazers_count", 'html_url')
LAST_PAGE_DEFAULT = 1
LIMIT_DEFAULT = 10


app = Flask(__name__)


def format_repo(repo):
    dict_ = {}
    for key in KEYS:
        if key == 'stargazers_count':
            dict_['stars'] = repo['stargazers_count']
            continue
        dict_[key] = repo[key]
    return dict_


def format_cached_repos(cached_repos):
    repos = []
    for repo in cached_repos:
        dict_ = {}
        dict_['id'] = repo[0]
        dict_['name'] = repo[1]
        dict_['stars'] = repo[2]
        dict_['html_url'] = repo[3]
        repos.append(dict_)
    return repos


async def get_page_response(url, params):
    async with aiohttp.ClientSession() as session:
        async with session.get(
            url, params=params, auth=aiohttp.BasicAuth(
                LOGIN, TOKEN, encoding='utf-8'
            )
        ) as response:
            return await response.json()


async def get_full_response(url, i, full_response):
    params = {'page': i}
    response = await get_page_response(url, params)
    full_response.append(response)


def get_from_cache(username, updated_at):
    try:
        cached_repos = sql.get_repos(username, updated_at)
    except sqlite3.Error as e:
        return jsonify('SQLite3 error:', str(e))
    if cached_repos:
        sorted_repos = sorted(
            json.loads(
                cached_repos.replace("'", "\"")), 
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

    try:
        loop.run_until_complete(
            asyncio.gather(*requests, return_exceptions=True)
        )
    except aiohttp.web.HTTPException as e:
        return jsonify(str(e))

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


@app.route('/api/top/<username>', methods=['GET'])
def get_top_repos(username):
    start = datetime.now()

    sql.create_tables()

    last_page = LAST_PAGE_DEFAULT
    full_response = []
    url = f'https://api.github.com/users/{username}/repos'
    limit = request.args.get('limit')

    if not limit:
        limit = LIMIT_DEFAULT
    limit = int(limit)

    first_page_params = {'per_page': 1, 'page': 1, 'sort': 'updated'}
    try:
        first_page_response = req.get(
            url, params=first_page_params, auth=(LOGIN, TOKEN),
        )
        first_page_response.raise_for_status()
    except req.exceptions.RequestException as e:
        return jsonify(str(e))

    content = json.loads(first_page_response.content)
    if not content:
        return jsonify(content)

    updated_at = content[0]['updated_at']

    cached_top_repos = get_from_cache(username, updated_at)

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
