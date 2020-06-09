import os

import toml

def _or(val_a, val_b, default=None):
    """ Used to allow specifying config values through
    os.environ

    Args:
        val_a:
        val_b:
    """
    if val_a is not None:
        return val_a
    elif val_b is not None:
        return val_b
    else:
        return default


class Config(object):
    def __init__(self, source):
        self.debug = _or(
            source.get('debug'),
            os.environ.get("DEBUG"),
            default=False
        )

        self.port = _or(
            source.get('port'),
            os.environ.get("PORT"),
            default=8000
        )
        self.environment = _or(
            source.get("environment"),
            os.environ.get("ENVIRONMENT"),
            default="development"
        )


        abs_path = "/".join(os.path.abspath(__file__).split("/")[:-1])
        static_root = _or(
            source.get("static_root"),
            os.environ.get("STATIC_ROOT")
        )

        if static_root is not None:
            if not static_root.startswith("/"):
                static_root = os.path.normpath(os.path.join(abs_path, static_root))
        self.static_root = static_root

        docs_static_root = _or(
            source.get("docs_static_root"),
            os.environ.get("DOCS_STATIC_ROOT")
        )
        if docs_static_root is not None:
            if not docs_static_root.startswith("/"):
                docs_static_root = os.path.normpath(os.path.join(abs_path, docs_static_root))

        self.docs_static_root = docs_static_root

        db = source.get("database", {})
        self.db_host = _or(
            db.get("db_host", None),
            os.environ.get("DB_HOST")
        )
        self.db_port = _or(
            db.get("db_port"),
            os.environ.get("DB_PORT"),
            default=5432
        )
        self.db_name = _or(
            db.get("db_name"),
            os.environ.get("DB_NAME")
        )
        self.db_user = _or(
            db.get("db_user"),
            os.environ.get("DB_USER")
        )
        self.db_password = _or(
            db.get("db_password", None),
            os.environ.get("DB_PASSWORD")
        )
        self.min_conns = db.get("min_conns", 1)
        self.max_conns = db.get("max_conns", 30)

        sentry = source.get("sentry", {})
        self.sentry_dsn = _or(
            sentry.get("dsn"),
            os.environ.get("SENTRY_DSN")
        )

        github = source.get("github", {})
        self.github_token = _or(
            github.get("github_token"),
            os.environ.get("github_token"),
            default=None
        )

        self.github_user = _or(
            github.get("github_user"),
            os.environ.get("github_user"),
            default=None
        )

        analytics = source.get("analytics", {})
        self.ga_code = _or(
            analytics.get("ga_code"),
            os.environ.get("GA_CODE"),
            default=None
        )
        self.hotjar_code = _or(
            analytics.get("hotjar_code"),
            os.environ.get("HOTJAR_CODE"),
            default=None
        )


def init(config):
    global CONFIG
    CONFIG = Config(config)
