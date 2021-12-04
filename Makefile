set:
	export FLASK_APP=./toprepos/app.py
	export FLASK_ENV=development

run:
	python3 -m flask run 

run_gunicorn:
	gunicorn --workers=4 --bind=127.0.0.1:5000 hello_world:app

install:
	poetry install

lint:
	poetry run flake8 toprepos
	# poetry run flake8 tests

test:
	poetry run pytest -vv