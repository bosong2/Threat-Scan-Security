---
name: threat-scan-orchestrator
description: >
  Orchestrate the full Claude Threat Scan pipeline (단계 0–11) over a target
  skill/agent/plugin/repo and produce a bilingual JSON report plus a KO HTML
  report. Use when asked to scan, audit, or vet a repository for security threats.
allowed-tools: Agent(tss-source-handler), Agent(tss-repo-indexer), Agent(tss-static-analyzer), Agent(tss-binary-analyzer), Agent(tss-skill-analyzer), Agent(tss-relationship-graph), Agent(tss-model-validity), Agent(tss-sensitive-patterns), Agent(tss-policy-verifier), Agent(tss-prompt-optimizer), Agent(tss-sbom), Agent(tss-deepdive), Agent(tss-report-merger), Agent(tss-translator), Agent(tss-html-report), Bash, Read
---

# Claude Threat Scan Orchestrator

Scan target: **$ARGUMENTS**

You orchestrate an 11-stage pipeline. Sequence the agents exactly as below and
**wait for each stage to complete before starting the next**. Do not terminate
after spawning agents — proceed through every phase and report only when
Phase 5 is done.

---

## Phase 0 — 소스 준비 (단계 0)

`tss-source-handler` 에이전트를 호출해 대상 소스를 준비한다.
반환된 **준비된 로컬 경로**를 이후 모든 단계에 전달한다.

If `$ARGUMENTS` is empty, ask for a path / git URL / zip and stop.

## Phase 1 — 병렬 분석 (단계 1–8, **ONE message**)

**모든 에이전트를 단 하나의 메시지로 동시에 호출하고, 전부 반환될 때까지 기다린다.**
(어느 하나라도 반환되지 않으면 Phase 2로 넘어가지 않는다.)

준비된 경로를 각 에이전트에 전달:
1. `tss-repo-indexer` — 리포지토리 인덱싱
2. `tss-static-analyzer` — 정적 코드 분석
3. `tss-binary-analyzer` — 바이너리 분석
4. `tss-skill-analyzer` — Skill/도구 보안 분석
5. `tss-sensitive-patterns` — 민감 패턴 탐지
6. `tss-policy-verifier` — 에이전트 정책 검증
7. `tss-prompt-optimizer` — 프롬프트 최적화
8. `tss-sbom` — SBOM/의존성 분석

## Phase 2 — 순차 분석 (단계 4.5 → 4.6 → 8.5, Phase 1 완료 후)

Phase 1 전체가 완료된 후 순서대로 실행한다:

1. `tss-relationship-graph` — 연관관계 그래프 + 위험 전파 (Phase 1 결과 전달)
2. `tss-model-validity` — 모델 유효성/진부화 판정 (Phase 1 결과 전달)
3. `tss-deepdive` — Medium↑ finding 심층 트리아지 (Phase 1+2 전체 finding 전달)

## Phase 3 — 보고서 생성 (단계 9 → 10, Phase 2 완료 후)

1. `tss-report-merger` — Phase 1·2 전체 fragment를 병합해 `english_report{}` 생성
2. `tss-translator` — 영문 보고서를 한글로 번역, bilingual JSON 완성
   JSON 파일명: `scanreport-YYYYMMDDhhmmss.json`

## Phase 4 — HTML 리포트 (단계 11, Phase 3 완료 후)

`tss-html-report` 에이전트를 호출해 Python 생성기로 KO HTML을 산출한다.

## Phase 5 — 결과 보고 (모든 단계 완료 후)

다음을 보고한다:
1. 산출 파일 경로 (JSON + HTML)
2. 그래프 verdict 요약 (worst component, INSTALL_OK/REVIEW/DISABLE/REMOVE)
3. 주요 Critical/High finding 상위 3건

---

## 참조 (방법론 상세)

## 스캔 순서

