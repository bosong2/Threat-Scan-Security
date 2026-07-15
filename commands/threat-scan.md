---
description: Run a full Claude Threat Scan security audit and emit bilingual JSON + KO HTML report
argument-hint: <path-or-git-url-or-zip>
---

Use the `threat-scan-orchestrator` skill to run a full security audit on: **$ARGUMENTS**

The skill sequences all 11 stages (Phase 0–5). Do not stop until Phase 5
(result report) is complete — all agents must finish before you report back.

> 권한 규칙이 없으면 시작 시 오케스트레이터가 1회 승인을 요청해 자동 등록합니다
> (사전 등록을 원하면 `/threat-scan-setup`). 승인 후에는 무정지로 완주합니다.
