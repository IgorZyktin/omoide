#!/bin/bash
source venv/bin/activate
python -m omoide.daemons.downloader.run_forever --no-dry-run --no-strict