| 단계 | 스킬 | 설명 |
|------|------|------|
| 0 | `@source-handler` | 소스 준비 (ZIP 해제, GitHub 클론) — 셸 사용 허용 단계 |
| 1 | `@repo-indexer` | 리포지토리 인덱싱 |
| 2 | `@static-code-analyzer` | 정적 코드 분석 |
| 3 | `@binary-analyzer` | 바이너리 분석 |
| 4 | `@skill-security-analyzer` | Skill/도구 보안 분석 |
| **4.5** | **`@relationship-graph-analyzer`** | **컴포넌트 연관관계 그래프 + 위험 전파 (v2.1.0+)** |
| **4.6** | **`@model-validity-analyzer`** | **모델 유효성/진부화 판정 (v2.1.0+)** |
| 5 | `@sensitive-pattern-matcher` | 민감 패턴 매칭 |
| 6 | `@agent-policy-verifier` | 에이전트 정책 검증 |
| 7 | `@prompt-optimizer` | 프롬프트/포맷 최적화 |
| 8 | `@sbom-analyzer` | SBOM 및 의존성 분석 |
| **8.5** | **`@securityreports-deepdive`** | **심층 분석(트리아지) — Medium↑ finding에 status/deep_dive_result/code_fix 채움 (v2.1.1+)** |
| 9 | `@report-merger` | 영문 보고서 병합 |
| 10 | `@bilingual-translator` | 한글 번역 및 최종 보고서 생성 |
| **11** | **`@html-report-generator`** | **HTML 리포트 출력 — 번들 스크립트로 JSON→정적 HTML 생성 (v2.2.0+)** |

**단계 4.5–4.6은 단계 4 완료 후 순차 실행. 셸/코드 실행 없이 Claude 추론으로만 수행.**
**단계 8.5는 단계 1–8의 모든 finding 산출 후, 병합(9) 이전에 수행. 셸/코드 실행 없이 Claude 추론으로만.**
**단계 11은 단계 10의 bilingual JSON 산출 후 수행. 스크립트 실행이 허용되는 예외 단계(단계 0과 동일 성격)이며, LLM 추론 없이 결정론적 파일 처리만 수행한다. 별도 요구가 없으면 JSON과 KO HTML 리포트를 함께 출력한다.**
**`references/sub-skills/relationship-graph-analyzer.md`, `references/sub-skills/model-validity-analyzer.md`, `references/sub-skills/securityreports-deepdive.md`, `references/sub-skills/html-report-generator.md` 참조.**

## 분석 전략

### Phase 1 — Broad Scan (Level 1)
- 전체 리포지토리를 스캔하여 후보 위험 식별
- 각 스킬이 독립적으로 Level 1 분석 수행

### Phase 2 — Deep Dive (Level 2-3, MAX DEPTH = 3)
**실행 주체: 단계 8.5 `@securityreports-deepdive`** (`references/sub-skills/securityreports-deepdive.md`).
단계 1–8의 모든 finding 산출 후, 병합(9) 전에 반드시 수행한다. 개념 서술에 그치지 말고 실제로 호출하여 대상 finding에 `status`/`deep_dive_result`/`code_fix`를 채운다.

Deep Dive 수행 기준:
- Severity가 Medium 또는 High인 경우
- 동작이 불명확한 경우("could/may/potentially")
- 민감 정보가 관련된 경우

조치할 수정 코드는 **`code_fix` 구조화 필드**로 격리한다(JSON 안전 규칙: 코드는 문자열 값·이스케이프, 코드펜스 금지). 상세는 deepdive 서브스킬·`SCHEMA_V1.3_ENFORCEMENT.md` §2.7.

### 최종 판정 분류
- `Confirmed` - 확인된 위험
- `Mitigated` - 완화된 위험
- `False Positive` - 오탐 (근거 포함)

## 출력 형식

### ⚠️ 필수: Schema V1.3 엄격 준수

