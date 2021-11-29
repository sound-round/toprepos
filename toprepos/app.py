#!/usr/bin/env python3

import requests
import os
import asyncio
import aiohttp
import itertools
from flask import Flask
from flask import request
import json
from flask import jsonify
from functools import reduce
from urllib.parse import urlparse
from urllib.parse import parse_qs
from dotenv import load_dotenv
from datetime import datetime


load_dotenv()


MY_NAME = 'sound-round'
TOKEN = os.environ.get('TOKEN')
KEYS = ('id', 'name', "stargazers_count", 'html_url')


app = Flask(__name__)


def format_repo(repo):
    dict_ = {}
    for key in KEYS:
        if key == 'stargazers_count':
            dict_['stars'] = repo['stargazers_count']
            continue
        dict_[key] = repo[key]
    return dict_


async def fetch(url, params):
        async with aiohttp.ClientSession() as session:
            async with session.get(
                url, params=params, auth=aiohttp.BasicAuth(
                    MY_NAME, TOKEN, encoding='utf-8'
                )
            ) as response:
                return await response.json()

async def get(url, i, full_response):
    params = {'page': i}
    response = await fetch(url, params)
    full_response.append(response)


@app.route('/api/top/<username>', methods=['GET'])
def main(username):
    # start = datetime.now()

    full_response = []
    url = f'https://api.github.com/users/{username}/repos'
    limit = request.args.get('limit')

    if not limit:
        limit = 10
    limit = int(limit)



    last_page = 5
    requests = [get(url, i, full_response) for i in range(1, last_page + 1)]

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(asyncio.gather(*requests))
    print(full_response)
    flat_full_response = reduce(lambda a, b: a+b, full_response)
    repos = [format_repo(repo) for repo in flat_full_response]
    sorted_repos = sorted(repos, key=lambda repo: -repo['stars'])

    # finish = datetime.now()
    # res = finish - start

    return jsonify(sorted_repos[:limit])
