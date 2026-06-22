# Schema V1.3 강제 준수 가이드라인

> **⚠️ 이 문서는 모든 Security Reports 스킬이 반드시 따라야 하는 절대 규칙입니다.**
> V1.2 규칙을 모두 상속하며, V1.3 신규 필드 규칙이 추가된다.

---

## 1. 하위 호환성 보장 원칙

**V1.3은 V1.2의 완전한 상위집합이다.**

- V1.2 페이로드는 V1.3에서 수정 없이 유효하다.
- 신규 필드는 **전부 optional** — 생략 시 파서/뷰어가 오류를 내지 않는다.
- 기존 금지 필드 목록은 그대로 유지된다.

---

## 2. V1.3 신규 필드 — 전부 optional

### 2.1 `verdict` (보안/그래프 verdict)

```json
"verdict": "REVIEW"
```

| 규칙 | 내용 |
|------|------|
| 허용 값 | `INSTALL_OK` \| `REVIEW` \| `DISABLE` \| `REMOVE` (대문자 필수) |
| 위치 | 모든 finding 배열 항목 (static/binary/skill/agent/sensitive/opt/rel) |
| severity 매핑 | Critical→`REMOVE`, High→`DISABLE`, Medium→`REVIEW`, Low/Info→`INSTALL_OK` |
| 강등 규칙 | `model_effectiveness`가 OBSOLETE/MODEL_LOCKED이면 INSTALL_OK → REVIEW |

#### ❌ 금지 패턴
```
"verdict": "remove"       → 소문자 금지
"verdict": "OK"           → INSTALL_OK 사용
"verdict": "BLOCK"        → 정의되지 않은 값
"verdict": "SAFE"         → 정의되지 않은 값
```

### 2.2 `model_effectiveness` (모델 유효성 verdict)

```json
"model_effectiveness": "MODEL_LOCKED"
```

| 규칙 | 내용 |
|------|------|
| 허용 값 | `VALID` \| `DEGRADED` \| `OBSOLETE` \| `MODEL_LOCKED` (대문자 필수) |
| 위치 | skill_risk_findings, prompt_optimization, model_validity_findings |
| model_validity_findings | `model_effectiveness` 필드 **필수** (해당 배열 내에서만) |

#### ❌ 금지 패턴
```
"model_effectiveness": "valid"       → 소문자 금지
"model_effectiveness": "DEPRECATED"  → 정의되지 않은 값
"model_effectiveness": "OUTDATED"    → 정의되지 않은 값
```

### 2.3 `graph_verdict` (summary 객체)

```json
"graph_verdict": {
  "security_verdict": "REMOVE",
  "worst_component": "malicious-agent",
  "rationale": "Plugin bundles agent rated REMOVE."
}
```

| 규칙 | 내용 |
|------|------|
| 위치 | `repository_summary` 내부 (optional) |
| `security_verdict` | verdict 4종 중 하나 (대문자) |
| `worst_component` | string — 컴포넌트 이름 |
| `rationale` | string — 전파 경로 포함 근거 |

### 2.4 `relationship_findings[]` 배열

```json
{
  "id": "REL-001",
  "component": "my-plugin",
  "component_type": "Plugin",
  "edge_type": "bundles",
  "target_component": "risky-agent",
  "target_type": "Agent",
  "severity": "Critical",
  "issue": "Plugin bundles a REMOVE-rated agent.",
  "recommendation": "Remove risky-agent from bundle.",
  "verdict": "REMOVE"
}
```

| 규칙 | 내용 |
|------|------|
| ID 형식 | `REL-NNN` (3자리 숫자) |
| 필수 필드 | `id`, `component`, `component_type`, `edge_type`, `target_component`, `target_type`, `severity`, `issue`, `recommendation` |
| `component_type` 허용 값 | `Plugin` \| `Skill` \| `Agent` \| `Hook` \| `MCPServer` \| `Command` |
| `edge_type` 허용 값 | `bundles` \| `delegates_to` \| `preloads` \| `uses_mcp` \| `invokes_hook` \| `references` |

#### ❌ 금지 필드 (REL finding 내)
| 사용 금지 | 올바른 필드 |
|-----------|-------------|
| `finding_id` | `id` |
| `source_component` | `component` |
| `risk_type` | `issue` |
| `remediation` | `recommendation` |

### 2.5 `model_validity_findings[]` 배열

```json
{
  "id": "MODEL-001",
  "file": "skills/tool/SKILL.md",
  "component": "tool",
  "pattern_type": "MC1",
  "issue": "Hardcoded retired model ID: claude-instant-1",
  "evidence": "claude-instant-1 found in retired_model_ids registry.",
  "severity": "High",
  "recommendation": "Replace with a current model ID.",
  "verdict": "DISABLE",
  "model_effectiveness": "MODEL_LOCKED"
}
```