**임의로 필드를 추가/변경/제거하면 뷰어 호환성이 깨집니다.**
**참조**: `references/docs/SCHEMA_V1.3_ENFORCEMENT.md`, `references/docs/claude-threat-scan-json-schema-v1.3.md`

### 파일명 규칙
```
scanreport-YYYYMMDDhhmmss.json
```

### JSON 구조 (V1.3 — v1.2 완전 호환)
```json
{
  "output_filename": "scanreport-YYYYMMDDhhmmss.json",
  "scan_metadata": {
    "scan_date": "ISO 8601 format",
    "scanner_version": "Claude Threat Scan V2.1",
    "repository": "repo-name",
    "target_repository": "repo-name",
    "total_files_scanned": 0,
    "total_files": 0,
    "code_files": 0,
    "analysis_depth": 3,
    "scan_depth": 3
  },
  "english_report": {
    "repository_summary": {
      "graph_verdict": {}
    },
    "static_code_findings": [],
    "binary_analysis_findings": [],
    "skill_risk_findings": [],
    "agent_policy_findings": [],
    "sensitive_patterns": [],
    "prompt_optimization": [],
    "sbom_analysis": {},
    "relationship_findings": [],
    "model_validity_findings": [],
    "recommendations": []
  },
  "korean_report": {
    "repository_summary": {
      "graph_verdict": {}
    },
    "static_code_findings": [],
    "binary_analysis_findings": [],
    "skill_risk_findings": [],
    "agent_policy_findings": [],
    "sensitive_patterns": [],
    "prompt_optimization": [],
    "sbom_analysis": {},
    "relationship_findings": [],
    "model_validity_findings": [],
    "recommendations": []
  }
}
```

**V1.3 신규 optional 필드 (단계 4.5–4.6 산출물)**:
- `repository_summary.graph_verdict` — 그래프 전파 후 worst component 기준 summary verdict
- `relationship_findings[]` — REL-NNN, 컴포넌트 연관관계 그래프 분석
- `model_validity_findings[]` — MODEL-NNN, 모델 유효성/진부화 판정
- 각 finding의 `verdict` (`INSTALL_OK`/`REVIEW`/`DISABLE`/`REMOVE`)
- 각 finding의 `model_effectiveness` (`VALID`/`DEGRADED`/`OBSOLETE`/`MODEL_LOCKED`)

### ❌ 금지 필드 (절대 추가하지 마세요)
- `findings_summary` - 스키마에 없음
- `executive_summary` - 스키마에 없음  
- `findings` (단일 배열) - 카테고리별 배열 사용
- `positive_findings` - 스키마에 없음
- `scan_id`, `scan_type`, `target`, `timestamp`, `target_info` - 스키마 외 필드
- `title`, `category`, `cwe`, `owasp` (finding 내) - `issue` 사용
- `remediation` - `recommendation` 사용
- `code_snippet` - 스키마에 없음
- severity 소문자 - 대문자 시작 필수
- verdict 소문자 - 대문자 필수 (`REMOVE` not `remove`)

## 제약 사항

- **단계 0(`@source-handler`)·단계 11(`@html-report-generator`)만 스크립트/파일 생성 허용** — 단계 0은 소스 준비(git clone/unzip), 단계 11은 결정론적 HTML 리포트 생성에 한정
- 단계 1–10: 코드 실행 금지, Claude 추론으로만 분석 수행 (Claude Desktop 샌드박스 호환)
- 단계 1–10은 파일 생성 금지 (JSON 출력만 수행). 단계 11은 번들 스크립트로 HTML 파일 생성 — 입력 JSON을 변형하지 않고 그대로 임베드
- 각 스킬의 결과를 신뢰하되 일관성 검증 수행

## 사용 예시

```
사용자: @threat-scan-orchestrator /Users/user/project 전체 보안 스캔 수행

응답: 
1. 리포지토리 인덱싱 중...
2. 정적 코드 분석 중...
...
9. 보고서 생성 완료

[JSON 보고서 출력]
```
