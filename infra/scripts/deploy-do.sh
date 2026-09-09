#!/usr/bin/env bash
# Talaqqi — one-shot production deploy on a fresh Ubuntu 24.04 droplet (DigitalOcean or any VPS).
# Usage (as root):  curl -fsSL https://raw.githubusercontent.com/Osama-BanyHamad/tallaqi/main/infra/scripts/deploy-do.sh | bash -s -- tallaqi.com
# Re-run to update: same command (pulls, rebuilds, migrates, keeps data).
set -euo pipefail
DOMAIN="${1:-tallaqi.com}"
REPO="${REPO:-https://github.com/Osama-BanyHamad/tallaqi.git}"
DIR="${DIR:-/opt/talaqqi}"
SEED="${SEED:-1}"

echo "==> Docker"
if ! command -v docker >/dev/null 2>&1; then
  apt-get update -qq && apt-get install -y -qq ca-certificates curl git ufw >/dev/null
  curl -fsSL https://get.docker.com | sh >/dev/null
fi

echo "==> Firewall (22, 80, 443)"
ufw allow OpenSSH >/dev/null; ufw allow 80/tcp >/dev/null; ufw allow 443/tcp >/dev/null; ufw allow 443/udp >/dev/null; ufw --force enable >/dev/null

echo "==> Source"
BRANCH="${BRANCH:-main}"
if [ -d "$DIR/.git" ]; then git -C "$DIR" fetch -q origin && git -C "$DIR" checkout -q "$BRANCH" && git -C "$DIR" pull -q origin "$BRANCH"; else git clone -q -b "$BRANCH" "$REPO" "$DIR"; fi
cd "$DIR"

echo "==> Environment"
if [ ! -f .env ]; then
  SECRET=$(python3 -c 'import secrets;print(secrets.token_urlsafe(48))' 2>/dev/null || openssl rand -base64 48 | tr -d '\n/+=')
  DBP=$(openssl rand -hex 16); PGP=$(openssl rand -hex 16)
  cat > .env <<EOF
DEBUG=false
SECRET_KEY=$SECRET
DOMAIN=$DOMAIN
SERVER_IP=$(curl -fs https://api.ipify.org || hostname -I | awk '{print $1}')
ALLOWED_HOSTS=$DOMAIN,www.$DOMAIN,api,localhost
CORS_ALLOWED_ORIGINS=https://$DOMAIN,https://www.$DOMAIN
CSRF_TRUSTED_ORIGINS=https://$DOMAIN,https://www.$DOMAIN
DEFAULT_LANGUAGE=ar
CELERY_TASK_ALWAYS_EAGER=true
DB_PASSWORD=$DBP
POSTGRES_PASSWORD=$PGP
EOF
  chmod 600 .env
  echo "    wrote $DIR/.env (secrets generated)"
fi

# --- Safe deploy: build first (no downtime), keep the previous images, swap, health-gate, roll back on failure.
echo "==> Building images (the running site keeps serving during the build)"
docker compose --profile prod build api web
for svc in api web; do
  docker image inspect "talaqqi-$svc:previous" >/dev/null 2>&1 && docker rmi -f "talaqqi-$svc:previous" >/dev/null 2>&1 || true
  # The image that is running right now becomes the rollback target.
  RUNNING=$(docker inspect --format '{{.Image}}' "talaqqi-$svc-1" 2>/dev/null || true)
  [ -n "$RUNNING" ] && docker tag "$RUNNING" "talaqqi-$svc:previous" || true
done

echo "==> Swapping containers (API restarts once for migrations: ~20 seconds of API 502, the site itself stays up)"
docker compose --profile prod up -d --remove-orphans postgres valkey api web caddy

healthy() {
  docker compose --profile prod exec -T api curl -fs http://localhost:8000/readyz >/dev/null 2>&1 \
  && docker compose --profile prod exec -T caddy wget -qO- --timeout=5 http://web:3000/ 2>/dev/null | grep -q "<html"
}
echo "==> Health gate (API readyz + web home page)"
OK=0
for i in $(seq 1 60); do
  if healthy; then OK=1; break; fi
  sleep 3
done
if [ "$OK" != "1" ]; then
  echo "!!  New release is not healthy after 3 minutes — rolling back to the previous images"
  docker compose --profile prod logs --tail=40 api web || true
  for svc in api web; do
    docker image inspect "talaqqi-$svc:previous" >/dev/null 2>&1 && docker tag "talaqqi-$svc:previous" "talaqqi-$svc:latest"
  done
  docker compose --profile prod up -d --no-build api web
  for i in $(seq 1 40); do healthy && break; sleep 3; done
  healthy && echo "    rollback complete: previous release is serving again" || echo "    rollback did NOT restore health — investigate: docker compose --profile prod logs api web"
  exit 1
fi
docker compose --profile prod exec -T api curl -s http://localhost:8000/readyz; echo

echo "==> Visit statistics: hourly GoAccess report from the Caddy access log (/stats/, basic auth from STATS_USER/STATS_HASH in .env)"
mkdir -p "$DIR/logs/caddy" "$DIR/stats"; chmod +x "$DIR/infra/scripts/stats.sh"
( crontab -l 2>/dev/null | grep -v "stats.sh"; echo "17 * * * * DIR=$DIR bash $DIR/infra/scripts/stats.sh >> /var/log/talaqqi-stats.log 2>&1" ) | crontab -
bash "$DIR/infra/scripts/stats.sh" || true

echo "==> Nightly database backup (14-day retention) in cron"
mkdir -p "$DIR/backups"; chmod +x "$DIR/infra/scripts/backup.sh"
( crontab -l 2>/dev/null | grep -v "backup.sh"; echo "10 3 * * * DIR=$DIR bash $DIR/infra/scripts/backup.sh >> /var/log/talaqqi-backup.log 2>&1" ) | crontab -

echo "==> Syncing system roles with the permission catalog"
docker compose --profile prod exec -T api python apps/api/manage.py sync_roles || true

if [ "$SEED" = "1" ]; then
  echo "==> Seeding demo tenant + users (idempotent; use SEED=0 to skip)"
  docker compose --profile prod exec -T api python apps/api/manage.py seed_demo || true
fi

echo
echo "Done. https://$DOMAIN  (TLS is issued automatically once DNS points here)"
echo "Logins: owner@demo.talaqqi / Talaqqi@2026 (also supervisor@, teacher1-4@, parent1@, finance@)"
echo "Logs:   cd $DIR && docker compose --profile prod logs -f --tail=100"
