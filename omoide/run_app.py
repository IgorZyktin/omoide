# -*- coding: utf-8 -*-
"""Development runner, do not use in production!
"""
import uvicorn

from omoide.presentation import app_config


def init_app() -> app_config.Config:
    """Prepare all resources for the app start."""
    app_config.init()
    config = app_config.get_config()
    return config


def main():
    """Entry point."""
    config = init_app()
    uvicorn.run(
        'omoide.presentation.app:app',
        host=config.app.host,
        port=config.app.port,
        debug=config.app.debug,
        reload=config.app.reload,
    )


if __name__ == '__main__':
    main()
