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
if [ -d "$DIR/.git" ]; then git -C "$DIR" pull -q; else git clone -q "$REPO" "$DIR"; fi
cd "$DIR"

echo "==> Environment"
if [ ! -f .env ]; then
  SECRET=$(python3 -c 'import secrets;print(secrets.token_urlsafe(48))' 2>/dev/null || openssl rand -base64 48 | tr -d '\n/+=')
  DBP=$(openssl rand -hex 16); PGP=$(openssl rand -hex 16)
  cat > .env <<EOF
DEBUG=false
SECRET_KEY=$SECRET
DOMAIN=$DOMAIN
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

echo "==> Build & start (this takes a few minutes the first time)"
docker compose --profile prod up -d --build --remove-orphans postgres valkey api web caddy

echo "==> Waiting for the API"
for i in $(seq 1 60); do
  if docker compose --profile prod exec -T api curl -fs http://localhost:8000/readyz >/dev/null 2>&1; then break; fi
  sleep 3
done
docker compose --profile prod exec -T api curl -s http://localhost:8000/readyz; echo

if [ "$SEED" = "1" ]; then
  echo "==> Seeding demo tenant + users (idempotent; use SEED=0 to skip)"
  docker compose --profile prod exec -T api python apps/api/manage.py seed_demo || true
fi

echo
echo "Done. https://$DOMAIN  (TLS is issued automatically once DNS points here)"
echo "Logins: owner@demo.talaqqi / Talaqqi@2026 (also supervisor@, teacher1-4@, parent1@, finance@)"
echo "Logs:   cd $DIR && docker compose --profile prod logs -f --tail=100"
