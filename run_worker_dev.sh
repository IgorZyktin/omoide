#!/bin/bash
source venv/bin/activate
python -m omoide.daemons.worker \
  --name "$OMOIDE_WORKER_NAME" \
  --db-url "$OMOIDE_DB_URL" \
  --hot-folder "$OMOIDE_HOT_FOLDER" \
  --cold-folder "$OMOIDE_COLD_FOLDER" \
  --save-hot \
  --save-cold \
  --download-media \
  --manual-copy \
  --drop-done-media \
  --drop-done-copies \
  --max-interval 10 \
  --batch-size 5 \
  --log-level "debug" \
  --single-run \
  --debug \
  --echo \
  --replication-formula "$OMOIDE_REPLICATION_FORMULA"
