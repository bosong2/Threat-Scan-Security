---
name: securityreports-deepdive
description: >
  Deep-dive triage on Medium+ findings: up to 3-level recursive analysis,
  status confirmation (Confirmed/Mitigated/False Positive), and code_fix suggestions.
  Internal use — called by threat-scan-orchestrator step 8.5.
---

# Security Reports - Deep Dive Analysis (Internal)

**내부 참조 전용** - `threat-scan-orchestrator`(단계 8.5) 및 `securityreports-scan`에서 자동 호출됩니다.

스캔 레포트의 발견 사항을 심층 검증(트리아지)합니다.

## 개요

1차 스캔에서 탐지된 보안 이슈를 **최대 3단계 재귀 분석**하여:
- **Confirmed** - 실제 위험 확인
- **Mitigated** - 완화됨 (보호 조치 존재)
- **False Positive** - 오탐 (근거 포함)

으로 최종 판정합니다.

## 입력

1차 스캔 레포트 JSON 파일 (`scanreport-*.json`)

## Deep Dive 대상 선정 기준

다음 조건에 해당하는 finding은 Deep Dive 필수:

| 조건 | 설명 |
|------|------|
| Severity ≥ Medium | 중간 이상 심각도 |
| status 미정 | status 필드가 없거나 빈 값 |
| deep_dive_result 없음 | 1차 분석만 완료된 상태 |
| 동작 불명확 | description에 "could", "may", "potentially" 포함 |

## Deep Dive 분석 방법 (MAX DEPTH = 3)

### Level 1: 직접 분석
- 해당 파일/라인의 코드 확인
- 위험 패턴 존재 여부 1차 판단

### Level 2: 컨텍스트 추적
- 입력 소스 추적 (사용자 입력 → 함수 → 위험 코드)
- 검증/새니타이징 로직 확인
- 호출 경로 분석

### Level 3: 영향도 평가
- 실제 악용 시나리오 구성
- 보호 조치 효과 평가
- 최종 위험 등급 결정

## 출력 형식

### 개별 Finding 업데이트

각 finding에 다음 필드를 **추가/갱신**:

```json
{
  "id": "STATIC-001",
  "file": "src/utils/localMermaidRenderer.ts",
  "line": 144,
  "issue": "Command Injection Risk",
  "description": "...",
  "severity": "Medium",
  "status": "Mitigated",
  "deep_dive_result": "Level 1: exec()가 mmdc 바이너리 실행에 사용됨. Level 2: tempFile/outputFile은 timestamp+randomId 패턴으로 내부 생성됨(line 103-104). Level 3: 사용자 입력이 명령어 구성에 도달하지 않음. mmdcPath는 node_modules/.bin/mmdc로 고정. 결론: 주입 위험 없는 안전한 구현.",
  "recommendation": "현재 구현은 안전함. 내부 생성 경로만 계속 사용할 것."
}
```

### 필수 출력 필드

| 필드 | 설명 | 필수 |
|------|------|------|
| `status` | `Confirmed` \| `Mitigated` \| `False Positive` | ✓ |
| `deep_dive_result` | 3단계 분석 결과 **문자열** (NOT 객체) | ✓ |
| `code_fix` | 수정 코드 격리 객체 `{language, before?, after, note?}` | ○ (수정 코드가 있을 때) |

### 🔧 code_fix — 수정 코드 격리 (Confirmed에 권장)

트리아지 결과 조치할 코드가 있으면 **반드시 `code_fix` 구조화 필드**에 담는다. prose(설명) 필드에 코드를 섞지 않는다.

```json
{
  "id": "STATIC-001",
  "status": "Confirmed",
  "deep_dive_result": "Level 1: exec()로 mmdc 실행. Level 2: userInput이 명령 문자열에 도달(검증 없음). Level 3: 쉘 메타문자로 임의 명령 실행 가능. 결론: Confirmed.",
  "code_fix": {
    "language": "typescript",
    "before": "const cmd = `mmdc -i ${userInput}`;\nexec(cmd);",
    "after": "execFile('mmdc', ['-i', userInput]);",
    "note": "execFile은 쉘을 거치지 않아 문자열 보간 인젝션을 차단한다."
  },
  "recommendation": "exec(문자열) → execFile(인자배열)로 전환."
}
```

