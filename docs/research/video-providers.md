# Research — Real-time Video/Audio Providers (accessed 2026-09-08)

All figures read from official pricing pages on 2026-09-08 unless flagged **[unverified]** (page unreachable; secondary source named).

## Assumptions used for scenarios

| Item | Value |
|---|---|
| Weeks/month | 4.33 |
| Student minutes/month per student | 2 × 45 × 4.33 = 389.7 |
| Student minutes A / B / C (100 / 1,000 / 10,000 students) | 38,970 / 389,700 / 3,897,000 |
| 1:1 model (teacher + student) | total participant-minutes = 2 × student minutes = 77,940 / 779,400 / 7,794,000 |
| Halaqah model (8 students + 1 teacher) | teacher minutes = student minutes ÷ 8 → total = 1.125 × = 43,841 / 438,413 / 4,384,125 |
| Bitrates | audio 40 kbps (0.3 MB/stream-min); 360p 400 kbps (3 MB/stream-min); 720p 1.5 Mbps (11.25 MB/stream-min) |
| Streams downloaded per participant | 1:1 → 1; Halaqah → 2 (active speaker + pinned) |
| Peak concurrency (self-host sizing) | classes in a ~6 h/day window, peak = 2× average → ≈ 14 / 144 / 1,444 concurrent participants (1:1) |
| EUR→USD | ≈ 1.17 (assumption) |

Downstream GB/month: audio 1:1 = 23 / 234 / 2,338 GB; audio Halaqah = 26 / 263 / 2,630 GB; 360p 1:1 = 234 / 2,338 / 23,382 GB; 360p Halaqah = 263 / 2,630 / 26,305 GB.

## Verified unit prices

