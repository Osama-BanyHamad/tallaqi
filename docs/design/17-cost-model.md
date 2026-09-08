# 17 — Cost Model (Free / Low-Cost / Scalable options per dependency)

Sources and unverified items: `docs/research/infra-costs.md` and `docs/research/video-providers.md` (official pricing pages, accessed 2026-09-08). Figures are order-of-magnitude planning numbers; VAT excluded.

## 17.1 Per-dependency options

| Dependency | Free / open-source | Low-cost managed | Scalable managed | Notes |
|---|---|---|---|---|
| Compute | Any VPS: Hetzner CX23 €5.49, CX33 €8.49; Coolify/Dokploy (Apache-2.0) for self-managed PaaS | DigitalOcean 2/4 $24; Fly.io shared-cpu $6–11 | Hetzner CCX/dedicated AX (€57–317), DigitalOcean GP, Kubernetes | Hetzner has no Middle East/South Asia region |
| PostgreSQL | Self-managed on the VPS + pgBackRest/WAL-G to object storage | Supabase Pro ≈ $35; Neon Launch ≈ $95 (1 CU + 50 GB); DO Managed 4 GB $61 | DO HA ≈ $122; Crunchy Standard-8 $140; RDS (unverified ≈ $200) | Backups: B2 $6.95/TB |
| Cache/queue | Valkey (BSD-3) on the VPS | Upstash fixed 1 GB $20 | Redis Cloud Pro | Avoid Redis 8 licensing questions by standardizing on Valkey |
| Object storage | Garage (AGPL) / SeaweedFS (Apache-2.0) on a Hetzner storage box or SX server (€82) | Cloudflare R2 ($0.015/GB, free egress) ≈ $30 for 2 TB; Backblaze B2 ≈ $14; Hetzner Object Storage ≈ €14 | R2/B2 at scale; S3+CloudFront ≈ $387 for the same profile | MinIO community archived April 2026 |
| Video | LiveKit OSS + coturn on Hetzner: ≈ $20 (A) / $137 (B) / $660 (C) | LiveKit Cloud Ship $50 (A), ≈ $196–365 (B); Stream Video $0–134 | LiveKit Cloud Scale ≈ $1,654–3,018 (C audio); Cloudflare RealtimeKit at GA ≈ $2,187–3,892 | Audio-only default; TURN via Cloudflare $0.05/GB after 1 TB |
| Email | Self-hosted Postal/Stalwart (needs IP warm-up; Hetzner blocks port 25 initially) | Amazon SES $0.10/1k (≈ $6 for 60k/mo); Resend $20–35 | SES with dedicated IPs; Postmark/Mailgun tiers | |
| SMS | None truly free; local aggregators cheapest (Egypt EGP 0.38–1.00) | Regional aggregators (Msegat, SMS Misr, Umniah quote) | Twilio/AWS international routes ($0.19 Saudi, $0.35–0.44 Jordan, $0.31–0.40 Egypt, $0.45–0.47 Pakistan) | Sender-ID registration required in KSA/UAE/JO/EG; prefer push/WhatsApp |
| WhatsApp | Meta Cloud API direct (no BSP fee); service messages free inside 24-h window | 360dialog €49/number/month | Twilio +$0.005/message; Gupshup $0.001/message | Utility/auth ≈ $0.01 (Saudi, Pakistan), ≈ $0.007–0.013 (Egypt), ≈ $0.025 (Indonesia); auth-international higher |
| Push | FCM/APNs free (Apple Developer $99/yr); Web Push free | OneSignal free ≤ 1,000 MAU, Growth $19+ | Novu cloud $30+ or self-host (MIT) | |
| AI / ASR (optional) | Self-hosted faster-whisper / mohammed/fastconformer-quran-ar (CC-BY-4.0) / tarteel whisper-base-ar-quran (Apache-2.0) on a RunPod 4090 ≈ $248/mo or on-device | DeepInfra whisper-turbo $0.0002/min (≈ $44 for 220k min); Groq $0.04/hr | Deepgram Nova-3 $0.0043/min (≈ $950); AssemblyAI $0.15/hr (≈ $550) | Strongest Quran models (Quran-Lab, Muno459) are non-commercial licensed |
| LLM (optional) | Self-hosted vLLM on L4 ≈ $358/mo flat; or none | Small models $1–15/month for 26M tokens (Haiku $50) | Frontier models $100–250/month at the same volume | Not required by any core feature |
| Observability | Prometheus + Grafana + Loki, GlitchTip (MIT), Uptime Kuma (MIT) self-hosted | GlitchTip hosted $15; Grafana Cloud free tier; UptimeRobot free | Sentry Team $26+ / Business $80+; Grafana Cloud Pro | |
| Payments | Manual/bank/cash (no fees) | Paymob 2.75–2.9% + fixed; Safepay 2.9% + Rs 30; Telr plans with mada 1% | Stripe where available (UAE, Malaysia, EU/US) 2.9% + fixed; Paddle 5% + 50¢ for software-only sales | Stripe unavailable in Jordan, Saudi, Egypt, Pakistan |
| Fonts | DigitalKhatt (OFL), Amiri (OFL), SIL fonts (OFL) | — | — | KFGQPC free but no-derivatives |
| CDN | Cloudflare free plan in front of R2 | bunny.net | Cloudflare paid, CloudFront | |

