# Schema V1.2 강제 준수 가이드라인

> **⚠️ 이 문서는 모든 Security Reports 스킬이 반드시 따라야 하는 절대 규칙입니다.**

---

## 1. 루트 구조 (Root Structure)

```json
{
  "output_filename": "scanreport-YYYYMMDDhhmmss.json",  // ✓ 필수
  "scan_metadata": { ... },                             // ✓ 필수
  "english_report": { ... },                            // ✓ 필수
  "korean_report": { ... }                              // ✓ 필수
}
```

### ❌ 금지된 루트 필드 (절대 추가 금지)
```
findings_summary      → 제거
executive_summary     → 제거
positive_findings     → 제거
findings              → 제거 (단일 배열 금지)
recommendations       → english_report/korean_report 내부로
scan_results          → 제거
summary               → 제거
```

---

## 2. scan_metadata 필수 필드

```json
"scan_metadata": {
  "scan_date": "2026-02-05T14:30:22Z",     // ✓ 필수 (ISO 8601)
  "scanner_version": "Claude Threat Scan V2.0",
  "repository": "project-name",             // ✓ 필수
  "target_repository": "project-name",      // ✓ 필수 (뷰어 표시)
  "total_files_scanned": 156,               // ✓ 필수
  "total_files": 156,                       // ✓ 필수 (뷰어 summary card)
  "code_files": 42,                         // ✓ 필수
  "analysis_depth": 3,                      // ✓ 필수
  "scan_depth": 3                           // ✓ 필수 (뷰어 표시)
}
```

### ❌ 금지된 필드명
| 사용 금지 | 올바른 필드 |
|-----------|-------------|
| `scan_id` | `scan_date` 사용 |
| `timestamp` | `scan_date` 사용 |
| `target` | `target_repository` 사용 |
| `target_info` | 플랫 구조 사용 |
| `scan_type` | 제거 |

---

## 3. english_report / korean_report 구조

```json
"english_report": {
  "repository_summary": {},          // ✓ 필수 객체
  "static_code_findings": [],        // ✓ 필수 배열
  "binary_analysis_findings": [],    // ✓ 필수 배열
  "skill_risk_findings": [],         // ✓ 필수 배열
  "agent_policy_findings": [],       // ✓ 필수 배열
  "sensitive_patterns": [],          // ✓ 필수 배열
  "prompt_optimization": [],         // ✓ 필수 배열
  "sbom_analysis": {},               // ✓ 필수 객체 (V1.2)
  "recommendations": []              // ✓ 필수 배열
}
```

---

## 4. 카테고리별 필수 필드 (엄격 준수)

### 4.1 static_code_findings

```json
{
  "id": "STATIC-001",           // ✓ 필수 - 형식: STATIC-NNN
  "file": "src/utils/shell.py", // ✓ 필수 - 파일 경로
  "line": 45,                   // ○ 선택 - 숫자만 (NOT 범위)
  "issue": "Command Injection", // ✓ 필수 - 이슈 제목
  "description": "...",         // ✓ 필수 - 상세 설명
  "severity": "High",           // ✓ 필수 - 대문자 시작
  "status": "Confirmed",        // ○ 선택
  "deep_dive_result": "...",    // ○ 선택
  "recommendation": "..."       // ✓ 필수 - 권장 조치
}
```

#### ❌ 금지 필드
| 사용 금지 | 올바른 필드 |
|-----------|-------------|
| `finding_id` | `id` |
| `location` | `file` |
| `title` | `issue` |
| `type` | `issue` |
| `category` | 제거 |
| `remediation` | `recommendation` |
| `code_snippet` | 제거 |
| `cwe`, `owasp` | 제거 |
| `column` | 제거 |

---

### 4.2 sensitive_patterns

```json
{
  "id": "SENS-001",                    // ✓ 필수 - 형식: SENS-NNN
  "file": ".env.production",           // ✓ 필수 - 파일 경로
  "pattern": "AWS Secret Key",         // ✓ 필수 - 패턴 이름
  "detail": "AWS_SECRET_ACCESS_KEY=***", // ✓ 필수 - 상세 내용
  "severity": "Critical",              // ✓ 필수 - 대문자 시작
  "status": "Confirmed",               // ○ 선택
  "gitignore_status": "Not in .gitignore - RISK" // ○ 선택
}
```

