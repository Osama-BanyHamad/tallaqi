# Research — Infrastructure Service Costs (accessed 2026-09-08)

All figures read from official pages on 2026-09-08 unless marked **UNVERIFIED** (page JS-rendered, blocked, or not published). Video providers are in `video-providers.md`.

## 1. Object storage (S3-compatible)

| Provider | Storage | Ops | Egress | Free tier | Notes |
|---|---|---|---|---|---|
| Cloudflare R2 Standard | $0.015/GB-mo | Class A $4.50/M, Class B $0.36/M | **Free** | 10 GB, 1M A, 10M B per month | No minimum duration |
| Backblaze B2 | $6.95/TB-mo | Class A/B/C free per fetched page; Class D $0.004/10k | Free up to 3× stored volume, then $0.01/GB; unlimited free via Cloudflare/bunny/Fastly | 10 GB | No min duration/size |
| Hetzner Object Storage | €4.99/mo base incl. 1 TB storage + 1 TB egress; extra €0.0067/TB-h (≈ €4.98/TB-mo) | Free | Extra €1/TB | — | EU only (pressroom release; live page prices not rendered) |
| Wasabi | $7.99/TB-mo | Free | "No egress fees" but free only while egress ≤ stored volume | none; 1 TB min billable | 90-day minimum retention |
| AWS S3 Standard (us-east-1) | $0.023/GB | PUT $0.005/1k, GET $0.0004/1k | $0.09/GB first 10 TB (100 GB/mo free) | — | CloudFront: 1 TB/mo free, then $0.085/GB |
| DigitalOcean Spaces | $5/mo incl. 250 GiB; $0.02/GiB extra | — | 1 TiB incl.; $0.01/GiB extra | — | CDN included |

Self-host: MinIO repo **archived April 2026** (AGPLv3, source-only community); **Garage** v2.4.1 (AGPLv3); **SeaweedFS** (Apache-2.0; EE $2/TB-mo). Hetzner SX65-2 storage server (4× 16–22 TB) €82.30/mo + €39 setup.

Medium org (2 TB stored, 5 TB/mo egress): R2 ≈ $30; B2 ≈ $14–15; Hetzner ≈ €14; DO Spaces ≈ $80; S3+CloudFront ≈ $387; S3 direct ≈ $488.

## 2. Transactional email

| Provider | Free | Paid | Notes |
|---|---|---|---|
| Amazon SES | $200 credits for 6 months (old 3,000/mo tier not on current page) | $0.10/1,000 à la carte | Dedicated IP $24.95/mo; sandbox until production access |
| Postmark | 100/mo | Basic $15/mo (10k), $1.80/1k over; Pro $16.50 ($1.30/1k) | 45-day retention |
| Resend | 3,000/mo, 100/day | Pro $20/mo (50k), $35 (100k); Scale from $90 | Dedicated IP $30/mo |
| Brevo | 300/day | Starter $9/mo from 5k; Professional $499 (150k) | intermediate tiers UNVERIFIED |
| Mailgun | 100/day | Basic $15 (10k); Foundation $35 (50k, 1 dedicated IP); Scale $90 (100k) | |
| SendGrid (Twilio) | 60-day trial only | Essentials from $19.95; Pro from $89.95 | |
| Self-host | Postal (MIT), Haraka (MIT), Stalwart (AGPL + enterprise) | VPS + IP warm-up (2–6 weeks) | Hetzner blocks port 25 until first invoice paid + request |

Medium org (2,000/day ≈ 60k/mo): SES ≈ $6; Resend $35; Mailgun ≈ $48; Postmark ≈ $80.

## 3. SMS

Twilio outbound per segment (verified): US $0.0083; UK $0.056; Saudi $0.1949; Jordan $0.4429; Egypt $0.3959; Pakistan $0.4734; Indonesia $0.4414. AWS End User Messaging (verified CSV): Saudi $0.195; Jordan $0.350; Egypt $0.314; Pakistan $0.452; Indonesia $0.428; UK $0.05; US ≈ $0.012 incl. carrier fee. Twilio Verify $0.05 per successful verification + channel cost. Vonage per-country prices UNVERIFIED (403).

Regional: Unifonic plans from $499/mo (per-SMS not published); Msegat (KSA) points system, sender-name licence 230 SAR/year, SAR/point UNVERIFIED; SMS Misr (Egypt) EGP 1.00/SMS at 5k down to EGP 0.38 at 1M; Umniah/Zain (Jordan) quote only; Africa's Talking pricing page 403, Kenya sender ID KES 8,700 one-off.

