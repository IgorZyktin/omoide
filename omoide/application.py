"""Application server.

Here we're only gluing two components together.
"""

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
if config.metrics.enabled:
    app.add_middleware(PrometheusMiddleware, app_name=config.metrics.server_name)
    app.add_route('/metrics', handle_metrics)