| 규칙 | 내용 |
|------|------|
| ID 형식 | `MODEL-NNN` (3자리 숫자) |
| 필수 필드 | `id`, `file`, `component`, `pattern_type`, `issue`, `evidence`, `severity`, `recommendation`, `model_effectiveness` |
| `pattern_type` 허용 값 | `MC1` \| `MC2` \| `MC3` \| `MC4` \| `OB1` |
| `model_effectiveness` | 이 배열에서 **필수** |

#### ❌ 금지 필드 (MODEL finding 내)
| 사용 금지 | 올바른 필드 |
|-----------|-------------|
| `finding_id` | `id` |
| `location` | `file` |
| `title` | `issue` |
| `proof` | `evidence` |
| `remediation` | `recommendation` |
| `model_verdict` | `model_effectiveness` |

### 2.6 `recommendations[]` 추적성 필드 (V1.3.1 보강)

```json
{
  "id": "REC-001",
  "rank": 1,
  "priority": "Critical",
  "category": "Secret Management",
  "action": "Remove plaintext credential auto-login",
  "rationale": "Plaintext passwords leak via /proc, CI logs, container inspection.",
  "finding_ids": ["STATIC-001", "SENS-001"],
  "affected_files": ["src/config.ts"]
}
```

| 규칙 | 내용 |
|------|------|
| ID 형식 | `REC-NNN` (3자리 숫자) — 신규 필드(optional) |
| `rank` | integer, 1부터 처리 순서 (1=최우선). **순서는 여기에만.** |
| `priority` | **문자열만**: `Critical`/`High`/`Medium`/`Low`. **정수 금지.** 참조 finding들의 최고 severity. |
| `finding_ids` | string[], 근거 finding ID. **보고서 내 실제 존재하는 finding id만 참조**, 빈 배열 금지(최소 1개). |
| 번역 처리 | `id`/`rank`/`finding_ids`는 **번역 비대상(구조 필드)**. `priority`는 severity처럼 등급 번역(Critical→심각). `action`/`rationale`/`category` 번역. |

#### ❌ 금지 패턴 (recommendations 내)
```
"priority": 1            → 정수 금지. 순서는 rank, 등급은 priority 문자열.
"priority": "1"          → 숫자 문자열 금지.
"finding_ids": []        → 빈 배열 금지. 근거 finding 최소 1개.
finding_ids에 없는 ID    → 보고서에 실재하는 finding id만 참조.
```

### 2.7 Deep Dive 필드 + `code_fix` (V1.3.1 보강)

Deep Dive(심층 분석)가 Medium↑ finding에 채우는 optional 필드. 트리아지 수정 코드는 **`code_fix` 구조화 필드로 격리**한다.

```json
{
  "id": "STATIC-001",
  "status": "Confirmed",
  "deep_dive_result": "Level 1: exec()로 mmdc 실행. Level 2: userInput이 명령 문자열에 도달. Level 3: 쉘 인젝션 악용 가능. 결론: Confirmed.",
  "code_fix": {
    "language": "typescript",
    "before": "const cmd = `mmdc -i ${userInput}`;\nexec(cmd);",
    "after": "execFile('mmdc', ['-i', userInput]);",
    "note": "Use execFile to avoid shell string interpolation."
  }
}
```

| 필드 | 타입 | 규칙 |
|------|------|------|
| `status` | string | `Confirmed`/`Mitigated`/`False Positive`/`Potential Risk` |
| `deep_dive_result` | string | 3단계 분석 서술 **문자열**(객체 금지). 줄바꿈 `\n` 허용. |
| `code_fix` | object | `{language, before?, after, note?}` — optional |
| `code_fix.language` | string | 소문자 식별자(typescript/python/bash 등). 번역 비대상. |
| `code_fix.before` | string | 취약 코드(optional). 번역 비대상. |
| `code_fix.after` | string | 수정 코드(필수, code_fix 사용 시). 번역 비대상. |
| `code_fix.note` | string | 보충 설명(optional). 번역 대상. |

