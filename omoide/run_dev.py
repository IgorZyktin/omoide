"""Development runner, do not use in production."""

import os

from fastapi import Request
import python_utilz as pu
import uvicorn

from omoide import cfg
from omoide.application import app


def main() -> None:
    """Entry point."""
    log_config = uvicorn.config.LOGGING_CONFIG
    log_config['formatters']['access']['fmt'] = '%(asctime)s - %(levelname)s - %(message)s'
    log_config['formatters']['default']['fmt'] = '%(asctime)s - %(levelname)s - %(message)s'

    config = pu.from_env(cfg.Config, env_prefix='omoide_app')

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
        port=config.port,
    )


if __name__ == '__main__':
    main()