Sender-ID regulation (Twilio guideline pages): **Saudi (CST)** alphanumeric pre-registration required, ~2 weeks, promotional IDs need "-AD" suffix and 09:00–20:00 window, Twilio cannot register domestic brands; **UAE (TDRA)** registered IDs only, $225 setup + $115/mo per international sender ID (snippet); **Jordan (TRC)** pre-registration required, ~12 days, marketing IDs prefixed "adv", no marketing after 21:00, Zain/Orange block generic IDs; **Egypt (NTRA)** domestic registration required (~3 weeks), marketing curfew 21:00–09:00; **Pakistan (PTA)** not required on Twilio but IDs may be overwritten.

Medium org (9,000 SMS/mo): Twilio Jordan ≈ $3,986; Saudi ≈ $1,754; Egypt ≈ $3,563; Pakistan ≈ $4,261. Local aggregator Egypt ≈ EGP 6,300. Conclusion: international-route SMS into JO/EG/PK is 20–50× costlier than local aggregators; prefer WhatsApp authentication or local aggregators for OTP.

## 4. WhatsApp Business Platform (Meta Cloud API)

Verified model (developers.facebook.com/docs/whatsapp/pricing): per-message pricing since 1 July 2025; only delivered template messages (marketing, utility, authentication) are charged; service conversations free and unlimited since 1 Nov 2024; non-template messages inside the 24-hour customer service window free; utility templates inside the window free; volume tiers apply to utility/authentication only; authentication-international rate for many markets (Egypt, Pakistan, Saudi, UAE, Indonesia, India). Rate cards effective 1 July 2026 (CSV links JS-injected, not fetched). 2026 changes: SAR/AED billing currencies from April 2026; higher Saudi marketing rate ($0.0501 from $0.0455 per Alibaba BSP notice); Pakistan utility/auth $0.01 (from $0.0054).

Per-message USD (mostly BSP/third-party mirrors, treat as provisional): Saudi utility/auth ≈ $0.0107, auth-international ≈ $0.0597, marketing $0.0501; Pakistan utility/auth $0.01; Egypt utility ≈ $0.0073, auth ≈ $0.013; Indonesia utility/auth ≈ $0.025; UK utility ≈ $0.022; US utility/auth $0.0034 (Twilio official). Jordan falls under "Rest of Middle East" (numbers UNVERIFIED).

BSP fees: Meta direct none; Twilio +$0.005/message; 360dialog €49/number/month, no markup; Gupshup $0.001/message. Requirements: Meta business verification to scale limits (250 → 2,000 → 10k → 100k), templates approved per category (≤ 24 h review), explicit opt-in.

Medium org (5,000 utility + 3,000 auth per month): Saudi ≈ $86 Meta (+$40 Twilio); Egypt ≈ $76; Pakistan ≈ $80; Indonesia ≈ $200.

## 5. Push notifications

FCM and APNs: no per-message fee (Apple Developer Program $99/yr). Expo push free (600/s limit). OneSignal free ≤ 1,000 MAU, Growth from $19/mo ($0.012/MAU mobile). Novu: MIT core; cloud free 10k runs/mo, Pro $30, overage $1.20/1k. ntfy (Apache-2.0/GPLv2, self-host), Gotify (MIT, Android/web only). Web Push (VAPID) free; iOS 16.4+ for home-screen web apps. Medium org (5,000/day): $0 with FCM/APNs direct.

## 6. Speech recognition (optional YELLOW feature)

Managed (per minute unless noted): OpenAI whisper-1 $0.006; gpt-4o-mini-transcribe $0.003; Deepgram Nova-3 $0.0043 batch / $0.0048 streaming (Arabic incl. ar-JO, ar-SA, ar-EG); AssemblyAI Universal-2 $0.15/hr (Arabic "good" tier); Google STT v2 $0.016 standard (current table UNVERIFIED), 60 min/mo free; Azure per-hour UNVERIFIED (F0 5 h/mo free); ElevenLabs Scribe v2 $0.22/hr; Gladia $0.20–0.61/hr; Speechmatics $0.129/hr batch; Groq whisper-large-v3-turbo $0.04/hr; Mistral Voxtral Mini Transcribe 2 $0.003/min (13 languages incl. Arabic), realtime $0.006; DeepInfra whisper-large-v3-turbo $0.0002/min.