#### ❌ 금지 필드
| 사용 금지 | 올바른 필드 |
|-----------|-------------|
| `finding_id` | `id` |
| `location` | `file` |
| `issue` | `pattern` |
| `type` | `pattern` |
| `description` | `detail` |

---

### 4.3 agent_policy_findings

```json
{
  "id": "AGENT-001",            // ✓ 필수 - 형식: AGENT-NNN
  "file": "src/mcpServer.ts",   // ✓ 필수 - 파일 경로
  "agent": "MCP Server",        // ✓ 필수 - 에이전트 이름
  "issue": "No rate limiting",  // ✓ 필수 - 이슈 설명
  "disallowed_tools": [],       // ○ 선택 - 배열
  "severity": "Medium",         // ✓ 필수 - 대문자 시작
  "recommendation": "..."       // ✓ 필수 - 권장 조치
}
```

#### ❌ 금지 필드
| 사용 금지 | 올바른 필드 |
|-----------|-------------|
| `location` | `file` |
| `title` | `issue` |
| `remediation` | `recommendation` |

---

### 4.4 skill_risk_findings

```json
{
  "id": "SKILL-001",              // ✓ 필수 - 형식: SKILL-NNN
  "file": "src/utils/exec.ts",    // ✓ 필수 - 파일 경로
  "fragment": "exec(...)",        // ✓ 필수 - 코드 조각
  "risk_type": "Command Execution", // ✓ 필수 - 위험 유형
  "analysis": "...",              // ✓ 필수 - 분석 내용
  "severity": "High",             // ✓ 필수 - 대문자 시작
  "status": "Mitigated",          // ○ 선택
  "recommendation": "..."         // ✓ 필수 - 권장 조치
}
```

---

### 4.5 binary_analysis_findings

```json
{
  "id": "BIN-001",               // ✓ 필수 - 형식: BIN-NNN
  "file": "dist/app.pyc",        // ✓ 필수 - 파일 경로
  "behaviors": ["Network", "File"], // ✓ 필수 - 배열
  "risk_summary": "...",         // ✓ 필수 - 위험 요약
  "severity": "Medium"           // ✓ 필수 - 대문자 시작
}
```

---

### 4.6 prompt_optimization

```json
{
  "id": "OPT-001",               // ✓ 필수 - 형식: OPT-NNN
  "file": "prompts/main.md",     // ✓ 필수 - 파일 경로
  "issue": "Excessive whitespace", // ✓ 필수 - 이슈
  "examples": "Lines 50-100...", // ✓ 필수 - 예시
  "severity": "Low",             // ✓ 필수 - 대문자 시작
  "recommendation": "..."        // ✓ 필수 - 권장 조치
}
```

---

### 4.7 recommendations

```json
{
  "priority": "Critical",        // ✓ 필수 - 대문자 시작
  "action": "What to do",        // ✓ 필수 - 뷰어 렌더링용
  "rationale": "Why",            // ✓ 필수 - 뷰어 렌더링용
  "category": "Security",        // ○ 선택
  "affected_files": []           // ○ 선택 - 배열
}
```

#### ❌ 금지 필드
| 사용 금지 | 올바른 필드 |
|-----------|-------------|
| `description` (메인) | `rationale` |
| `affected_file` (단수) | `affected_files` (배열) |

---

## 5. SBOM Analysis 필수 구조 (V1.2)

