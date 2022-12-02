#!/bin/bash
source venv/bin/activate
gunicorn omoide.presentation.app:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8080