Self-host: Whisper large-v3 / turbo (MIT), faster-whisper (MIT; ≈ 46× real-time batched on an RTX 3070 Ti), whisper.cpp (MIT, CPU-capable); Parakeet/Canary have **no Arabic**; Voxtral-Mini-4B-Realtime-2602 (Apache-2.0) has Arabic (FLEURS WER 22.5%). GPU: RunPod RTX 4090 $0.34/hr community ($0.74 secure), L4 $0.44–0.49/hr, A40 $0.35–0.49; AWS g6.xlarge ≈ $0.805/hr (third party); Lambda A10 $1.29/hr; Hetzner GEX45 price UNVERIFIED (≈ €184–250 third party).

Quran-specific models on Hugging Face: tarteel-ai/whisper-base-ar-quran (Apache-2.0, WER 5.75%, 2022); tarteel-ai/whisper-tiny-ar-quran (Apache-2.0, WER 7.05%); mohammed/fastconformer-quran-ar (**CC-BY-4.0**, NVIDIA FastConformer fine-tune on tarteel-ai/everyayah, streaming capable, June 2026); Muno459/fastconformer-quran and -streaming (**NPL-1.1 non-commercial**, WER 5.41% on leakage-free benchmark, phone-audio ≈ 20%); Quran-Lab/zipformer_p-arabic-v3 (phoneme/tajweed-aware, **NPL-1.2 non-commercial**); rabah2026/wav2vec2-large-xlsr-53-arabic-quran (Apache-2.0 model, CC-BY-NC-SA data). Datasets: tarteel-ai/everyayah (labelled CC-BY-4.0, 117 GB; rights to underlying recordings unclear, see audio research); IqraEval mispronunciation datasets and ArabicNLP 2025 shared task; obadx/muaalem-annotated-v3 (MIT, 848 h, tajweed attributes); obadx/qdat (MIT). Tarteel has no public API (support article) and points to QUL.

Compute estimate for 220,000 audio-min/month (1,000 students × 10 min × 22 days): DeepInfra turbo ≈ $44; Groq turbo ≈ $147; AssemblyAI ≈ $550; Mistral/OpenAI mini ≈ $660; Deepgram ≈ $950; dedicated RunPod 4090 24/7 ≈ $248–540 (peak concurrency is the constraint, not total minutes).

Key takeaway: generic Arabic ASR plus text diff catches word-level mismatches only; phoneme-level Tajweed detection needs the IqraEval/Quran-Lab class of models, most of which are non-commercial. Commercially clean starting points: mohammed/fastconformer-quran-ar (CC-BY-4.0), tarteel whisper-base-ar-quran (Apache-2.0).

## 7. LLM APIs (optional)

Per million tokens input/output (official pages 2026-09-08): Claude Haiku 4.5 $1/$5; Sonnet 5 $2/$10; Opus 5 $5/$25; OpenAI GPT-5-nano $0.05/$0.40, GPT-5.6 Luna $0.20/$1.20, GPT-5.4-mini $0.75/$4.50; Gemini 2.5 Flash-Lite $0.10/$0.40, 2.5 Flash $0.30/$2.50; Mistral Small 4 $0.15/$0.60, Ministral 3 8B $0.15/$0.15; Groq gpt-oss-20b $0.075/$0.30; DeepInfra Llama 3.3 70B $0.10/$0.32; self-host vLLM (Apache-2.0) on RunPod L4 ≈ $358/mo flat. For 20M in + 6M out tokens/month: $1.44 (DeepInfra gpt-oss-20b) to $250 (Opus 5). Dedicated GPU only justified for data residency.

## 8. Managed PostgreSQL and Redis

Neon Launch $0.106/CU-hour + $0.35/GB-mo (1 CU always-on + 50 GB ≈ $95). Supabase Pro $25/mo + compute add-ons (Small $15, Medium $60, Large $110), storage $0.125/GB (≈ $35–80). Crunchy Bridge Standard-8 $140. DigitalOcean Managed PG 4 GiB/2 vCPU $60.90 single, ≈ $122 with standby. AWS RDS UNVERIFIED (JS-rendered; ≈ $190–215 order of magnitude for db.t4g.medium Multi-AZ + 100 GB). Hetzner self-managed: server + 20% backup add-on + €0.50 IPv4 + B2 offsite backups ($6.95/TB). Backup tools: pgBackRest (MIT), WAL-G (Apache-2.0), Barman (GPLv3).