```json
"sbom_analysis": {
  "manifest_files_found": [             // ✓ 필수 배열
    {
      "file": "package.json",           // ✓ 필수
      "ecosystem": "npm",               // ✓ 필수
      "direct_dependencies": 25,        // ✓ 필수
      "dev_dependencies": 15            // ✓ 필수
    }
  ],
  "dependency_statistics": {            // ✓ 필수 객체
    "total_direct": 40,                 // ✓ 필수
    "total_dev": 15,                    // ✓ 필수
    "total_transitive": 450,            // ○ 선택
    "by_ecosystem": { "npm": 40 }       // ✓ 필수
  },
  "license_summary": {                  // ✓ 필수 객체
    "MIT": 35,
    "Apache-2.0": 8,
    "ISC": 5
  },
  "vulnerability_findings": [],         // ✓ 필수 배열
  "license_findings": [],               // ✓ 필수 배열
  "version_risk_findings": [],          // ✓ 필수 배열
  "supply_chain_findings": [],          // ✓ 필수 배열
  "sbom_documentation_status": {        // ✓ 필수 객체
    "sbom_file_exists": false,          // ✓ 필수 boolean
    "sbom_format": null,                // ✓ 필수 (string|null)
    "ci_sbom_generation": false,        // ✓ 필수 boolean
    "completeness": "Missing",          // ✓ 필수 string
    "recommendation": "..."             // ○ 선택
  },
  "risk_matrix": {                      // ✓ 필수 객체
    "vulnerabilities": {"critical": 0, "high": 0, "medium": 0, "low": 0},
    "license_issues": {"critical": 0, "high": 0, "medium": 0, "low": 0},
    "version_risks": {"critical": 0, "high": 0, "medium": 0, "low": 0},
    "supply_chain": {"critical": 0, "high": 0, "medium": 0, "low": 0}
  },
  "priority_actions": []                // ✓ 필수 배열
}
```

### 5.1 vulnerability_findings

```json
{
  "id": "VULN-001",              // ✓ 필수 - 형식: VULN-NNN
  "file": "package.json",        // ✓ 필수
  "package": "lodash",           // ✓ 필수
  "version": "4.17.15",          // ✓ 필수
  "cve_ids": ["CVE-2020-8203"],  // ○ 선택 - 배열
  "severity": "High",            // ✓ 필수
  "description": "...",          // ✓ 필수
  "fixed_version": "4.17.21",    // ○ 선택
  "recommendation": "..."        // ✓ 필수
}
```

### 5.2 license_findings

```json
{
  "id": "LIC-001",               // ✓ 필수 - 형식: LIC-NNN
  "file": "package.json",        // ✓ 필수
  "package": "gpl-package",      // ✓ 필수
  "version": "1.0.0",            // ✓ 필수
  "license": "GPL-3.0",          // ✓ 필수
  "issue": "Copyleft",           // ✓ 필수
  "project_license": "MIT",      // ○ 선택
  "severity": "High",            // ✓ 필수
  "recommendation": "..."        // ✓ 필수
}
```

### 5.3 version_risk_findings

```json
{
  "id": "VER-001",               // ✓ 필수 - 형식: VER-NNN
  "file": "package.json",        // ✓ 필수
  "package": "express",          // ✓ 필수
  "current_version": "^4.17.0",  // ✓ 필수
  "issue": "Unpinned",           // ✓ 필수
  "severity": "Low",             // ✓ 필수
  "recommendation": "..."        // ✓ 필수
}
```

### 5.4 supply_chain_findings

```json
{
  "id": "SUPPLY-001",            // ✓ 필수 - 형식: SUPPLY-NNN
  "file": "package.json",        // ✓ 필수
  "package": "lod-ash",          // ✓ 필수
  "risk_type": "Typosquatting",  // ✓ 필수
  "severity": "Critical",        // ✓ 필수
  "detail": "...",               // ✓ 필수
  "recommendation": "..."        // ✓ 필수
}
```

### 5.5 priority_actions

```json
{
  "rank": 1,                     // ✓ 필수 - 숫자
  "category": "Vulnerability",   // ✓ 필수
  "package": "lodash",           // ✓ 필수
  "current_version": "4.17.15",  // ✓ 필수
  "action": "Upgrade to 4.17.21", // ✓ 필수
  "severity": "High",            // ✓ 필수
  "rationale": "..."             // ✓ 필수
}
```

### ❌ SBOM 금지 필드
| 사용 금지 | 올바른 필드 |
|-----------|-------------|
| `total_dependencies` | `dependency_statistics.total_direct` |
| `direct_dependencies` (root) | `dependency_statistics.total_direct` |
| `dev_dependencies` (root) | `dependency_statistics.total_dev` |
| `vulnerabilities` (카운트 객체) | `vulnerability_findings` (배열) |
| `license_analysis` | `license_summary` (카운트 객체) |
| `notable_packages` | 제거 |
| `version_pinning` | `version_risk_findings` 배열로 |