| code_fix 키 | 설명 | 필수 |
|------------|------|------|
| `language` | 소문자 식별자 (typescript/python/bash/go 등) | ✓ |
| `before` | 취약 코드 (대조용) | ○ |
| `after` | 수정 코드 | ✓ (code_fix 사용 시) |
| `note` | 보충 설명 (번역 대상) | ○ |

### ⚠️ JSON 안전 규칙 (코드 포함 시 — 절대 위반 금지)

수정 코드에는 따옴표·줄바꿈·`<`/`>`·백슬래시가 흔하므로 JSON이 깨지기 쉽다. 다음을 반드시 지킨다:

```
1. 모든 코드는 JSON 문자열 값으로만 둔다 (code_fix.before / code_fix.after).
2. 표준 이스케이프: 줄바꿈 → \n, 큰따옴표 → \", 백슬래시 → \\, 탭 → \t.
3. 마크다운 코드펜스(``` )를 JSON 문자열 안에 넣지 않는다 — 뷰어가 <pre><code>로 자동 렌더한다.
4. deep_dive_result / recommendation 같은 prose 필드에 코드 블록을 넣지 않는다 (code_fix로 분리).
5. 출력 직전 전체 JSON 유효성(파싱 가능)을 self-check 한다.
```

### ❌ 금지: deep_dive_result 객체 사용

```json
// ❌ 잘못된 형식 (뷰어에서 [object Object]로 표시)
"deep_dive_result": {
  "analysis_depth": 3,
  "root_cause": "...",
  "attack_vector": "..."
}

// ✓ 올바른 형식
"deep_dive_result": "Level 1: 직접 분석 내용. Level 2: 컨텍스트 추적. Level 3: 영향도 평가. 결론: 판정 결과."
```

### Deep Dive 결과 형식

```
Level 1: [직접 분석 내용]
Level 2: [컨텍스트 추적 내용]  
Level 3: [영향도 평가 내용]
결론: [최종 판정]
```

## 카테고리별 분석 지침

### static_code_findings
```
- 입력 소스 추적 (HTTP request → 함수 파라미터 → 위험 호출)
- 검증 로직 확인 (sanitize, validate, escape 함수)
- 실행 컨텍스트 확인 (shell=True, eval, exec)
```

### sensitive_patterns
```
- .gitignore 포함 여부 확인
- Git 히스토리에 실제 값 노출 여부
- 로그/테스트에 값 유출 여부
- 환경별 분리 여부 (dev/prod)
```

### agent_policy_findings
```
- disallowed_tools 정책 존재 여부
- 도구 호출 제한 메커니즘 확인
- Rate limiting 구현 확인
```

### sbom_analysis (vulnerability_findings)
```
- CVE 영향 버전 확인
- 패치 버전 가용성
- 전이 의존성 체인 추적
```

## 레포트 갱신 절차

1. 입력 레포트 파싱
2. Deep Dive 대상 선정
3. 각 대상에 대해 3단계 분석 수행
4. `status`, `deep_dive_result` 필드 추가/갱신
5. 갱신된 레포트 출력

## ⚠️ 필수: 갱신된 레포트 저장

### 파일명
원본과 동일: `scanreport-{SESSION_ID}.json`

### 갱신 확인 출력
```
=== Deep Dive 분석 완료 ===

📊 분석 결과:
  - 분석 대상: 12건
  - Confirmed: 3건
  - Mitigated: 7건
  - False Positive: 2건

📁 레포트 갱신: ./scanreport-20260205-143022.json

