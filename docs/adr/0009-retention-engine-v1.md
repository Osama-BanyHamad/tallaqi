# ADR-0009 — Retention Engine v1 and Planner v1 are deterministic and explainable

Status: accepted · Date: 2026-09-08

## Decision
`packages/hifz_engine/retention.py` implements an FSRS-style forgetting curve `R(t) = 1 / (1 + t / 9S)` per Ayah, where stability `S` grows with quality-weighted successful recalls (spacing bonus after real intervals) and shrinks on failures. States derive from thresholds in the tenant's Learning Policy. Every state carries Arabic explanations. Session outcome semantics: `pass` → all Ayat pass; `partial` → Ayat without a major mistake pass; `repeat` → only untouched Ayat pass, with capped growth.

`planner.py` produces the daily plan (new / near / far) from the policy and the map, with pause rules (critical Ayat, backlog, low recent retention). Teachers approve, edit, override, or carry forward; every action is recorded.

## Why
Teachers must trust and be able to contest the number; a black box would be rejected and could not be audited. AI, if ever used, may propose parameter changes but never replaces the algorithm. The engine version is stored on every state event so history is reproducible after upgrades.
