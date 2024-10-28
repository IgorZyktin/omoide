"""Development runner, do not use in production."""

from fastapi import Request
import uvicorn

from omoide.presentation import app_config
from omoide.presentation.app import app


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

    uvicorn.run(
        app,
        host=config.host,
        port=8080,
    )


if __name__ == '__main__':
    main()
