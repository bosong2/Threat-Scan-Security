---
name: threat-scan-orchestrator
description: >
  Orchestrate the full Claude Threat Scan pipeline (단계 0–11) over a target
  skill/agent/plugin/repo and produce a bilingual JSON report plus a KO HTML
  report. Use when asked to scan, audit, or vet a repository for security threats.
allowed-tools: Agent(tss-source-handler), Agent(tss-repo-indexer), Agent(tss-static-analyzer), Agent(tss-binary-analyzer), Agent(tss-skill-analyzer), Agent(tss-relationship-graph), Agent(tss-model-validity), Agent(tss-sensitive-patterns), Agent(tss-policy-verifier), Agent(tss-prompt-optimizer), Agent(tss-sbom), Agent(tss-deepdive), Agent(tss-report-merger), Agent(tss-translator), Agent(tss-html-report), Bash, Read, Write
---

# Claude Threat Scan Orchestrator

Scan target: **$ARGUMENTS**

You orchestrate an 11-stage pipeline. **Do not terminate after spawning agents —
proceed through every phase and report only when Phase 5 is done.**

If `$ARGUMENTS` is empty, ask for a path / git URL / zip and stop.

---

## 실행 절차 — Claude Code Plugin

> 이 섹션은 Claude Code Plugin 모드 전용입니다. Claude Desktop은 아래
> **실행 절차 — Claude Desktop** 섹션과 **스캔 순서** 표를 따릅니다.

> **모델 권장(v2.3.3):** 이 오케스트레이터는 finding 본문을 파일로 라우팅해
> 컨텍스트를 얇게 유지하므로 **Opus** 사용을 권장한다(라우팅·검증 판단력 ↑, 토큰 ↓).
> 워커 모델은 각 `agents/tss-*.md` frontmatter에 고정돼 있다.

> **⛔ Agent 호출 = 동기(blocking):** `Agent(tss-*)` 호출은 에이전트가 반환할 때까지
> **자동으로 대기**한다. `Monitor` 도구, 백그라운드 실행, 폴링 루프는 절대 사용하지 않는다.
> 에이전트가 "실행 중"이어도 추가 대기 코드 없이 반환값을 직접 받는다.

### Phase 0' — 스캔 세션 값 확정 (Bash, 최초 1회)

> **핵심 원칙:** Bash 도구는 호출마다 새 쉘을 생성해 변수가 유지되지 않는다.
> 아래 Bash 출력값을 **컨텍스트에 기록**하고, 이후 모든 Write·Bash·Agent 호출에서
> `$변수` 대신 **실제 경로/값을 직접 대입**한다.

```bash
SCAN_TMP=$(mktemp -d -t tss.XXXXXXXX)   # 스캔별 고유 임시 디렉터리
OUT_DIR=$(pwd)                           # 최종 산출물 저장 위치 (실행 시점 고정)
TIMESTAMP=$(date +%Y%m%d%H%M%S)         # 파일명 고유성 보장용
printf '\n=== TSS SESSION VALUES ===\nSCAN_TMP=%s\nOUT_DIR=%s\nTIMESTAMP=%s\n=========================\n' \
  "$SCAN_TMP" "$OUT_DIR" "$TIMESTAMP"
```

**출력 예시 (반드시 기록 — 이후 모든 단계에서 실제 값 직접 대입):**

```
=== TSS SESSION VALUES ===
SCAN_TMP=/tmp/tss.A1B2C3D4
OUT_DIR=/Users/user/my-project
TIMESTAMP=20260623150000
=========================
```

이후 모든 Write 경로와 Bash 명령에는 `$SCAN_TMP` 변수가 아닌 `/tmp/tss.A1B2C3D4`와 같은
**실제 경로값**을 직접 사용한다.

### Phase 0 — 소스 준비 (단계 0)

`tss-source-handler` 에이전트를 호출한다.
**반환값(TARGET_PATH)을 받을 때까지 Phase 1을 시작하지 않는다.**

반환된 경로를 Bash로 검증한다 (실제 TARGET_PATH 값 대입):

```bash
test -d "/actual/target/path" && echo "TARGET_PATH OK" || echo "FAIL: not a directory"
```

`FAIL`이면 오류를 보고하고 중단한다.

### Phase 1 — 병렬 분석 (단계 1–8, **ONE message**)

