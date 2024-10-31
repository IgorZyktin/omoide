"""Development runner, do not use in production."""

import os

from fastapi import Request
import uvicorn

from omoide.application import app
from omoide.presentation import app_config


def main() -> None:
    """Entry point."""
    config = app_config.Config()

    @app.get('/all_routes')
    def get_all_urls_from_request(
        request: Request,
    ) -> list[dict[str, str]]:
        """List all URLs for this Fastapi instance.

        Use only for debugging!
        """
        url_list = [{'path': route.path, 'name': route.name} for route in request.app.routes]
        return url_list

    if os.name == 'nt':
        host = '127.0.0.1'
    else:
        host = config.host

    uvicorn.run(
        app,
        host=host,
        port=8080,
    )


if __name__ == '__main__':
    main()
