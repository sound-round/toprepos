import sqlite3
import requests as req
import json
import os
import asyncio
import aiohttp
from toprepos import sql
from flask import Flask, jsonify, request, make_response
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
CONNECTION_ERROR = {
        "status_code": 503,
        "name": 'ConnectionError',
        "description": 'Server is not available.',
    }
HTTP_ERROR = {
        "status_code": 404,
        "name": 'Not Found',
        "description": 'URL not found',
    }
REQUEST_ERROR = {
        "status_code": 500,
        "name": 'Request error',
        "description": 'Something went wrong during request',
    }
PROGRAMMING_ERROR = {
        "status_code": 500,
        "name": 'SQL programming error',
        "description": 'ProgrammingError occured',
    }
OPERATIONAL_ERROR = {
        "status_code": 500,
        "name": 'SQL operational error',
        "description": 'OperationalError occured',
    }
SQL_ERROR =  {
        "status_code": 500,
        "name": 'SQL error',
        "description": 'SQL error occured',
    }


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
    except sqlite3.ProgrammingError:
        response_data = PROGRAMMING_ERROR
        response = make_response(response_data, 500)
        response.content_type = "application/json"
        return response
    except sqlite3.OperationalError:
        response_data = OPERATIONAL_ERROR
        response = make_response(response_data, 500)
        response.content_type = "application/json"
        return response
    except sqlite3.Error:
        response_data = SQL_ERROR
        response = make_response(response_data, 500)
        response.content_type = "application/json"
        return response

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
    except aiohttp.web.HTTPServerUnavailable:
        response_data = CONNECTION_ERROR
        response = make_response(response_data, 503)
        response.content_type = "application/json"
        return response
    except aiohttp.web.HTTPNotFound:
        response_data = HTTP_ERROR
        response = make_response(response_data, 404)
        response.content_type = "application/json"
        return response
    except aiohttp.web.HTTPException:
        response_data = REQUEST_ERROR
        response = make_response(response_data)
        response.content_type = "application/json"
        return response


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
    except req.ConnectionError:
        response_data = CONNECTION_ERROR
        response = make_response(response_data, 503)
        response.content_type = "application/json"
        return response
    except req.HTTPError:
        response_data = HTTP_ERROR
        response = make_response(response_data, 404)
        response.content_type = "application/json"
        return response
    except req.exceptions.RequestException:
        response_data = REQUEST_ERROR
        response = make_response(response_data)
        response.content_type = "application/json"
        return response

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
