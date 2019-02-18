from copy import deepcopy

import airflow.config_templates.airflow_local_settings

# Extend default logging config so that task logging also goes to
# stderr. See docker-compose.yml for invocation.
#
# NB: other implementation paths, such as (1) re-using Airflow's existing
# console handler, or (2) setting propagate for this logger to True
# result in a recursive loop getting set up when handling log events.
# (The first issue hit comes from Sentry's logging integration, but it
# also seems to occur even when that integration is disabled.)
# Thankfully, using a separate logging.StreamHandler does not.
CONSOLE_LOGGING_CONFIG = deepcopy(
    airflow.config_templates.airflow_local_settings.DEFAULT_LOGGING_CONFIG
)
CONSOLE_LOGGING_CONFIG['handlers']['stderr'] = {
    'class': 'logging.StreamHandler',
    'formatter': 'airflow',
    'stream': 'ext://sys.stderr'
}
CONSOLE_LOGGING_CONFIG['loggers']['airflow.task']['handlers'].append(
    'stderr'
)
