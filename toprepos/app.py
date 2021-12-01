#!/usr/bin/env python3
import requests as req
import json
import os
import asyncio
import aiohttp
from toprepos import sql
from flask import Flask
from flask import request
from flask import jsonify
from functools import reduce
from urllib.parse import urlparse
from urllib.parse import parse_qs
from dotenv import load_dotenv
from datetime import datetime


MY_NAME = 'sound-round'
TOKEN = os.environ.get('TOKEN')
KEYS = ('id', 'name', "stargazers_count", 'html_url')
LAST_PAGE_DEFAULT = 1
LIMIT_DEFAULT = 10


load_dotenv()
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
                MY_NAME, TOKEN, encoding='utf-8'
            )
        ) as response:
            return await response.json()


async def get_full_response(url, i, full_response):
    params = {'page': i}
    response = await get_page_response(url, params)
    full_response.append(response)


@app.route('/api/top/<username>', methods=['GET'])
def main(username):
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
    first_page_resp = req.get(url, params=first_page_params)

    content = json.loads(first_page_resp.content)
    if not content:
        return jsonify(f"{username} doesn't have any public repositories yet")
    updated_at = content[0]['updated_at']

    cached_repos = sql.get_repos(username, updated_at)
    if cached_repos:
        repos = format_cached_repos(cached_repos)
        sorted_repos = sorted(
            repos, key=lambda repo: (-repo['stars'], repo['name'])
        )

        finish = datetime.now()
        res = finish - start
        print('pulled from cache')
        return jsonify(sorted_repos[:limit], str(res))

    if first_page_resp.links.get('last'):
        last_url = first_page_resp.links['last']['url']
        parsed_url = urlparse(last_url)
        last_page = int(parse_qs(parsed_url.query)['page'][0])

    requests = [
        get_full_response(
            url, i, full_response
        ) for i in range(1, last_page + 1)
    ]

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(asyncio.gather(*requests))

    flat_full_response = reduce(lambda a, b: a+b, full_response)
    repos = [format_repo(repo) for repo in flat_full_response]
    sorted_repos = sorted(
        repos, key=lambda repo: (-repo['stars'], repo['name'])
    )
    sql.cache(username, sorted_repos)
    print('cached')
    finish = datetime.now()
    res = finish - start

    return jsonify(sorted_repos[:limit], str(res))
