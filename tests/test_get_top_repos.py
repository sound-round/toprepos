import pytest
import os
import pathlib
import json
import tempfile
from toprepos.app import app, get_from_cache
from aioresponses import aioresponses
from toprepos import db


USERNAME = 'sound-round'
FIXTURES_DIR = 'fixtures'
URL = f'http://test.com/api/top/{USERNAME}?limit=4'
GITHUB_URL = f'https://api.github.com/users/{USERNAME}/repos?page=1'
GITHUB_API_RESPONSE = 'github_api_response.json'
EXPECTED = 'expected.json'


def read(file_path, mode='r'):
    with open(file_path, mode) as f:
        file = f.read()
    return file


def get_fixture_path(fixture_name):
    return os.path.join(
        pathlib.Path(__file__).absolute().parent,
        FIXTURES_DIR,
        fixture_name
    )


@pytest.fixture(scope='module')
def test_client():
    db_fd, db_path = tempfile.mkstemp()
    test_config = {'TESTING': True, 'DATABASE': db_path}
    app.config.update(test_config)

    with app.test_client() as testing_client:
        yield testing_client

    os.close(db_fd)
    os.unlink(db_path)


def test_get_top_repos(requests_mock, test_client):

    requests_mock.get(
        GITHUB_URL,
        content=read(get_fixture_path(GITHUB_API_RESPONSE), 'rb'),
        status_code=200,
    )
    with aioresponses() as mocked:
        mocked.get(
            GITHUB_URL,
            status=200,
            body=read(get_fixture_path(GITHUB_API_RESPONSE), 'rb')
        )
        response = test_client.get(URL)
        assert response.status_code == 200
        assert response.get_json() == json.loads(
            read(get_fixture_path(EXPECTED), 'rb')
        )


def test_404_not_found(test_client):

    response = test_client.get('')
    assert response.status_code == 404


def test_db():
    db_fd, db_path = tempfile.mkstemp()
    test_config = {'TESTING': True, 'DATABASE': db_path}
    app.config.update(test_config)

    with app.app_context():
        db.create_tables()
        db.save_to_cache(USERNAME, json.loads(
            read(get_fixture_path(EXPECTED), 'rb')
        ))

        repos = get_from_cache(USERNAME, 123)
        assert repos == json.loads(read(get_fixture_path(EXPECTED), 'rb'))

    os.close(db_fd)
    os.unlink(db_path)
