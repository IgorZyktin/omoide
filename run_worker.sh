#!/bin/bash
source venv/bin/activate
python -m omoide.daemons.worker \
  --name "$OMOIDE_WORKER_NAME" \
  --db-url "$OMOIDE_DB_URL_WORKER" \
  --hot-folder "$OMOIDE_HOT_FOLDER" \
  --cold-folder "$OMOIDE_COLD_FOLDER" \
  --save-hot \
  --save-cold \
  --download-media \
  --manual-copy \
  --log-level "debug" \
  --debug \
  --drop-done-media \
  --drop-done-copies \
  --replication-formula "$OMOIDE_REPLICATION_FORMULA"
