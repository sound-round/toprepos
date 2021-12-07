import json
from toprepos import db


def get_from_cache(username, updated_at):

    cached_repos = db.get_repos(username, updated_at)

    if cached_repos:
        sorted_repos = sorted(
            json.loads(cached_repos.replace("'", "\"")),
            key=lambda repo: (-repo['stars'], repo['name']),
        )
        return sorted_repos