Redis/Valkey: Upstash free 500k commands/mo; PAYG $0.2/100k commands; fixed 1 GB $20/mo. Redis Cloud Essentials from $5/mo. Licenses: Redis 8+ tri-license (RSALv2/SSPL/AGPLv3); **Valkey BSD-3** (recommended for self-host); Dragonfly BSL 1.1.

## 9. Hosting baseline

Hetzner Cloud (EUR, excl. VAT, effective 15 June 2026, from official price-adjustment doc): CX23 2 vCPU/4 GB €5.49; CX33 4/8 €8.49; CX43 8/16 €15.99; CX53 16/32 €29.49; CAX11–41 (ARM) €5.99/10.49/20.99/40.99; CCX13 €42.99; CCX23 €85.99; CCX33 €138.49; CCX43 €275.99. Backups 20% of server price; IPv4 €0.50/mo; extra traffic €1/TB; 20 TB included (EU). Dedicated AX41-1-LTD €57.30; AX42-1-LTD €77.30; AX102-1-LTD €157.30; AX162-1-LTD €317.30. Load balancer and volume prices UNVERIFIED.

DigitalOcean: Basic 2 vCPU/4 GiB $24; 4/8 $48; 8/16 $96; GP 4/16 $126; backups 20–30%; volumes $0.10/GiB; LB $12/node; overage $0.01/GiB. Fly.io: shared-cpu-1x 1 GB $5.92; performance-1x 4 GB $42.58; egress $0.02/GB; Managed PG from $38. Railway: Hobby $5, Pro $20/workspace, ≈ $20/vCPU-mo, $10/GB-mo, egress $0.05/GB. Render: Starter $7, Standard $25, Pro $85; Postgres $19–75; bandwidth overage $0.15/GB. Coolify (Apache-2.0; cloud $5/mo base), Dokploy (Apache-2.0 + proprietary dir; cloud $4.50/server).

Computed: small center single VPS = Hetzner CX23 + backups + IPv4 ≈ **€7.09/mo** (CX33 ≈ €10.69); DigitalOcean 2/4 ≈ $28.80. Medium org (2 app + 1 DB + LB) ≈ **€32–73/mo** on Hetzner Cloud (+ LB/volume), ≈ $195 on DigitalOcean. Large (10k students sketch) ≈ €150–415/mo Hetzner Cloud or ≈ €411 dedicated, ≈ $1,090 DigitalOcean.

## 10. Observability

Sentry cloud: Developer free (5k errors, 1 user); Team $26/mo annual; Business $80/mo; self-hosted FSL license needs 16 GB RAM. GlitchTip: hosted free 1k events, Small $15/mo (100k); self-host MIT. Grafana Cloud free (10k series, 50 GB logs, 3 users); Pro $19 + usage. SigNoz (MIT core; cloud from $49). OpenObserve (AGPL). Uptime Kuma (MIT). UptimeRobot free 50 monitors. Typical hosted stack ≈ $15–44/mo; self-hosted ≈ VPS only.

## 11. Payment gateways (merchant availability by country)

- **Stripe direct**: UAE and Malaysia fully; Indonesia/India "Preview"; Nigeria etc. via Paystack; **Jordan, Saudi, Egypt, Pakistan, Türkiye not listed**. Stripe Atlas possible but "can't guarantee approval", $500 + $100/yr, US phone required.
- **PayPal**: receive/withdraw in Jordan, Saudi, UAE, Indonesia; Egypt, Pakistan, Nigeria absent from the eligibility table.
- **Paddle** (MoR, 5% + 50¢): software-only AUP; live tuition/coaching likely out of scope. Lemon Squeezy UNVERIFIED (403).
- **Saudi**: Paymob KSA 2.9% + SAR 1 (daily settlement); Telr SAR 99–259/mo with mada 1%, STC Pay 0.9%, cards 2.6–3% + SAR 1; Moyasar self-serve (pricing via sales); HyperPay sales-led; Tap (pricing not public); mada scheme fee capped 1%/SAR 200.
- **Egypt**: Paymob 2.75% + EGP 3 (weekly); Paystack 2.7% + EGP 2.5 (Meeza 2.0%), intl 3.5%; Fawry custom fees with tokenized recurring.
- **Pakistan**: Safepay 2.9% + Rs 30, wallets 1.5%, subscriptions free; JazzCash business (fees unpublished); Paymob PK UNVERIFIED.
- **UAE**: Stripe 2.9% + AED 1; Paymob 2.9% + AED 1; Telr plans.
- **Jordan**: HyperPay (sales-led), Tap (en-jo site), MyFatoorah (JO listed; pricing page cert expired), PayPal; CliQ only via bank/PSP (jopacc.com unreachable); eFAWATEERcom unreachable.
- **Indonesia**: Midtrans 2.9% + IDR 2,000, QRIS 0.7%; Xendit UNVERIFIED. **Malaysia**: Stripe 3% + RM1, FPX 3% + RM1. **Nigeria**: Paystack 1.5% + NGN 100 (cap NGN 2,000); Flutterwave 2% local / 4.8% intl.

