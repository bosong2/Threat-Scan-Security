---
description: Run a full Claude Threat Scan security audit and emit bilingual JSON + KO HTML report
argument-hint: <path-or-git-url-or-zip>
---

Use the `threat-scan-orchestrator` skill to run a full security audit on: **$ARGUMENTS**

The skill sequences all 11 stages (Phase 0–5). Do not stop until Phase 5
(result report) is complete — all agents must finish before you report back.
