"""Application server.

Here we're only gluing two components together.
"""

import os

from fastapi import FastAPI
from prometheus_client import CollectorRegistry
from prometheus_client.multiprocess import MultiProcessCollector
from starlette_exporter import PrometheusMiddleware
from starlette_exporter import handle_metrics

from omoide import dependencies
from omoide.omoide_api import application as api_application
from omoide.omoide_app import application as app_application

app = app_application.get_app()
api = api_application.get_api()

app.mount('/api', api)

api_application.apply_api_routes_v1(api)
app_application.apply_app_routes(app)
app_application.apply_middlewares(app)

config = dependencies.get_config()


def add_metrics(current_app: FastAPI):
    """Add metrics instrumentation."""
    if 'PROMETHEUS_MULTIPROC_DIR' in os.environ:
        registry = CollectorRegistry()
        path = os.environ['PROMETHEUS_MULTIPROC_DIR']
        MultiProcessCollector(registry, path=path)

    current_app.add_middleware(PrometheusMiddleware, app_name=config.metrics.server_name)
    current_app.add_route('/metrics', handle_metrics)


if config.metrics.enabled:
    add_metrics(app)
