"""Development runner, do not use in production."""

from collections.abc import Iterator
import os

from fastapi import FastAPI
from fastapi import Request
from fastapi.routing import APIRoute
import python_utilz as pu
from starlette.routing import Mount
import uvicorn

from omoide import cfg
from omoide.application import app


def setup_uvicorn_logging() -> None:
    """Make uvicorn logs more verbose."""
    log_config = uvicorn.config.LOGGING_CONFIG
    log_config['formatters']['access']['fmt'] = '%(asctime)s - %(levelname)s - %(message)s'
    log_config['formatters']['default']['fmt'] = '%(asctime)s - %(levelname)s - %(message)s'


def route_iter(current_app: FastAPI, mount: str = '') -> Iterator[dict[str, str]]:
    """Iterate on all routes, including nested applications."""
    for route in current_app.routes:
        if isinstance(route, APIRoute):
            yield {'path': mount + route.path, 'name': route.name}
        elif isinstance(route, Mount) and isinstance(route.app, FastAPI):
            yield from route_iter(route.app, mount=mount + route.path)


def main() -> None:
    """Entry point."""
    config = pu.from_env(cfg.Config, env_prefix='omoide_app')

    setup_uvicorn_logging()

    @app.get('/all_routes')
    def get_all_urls_from_request(request: Request) -> list[dict[str, str]]:
        """List all URLs for this Fastapi instance.

        Use only for debugging!
        """
        return list(route_iter(request.app))

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
