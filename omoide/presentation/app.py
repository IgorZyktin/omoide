"""Application server.

Here we're only gluing two components together.
"""

from omoide.omoide_api import application as api_application
from omoide.omoide_app import application as app_application

app = app_application.get_app()
api = api_application.get_api()

# TODO - change mounting point after all endpoints will be migrated
app.mount('/api-new', api)

api_application.apply_api_routes_v1(api)
app_application.apply_app_routes(app)
app_application.apply_middlewares(app)