## 17.2 Deployment totals (order of magnitude, per month)

| Deployment | Compute + DB + cache | Storage | Video (audio-first) | Email/push | Notifications (SMS/WhatsApp) | Observability | **Total** |
|---|---|---|---|---|---|---|---|
| Small center, 100 students, in-person + some online, self-hosted single VPS | Hetzner CX33 + backups ≈ €11 | R2 ≈ $1 | self-hosted LiveKit on the same or a €5 box ≈ $6–20 | ≈ $1 (SES) + $0 | WhatsApp utility ≈ $5–15 | $0 (self-host) | **≈ $25–50** |
| Small center on managed services | DO 2/4 $29 + Supabase $35 | R2 $1 | LiveKit Cloud Ship $50 | $1 | $10 | GlitchTip $15 | **≈ $140** |
| Medium org, 1,000 students, 3 nodes self-hosted | Hetzner ≈ €40–80 | R2 ≈ $30 | self-hosted ≈ $137 | ≈ $6 | ≈ $80–200 | Sentry Team $26 or $0 | **≈ $300–500** |
| Medium org on managed | DO ≈ $195 + DO PG HA $122 | R2 $30 | LiveKit Cloud ≈ $200–365 | $6 | $80–200 | $26 | **≈ $650–950** |
| Large org, 10,000 students, HA self-hosted | Hetzner dedicated ≈ €411 (+ setup) | ≈ $100–300 | self-hosted ≈ $660 (+ Cloudflare TURN ≤ $125) | ≈ $60 | ≈ $500–2,000 | ≈ $50–150 | **≈ $1,800–3,700** |
| Large org on managed | DO ≈ $1,100 + managed PG HA | ≈ $300 | LiveKit Cloud Scale ≈ $1,650–3,000 | $60 | $500–2,000 | $150 | **≈ $3,800–6,700** |

## 17.3 Cost controls built into the product

1. Audio-only classroom default; video requires teacher action and tenant opt-in.
2. Push and in-app as default channels; SMS only for verification fallbacks; WhatsApp utility templates inside the free service window where possible.
3. Reciter audio served through CDN with client caching and offline packs (fewer origin reads).
4. Retention decay and plan generation batched per tenant during off-peak hours.
5. Per-tenant usage metrics (minutes, storage, notifications) visible to admins.
6. Everything runs with AI disabled; ASR jobs are queued and budgeted per tenant when enabled.
7. Single-VPS profile as a first-class, tested deployment.
