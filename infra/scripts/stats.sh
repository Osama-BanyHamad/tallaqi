#!/usr/bin/env bash
# Build the visit-statistics dashboard from Caddy's JSON access log with GoAccess (self-hosted, no third-party trackers).
# Runs hourly from cron (installed by deploy-do.sh). Output: /opt/talaqqi/stats/index.html, served at https://<domain>/stats/ behind basic auth.
set -euo pipefail
DIR="${DIR:-/opt/talaqqi}"
LOGS="$DIR/logs/caddy"
OUT="$DIR/stats"
mkdir -p "$OUT"
if ! ls "$LOGS"/access.log* >/dev/null 2>&1; then
  echo "no access log yet"; exit 0
fi
# Only real site traffic: drop the API health checks and our own verification scripts (Python-urllib), keep everything a person or a phone did.
cat "$LOGS"/access.log* \
  | grep -v '"uri":"/readyz"' | grep -v '"uri":"/healthz"' | grep -v 'Python-urllib' \
  > /tmp/talaqqi-access.json || true
docker run --rm -i \
  -v "$OUT":/out \
  allinurl/goaccess:latest \
  --log-format=CADDY --date-format=CADDY --time-format=CADDY \
  --no-global-config --ignore-crawlers --real-os --anonymize-ip \
  --html-report-title="تَلَقِّي · Visit statistics" \
  -o /out/full.html - < /tmp/talaqqi-access.json
rm -f /tmp/talaqqi-access.json
# Branded summary (app downloads, visitors, pages, referrers) on top of the full GoAccess report
python3 "$DIR/infra/scripts/stats_page.py" "$LOGS" "$OUT/index.html"
echo "stats written: $OUT/index.html + full.html ($(date -u +%FT%TZ))"
