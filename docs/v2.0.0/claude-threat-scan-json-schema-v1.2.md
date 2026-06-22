# Claude Threat Scan JSON Schema Specification v1.2

본 문서는 `security-report-viewer-claude.html` 뷰어와 호환되는 JSON 출력 규격을 정의한다.

**V1.2 변경사항**: SBOM(Software Bill of Materials) 및 의존성 보안 분석 필드 추가

---

## 1. Root Structure

```json
{
  "output_filename": "scanreport-YYYYMMDDhhmmss.json",
  "scan_metadata": {},
  "english_report": {},
  "korean_report": {}
}
```

모든 필드는 **필수**이다.

---

## 2. scan_metadata

```json
"scan_metadata": {
  "scan_date": "2026-01-06T12:00:00Z",
  "scanner_version": "Claude Threat Scan V2.0",
  "repository": "project-name",
  "target_repository": "project-name",
  "total_files_scanned": 32,
  "total_files": 32,
  "code_files": 8,
  "analysis_depth": 3,
  "scan_depth": 3
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `scan_date` | string | ✓ | ISO 8601 형식 |
| `scanner_version` | string | ✓ | 스캐너 버전 (V2.0+) |
| `repository` | string | ✓ | 저장소명 (짧은 이름) |
| `target_repository` | string | ✓ | 대상 저장소명 (뷰어 표시용) |
| `total_files_scanned` | number | ✓ | 스캔된 전체 파일 수 |
| `total_files` | number | ✓ | 전체 파일 수 (뷰어 summary card) |
| `code_files` | number | ✓ | 코드 파일 수 |
| `analysis_depth` | number | ✓ | 분석 깊이 (1-3) |
| `scan_depth` | number | ✓ | 스캔 깊이 (뷰어 표시용) |

---

## 3. english_report / korean_report Structure

```json
"english_report": {
  "repository_summary": {},
  "static_code_findings": [],
  "binary_analysis_findings": [],
  "skill_risk_findings": [],
  "agent_policy_findings": [],
  "sensitive_patterns": [],
  "prompt_optimization": [],
  "sbom_analysis": {},
  "recommendations": []
}
```

**V1.2 추가**: `sbom_analysis` 객체

---

## 4. repository_summary

```json
"repository_summary": {
  "description": "Project description here",
  "file_statistics": {
    "total_files": 32,
    "python_files": 0,
    "javascript_files": 1,
    "typescript_tsx": 7,
    "markdown_files": 6,
    "json_files": 4,
    "pem_files": 0,
    "yaml": 1,
    "css": 1,
    "svg": 5,
    "html": 1,
    "other": 6
  },
  "key_components": [
    "Component 1",
    "Component 2"
  ],
  "sensitive_files_detected": [
    ".cursor/config.json - Contains access token placeholder"
  ]
}
```

### ⚠️ 주의사항
- `dangerous_files_found` 사용 금지 → `sensitive_files_detected` 사용
- `file_statistics` 내 필드명은 **언더스코어(_) 형식** 사용

---

## 5. static_code_findings

```json
{
  "id": "STATIC-001",
  "file": ".cursor/config.json",
  "line": 9,
  "issue": "Hardcoded Credential Placeholder",
  "description": "Contains placeholder string 'YOUR_SUPABASE_ACCESS_TOKEN_HERE' which could be replaced with real credentials.",
  "severity": "High",
  "status": "Confirmed",
  "deep_dive_result": "File is not in .gitignore. HIGH RISK if token is added.",
  "recommendation": "Add .cursor/config.json to .gitignore immediately."
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | ✓ | 형식: `STATIC-NNN` |
| `file` | string | ✓ | 파일 경로 |
| `line` | number | ○ | 라인 번호 |
| `issue` | string | ✓ | 이슈 제목 |
| `description` | string | ✓ | 상세 설명 |
| `severity` | string | ✓ | `Critical` \| `High` \| `Medium` \| `Low` |
| `status` | string | ○ | `Confirmed` \| `Mitigated` \| `False Positive` |
| `deep_dive_result` | string | ○ | 심층 분석 결과 |
| `recommendation` | string | ✓ | 권장 조치 |

---

## 6. binary_analysis_findings

```json
{
  "id": "BIN-001",
  "file": "dist/app.pyc",
  "behaviors": ["Network communication", "File system access"],
  "risk_summary": "Compiled Python file with network capabilities detected.",
  "severity": "Medium"
}
```

| Field | Type | Required |
|-------|------|----------|
| `id` | string | ✓ |
| `file` | string | ✓ |
| `behaviors` | array | ✓ |
| `risk_summary` | string | ✓ |
| `severity` | string | ✓ |

---

## 7. skill_risk_findings

```json
{
  "id": "SKILL-001",
  "file": ".cursor/config.json",
  "fragment": "@supabase/mcp-server-supabase with --access-token",
  "risk_type": "Credential Exposure Risk",
  "analysis": "MCP server configuration requires access token for Supabase operations.",
  "severity": "High",
  "status": "Confirmed",
  "recommendation": "1. Add .cursor/ to .gitignore. 2. Use environment variables."
}
```

| Field | Type | Required |
|-------|------|----------|
| `id` | string | ✓ |
| `file` | string | ✓ |
| `fragment` | string | ✓ |
| `risk_type` | string | ✓ |
| `analysis` | string | ✓ |
| `severity` | string | ✓ |
| `status` | string | ○ |
| `recommendation` | string | ✓ |

---

## 8. agent_policy_findings

```json
{
  "id": "AGENT-001",
  "file": "agents/data-agent.yaml",
  "agent": "DataProcessingAgent",
  "issue": "No disallowed_tools policy defined.",
  "disallowed_tools": ["execute_command", "write_file", "network_request"],
  "severity": "Medium",
  "recommendation": "Define explicit disallowed_tools list."
}
```

| Field | Type | Required |
|-------|------|----------|
| `id` | string | ✓ |
| `file` | string | ✓ |
| `agent` | string | ✓ |
| `issue` | string | ✓ |
| `disallowed_tools` | array | ○ |
| `severity` | string | ✓ |
| `recommendation` | string | ✓ |

---

## 9. sensitive_patterns

```json
{
  "id": "SENS-001",
  "file": ".cursor/config.json",
  "pattern": "access-token",
  "detail": "Placeholder token detected. Safe currently but file should be gitignored.",
  "severity": "Medium",
  "status": "Potential Risk",
  "gitignore_status": "Not in .gitignore - RISK"
}
```

| Field | Type | Required |
|-------|------|----------|
| `id` | string | ✓ |
| `file` | string | ✓ |
| `pattern` | string | ✓ |
| `detail` | string | ✓ |
| `severity` | string | ✓ |
| `status` | string | ○ |
| `gitignore_status` | string | ○ |

---

## 10. prompt_optimization

```json
{
  "id": "OPT-001",
  "file": "app/page.tsx",
  "issue": "Large Monolithic Component",
  "examples": "Single file contains 1012 lines with multiple sub-components",
  "severity": "Low",
  "recommendation": "Consider splitting into separate component files."
}
```

| Field | Type | Required |
|-------|------|----------|
| `id` | string | ✓ |
| `file` | string | ✓ |
| `issue` | string | ✓ |
| `examples` | string | ✓ |
| `severity` | string | ✓ |
| `recommendation` | string | ✓ |

---

## 11. sbom_analysis (NEW in V1.2)

SBOM 분석 결과를 포함하는 객체.

```json
"sbom_analysis": {
  "manifest_files_found": [],
  "dependency_statistics": {},
  "license_summary": {},
  "vulnerability_findings": [],
  "license_findings": [],
  "version_risk_findings": [],
  "supply_chain_findings": [],
  "sbom_documentation_status": {},
  "risk_matrix": {},
  "priority_actions": []
}
```

### 11.1 manifest_files_found

```json
"manifest_files_found": [
  {
    "file": "package.json",
    "ecosystem": "npm",
    "direct_dependencies": 25,
    "dev_dependencies": 15
  },
  {
    "file": "requirements.txt",
    "ecosystem": "pip",
    "direct_dependencies": 12,
    "dev_dependencies": 0
  }
]
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `file` | string | ✓ | 매니페스트 파일 경로 |
| `ecosystem` | string | ✓ | `npm` \| `pip` \| `maven` \| `gradle` \| `go` \| `cargo` \| `gem` \| `composer` \| `nuget` |
| `direct_dependencies` | number | ✓ | 직접 의존성 수 |
| `dev_dependencies` | number | ✓ | 개발 의존성 수 |

### 11.2 dependency_statistics

```json
"dependency_statistics": {
  "total_direct": 40,
  "total_dev": 15,
  "total_transitive": 450,
  "by_ecosystem": {
    "npm": 40,
    "pip": 0
  }
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `total_direct` | number | ✓ | 총 직접 의존성 수 |
| `total_dev` | number | ✓ | 총 개발 의존성 수 |
| `total_transitive` | number | ○ | 총 전이 의존성 수 (lock 파일 기준) |
| `by_ecosystem` | object | ✓ | 생태계별 의존성 수 |

### 11.3 license_summary

```json
"license_summary": {
  "MIT": 35,
  "Apache-2.0": 8,
  "ISC": 5,
  "BSD-3-Clause": 2,
  "GPL-3.0": 1,
  "Unknown": 2
}
```

라이선스 타입별 패키지 수를 집계.

### 11.4 vulnerability_findings

```json
{
  "id": "VULN-001",
  "file": "package.json",
  "package": "lodash",
  "version": "4.17.15",
  "cve_ids": ["CVE-2020-8203", "CVE-2021-23337"],
  "severity": "High",
  "description": "Prototype pollution vulnerability in lodash before 4.17.19",
  "fixed_version": "4.17.21",
  "recommendation": "Upgrade lodash to version 4.17.21 or later"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | ✓ | 형식: `VULN-NNN` |
| `file` | string | ✓ | 매니페스트 파일 경로 |
| `package` | string | ✓ | 패키지명 |
| `version` | string | ✓ | 현재 버전 |
| `cve_ids` | array | ○ | 관련 CVE ID 목록 |
| `severity` | string | ✓ | `Critical` \| `High` \| `Medium` \| `Low` |
| `description` | string | ✓ | 취약점 설명 |
| `fixed_version` | string | ○ | 패치된 버전 |
| `recommendation` | string | ✓ | 권장 조치 |

### 11.5 license_findings

```json
{
  "id": "LIC-001",
  "file": "package.json",
  "package": "gpl-package",
  "version": "1.0.0",
  "license": "GPL-3.0",
  "issue": "Copyleft",
  "project_license": "MIT",
  "severity": "High",
  "recommendation": "GPL-3.0 license is incompatible with MIT. Consider alternative package or license review."
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | ✓ | 형식: `LIC-NNN` |
| `file` | string | ✓ | 매니페스트 파일 경로 |
| `package` | string | ✓ | 패키지명 |
| `version` | string | ✓ | 버전 |
| `license` | string | ✓ | 라이선스 유형 |
| `issue` | string | ✓ | `Incompatible` \| `Copyleft` \| `Unknown` \| `Missing` |
| `project_license` | string | ○ | 프로젝트 라이선스 |
| `severity` | string | ✓ | 심각도 |
| `recommendation` | string | ✓ | 권장 조치 |

### 11.6 version_risk_findings

```json
{
  "id": "VER-001",
  "file": "package.json",
  "package": "express",
  "current_version": "^4.17.0",
  "issue": "Unpinned",
  "severity": "Low",
  "recommendation": "Consider pinning to exact version for reproducible builds"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | ✓ | 형식: `VER-NNN` |
| `file` | string | ✓ | 매니페스트 파일 경로 |
| `package` | string | ✓ | 패키지명 |
| `current_version` | string | ✓ | 현재 버전/범위 |
| `issue` | string | ✓ | `Unpinned` \| `Wildcard` \| `Outdated` \| `Deprecated` |
| `severity` | string | ✓ | 심각도 |
| `recommendation` | string | ✓ | 권장 조치 |

### 11.7 supply_chain_findings

```json
{
  "id": "SUPPLY-001",
  "file": "package.json",
  "package": "lod-ash",
  "risk_type": "Typosquatting",
  "severity": "Critical",
  "detail": "Package name 'lod-ash' is suspiciously similar to popular package 'lodash'",
  "recommendation": "Verify package authenticity. Replace with official 'lodash' if intended."
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | ✓ | 형식: `SUPPLY-NNN` |
| `file` | string | ✓ | 매니페스트 파일 경로 |
| `package` | string | ✓ | 패키지명 |
| `risk_type` | string | ✓ | `Typosquatting` \| `UnmaintainedPackage` \| `NonStandardRegistry` \| `GitDependency` \| `LocalPath` |
| `severity` | string | ✓ | 심각도 |
| `detail` | string | ✓ | 상세 설명 |
| `recommendation` | string | ✓ | 권장 조치 |

### 11.8 sbom_documentation_status

```json
"sbom_documentation_status": {
  "sbom_file_exists": false,
  "sbom_format": null,
  "sbom_file_path": null,
  "ci_sbom_generation": false,
  "completeness": "Missing",
  "recommendation": "Generate SBOM using CycloneDX or SPDX format for supply chain transparency"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `sbom_file_exists` | boolean | ✓ | SBOM 파일 존재 여부 |
| `sbom_format` | string \| null | ✓ | `SPDX` \| `CycloneDX` \| `null` |
| `sbom_file_path` | string \| null | ○ | SBOM 파일 경로 |
| `ci_sbom_generation` | boolean | ✓ | CI/CD SBOM 생성 설정 여부 |
| `completeness` | string | ✓ | `Complete` \| `Partial` \| `Missing` |
| `recommendation` | string | ○ | 권장 조치 |

### 11.9 risk_matrix

```json
"risk_matrix": {
  "vulnerabilities": {
    "critical": 0,
    "high": 2,
    "medium": 5,
    "low": 3
  },
  "license_issues": {
    "critical": 0,
    "high": 1,
    "medium": 2,
    "low": 0
  },
  "version_risks": {
    "critical": 0,
    "high": 0,
    "medium": 8,
    "low": 15
  },
  "supply_chain": {
    "critical": 0,
    "high": 0,
    "medium": 1,
    "low": 2
  }
}
```

### 11.10 priority_actions

```json
"priority_actions": [
  {
    "rank": 1,
    "category": "Vulnerability",
    "package": "lodash",
    "current_version": "4.17.15",
    "action": "Upgrade to 4.17.21",
    "severity": "High",
    "rationale": "Multiple prototype pollution CVEs affecting current version"
  },
  {
    "rank": 2,
    "category": "License",
    "package": "gpl-package",
    "current_version": "1.0.0",
    "action": "Replace with MIT-licensed alternative",
    "severity": "High",
    "rationale": "GPL-3.0 incompatible with project MIT license"
  }
]
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `rank` | number | ✓ | 우선순위 (1이 가장 높음) |
| `category` | string | ✓ | `Vulnerability` \| `License` \| `Version` \| `SupplyChain` |
| `package` | string | ✓ | 패키지명 |
| `current_version` | string | ✓ | 현재 버전 |
| `action` | string | ✓ | 권장 조치 |
| `severity` | string | ✓ | 심각도 |
| `rationale` | string | ✓ | 근거 |

---

## 12. recommendations ⚠️ CRITICAL

```json
{
  "priority": "Critical",
  "category": "Secret Management",
  "title": "Add .cursor/ directory to .gitignore",
  "action": "Add '.cursor/' to .gitignore file",
  "description": "The .cursor/config.json file contains placeholder for access tokens.",
  "rationale": "The .cursor/config.json file contains placeholder for access tokens and should never be committed with real credentials.",
  "affected_files": [".cursor/config.json", ".gitignore"]
}
```

### ⚠️ 필수 필드 (뷰어 렌더링용)

| Field | Viewer Display | Required |
|-------|----------------|----------|
| `priority` | ✓ (색상 구분) | ✓ |
| `action` | ✓ (메인 제목) | ✓ |
| `rationale` | ✓ (설명 텍스트) | ✓ |
| `affected_files` | ✓ (파일 목록) | ○ |
| `category` | ✗ | ○ |
| `title` | ✗ | ○ |
| `description` | ✗ | ○ |

---

## 13. Severity Values

유효한 severity 값:
- `Critical` - 즉시 조치 필요
- `High` - 우선 조치 필요
- `Medium` - 계획된 조치 필요
- `Low` - 개선 권장
- `Info` - 정보성 (sensitive_patterns에서만 사용)
- `None` - 해당 없음

---

## 14. ID Naming Convention

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

---

## 15. Common Mistakes to Avoid

| ❌ Wrong | ✓ Correct |
|----------|-----------|
| `dangerous_files_found` | `sensitive_files_detected` |
| `description` (in recommendations) | `rationale` |
| `affected_file` | `affected_files` (배열) |
| severity 소문자 | severity **첫 글자 대문자** |
| `javascriptFiles` | `javascript_files` |
| `vulnerabilityFindings` | `vulnerability_findings` |
| `licenseFindings` | `license_findings` |

---

## 16. Validation Checklist

JSON 생성 후 다음 항목 확인:

### 기본 필드 (V1.1)
- [ ] `scan_metadata.target_repository` 존재
- [ ] `scan_metadata.total_files` 존재
- [ ] `scan_metadata.code_files` 존재
- [ ] `scan_metadata.scan_depth` 존재
- [ ] `repository_summary.sensitive_files_detected` 사용 (NOT `dangerous_files_found`)
- [ ] `repository_summary.file_statistics.python_files` 존재
- [ ] `repository_summary.file_statistics.javascript_files` 존재
- [ ] `recommendations[].action` 존재
- [ ] `recommendations[].rationale` 존재
- [ ] 모든 severity 값 첫 글자 대문자

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
- [ ] 모든 SBOM finding ID 형식 준수 (`VULN-NNN`, `LIC-NNN`, `VER-NNN`, `SUPPLY-NNN`)

---

## 17. Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2025-12-31 | Initial specification |
| 1.1 | 2026-01-05 | Added viewer compatibility fields, fixed field naming conventions |
| 1.2 | 2026-01-06 | Added SBOM analysis section: vulnerability_findings, license_findings, version_risk_findings, supply_chain_findings, sbom_documentation_status, risk_matrix, priority_actions |

