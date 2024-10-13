"""Development runner, do not use in production."""
import uvicorn

from omoide.presentation import app_config
from omoide.presentation.app import app


def main():
    """Entry point."""
    config = app_config.Config()
    uvicorn.run(
        app,
        host=config.host,
        port=8080,
    )


if __name__ == '__main__':
    main()
