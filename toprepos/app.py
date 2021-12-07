import json
import requests as req
from toprepos import db
from flask import Flask, jsonify, request, make_response
from toprepos.http import get_first_page, get_from_github
from toprepos.cache import get_from_cache
from toprepos.formatters import format_to_unix_time


LAST_PAGE_DEFAULT = 1
LIMIT_DEFAULT = 10


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.from_mapping(
        DATABASE="cache.db",
        JSONIFY_PRETTYPRINT_REGULAR=True,
    )

    if test_config:
        app.config.update(test_config)

    return app


app = create_app()


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
    db.create_tables()

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
        return jsonify(cached_top_repos[:limit])

    top_repos = get_from_github(
        url, first_page_response, full_response, last_page,
    )
    db.save_to_cache(username, top_repos)

    return jsonify(top_repos[:limit])