#### ⚠️ JSON 안전 규칙 (코드 포함 시 필수)
```
1. 모든 코드는 JSON 문자열 값 안에만 둔다 (code_fix.before / code_fix.after).
2. 표준 이스케이프: 줄바꿈 \n, 큰따옴표 \", 백슬래시 \\, 탭 \t.
3. 마크다운 코드펜스(``` )를 JSON 문자열에 넣지 않는다 — 뷰어가 <pre><code>로 자동 렌더.
4. 실제 수정 코드는 code_fix 에만. deep_dive_result/recommendation prose에 코드 블록 금지.
```

#### ❌ `code_snippet` vs ✓ `code_fix`
- `code_snippet`(자유서술, finding 본문) — **금지 유지**(§ finding 공통 금지).
- `code_fix`(구조화, deep-dive 수정 코드) — **승인된 신규 필드**. 둘을 혼동하지 말 것.

---

## 3. V1.2 금지 필드 정책 유지

V1.2의 모든 금지 필드 정책은 V1.3에서도 그대로 적용된다.

### 루트 레벨 금지 필드
```
findings_summary      → 제거
executive_summary     → 제거
positive_findings     → 제거
findings              → 제거 (단일 배열 금지)
scan_results          → 제거
summary               → 제거
```

### scan_metadata 금지 필드
```
scan_id       → scan_date 사용
timestamp     → scan_date 사용
target        → target_repository 사용
scan_type     → 제거
```

### finding 공통 금지 필드
```
finding_id    → id
location      → file
title         → issue
remediation   → recommendation
code_snippet  → 제거
cwe, owasp    → 제거
```

---

## 4. ID 형식 전체 목록 (V1.3 갱신)

| 카테고리 | ID 형식 | 예시 |
|----------|---------|------|
| static_code_findings | `STATIC-NNN` | `STATIC-001` |
| binary_analysis_findings | `BIN-NNN` | `BIN-001` |
| skill_risk_findings | `SKILL-NNN` | `SKILL-001` |
| agent_policy_findings | `AGENT-NNN` | `AGENT-001` |
| sensitive_patterns | `SENS-NNN` | `SENS-001` |
| prompt_optimization | `OPT-NNN` | `OPT-001` |
| vulnerability_findings | `VULN-NNN` | `VULN-001` |
| license_findings | `LIC-NNN` | `LIC-001` |
| version_risk_findings | `VER-NNN` | `VER-001` |
| supply_chain_findings | `SUPPLY-NNN` | `SUPPLY-001` |
| **relationship_findings** | **`REL-NNN`** | **`REL-001`** |
| **model_validity_findings** | **`MODEL-NNN`** | **`MODEL-001`** |
| **recommendations** | **`REC-NNN`** | **`REC-001`** |

---

## 5. Severity 값 규칙 (V1.2와 동일)

### 허용된 값 (대문자 시작 필수)
```
Critical | High | Medium | Low | Info | None
```

### ❌ 금지된 값
```
critical | high | medium | low | info | none
CRITICAL | HIGH | MEDIUM | LOW | INFO | NONE
```

---

## 6. V1.3 검증 체크리스트

### 필수 검증 (V1.2 상속)
```
□ output_filename 존재
□ scan_metadata 필수 필드 전부 존재
□ english_report / korean_report 구조 준수
□ sbom_analysis 구조 준수
□ recommendations[].action + rationale 존재
□ 모든 severity 첫 글자 대문자
□ 모든 ID 형식 일관성
```

### V1.3.1 recommendations 추적성 검증 (신규 필드 존재 시)
```
□ recommendations[].id 형식: REC-NNN
□ recommendations[].priority 문자열 (정수 1~7 금지)
□ recommendations[].rank 정수 (처리 순서)
□ recommendations[].finding_ids 비어있지 않음 (최소 1개)
□ finding_ids의 모든 ID가 보고서 내 실재하는 finding id 참조
□ id/rank/finding_ids 번역 비대상 (EN/KO 동일)
```

### V1.3.1 Deep Dive 검증 (신규 필드 존재 시)
```
□ deep_dive_result는 문자열 (객체 금지)
□ code_fix.after 존재 (code_fix 사용 시), language 소문자 식별자
□ code_fix.before/after/language 번역 비대상, note만 번역
□ 코드는 code_fix에만 (prose/recommendation에 코드블록 금지)
□ 마크다운 코드펜스(```)가 JSON 문자열 안에 없음
□ 전체 산출 JSON이 유효 (코드 내 따옴표/줄바꿈 정상 이스케이프)
```

### V1.3 추가 검증 (신규 필드 존재 시에만 적용)
```
□ relationship_findings[].id 형식: REL-NNN
□ model_validity_findings[].id 형식: MODEL-NNN
□ verdict 값 대문자, 4종 중 하나
□ model_effectiveness 값 대문자, 4종 중 하나
□ model_validity_findings[].model_effectiveness 필수 존재
□ graph_verdict.security_verdict 대문자 verdict 값
□ severity→verdict 매핑 일관성
□ 신규 금지 필드 0개 추가 확인
```

---

## 7. 위반 시 결과

- **하위 호환 파괴**: v1.2 금지 필드를 추가하면 뷰어 렌더링 실패
- **verdict 값 오류**: 소문자/비정의 값은 뷰어에서 unknown으로 처리
- **model_validity_findings 내 model_effectiveness 누락**: 판정 불가, 해당 finding 무효
- **ID 형식 불일치**: 추적성 손실, 뷰어 dedup 실패

---

**이 문서는 모든 스킬 개발 및 수정 시 반드시 참조해야 합니다.**

마지막 업데이트: 2026-06-22 (Schema V1.3.1 — recommendations 추적성 보강)
