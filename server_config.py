"""Gunicorn configuration."""

import os

from gunicorn.arbiter import Arbiter
from gunicorn.workers.base import Worker
from prometheus_client import multiprocess

_host = os.getenv('OMOIDE_APP__HOST', '0.0.0.0')
_port = os.getenv('OMOIDE_APP__PORT', '8080')
bind = f'{_host}:{_port}'

workers = int(os.getenv('OMOIDE_APP__GUNICORN__WORKERS', '4'))
worker_class = os.getenv('OMOIDE_APP__GUNICORN__WORKER_CLASS', 'uvicorn.workers.UvicornWorker')

log_file = os.getenv('OMOIDE_APP__GUNICORN__LOG_PATH', '-')

max_requests = int(os.getenv('OMOIDE_APP__GUNICORN__MAX_REQUESTS', '0'))
max_requests_jitter = int(os.getenv('OMOIDE_APP__GUNICORN__MAX_REQUESTS_JITTER', '0'))


def post_fork(server: Arbiter, worker: Worker) -> None:
    """Gunicorn callable."""
    _ = server
    worker.log.info('[post_fork] age: %s. pid: %s', worker.age, worker.pid)


def post_worker_init(worker: Worker) -> None:
    """Gunicorn callable."""
    worker.log.info('[post_worker_init] age: %s. pid: %s', worker.age, worker.pid)


def when_ready(server: Arbiter) -> None:
    """Gunicorn callable."""
    server.log.info('Server is ready. Spawning workers')


def child_exit(server, worker):
    """Add special tuning for metrics collector."""
    _ = server
    multiprocess.mark_process_dead(worker.pid)
