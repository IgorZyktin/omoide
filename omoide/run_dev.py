# -*- coding: utf-8 -*-
"""Development runner, do not use in production!
"""
import uvicorn


def main():
    """Entry point."""
    uvicorn.run(
        'omoide.presentation.app:app',
        host='192.168.1.64',
        port=8080,
        debug=True,
        reload=True,
    )


if __name__ == '__main__':
    main()
