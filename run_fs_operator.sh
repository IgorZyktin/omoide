#!/bin/bash
source venv/bin/activate
python -m omoide.daemons.fs_operator.run_forever --no-dry-run --no-strict
