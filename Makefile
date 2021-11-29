set:
	export FLASK_APP=app.py
	export FLASK_ENV=development

run:
	python3 -m flask run --port=4000 --host=0.0.0.0

run_gunicorn:
	gunicorn --workers=4 --bind=127.0.0.1:5000 hello_world:app

install:
	poetry install

lint:
	poetry run flake8 toprepos
	# poetry run flake8 tests