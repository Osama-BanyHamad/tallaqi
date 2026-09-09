# Deploying Talaqqi on DigitalOcean (tallaqi.com)

Single droplet, Docker Compose, Caddy with automatic TLS. About 15 minutes.

## 1. Create the droplet

DigitalOcean → Create → Droplets:

| Setting | Value |
|---|---|
| Region | Frankfurt (FRA1) or Amsterdam (AMS3) — closest to Jordan/Gulf with good peering |
| Image | Ubuntu 24.04 LTS |
| Size | Basic · Regular · **2 vCPU / 4 GB** ($24/mo). 1 vCPU / 2 GB works for a demo but the first Docker build is slow |
| Authentication | **SSH key** (paste your public key; see below) |
| Hostname | `tallaqi` |

Optional but recommended: enable **Backups** (+20%).

## 2. DNS (at your registrar or DigitalOcean DNS)

| Type | Name | Value | TTL |
|---|---|---|---|
| A | `@` | droplet IPv4 | 300 |
| A | `www` | droplet IPv4 | 300 |

TLS is issued automatically by Caddy the first time the domain resolves to the droplet. Set DNS before running the deploy so the certificate is issued on the first start.

## 3. Deploy (one command)

SSH in as root and run:

```bash
curl -fsSL https://raw.githubusercontent.com/Osama-BanyHamad/tallaqi/main/infra/scripts/deploy-do.sh | bash -s -- tallaqi.com
```

The script installs Docker, opens ports 22/80/443, clones the repo into `/opt/talaqqi`, generates `.env` with random secrets, builds and starts PostgreSQL, Valkey, the API, the web app, and Caddy, runs migrations, loads and verifies the Quran Core, and seeds the demo tenant and users.

Re-running the same command later pulls the latest code, rebuilds, migrates, and keeps the data. Use `SEED=0` to skip seeding.

## 4. Verify

- https://tallaqi.com → public site · https://tallaqi.com/login → app · https://tallaqi.com/api/docs/ → API docs · https://tallaqi.com/readyz → `quran_core: ok (… verified)`.
- Demo logins (tenant `demo`, password `Talaqqi@2026`): `owner@demo.talaqqi`, `supervisor@`, `teacher1@`–`teacher4@`, `parent1@`, `finance@`.

## 5. Day-2 operations

```bash
cd /opt/talaqqi
docker compose --profile prod logs -f --tail=100          # logs
docker compose --profile prod exec api python apps/api/manage.py run_decay_all   # daily decay + plans (add to cron: 0 2 * * *)
docker compose --profile prod exec postgres pg_dump -U postgres talaqqi | gzip > /root/talaqqi-$(date +%F).sql.gz   # backup
```

Daily cron for decay and plans:

```bash
(crontab -l 2>/dev/null; echo "0 2 * * * cd /opt/talaqqi && docker compose --profile prod exec -T api python apps/api/manage.py run_decay_all >> /var/log/talaqqi-decay.log 2>&1") | crontab -
```

## 6. Mobile app against production

```bash
cd apps/mobile && flutter build apk --dart-define=API_URL=https://tallaqi.com
```

## Notes

- The API role is a non-superuser (`talaqqi_app`) so PostgreSQL row-level security applies; passwords are generated into `.env` on first run. Keep `/opt/talaqqi/.env` private.
- Recording, AI, and finance modules are off by default; enable per tenant from the app.
- To reset the demo data: `docker compose --profile prod exec api python apps/api/manage.py seed_demo --reset`.

## Visit statistics

Caddy writes a JSON access log to `/opt/talaqqi/logs/caddy/access.log` (rolled, kept 30 days). Every hour `infra/scripts/stats.sh` runs GoAccess (Docker image, no third-party trackers, IPs anonymized in the report) and writes `/opt/talaqqi/stats/index.html`, served at `https://tallaqi.com/stats/` behind HTTP basic auth.

- Credentials: `STATS_USER` / `STATS_HASH` in `/opt/talaqqi/.env`. Generate a hash with `docker run --rm caddy:2 caddy hash-password --plaintext 'your-password'`.
- Rebuild the report on demand: `bash /opt/talaqqi/infra/scripts/stats.sh`.
- The report excludes `/readyz`, `/healthz`, and requests from `Python-urllib` (our own verification scripts).
