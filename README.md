# toprepos


## Badges
[![Maintainability](https://api.codeclimate.com/v1/badges/4280c2d155520aa63f06/maintainability)](https://codeclimate.com/github/sound-round/toprepos/maintainability)
[![Github Actions Status](https://github.com/sound-round/toprepos/workflows/linter/badge.svg)](https://github.com/sound-round/toprepos/actions)
[![Github Actions Status](https://github.com/sound-round/toprepos/workflows/tests/badge.svg)](https://github.com/sound-round/toprepos/actions)
[![Test Coverage](https://api.codeclimate.com/v1/badges/4280c2d155520aa63f06/test_coverage)](https://codeclimate.com/github/sound-round/toprepos/test_coverage)


## Description
toprepos — a web service that uses the Github REST API and provides an API with information about the most popular user repositories.

## Prerequisites
- python3.8 - https://www.python.org/
- poetry - https://python-poetry.org/

## install
Use the following command to install app:
```
poetry config virtualenvs.in-project true
make install
```

## Local testing
Use the following commands to test the app:
```
make test
make lint
```

## Authentication
Toprepos uses GITHUB API to get information. Unauthenticated GITHUB clients can make limit number of requests per hour. To get more requests per hour, you'll need to authenticate.
To do that, add a ```.env``` file in the root directory of the project (/toprepos). Template of the file content:
```
LOGIN=your_gihub_username
TOKEN=your_github_access_token
```

## Run
Being in the root directory of the project (/toprepos), use the following commands to run the app:
```
export FLASK_APP=./toprepos/app.py
poetry shell
make run
```
Now, you can send GET requests to http://127.0.0.1:5000/ to get information about the most popular user repositories in json.

Request template: 
```
/api/top/{username}
```

Also, you can change number of repositories, which response will contain, using URL's query string parameter "limit".
For example:
```
HTTP GET /api/top/mokevnin?limit=4

[
    {
      "html_url": "https://github.com/mokevnin/dotfiles", 
      "id": 20793939, 
      "name": "dotfiles", 
      "stars": 265
    }, 
    {
      "html_url": "https://github.com/mokevnin/you-don-t-know-oop", 
      "id": 86457982, 
      "name": "you-don-t-know-oop", 
      "stars": 174
    }, 
    {
      "html_url": "https://github.com/mokevnin/railsify", 
      "id": 10367628, 
      "name": "railsify", 
      "stars": 98
    }, 
    {
      "html_url": "https://github.com/mokevnin/ipgeobase", 
      "id": 3427771, 
      "name": "ipgeobase", 
      "stars": 64
    }
]
```


## Support
If you have questions you can email me to yudaev1@gmail.com

## Links
This project was built using these tools:

| Tool                                                                        | Description                                             |
|-----------------------------------------------------------------------------|---------------------------------------------------------|
| [flask](https://flask.palletsprojects.com/)                                 | "Lightweight WSGI web application framework."           |
| [aiohttp](https://docs.aiohttp.org/)                                        | "Automatization software workflows with  CI/CD"         |
| [requests](https://docs.python-requests.org/)                               | "Simple HTTP library for Python"                        |
| [poetry](https://poetry.eustace.io/)                                        | "Python dependency management and packaging made easy"  |
| [flake8](https://flake8.pycqa.org/en/latest/)                               | "The tool for style guide enforcement"                  |
| [code climate](https://codeclimate.com/)                                    | "Actionable metrics for engineering"                    |
| [github actions](https://github.com/features/actions)                       | "Asynchronous HTTP Client/Server for asyncio and Python"|



