set:
	export FLASK_APP=./toprepos/app.py
	export FLASK_ENV=development

run:
	python3 -m flask run

install:
	poetry install

lint:
	poetry run flake8 toprepos
	# poetry run flake8 tests

test:
	poetry run pytest -vv

test-coverage:
	poetry run pytest --cov=toprepos --cov-report xml tests/