---

## 6. repository_summary 필수 필드

```json
"repository_summary": {
  "description": "Project description",
  "file_statistics": {
    "total_files": 156,           // ✓ 필수
    "python_files": 12,           // ✓ 필수 (underscore)
    "javascript_files": 8,        // ✓ 필수 (underscore)
    "typescript_tsx": 25,         // ✓ 필수
    "markdown_files": 10,         // ✓ 필수
    "json_files": 5,              // ✓ 필수
    "pem_files": 0,               // ✓ 필수
    "yaml": 3,
    "css": 2,
    "svg": 1,
    "html": 2,
    "other": 88
  },
  "key_components": [],
  "sensitive_files_detected": []  // ✓ 필수 (NOT dangerous_files_found)
}
```

### ❌ 금지 필드
| 사용 금지 | 올바른 필드 |
|-----------|-------------|
| `dangerous_files_found` | `sensitive_files_detected` |
| `pythonFiles` (camelCase) | `python_files` (underscore) |
| `javascriptFiles` | `javascript_files` |

---

## 7. Severity 값 규칙

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

## 8. ID 형식 규칙

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

---

## 9. 검증 체크리스트

### 필수 검증 (스캔 완료 전)

```
□ output_filename 존재 (Root)
□ scan_metadata.scan_date 존재 (NOT timestamp)
□ scan_metadata.repository 존재
□ scan_metadata.target_repository 존재 (NOT target)
□ scan_metadata.total_files 존재
□ scan_metadata.code_files 존재
□ scan_metadata.scan_depth 존재

□ english_report.repository_summary 객체 존재
□ repository_summary.sensitive_files_detected 사용 (NOT dangerous_files_found)
□ repository_summary.file_statistics.python_files 존재 (underscore)
□ repository_summary.file_statistics.javascript_files 존재 (underscore)

□ static_code_findings 배열 존재
□ static_code_findings[].id 형식: STATIC-NNN
□ static_code_findings[].file 필드 사용 (NOT location)
□ static_code_findings[].issue 필드 사용 (NOT title)
□ static_code_findings[].recommendation 필드 사용 (NOT remediation)

□ sensitive_patterns 배열 존재
□ sensitive_patterns[].pattern 필드 사용 (NOT issue, NOT type)
□ sensitive_patterns[].detail 필드 사용 (NOT description)

□ agent_policy_findings 배열 존재
□ agent_policy_findings[].agent 필드 존재

□ sbom_analysis 객체 존재
□ sbom_analysis.manifest_files_found 배열 존재
□ sbom_analysis.dependency_statistics 객체 존재
□ sbom_analysis.dependency_statistics.total_direct 존재
□ sbom_analysis.dependency_statistics.total_dev 존재
□ sbom_analysis.license_summary 객체 존재 (카운트 형태)
□ sbom_analysis.vulnerability_findings 배열 존재
□ sbom_analysis.license_findings 배열 존재
□ sbom_analysis.version_risk_findings 배열 존재
□ sbom_analysis.supply_chain_findings 배열 존재
□ sbom_analysis.sbom_documentation_status 객체 존재
□ sbom_analysis.risk_matrix 객체 존재
□ sbom_analysis.priority_actions 배열 존재

□ recommendations 배열 존재 (NOT 객체)
□ recommendations[].action 존재
□ recommendations[].rationale 존재

□ 모든 severity 값 첫 글자 대문자
□ 모든 ID 형식 일관성 검증
```

---

## 10. 위반 시 결과

- **뷰어 렌더링 실패**: 잘못된 필드명으로 인해 빈 섹션 표시
- **SBOM 섹션 미표시**: sbom_analysis 구조 불일치 시 완전 누락
- **Summary Card 오류**: total_files, code_files 누락 시 0 표시
- **권장사항 미표시**: action, rationale 누락 시 빈 카드

---

**이 문서는 모든 스킬 개발 및 수정 시 반드시 참조해야 합니다.**

마지막 업데이트: 2026-02-05 (Schema V1.2)