**아래 8개 에이전트를 단 하나의 메시지로 동시에 호출한다. 전부 반환될 때까지 기다린다.**
어느 하나라도 반환되지 않으면 Phase 2로 넘어가지 않는다.

각 에이전트에 **실제 TARGET_PATH**를 전달한다. 8개 전부 반환된 후, Write 도구로 각 결과를
아래 경로에 저장한다 (경로에 실제 SCAN_TMP 값 대입):

| 에이전트 | 저장 파일 경로 (실제값 대입 예시) |
|----------|----------------------------------|
| `tss-repo-indexer` | `/tmp/tss.A1B2C3D4/step1-repo-indexer.json` |
| `tss-static-analyzer` | `/tmp/tss.A1B2C3D4/step2-static.json` |
| `tss-binary-analyzer` | `/tmp/tss.A1B2C3D4/step3-binary.json` |
| `tss-skill-analyzer` | `/tmp/tss.A1B2C3D4/step4-skill.json` |
| `tss-sensitive-patterns` | `/tmp/tss.A1B2C3D4/step5-sensitive.json` |
| `tss-policy-verifier` | `/tmp/tss.A1B2C3D4/step6-policy.json` |
| `tss-prompt-optimizer` | `/tmp/tss.A1B2C3D4/step7-prompt.json` |
| `tss-sbom` | `/tmp/tss.A1B2C3D4/step8-sbom.json` |

**Write 순서:** 8개 결과를 한 번에 하나씩 순서대로 Write한다. 모두 쓴 뒤 체크포인트를 실행한다.

#### 체크포인트 (Write 완료 후 — Bash, 실제 경로 직접 대입)

```bash
# 실제 SCAN_TMP 경로로 대입해서 실행 (변수 미사용)
ls "/tmp/tss.A1B2C3D4/"step*.json 2>/dev/null | wc -l
# → 8이면 정상. 8 미만이면 누락 파일을 확인한다.
python3 -c "
import json, glob
for p in sorted(glob.glob('/tmp/tss.A1B2C3D4/step*.json')):
    d = json.load(open(p))
    m = d.get('_meta', {})
    print(m.get('agent','?'), 'scanned='+str(m.get('files_scanned','?')), 'findings='+str(m.get('findings','?')))
"
```

### Phase 2 — 순차 분석 (단계 4.5 → 4.6 → 8.5, Phase 1 완료 후)

각 에이전트에 Phase 1 파일의 **실제 경로 목록**을 전달한다. 반환 JSON도 Write로 저장한다.

1. `tss-relationship-graph` ← Phase 1 실제 파일 경로들 → Write `/tmp/tss.A1B2C3D4/step4.5-graph.json`
2. `tss-model-validity` ← 동일 파일 경로들 → Write `/tmp/tss.A1B2C3D4/step4.6-model.json`
3. `tss-deepdive` ← 전체 파일 경로들 → Write `/tmp/tss.A1B2C3D4/step8.5-deepdive.json`

### Phase 3 — 보고서 생성 (단계 9 → 10, Phase 2 완료 후)

1. `tss-report-merger` ← `/tmp/tss.A1B2C3D4/*.json` 경로 목록 →
   Write `/tmp/tss.A1B2C3D4/step9-english.json`
2. `tss-translator` ← `/tmp/tss.A1B2C3D4/step9-english.json` →
   Write `/Users/user/my-project/scanreport-20260623150000.json`
   (OUT_DIR 실제값 + `/scanreport-` + TIMESTAMP 실제값 + `.json`)

### Phase 4 — HTML 리포트 (단계 11, Phase 3 완료 후)

`tss-html-report` ← `/Users/user/my-project/scanreport-20260623150000.json` 경로 전달
(OUT_DIR 실제값 + `/scanreport-` + TIMESTAMP 실제값 + `.json`)

### Phase 5 — 결과 보고

산출 파일 경로(JSON·HTML), `_meta` 집계 요약, 그래프 verdict, 주요 Critical/High finding 상위 3건을 보고한다.
완료 후 임시 디렉터리를 정리한다:

```bash
rm -rf "/tmp/tss.A1B2C3D4"   # 실제 SCAN_TMP 값 대입
```

---

## 실행 절차 — Claude Desktop

Claude Desktop에서는 아래 **스캔 순서** 표에 따라 각 `@sub-skill` 을 순서대로 호출한다.
모든 finding 산출 후 단계 9(병합) → 10(번역) → 11(HTML) 순으로 완주한다.

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