**LiveKit Cloud** (https://livekit.com/pricing; quotas https://docs.livekit.io/deploy/admin/quotas-and-limits/): Build $0 (5,000 participant-min, 50 GB downstream, 100 concurrent participants cap, 2 concurrent egresses). Ship from $50/mo (150,000 participant-min then $0.0005/min; 250 GB then $0.12/GB; recording 600 min then $0.02/min video, $0.005/min audio). Scale from $500/mo (1.5M participant-min then $0.0004/min; 3 TB then $0.10/GB). Egress/recording is a separate opt-in service; when self-hosting, do not deploy the egress container. Regions incl. UAE, Saudi Arabia, India, South Africa, EU, UK, US, Brazil, Japan, Singapore, Australia (status.livekit.io). OSS server Apache-2.0; first-party Flutter (`livekit_client`), React Native, JS SDKs; E2EE documented for web/Flutter/RN.

**Daily** (https://www.daily.co/pricing/video-sdk/): 10,000 free min/month. Video $0.004 → $0.0015/participant-min (volume tiers); audio-only $0.00099 → $0.00036. Recording $0.01349/min video, $0.005 audio, only if started per room. 1,000 interactive participants. Official Flutter + RN SDKs. E2EE in SFU mode **[unverified]**.

**Agora** (https://www.agora.io/en/pricing/): 10,000 free min/month. Per 1,000 min: audio $0.99; video HD $3.99; Full HD $8.99; 2K $15.99. Billed on aggregate subscribed resolution. Cloud recording from $0.99/1,000 min, separate opt-in. 128 hosts/channel. Flutter + RN SDKs. No Middle East geofencing area (served via "Global").

**100ms** (https://www.100ms.live/pricing): 10,000 free min/month; $0.004/participant-min; audio-only $0.001/min; recording $0.0135/min, per-template setting, off by default. 100 A/V participants per room. Flutter + RN SDKs. No E2EE.

**Cloudflare RealtimeKit** (ex-Dyte; https://developers.cloudflare.com/realtime/realtimekit/pricing): beta and free currently; GA pricing published: A/V $0.002/min, audio-only $0.0005/min, 10,000 free min each; recording $0.010/min video. Flutter/RN SDK availability on the Cloudflare page **[unverified]**.

**Cloudflare Realtime SFU + TURN** (https://developers.cloudflare.com/realtime/sfu/pricing/, https://developers.cloudflare.com/realtime/turn/faq/): $0.05/GB egress, first 1,000 GB/month free (shared SFU + TURN). TURN free when used with the SFU. No Flutter/RN SDK, raw WebRTC API.

**Zoom Video SDK**: official pricing pages returned 404/JS-only shells. **[unverified, third party]** ≈ $0.0035/session-minute, $100/100 credits minimum. Flutter (wrapper) and RN SDKs exist.

**Vonage Video API**: pricing page returned 403. **[semi-verified, Vonage support article snippet]** $0.0041/participant-min up to 25 publishers.

**Stream Video** (https://getstream.io/video/pricing/): $100 free usage every month. Per 1,000 participant-min: audio $0.30; SD 480p $0.75; HD 720p $1.50; Full HD $3.00. Recording $1.50/1,000 call-min. Flutter, RN, JS SDKs.

**Amazon Chime SDK** (https://aws.amazon.com/chime/chime-sdk/pricing/): $0.0017/attendee-min, no free tier; media capture $0.0125/min opt-in. No official Flutter/RN SDKs; no Gulf media region.

**Jitsi as a Service (8x8)** (https://cpaas.8x8.com/en/pricing/jitsi-as-a-service-pricing/): MAU-priced, unlimited minutes: Developer free (25 MAU), Basic $99 (300), Standard $499 (1,500), Business $999 (3,000); overage $0.99/MAU; recording $0.01/min. 500 participants/meeting; E2EE ≤ 20 participants. Self-hosted Jitsi Meet Apache-2.0; RN + Flutter SDKs (embed style).

**Infrastructure & TURN**: Hetzner EU cloud includes 20 TB/month traffic (CCX33 30 TB); overage €1/TB **[third party]**; Hetzner plan prices (post June-2026 adjustment, from official docs price-adjustment page): CX23 €5.49, CX33 €8.49, CX43 €15.99, CX53 €29.49, CCX13 €42.99, CCX23 €85.99, CCX33 €138.49. No Hetzner region in the Middle East or South Asia. DigitalOcean: 2 vCPU/4 GB $24 (4 TB), 4/8 $48 (5 TB), overage $0.01/GiB. AWS egress ≈ $0.09/GB first 10 TB **[third party mirror]**. Cloudflare TURN $0.05/GB after 1 TB free. Twilio TURN $0.40/GB US/DE, $0.60/GB Singapore/Mumbai (https://www.twilio.com/en-us/stun-turn/pricing). Metered.ca TURN $99/150 GB … $499/2 TB (https://www.metered.ca/stun-turn). coturn: free (BSD).

## Comparison table

| Provider | Pricing model | Audio / 360p unit | Free tier | Recording disable-able | Self-host | Open source | Flutter | RN | Web | Regions of note | Max/room | E2EE |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| LiveKit Cloud | plan + participant-min + GB | $0.0005→0.0004/min + $0.12→0.10/GB | 5k min, 50 GB | Yes (egress opt-in) | Yes (same code) | Apache-2.0 | ✅ | ✅ | ✅ | UAE, KSA, India, ZA, EU | no stated cap | ✅ |
| Daily | participant-min | $0.00099→0.00036 / $0.004→0.0015 | 10k min | Yes | No | No | ✅ | ✅ | ✅ | not published | 1,000 | unverified |
| Agora | per 1,000 min by resolution | $0.99 / $3.99 per 1k | 10k min | Yes | No | No | ✅ | ✅ | ✅ | Global (no ME area) | 128 hosts | client-key |
| 100ms | participant-min | $0.001 / $0.004 | 10k min | Yes | No | No | ✅ | ✅ | ✅ | not published | 100 | ❌ |
| CF RealtimeKit | participant-min | $0.0005 / $0.002 (GA) | beta free | Yes | No | No | unverified | unverified | ✅ | CF anycast | n/s | n/s |
| CF SFU + TURN | per GB | $0.05/GB | 1,000 GB | n/a | No | No | DIY | DIY | API | CF anycast | n/a | DIY |
| Zoom Video SDK | credits | ~$0.0035/min [unverified] | 20 credits | Yes | No | No | ✅ | ✅ | ✅ | n/p | n/v | n/v |
| Vonage | participant-min | $0.0041 [semi-verified] | trial only | Yes | No | No | unverified | ✅ | ✅ | n/p | 25 pub | n/v |
| Stream Video | per 1,000 min by resolution | $0.30 / $0.75 per 1k | $100/mo | Yes | No | No | ✅ | ✅ | ✅ | n/p | ~1,000 | n/v |
| Chime SDK | attendee-min | $0.0017 | none | Yes | No | No | ❌ | ❌ | ✅ | Mumbai, Cape Town, no Gulf | 250 | ❌ |
| JaaS (8x8) | MAU | $99/300 MAU… | 25 MAU | Yes (JWT) | Yes (Jitsi) | Apache-2.0 | ✅ | ✅ | ✅ | n/p | 500 | ✅ (≤20) |
| Self-host LiveKit + coturn | VM + egress | see below | — | Yes | — | Apache-2.0 | ✅ | ✅ | ✅ | your choice | you decide | ✅ |

## Scenario costs (USD/month, list prices, after recurring free tier)

### Audio-only (recommended default)

| Provider | A 1:1 (77,940) | A Halaqah (43,841) | B 1:1 (779,400) | B Halaqah (438,413) | C 1:1 (7,794,000) | C Halaqah (4,384,125) |
|---|---|---|---|---|---|---|
| LiveKit Cloud | $50 (Ship) | $50 | $365 | $196 | $3,018 (Scale) | $1,654 |
| Daily | $67 | $34 | $762 | $424 | $7,706 (volume floor ≈ $2,800) | $4,330 (floor ≈ $1,575) |
| Agora | $67 | $34 | $762 | $424 | $7,706 | $4,330 |
| 100ms | $68 | $34 | $769 | $428 | $7,784 | $4,374 |
| CF RealtimeKit (GA) | $34 | $17 | $385 | $214 | $3,892 | $2,187 |
| CF SFU (raw GB) | $0 | $0 | $0 | $0 | $67 | $82 |
| Zoom [unverified] | $273 | $153 | $2,728 | $1,534 | $27,279 | $15,344 |
| Vonage | $320 | $180 | $3,196 | $1,797 | $31,955 | $17,975 |
| Stream | $0 | $0 | $134 | $32 | $2,238 | $1,215 |
| Chime | $133 | $75 | $1,325 | $745 | $13,250 | $7,453 |
| JaaS | $99 | $99 | $499 | $499 | ≈ $8,424 | ≈ $8,424 |

### 360p video (1:1 one stream; Halaqah two streams)

| Provider | A 1:1 | A Halaqah | B 1:1 | B Halaqah | C 1:1 | C Halaqah |
|---|---|---|---|---|---|---|
| LiveKit Cloud | $50 | $52 | $500 | $480 | $5,056 | $3,984 |
| Daily | $272 | $135 | $3,078 | $1,714 | $31,136 (floor ≈ $11,700) | $17,497 (floor ≈ $6,560) |
| Agora (HD tier) | $271 | $135 | $3,070 | $1,709 | $31,058 | $17,453 |
| 100ms | $272 | $135 | $3,078 | $1,714 | $31,136 | $17,497 |
| CF RealtimeKit (GA) | $136 | $68 | $1,539 | $857 | $15,568 | $8,748 |
| CF SFU (raw GB) | $0 | $0 | $67 | $82 | $1,119 | $1,265 |
| Stream | $0 | $0 | $485 | $558 | $5,746 | $6,476 |
| Chime | $133 | $75 | $1,325 | $745 | $13,250 | $7,453 |
| JaaS | $99 | $99 | $499 | $499 | ≈ $8,424 | ≈ $8,424 |

## Self-hosted estimate (LiveKit OSS on Hetzner EU + coturn), USD/month

| | A (peak ≈ 14 participants) | B (≈ 144) | C (≈ 1,444; 360p ≈ 580 Mbps peak) |
|---|---|---|---|
| SFU nodes | 1× CX33 €8.49 | 1× CCX23 €85.99 | 3× CCX33 €415.47 |
| coturn | same box (or CX23 €5.49) | CX23 €5.49 | 2× CPX22 €38.98 |
| Redis + LB | — | CX23 €5.49 | CX33 €8.49 + LB ≈ €6 |
| Backups (~20%) | ≈ €3 | ≈ €20 | ≈ €95 |
| **Subtotal** | **≈ €17 ≈ $20** | **≈ €117 ≈ $137** | **≈ €564 ≈ $660** |
| Egress vs included 20–30 TB | $0 | $0 | $0 (worst case €1/TB) |
| Alt. TURN = Cloudflare | $0 | $0 | audio $0; 360p ≈ $125 |
| Alt. TURN = Twilio Mumbai | $21 | $211 | $2,104 (avoid) |

Same workload on AWS adds egress ≈ $210 (audio C) to ≈ $2,040 (360p C) on top of EC2. Hetzner has no Gulf/South Asia region: Falkenstein → Gulf ≈ 80–120 ms, → Pakistan ≈ 120–170 ms (typical, unmeasured); fine for audio, worse for video. Hidden cost is operations (upgrades, TURN certs, monitoring, on-call).

## Reliability notes

- LiveKit: per-region status incl. UAE/KSA at 99.99–100% over 90 days; Build plan hard-caps 100 concurrent participants; first-party Flutter/RN SDKs; E2EE documented.
- Daily: no incidents 90 days; Flutter SDK newer (2024) than RN/JS; volume tiers between 100k and 50M minutes unpublished.
- 100ms: 99.99%; 100-participant cap; no E2EE.
- Agora: no public incident history; resolution-aggregate billing can jump tiers when showing more than 2 tiles.
- Cloudflare RealtimeKit: beta; SDK list vague.
- Zoom/Vonage: pricing pages unreachable; highest per-minute rates in the set.
- Chime: no Flutter/RN SDK; no Gulf media region.
- JaaS/Jitsi: attractive MAU pricing; embed-style SDKs; E2EE ≤ 20 participants.

## Recommendation (research agent's conclusion)

1. Primary: **LiveKit** (OSS self-host + LiveKit Cloud managed). Same Apache-2.0 server, same first-party Flutter/RN/web SDKs, documented E2EE, recording is an opt-in egress service, verified Gulf/India PoPs on the cloud.
2. TURN: **Cloudflare Realtime TURN** ($0.05/GB after 1 TB free) for both modes; coturn as sovereign fallback.
3. Secondary adapters worth having: Stream Video (cheapest managed audio), Cloudflare RealtimeKit at GA, JaaS/Jitsi (MAU billing, self-hostable).
4. Avoid Vonage, Zoom, Chime for this use case.
5. Audio-only default at 40 kbps Opus with video off unless the teacher enables 360p cuts managed costs 3–8× at every provider.

## Sources (accessed 2026-09-08)

LiveKit: livekit.com/pricing · docs.livekit.io/deploy/admin/quotas-and-limits/ · docs.livekit.io/home/self-hosting/benchmark/ · status.livekit.io · docs.livekit.io/transport/encryption/start/ · pub.dev/packages/livekit_client. Daily: daily.co/pricing/video-sdk/ · status.daily.co · docs.daily.co/reference/flutter. Agora: agora.io/en/pricing/ · docs.agora.io/en/video-calling/overview/pricing · docs.agora.io/en/video-calling/advanced-features/geofencing · status.agora.io. 100ms: 100ms.live/pricing · status.100ms.live. Cloudflare: developers.cloudflare.com/realtime/ · …/sfu/pricing/ · …/turn/faq/ · …/realtimekit/pricing · realtime.cloudflare.com. Zoom: zoom.com/en/video-sdk/ · developers.zoom.us/docs/video-sdk/flutter/ · developers.zoom.us/docs/video-sdk/react-native/ · third-party rate: trtc.io/blog/details/zoom-video-sdk-pricing-2026 [unverified]. Vonage: api.support.vonage.com article 6646227378204 (snippet; direct fetch 403). Stream: getstream.io/video/pricing/ · getstream.io/video/docs/react/pricing-guide/. Chime: aws.amazon.com/chime/chime-sdk/pricing/ · docs.aws.amazon.com/chime-sdk/latest/dg/sdk-available-regions.html. JaaS/Jitsi: cpaas.8x8.com/en/pricing/jitsi-as-a-service-pricing/ · jitsi.github.io/handbook/docs/category/sdks/ · jitsi.org/e2ee-in-jitsi/. Hetzner: hetzner.com/cloud/general-purpose/ · docs.hetzner.com/cloud/billing/faq/ · docs.hetzner.com/general/infrastructure-and-availability/price-adjustment/ · overage via betterstack.com (Mar 2026, third party). DigitalOcean: digitalocean.com/pricing/droplets · docs.digitalocean.com/products/billing/bandwidth/. AWS egress: egresscost.com (third party). TURN: twilio.com/en-us/stun-turn/pricing · metered.ca/stun-turn.
