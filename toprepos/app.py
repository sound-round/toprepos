import requests
import os
from flask import Flask
from flask import request
import json
from flask import jsonify
from functools import reduce
from urllib.parse import urlparse
from urllib.parse import parse_qs
from dotenv import load_dotenv


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


@app.route('/')
def index():
    return 'Hello, World!'


def get_response(url):
    full_response = []
    params = {'page': 1, 'per_page': 100}

    response = requests.get(url, params=params, auth=(MY_NAME, TOKEN))
    response.raise_for_status()
    full_response.append(json.loads(response.content))
    if response.links.get('last'):
        last_url = response.links['last']['url']
        parsed_url = urlparse(last_url)
        last_page = int(parse_qs(parsed_url.query)['page'][0])

        for page_number in range(2, last_page + 1):
            params['page'] = page_number
            response = requests.get(url, params=params, auth=(MY_NAME, TOKEN))
            response.raise_for_status()
            full_response.append(json.loads(response.content))

    flat_full_response = reduce(lambda a, b: a+b, full_response)

    return flat_full_response


@app.route('/api/top/<username>', methods=['GET'])
def get_repos(username):
    url = f'https://api.github.com/users/{username}/repos'
    limit = request.args.get('limit')

    if not limit:
        limit = 10
    limit = int(limit)

    response = get_response(url)
    repos = [format_repo(repo) for repo in response]
    sorted_repos = sorted(repos, key=lambda repo: -repo['stars'])

    return jsonify(sorted_repos[:limit])
