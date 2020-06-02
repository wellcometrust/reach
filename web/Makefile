PYTHON := ${PWD}/venv/bin/python
GUNICORN := ${PWD}/venv/bin/gunicorn
STATIC_ROOT := ${PWD}/build/web/static
DOCS_STATIC_ROOT := ${PWD}/docs/build/html/_static
SENTRY_DSN := ""
CMD_ARGS := "--bind=127.0.0.1 --workers=1 --reload"
CONFIG_FILE := ${PWD}/config/dev.config.toml



.PHONY: setup
setup:
	python3 -m venv --copies venv
	./venv/bin/pip install -r requirements.txt

.PHONY: run-server
run-server:
	CONFIG_FILE=${PWD}/config/dev.config.toml ${GUNICORN} web:application

.PHONY: watch
watch:
	gulp -f Gulpfile.local.js watch


.PHONY: run
run: run-server watch