Implication: the platform must ship a **manual/bank-transfer/cash** payment path as first-class, plus a gateway adapter interface; no single gateway covers the core markets.

## 12. Monthly infrastructure estimate excluding video

| Deployment | Compute + DB | Storage | Email | Push | Observability | SMS/WhatsApp (notification budget) | **Total (order of magnitude)** |
|---|---|---|---|---|---|---|---|
| Small center (100 students), self-host | Hetzner CX33 ≈ €11 | R2 ≈ $1 | SES ≈ $1 | $0 (FCM/APNs) | GlitchTip self-host $0 / Sentry free | WhatsApp utility ≈ $5–15 | **≈ $15–30/mo** |
| Medium org (1,000), self-host 3 nodes | Hetzner ≈ €40–80 | R2 ≈ $30 / B2 ≈ $15 | SES ≈ $6 | $0 | Sentry Team $26 or self-host | WhatsApp ≈ $80–200 | **≈ $150–350/mo** |
| Large org (10,000), HA | Hetzner ≈ €400–450 or DO ≈ $1,100 | ≈ $100–300 | ≈ $60 | $0–30 | ≈ $50–150 | ≈ $500–2,000 (channel mix dependent) | **≈ $1,200–4,000/mo** |

## Sources

See per-section source lists in the agent reports; principal official pages: developers.cloudflare.com/r2/pricing/; backblaze.com/cloud-storage/pricing; hetzner.com/pressroom/object-storage/; docs.hetzner.com/general/infrastructure-and-availability/price-adjustment/; docs.hetzner.com/cloud/billing/faq/; aws.amazon.com/s3/pricing/; aws.amazon.com/ses/pricing/; postmarkapp.com/pricing; resend.com/pricing; mailgun.com/pricing/; twilio.com/en-us/sms/pricing/{us,jo,sa,eg,pk,gb,id}; twilio.com/en-us/verify/pricing; twilio.com/en-us/whatsapp/pricing; aws.amazon.com/end-user-messaging/pricing/ (CSV); developers.facebook.com/docs/whatsapp/pricing; developers.facebook.com/docs/whatsapp/pricing/updates-to-pricing; 360dialog.com/pricing; gupshup.ai ISV pricing; unifonic.com/en/pricing; msegat.com/en/faqs/; sms.com.eg; twilio.com/en-us/guidelines/{sa,ae,jo,eg,pk}/sms; firebase.google.com/pricing; onesignal.com/pricing; novu.co/pricing; developers.openai.com/api/docs/pricing; deepgram.com/pricing; assemblyai.com/pricing; elevenlabs.io/pricing/api; mistral.ai/news/voxtral-transcribe-2/; deepinfra.com; runpod.io/pricing; lambda.ai/pricing; huggingface.co (models/datasets listed above); platform.claude.com/docs/en/docs/about-claude/pricing; ai.google.dev/gemini-api/docs/pricing; neon.com/pricing; supabase.com/pricing; crunchydata.com/pricing; digitalocean.com/pricing/managed-databases; upstash.com/pricing/redis; redis.io/pricing/; digitalocean.com/pricing/droplets; fly.io/docs/about/pricing/; railway.com/pricing; render.com/pricing; coolify.io/pricing; dokploy.com/pricing; sentry.io/pricing/; glitchtip.com/pricing; grafana.com/pricing/; stripe.com/global; stripe.com/{ae,my}/pricing; docs.stripe.com/atlas/signup; paypal.com/us/webapps/mpp/merchant-fees; developer.paypal.com/payouts/supported-features; paddle.com/pricing; paymob.com/en/pricing; paymob.ae/en/pricing; paymob.sa/en/pricing; telr.com/pricing/; getsafepay.pk/pricing; midtrans.com/pricing; flutterwave.com/{ng,ke,gh}/pricing; support.paystack.com/en/articles/2130306; razorpay.com/pricing/.
