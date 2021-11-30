#!/usr/bin/env python3
import requests as req
import os
import asyncio
import aiohttp
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

    last_page = LAST_PAGE_DEFAULT
    full_response = []
    url = f'https://api.github.com/users/{username}/repos'
    limit = request.args.get('limit')

    if not limit:
        limit = LIMIT_DEFAULT
    limit = int(limit)

    first_page_resp = req.head(url)
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
    sorted_repos = sorted(repos, key=lambda repo: -repo['stars'])

    finish = datetime.now()
    res = finish - start

    return jsonify(sorted_repos[:limit], str(res))
