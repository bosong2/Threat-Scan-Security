---
name: report-merger
description: >
  Collect and merge all per-category finding arrays and metadata from scan
  steps into a single English scan report conforming to Schema V1.3.
---

# Report Merger Skill

## 개요

개별 스캔 결과를 수집하여 최종 bilingual JSON 보고서를 생성하는 스킬.

## 역할

1. 각 스캔 스킬의 결과 수집
2. ID 일관성 검증 및 재할당
3. Severity 집계 및 통계 생성
4. 영문/한글 병렬 보고서 생성
5. 최종 권장사항 도출

## 호출 방법

```
@report-merger <scan-results>
```

## 입력 형식

각 스킬의 출력을 JSON 형태로 수집:

```json
{
  "repo_indexer_result": { ... },
  "static_code_analyzer_result": { ... },
  "binary_analyzer_result": { ... },
  "skill_security_analyzer_result": { ... },
  "relationship_graph_analyzer_result": { ... },
  "model_validity_analyzer_result": { ... },
  "sensitive_pattern_matcher_result": { ... },
  "agent_policy_verifier_result": { ... },
  "prompt_optimizer_result": { ... },
  "sbom_analyzer_result": { ... }
}
```

## 출력 형식

### 최종 JSON 구조 (V1.3)

```json
{
  "output_filename": "scanreport-YYYYMMDDhhmmss.json",
  "scan_metadata": {
    "scan_date": "2026-02-05T12:00:00Z",
    "scanner_version": "Claude Threat Scan V2.1",
    "repository": "project-name",
    "target_repository": "project-name",
    "total_files_scanned": 156,
    "total_files": 156,
    "code_files": 42,
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

## ID 할당 규칙

| Section | Format | Example |
|---------|--------|---------|
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

## V1.3 신규 배열 병합 규칙

### relationship_findings[] 병합
- `@relationship-graph-analyzer` 출력의 `relationship_findings[]`를 `english_report`에 배치
- `graph_verdict` 객체를 `repository_summary.graph_verdict`에 배치
- ID 형식 `REL-NNN` 일관성 검증 후 재할당 (충돌 시)

### model_validity_findings[] 병합
- `@model-validity-analyzer` 출력의 `model_validity_findings[]`를 `english_report`에 배치
- ID 형식 `MODEL-NNN` 일관성 검증 후 재할당 (충돌 시)
- `model_effectiveness` 필드가 각 항목에 존재하는지 검증

### verdict 필드 전파
- 각 finding의 `verdict` 필드가 severity와 일관성 있는지 확인 (Critical→REMOVE 등)
- `model_effectiveness`가 OBSOLETE/MODEL_LOCKED이면 해당 finding의 verdict가 INSTALL_OK → REVIEW로 강등되었는지 확인

### Deep Dive 필드 병합 보존 (단계 8.5 산출)
- `@securityreports-deepdive`가 finding에 채운 `status`/`deep_dive_result`/`code_fix`를 **그대로 보존**하여 병합한다(덮어쓰기·누락 금지).
- `code_fix`는 객체 구조(`{language, before?, after, note?}`)와 JSON 이스케이프를 유지한다. prose로 펼치지 않는다.

## 번역 처리

### 영문 → 한글 필드 매핑

```json
{
  "severity": {
    "Critical": "심각",
    "High": "높음",
    "Medium": "중간",
    "Low": "낮음"
  },
  "status": {
    "Confirmed": "확인됨",
    "Mitigated": "완화됨",
    "False Positive": "오탐"
  },
  "issue_types": {
    "Command Injection": "명령 주입",
    "Hardcoded Credential": "하드코딩된 자격 증명",
    "Sensitive Pattern": "민감 패턴"
  }
}
```

### 번역 규칙
1. 파일 경로: 번역하지 않음
2. 코드 조각: 번역하지 않음
3. 기술 용어: 영문 유지 (괄호 한글 설명)
4. 권장 조치: 완전 번역

## 권장사항 생성

### 우선순위 기준
1. Critical severity 항목
2. High severity 항목
3. 여러 파일에 영향을 미치는 항목
4. 즉시 조치 가능한 항목

### 권장사항 구조 (V1.3.1 — 추적성 필수)
```json
{
  "id": "REC-001",
  "rank": 1,
  "priority": "Critical",
  "category": "Secret Management",
  "action": "Remove plaintext credential auto-login (LOGIN_EMAIL / LOGIN_PASSWORD)",
  "rationale": "Plaintext passwords leak via /proc, CI logs, and container inspection.",
  "finding_ids": ["STATIC-001", "SENS-001"],
  "affected_files": ["src/config.ts", ".gitignore"]
}
```

### ⚠️ 권장사항 산정 규칙 (필수)

각 권장조치는 **반드시 근거 finding에서 파생**되어야 한다. 추측으로 만들지 말 것.

| 필드 | 산정 방법 |
|------|-----------|
| `id` | `REC-NNN` 순차 부여 (REC-001, REC-002, …) |
| `finding_ids` | 이 권장이 해결하는 finding의 id 목록. **보고서 내 실재하는 finding id만** (STATIC-NNN, SENS-NNN, REL-NNN 등). **빈 배열 금지(최소 1개).** 여러 finding을 하나의 조치로 묶을 수 있음. |
| `priority` | `finding_ids`가 가리키는 finding들의 **최고 severity** (문자열: Critical/High/Medium/Low). **정수 금지.** |
| `rank` | priority 내림차순 정렬 순번 (정수, 1=최우선). **처리 순서는 priority가 아니라 rank에 넣는다.** |
| `action` / `rationale` / `category` | 기존대로 (번역 대상) |
| `affected_files` | 참조 finding들의 file 합집합 (optional) |

**금지**: `priority`에 정수(1~7)를 넣지 말 것. 순서는 `rank`, 등급은 `priority` 문자열로 분리한다. (BUG-002 재발 방지)

## ⚠️ 필수: Schema V1.3 강제 준수

**[SCHEMA_V1.3_ENFORCEMENT.md](../../docs/SCHEMA_V1.3_ENFORCEMENT.md) 필수 참조** (V1.2 규칙 포함)

**임의로 필드를 추가/변경/제거하지 마십시오.**

### 금지된 필드 (추가 금지)
```
❌ findings_summary     → 제거
❌ executive_summary    → 제거
❌ findings (단일 배열) → 카테고리별 배열 사용
❌ positive_findings    → 제거
❌ scan_id              → scan_date 사용
❌ scan_type            → 제거
❌ target               → target_repository 사용
❌ timestamp            → scan_date 사용
❌ target_info          → 플랫 구조 사용
❌ title (finding)      → issue 사용
❌ category (finding)   → 제거
❌ cwe, owasp           → 제거 (스키마 외)
❌ remediation          → recommendation 사용
❌ code_snippet         → 제거
```

### 필수 구조
```json
{
  "output_filename": "scanreport-YYYYMMDDhhmmss.json",  // ✓ 필수
  "scan_metadata": {
    "scan_date": "ISO 8601",           // ✓ 필수 (NOT timestamp)
    "scanner_version": "Claude Threat Scan V2.0",
    "repository": "name",              // ✓ 필수
    "target_repository": "name",       // ✓ 필수 (NOT target)
    "total_files_scanned": 0,
    "total_files": 0,                  // ✓ 필수
    "code_files": 0,                   // ✓ 필수
    "analysis_depth": 3,
    "scan_depth": 3                    // ✓ 필수
  },
  "english_report": {
    "repository_summary": {},          // ✓ 필수
    "static_code_findings": [],        // ✓ 필수 (배열)
    "binary_analysis_findings": [],
    "skill_risk_findings": [],
    "agent_policy_findings": [],
    "sensitive_patterns": [],
    "prompt_optimization": [],
    "sbom_analysis": {},               // ✓ 필수 (V1.2)
    "recommendations": []              // ✓ 필수 (배열, NOT 객체)
  },
  "korean_report": { /* 동일 구조 */ }
}
```

### Severity 값 (대문자 시작 필수)
```
✓ "Critical" "High" "Medium" "Low" "Info" "None"
✗ "critical" "high" "medium" "low" (소문자 금지)
```

### Finding 필드 (static_code_findings 예시)
```json
{
  "id": "STATIC-001",           // ✓ 필수
  "file": "path/to/file",       // ✓ 필수
  "line": 45,                   // ○ 선택
  "issue": "Issue Title",       // ✓ 필수 (NOT title)
  "description": "...",         // ✓ 필수
  "severity": "High",           // ✓ 필수 (대문자 시작)
  "status": "Confirmed",        // ○ 선택
  "deep_dive_result": "...",    // ○ 선택
  "recommendation": "..."       // ✓ 필수 (NOT remediation)
}
```

### Recommendation 필드 (V1.3.1 — 추적성 필수)
```json
{
  "id": "REC-001",               // ✓ 필수 - REC-NNN 형식
  "rank": 1,                     // ✓ 필수 - 정수, 처리 순서 (1=최우선)
  "priority": "Critical",        // ✓ 필수 - 문자열 등급 (정수 금지)
  "category": "Secret Management",
  "action": "What to do",        // ✓ 필수 (뷰어 렌더링)
  "rationale": "Why",            // ✓ 필수 (뷰어 렌더링)
  "finding_ids": ["STATIC-001"], // ✓ 필수 - 근거 finding (실재 id, 빈 배열 금지)
  "affected_files": []           // ○ 배열
}
```

---

## 검증 체크리스트

### 기본 필드 (V1.1)
- [ ] `output_filename` 존재 (Root 필수)
- [ ] `scan_metadata.scan_date` 존재 (NOT timestamp)
- [ ] `scan_metadata.repository` 존재
- [ ] `scan_metadata.target_repository` 존재 (NOT target)
- [ ] `scan_metadata.total_files` 존재
- [ ] `scan_metadata.code_files` 존재
- [ ] `scan_metadata.scan_depth` 존재
- [ ] `english_report.repository_summary` 객체 존재
- [ ] `repository_summary.sensitive_files_detected` 사용 (NOT `dangerous_files_found`)
- [ ] `repository_summary.file_statistics.python_files` 존재
- [ ] `repository_summary.file_statistics.javascript_files` 존재
- [ ] `static_code_findings` 등 카테고리별 배열 존재
- [ ] `recommendations[]` 배열 (NOT 객체)
- [ ] `recommendations[].action` 존재
- [ ] `recommendations[].rationale` 존재
- [ ] `recommendations[].id` 형식 REC-NNN
- [ ] `recommendations[].rank` 정수, `priority` 문자열 (정수 금지)
- [ ] `recommendations[].finding_ids` 비어있지 않음, 실재 finding id만 참조
- [ ] 모든 severity 값 첫 글자 대문자
- [ ] finding에 `issue` 필드 사용 (NOT title)

### 카테고리별 필수 필드 (상세)

#### static_code_findings
```json
{
  "id": "STATIC-001",           // ✓ 필수 - STATIC-NNN 형식
  "file": "src/utils/shell.py", // ✓ 필수 - 파일 경로 (NOT location)
  "line": 45,                   // ○ 선택 - 숫자 (NOT "45-50" 범위)
  "issue": "Command Injection", // ✓ 필수 - 이슈 제목 (NOT title)
  "description": "...",         // ✓ 필수 - 상세 설명
  "severity": "High",           // ✓ 필수 - 대문자 시작
  "status": "Confirmed",        // ○ 선택 - Confirmed|Mitigated|False Positive
  "deep_dive_result": "...",    // ○ 선택 - 3단계 분석 결과
  "recommendation": "..."       // ✓ 필수 - 권장 조치 (NOT remediation)
}
```

#### sensitive_patterns
```json
{
  "id": "SENS-001",                    // ✓ 필수 - SENS-NNN 형식
  "file": ".env.production",           // ✓ 필수 - 파일 경로 (NOT location)
  "pattern": "AWS Secret Key",         // ✓ 필수 - 패턴 이름 (NOT issue, NOT type)
  "detail": "AWS_SECRET_ACCESS_KEY=***", // ✓ 필수 - 상세 (NOT description)
  "severity": "Critical",              // ✓ 필수 - 대문자 시작
  "status": "Confirmed",               // ○ 선택
  "gitignore_status": "Not in .gitignore - RISK" // ○ 선택 - gitignore 상태
}
```

#### agent_policy_findings
```json
{
  "id": "AGENT-001",            // ✓ 필수 - AGENT-NNN 형식
  "file": "src/mcpServer.ts",   // ✓ 필수 - 파일 경로 (NOT location)
  "agent": "MCP Server",        // ✓ 필수 - 에이전트 이름
  "issue": "No rate limiting",  // ✓ 필수 - 이슈 설명
  "disallowed_tools": [],       // ○ 선택 - 비허용 도구 목록
  "severity": "Medium",         // ✓ 필수
  "recommendation": "..."       // ✓ 필수
}
```

#### skill_risk_findings
```json
{
  "id": "SKILL-001",              // ✓ 필수 - SKILL-NNN 형식
  "file": "src/utils/exec.ts",    // ✓ 필수 - 파일 경로
  "fragment": "exec(...)",        // ✓ 필수 - 코드 조각
  "risk_type": "Command Execution", // ✓ 필수 - 위험 유형
  "analysis": "...",              // ✓ 필수 - 분석 내용
  "severity": "High",             // ✓ 필수
  "status": "Mitigated",          // ○ 선택
  "recommendation": "..."         // ✓ 필수
}
```

#### binary_analysis_findings
```json
{
  "id": "BIN-001",               // ✓ 필수 - BIN-NNN 형식
  "file": "dist/app.pyc",        // ✓ 필수 - 파일 경로
  "behaviors": ["Network", "File"], // ✓ 필수 - 행동 목록 (배열)
  "risk_summary": "...",         // ✓ 필수 - 위험 요약
  "severity": "Medium"           // ✓ 필수
}
```

#### prompt_optimization
```json
{
  "id": "OPT-001",               // ✓ 필수 - OPT-NNN 형식
  "file": "prompts/main.md",     // ✓ 필수 - 파일 경로
  "issue": "Excessive whitespace", // ✓ 필수 - 이슈
  "examples": "Lines 50-100...", // ✓ 필수 - 예시
  "severity": "Low",             // ✓ 필수
  "recommendation": "..."        // ✓ 필수
}
```

### SBOM 필드 (V1.2 추가)
- [ ] `sbom_analysis` 객체 존재
- [ ] `sbom_analysis.manifest_files_found` 배열 존재
- [ ] `sbom_analysis.dependency_statistics` 객체 존재
- [ ] `sbom_analysis.license_summary` 객체 존재
- [ ] `sbom_analysis.vulnerability_findings` 배열 존재
- [ ] `sbom_analysis.license_findings` 배열 존재
- [ ] `sbom_analysis.version_risk_findings` 배열 존재
- [ ] `sbom_analysis.supply_chain_findings` 배열 존재
- [ ] `sbom_analysis.sbom_documentation_status` 객체 존재
- [ ] `sbom_analysis.risk_matrix` 객체 존재
- [ ] `sbom_analysis.priority_actions` 배열 존재

## 통계 생성

### Severity 분포
```json
{
  "severity_distribution": {
    "critical": 2,
    "high": 8,
    "medium": 15,
    "low": 23
  }
}
```

### 카테고리별 분포
```json
{
  "category_distribution": {
    "static_code": 12,
    "binary": 2,
    "skill_security": 5,
    "sensitive_pattern": 8,
    "agent_policy": 3,
    "prompt_optimization": 6,
    "sbom": 12
  }
}
```

## 일반적인 실수 방지

| ❌ 잘못된 형식 | ✓ 올바른 형식 |
|----------------|---------------|
| `dangerous_files_found` | `sensitive_files_detected` |
| `description` (recommendations) | `rationale` |
| `affected_file` | `affected_files` (배열) |
| severity 소문자 | severity **첫 글자 대문자** |
| `javascriptFiles` | `javascript_files` |
| `vulnerabilityFindings` | `vulnerability_findings` |

## 제약 사항

- 파일 생성 금지 (JSON 출력만)
- 원본 finding 수정 금지 (병합만)
- 시스템 명령 실행 금지

## 사용 예시

```
사용자: @report-merger [스캔 결과들]

응답:
최종 보고서 생성 완료

요약:
- 총 파일: 156개
- 코드 파일: 42개
- 발견된 이슈: 48개
  - Critical: 2
  - High: 8
  - Medium: 15
  - Low: 23

주요 권장사항:
1. [Critical] AWS 자격 증명 즉시 로테이션
2. [Critical] .env 파일 .gitignore에 추가
3. [High] lodash 4.17.21로 업그레이드
...

[JSON 보고서 출력]
```
