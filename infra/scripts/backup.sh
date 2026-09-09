#!/usr/bin/env bash
# Nightly PostgreSQL backup (compressed dump) with 14-day retention. Installed in cron by deploy-do.sh.
# Restore: gunzip -c backups/talaqqi-YYYYmmdd-HHMM.sql.gz | docker compose --profile prod exec -T postgres psql -U postgres talaqqi
set -euo pipefail
DIR="${DIR:-/opt/talaqqi}"
OUT="$DIR/backups"
KEEP_DAYS="${KEEP_DAYS:-14}"
mkdir -p "$OUT"
cd "$DIR"
STAMP=$(date -u +%Y%m%d-%H%M)
docker compose --profile prod exec -T postgres pg_dump -U postgres --no-owner --no-privileges talaqqi | gzip -6 > "$OUT/talaqqi-$STAMP.sql.gz"
SIZE=$(du -h "$OUT/talaqqi-$STAMP.sql.gz" | cut -f1)
find "$OUT" -name 'talaqqi-*.sql.gz' -mtime +"$KEEP_DAYS" -delete
echo "backup written: $OUT/talaqqi-$STAMP.sql.gz ($SIZE); kept $(ls "$OUT" | wc -l) files"
