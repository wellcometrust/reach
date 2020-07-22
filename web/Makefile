PYTHON := ${PWD}/venv/bin/python
GUNICORN := ${PWD}/venv/bin/gunicorn
STATIC_ROOT := ${PWD}/build/web/static
DOCS_STATIC_ROOT := ${PWD}/docs/build/html/_static
SENTRY_DSN := ""
CMD_ARGS := "--bind=127.0.0.1 --workers=1 --reload"
CONFIG_FILE := ${PWD}/config/dev.config.toml
APP_OUT_DIR := ${STATIC_ROOT}/js
APP_OUT_DIR := ${CSS_OUT_DIR}/css


.PHONY: setup
setup:
	python3 -m venv --copies venv
	./venv/bin/pip install -r requirements.txt

.PHONY: run-server
run-server:
	CONFIG_FILE=${PWD}/config/dev.config.toml ${GUNICORN} web:application

.PHONY: watch
watch: watch-styles watch-app

.PHONY: watch-app
watch-app:
	parcel watch web/src/js/app.js --out-dir ${APP_OUT_DIR}

.PHONY: watch-styles
watch-styles:
	parcel watch web/src/css/style.less --out-dir ${CSS_OUT_DIR}


.PHONY: run
run: run-server watch
