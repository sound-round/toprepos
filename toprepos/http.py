import os
import asyncio
import aiohttp
import requests as req
from functools import reduce
from urllib.parse import urlparse
from urllib.parse import parse_qs
from dotenv import load_dotenv
from toprepos.formatters import format_repo


load_dotenv()


LOGIN = os.environ.get('LOGIN')
TOKEN = os.environ.get('TOKEN')


def get_first_page(url):
    first_page_params = {'per_page': 1, 'page': 1, 'sort': 'updated'}
    if not LOGIN or not TOKEN:
        return req.get(
            url, params=first_page_params,
        )
    return req.get(
            url, params=first_page_params, auth=(LOGIN, TOKEN),
        )


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


async def get_full_response(url, i, full_response):
    params = {'page': i}
    response = await get_page_response(url, params)
    full_response.append(response)


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
