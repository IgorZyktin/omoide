# -*- coding: utf-8 -*-
"""Development runner, do not use in production!
"""
import uvicorn

from omoide.presentation import app_config


def main():
    """Entry point."""
    config = app_config.Config()
    uvicorn.run(
        'omoide.presentation.app:app',
        host=config.host,
        port=8080,
        reload=True,
    )


if __name__ == '__main__':
    main()