갱신된 항목:
1. [STATIC-001] Mitigated - exec()는 내부 생성 경로만 사용
2. [SENS-001] Confirmed - AWS SG ID가 public repo에 노출
3. [SKILL-002] False Positive - 기본값 비활성화 상태
```

## Schema V1.3 필드 규칙 준수

Deep Dive 후에도 다음 필드 규칙 준수 필수:

```
✓ file (NOT location)
✓ line (숫자, NOT 범위 문자열)
✓ issue (NOT title)
✓ pattern (sensitive_patterns용)
✓ detail (NOT description for sensitive_patterns)
✓ severity 대문자 시작 (Critical, High, Medium, Low)
✓ recommendation (NOT remediation)
✓ deep_dive_result 문자열 (NOT 객체)
✓ 수정 코드는 code_fix 구조화 필드 (NOT code_snippet, NOT prose 삽입)
✓ code_fix 내 코드는 JSON 이스케이프 (\n, \", \\)
```

## Tag Verification (v2.5.0 — CTID-V, Schema V1.4)

단계 8.5는 finding이 단계 1–8에서 부여받은 `compliance_tags`를 **검증·교정하는 유일한 추론
단계**다(단계 9–11은 태그 읽기전용). 상세 규칙은
`${CLAUDE_PLUGIN_ROOT}/docs/compliance-tagging-deepdive.md`(CTID-V)를 로드해 따른다.

기존 MAX DEPTH=3 분석에 **별도 pass 없이 폴딩**한다:

- **L1(직접 분석)**: primary 태그의 근본원인 트리거가 실제 코드와 일치하는지 확인.
- **L2(맥락 추적)**: 재귀속(re-attribution) 탐지 — 진짜 근본원인이 다른 제어면 primary 태그 교체.
- **L3(영향 평가)**: 추적으로 드러난 보조 태그 추가(총 ≤4), primary-first 순서 확정.

검증 규칙(요지):

- **V-1 재귀속**: primary 태그 교체 시 `deep_dive_result`에 1문장 기록
  (예: "Tag re-attributed #KISA-1_2 → #KISA-2_2: sink 도달 불가, 실제 결함은 소유권 검사 누락").
- **V-2 status 독립**: 태그는 위반한 제어 클래스를 기술, `status`는 악용가능성을 기술.
  `Mitigated`·`False Positive`여도 태그를 제거하지 않는다(면책은 status에).
- **V-3 추가**: 동일 증거가 독립적으로 위반하는 제어만 보조 태그로 추가(≤4, dedup 필수).
- **V-4 네임스페이스 규율**: `AILLM`은 추적 경로에 LLM/에이전트 기능이 확인될 때만.
  `TA`는 IaC/설정 아티팩트 증거만. 보고 편의로 AILLM→KISA 이동 금지(프레임워크 격리).
- **V-5 빈 배열 유효**: 해당 제어 없다고 판정하면 `[]` + `deep_dive_result`에 사유.
- **V-6 증거 확장 금지**: 태그 검증이 MASKING CONTRACT를 완화하지 않는다.
- **V-7 형식 재검증**: write-back 시 regex·대문자·유일·≤4·primary-first 재확인(8.5가 병합 전 마지막 추론).

세션당 1회 cross-finding sweep 3종: ① 동일 file:line 결함의 태그 일관성 정렬(finding 병합은
단계 9), ② 배열별 태그 범위 타당성(CTID-D §2), ③ AILLM 게이트 정합(태그가 있으면 대상에 LLM 기능 실재).

`code_fix` 자기일관성: fix는 **primary 태그**가 지목한 제어를 교정해야 한다 — 불일치 시 write-back 전 해소.

출력 계약 delta: `compliance_tags` in-place 검증·교정(빈 배열화 가능), 태그가 **변경된 경우에만**
`deep_dive_result`에 사유 1문장 추가. 그 외 신규 필드 없음.

## 참조

- [claude-threat-scan-json-schema-v1.4.md](../../docs/claude-threat-scan-json-schema-v1.4.md) — §18.5 Deep Dive 필드, §21 compliance_tags
- [SCHEMA_V1.4_ENFORCEMENT.md](../../docs/SCHEMA_V1.4_ENFORCEMENT.md) — §2.7 code_fix + JSON 안전 규칙, §8 태그 강제
- [compliance-tagging-deepdive.md](../../docs/compliance-tagging-deepdive.md) — CTID-V 전문(V-1~V-7 + 3 sweep)
- [claude_threat_scan_prompt_v_2.md](../../docs/claude_threat_scan_prompt_v_2.md) - SECTION 0 참조
