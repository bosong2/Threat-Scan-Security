---
description: Show Claude Threat Scan usage, pipeline steps, verdicts, and migration from legacy commands
---

**Claude Threat Scan** (v2.3.3) — AI 에이전트 생태계 아티팩트 보안 감사 도구.

## 커맨드

| 커맨드 | 설명 |
|--------|------|
| `/threat-scan <target>` | 전체 보안 스캔 (경로 / GitHub URL / ZIP) → JSON + KO HTML |
| `/threat-scan-html <json> [ko\|en]` | 기존 JSON → HTML 재생성 |
| `/threat-scan-help` | 이 안내 |

## 파이프라인 (단계 0–11)

| 단계 | 에이전트 | 설명 |
|------|---------|------|
| 0 | `tss-source-handler` | 소스 준비 (clone/unzip) |
| 1 | `tss-repo-indexer` | 파일 트리·통계 |
| 2 | `tss-static-analyzer` | 정적 코드 분석 |
| 3 | `tss-binary-analyzer` | 바이너리 분석 |
| 4 | `tss-skill-analyzer` | Skill/도구 보안 |
| 4.5 | `tss-relationship-graph` | 연관관계 그래프·전파 |
| 4.6 | `tss-model-validity` | 모델 유효성/진부화 |
| 5 | `tss-sensitive-patterns` | 민감 패턴 |
| 6 | `tss-policy-verifier` | 에이전트 정책 |
| 7 | `tss-prompt-optimizer` | 프롬프트 최적화 |
| 8 | `tss-sbom` | SBOM/의존성 |
| 8.5 | `tss-deepdive` | 심층 트리아지 |
| 9 | `tss-report-merger` | 영문 보고서 병합 |
| 10 | `tss-translator` | 한글 번역·bilingual JSON |
| 11 | `tss-html-report` | 정적 HTML 생성 |

## Verdict 의미

| Verdict | 의미 |
|---------|------|
| `INSTALL_OK` | 안전 |
| `REVIEW` | 검토 필요 |
| `DISABLE` | 사용 중지 권고 |
| `REMOVE` | 즉시 제거 |

**Model Effectiveness**: `VALID` · `DEGRADED` · `OBSOLETE` · `MODEL_LOCKED`

**Finding 상태**: `Confirmed` · `Mitigated` · `False Positive`

---

> ⚠️ **레거시 커맨드 안내**: `/securityreports-scan` 등 구 SecurityScan 커맨드는 **deprecated**입니다.
> 그래프 전파·모델 유효성·심층 트리아지·HTML 리포트가 포함된 `/threat-scan`을 사용하세요.

---

**Threat-scan-security** · Author: Bosung Hong (bosong2) · License: Apache-2.0
Repository: https://github.com/bosong2/Threat-Scan-Security
