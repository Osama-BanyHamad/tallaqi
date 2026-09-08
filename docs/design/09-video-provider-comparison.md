# 09 — Video Provider Comparison and Recommendation

Full research with sources and arithmetic: `docs/research/video-providers.md` (official pricing pages accessed 2026-09-08; items that could not be verified are flagged there).

## 9.1 What the classroom needs from a provider

| Requirement | Why |
|---|---|
| Audio quality on poor networks (Opus, FEC, DTX) | Recitation is audio; students in South Asia, Africa, rural MENA |
| Recording can be **absent**, not just off | Live-only promise |
| Self-host **and** managed paths with the same SDK | Open-source project; small centers self-host, large orgs pay |
| First-party Flutter, React Native/web SDKs | Our app stack |
| Regions near the Gulf, South Asia, Africa | Latency |
| Waiting room, per-participant publish grants, breakouts | Halaqah mode |
| Short-lived scoped tokens | Security |
| Cheap at 1:1 and group scale | Social-impact economics |

## 9.2 Comparison (verified pricing, 2026-09-08)

| Provider | Model | Audio-only price | Video (360p) price | Free tier | Recording controllable | Self-host | Open source | Flutter / RN / Web | Gulf/Asia presence | Notes |
|---|---|---|---|---|---|---|---|---|---|---|
| **LiveKit** (OSS + Cloud) | plan + participant-min + downstream GB | Ship $50/mo incl. 150k min then $0.0005/min; Scale $500 incl. 1.5M then $0.0004 | + $0.12→0.10/GB over plan | 5k min, 50 GB, 100 concurrent | Egress is a separate opt-in service; not deployed when self-hosting | **Yes**, same code | Apache-2.0 | first-party all three | Cloud PoPs in UAE, Saudi, India, South Africa | E2EE documented; Build plan caps 100 concurrent |
| Daily | participant-min | $0.00099→0.00036 | $0.004→0.0015 | 10k min | Per-room opt-in | No | No | first-party | not published | Volume tiers unpublished between 100k and 50M |
| Agora | per 1,000 min by resolution | $0.99/1k | $3.99/1k (HD tier) | 10k min | Separate service | No | No | first-party | "Global" routing, no ME geofence | Resolution-aggregate billing |
| 100ms | participant-min | $0.001 | $0.004 | 10k min | Template setting | No | No | first-party | not published | 100/room cap, no E2EE |
| Cloudflare RealtimeKit (ex-Dyte) | participant-min | $0.0005 (GA) | $0.002 (GA) | beta free | Opt-in | No | No | unverified | anycast | Beta; SDK list vague |
| Cloudflare SFU + TURN | per GB | $0.05/GB after 1 TB | same | 1 TB | n/a | No | No | DIY | anycast | Cheapest bytes, most engineering |
| Stream Video | per 1,000 min by resolution | $0.30/1k | $0.75/1k (SD) | $100/mo credit | Per call type | No | No | first-party | not published | Cheapest managed audio |
| Jitsi / JaaS (8x8) | MAU | $99/300 MAU… unlimited minutes | same | 25 MAU | JWT features | **Yes** (Jitsi Meet) | Apache-2.0 | embed-style SDKs | not published | E2EE ≤ 20 participants |
| Zoom Video SDK | credits | ≈ $0.0035/min [unverified] | same | 20 credits | API-initiated | No | No | wrapper SDKs | not published | Pricing pages unreachable |
| Vonage Video | participant-min | $0.0041 [semi-verified] | same | trial only | Opt-in | No | No | RN yes, Flutter unverified | not published | Most expensive |
| Amazon Chime SDK | attendee-min | $0.0017 | same | none | Opt-in | No | No | **none** | Mumbai, Cape Town, no Gulf | Excluded |

## 9.3 Scenario costs (USD/month)

Assumptions: 4.33 weeks/month; each student 2 × 45 min/week = 389.7 min/month; 1:1 model = 2 participants per session; Halaqah model = 8 students + 1 teacher (teacher minutes shared). Participant-minutes: A 1:1 = 77,940; A Halaqah = 43,841; B 1:1 = 779,400; B Halaqah = 438,413; C 1:1 = 7,794,000; C Halaqah = 4,384,125.

### Audio-only (recommended default)

| Provider | A 1:1 | A Halaqah | B 1:1 | B Halaqah | C 1:1 | C Halaqah |
|---|---|---|---|---|---|---|
| LiveKit Cloud | $50 | $50 | $365 | $196 | $3,018 | $1,654 |
| Daily / Agora / 100ms | ≈ $67 | ≈ $34 | ≈ $762 | ≈ $424 | ≈ $7,700 (volume floor ≈ $2,800) | ≈ $4,330 (floor ≈ $1,575) |
| Cloudflare RealtimeKit (GA) | $34 | $17 | $385 | $214 | $3,892 | $2,187 |
| Stream Video | $0 | $0 | $134 | $32 | $2,238 | $1,215 |
| JaaS | $99 | $99 | $499 | $499 | ≈ $8,424 | ≈ $8,424 |
| **Self-hosted LiveKit on Hetzner + coturn** | **≈ $20** | ≈ $20 | **≈ $137** | ≈ $137 | **≈ $660** | ≈ $660 |

### 360p video

| Provider | A 1:1 | A Halaqah | B 1:1 | B Halaqah | C 1:1 | C Halaqah |
|---|---|---|---|---|---|---|
| LiveKit Cloud | $50 | $52 | $500 | $480 | $5,056 | $3,984 |
| Daily / Agora / 100ms | ≈ $272 | ≈ $135 | ≈ $3,078 | ≈ $1,714 | ≈ $31,100 (floor ≈ $11,700) | ≈ $17,500 (floor ≈ $6,560) |
| Stream Video | $0 | $0 | $485 | $558 | $5,746 | $6,476 |
| Self-hosted LiveKit (Hetzner) | ≈ $20 | ≈ $20 | ≈ $137 | ≈ $137 | ≈ $660 (+ ≈ $125 if Cloudflare TURN) | ≈ $660 |

Self-hosted breakdown: A = 1× CX33 (€8.49) + backups ≈ €17; B = 1× CCX23 + CX23 TURN + CX23 Redis + backups ≈ €117; C = 3× CCX33 + 2× TURN nodes + Redis/LB + backups ≈ €564. Egress stays inside Hetzner's 20–30 TB/month allowance in all scenarios. Equivalent AWS egress alone would add ≈ $210 (audio C) to ≈ $2,040 (360p C). TURN cost with Twilio Mumbai at C would be ≈ $2,100 (avoid); Cloudflare TURN ≈ $0–125.

Self-hosting's hidden cost is operations: upgrades, TURN certificates, monitoring, on-call. Budget engineer hours; for a 1,000-student org this is typically a few hours per month once stable.

## 9.4 Recommendation

1. **Reference adapter: LiveKit.** Only provider where the same Apache-2.0 server, the same first-party Flutter/RN/web SDKs, and documented E2EE work identically self-hosted and on the managed cloud; recording is a separate egress component that self-hosters simply do not deploy; the cloud has verified PoPs in the UAE, Saudi Arabia, India, and South Africa. Cost: self-host ≈ $20 / $137 / $660 for A/B/C; cloud ≈ $50 / $196–365 / $1,654–3,018 audio.
2. **TURN: Cloudflare Realtime TURN** ($0.05/GB after 1 TB free) as the managed default for both modes; **coturn** for fully sovereign deployments.
3. **Second adapter: Jitsi/JaaS** for institutions that prefer MAU billing or already run Jitsi; self-hostable; weaker for deep UI customization.
4. **Community adapters**: Stream Video (cheapest managed audio) and Cloudflare RealtimeKit once GA. Neither is self-hostable, so they remain secondary.
5. **Excluded**: Vonage, Zoom, Chime (cost, no self-host, missing SDKs or regions).
6. **Audio-only default with 360p opt-in** is the single largest cost control: 3–8× cheaper than video at every provider.

## 9.5 Decision record

ADR-0007 "Video provider abstraction and LiveKit reference adapter" records this decision with the alternatives, the pricing snapshot date, and a review trigger (re-evaluate when LiveKit pricing changes, when Cloudflare RealtimeKit reaches GA, or annually).
