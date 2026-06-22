---
name: securityreports-scan
description: "[DEPRECATED v2.3.0+] Security Reports Scan Main Script. Use /threat-scan instead."
disable-model-invocation: true
argument-hint: <target-path-or-url>
---

> ⚠️ **DEPRECATED (v2.3.0+)**: 이 명령은 구 SecurityScan 세대입니다.
> v2.1 통합 파이프라인은 `/threat-scan <target>`을 사용하세요.
> (그래프 전파·모델 유효성·심층분석·HTML 리포트 포함)

# Security Reports - Full Security Scan

**$ARGUMENTS** 에 대해 전체 보안 스캔을 수행합니다.

## ⚠️ 필수: 세션 ID 생성

**스캔 시작 시 반드시 고유 세션 ID를 생성합니다.**

```
SESSION_ID = {YYYYMMDD}-{HHMMSS}
```
예시: `20260205-143022`

이 SESSION_ID는 모든 개별 레포트 파일명에 사용됩니다.

## 📊 토큰 사용량 추적

### 스캔 시작 시
스캔 시작 전 현재 토큰 사용량을 기록합니다:
```
[SCAN_START] SESSION_ID: {SESSION_ID}
[SCAN_START] 시작 시간: {timestamp}
```

### 스캔 완료 시
최종 레포트에 토큰 사용량 정보를 포함합니다:
```json
{
  "scan_metadata": {
    "session_id": "20260205-143022",
    "token_usage": {
      "note": "Use /cost command to check token usage for this session"
    }
  }
}
```

### 사용자에게 안내
스캔 완료 후 토큰 확인 방법 안내:
```
💡 토큰 사용량 확인: /cost 명령어 입력
```

## 입력 처리

- **GitHub URL**: `https://github.com/owner/repo` → 자동 클론 (100MB 제한)
- **로컬 경로**: `/path/to/project` → 직접 스캔
- **ZIP 파일**: `./project.zip` → 자동 압축 해제

## 스캔 절차

### Phase 0: 소스 준비
- GitHub URL → shallow clone (--depth 1)
- ZIP 파일 → 샌드박스에 압축 해제 (/tmp/security-scan/)
- 용량 검증 (100MB 제한)

### Phase 1: 파일 분석
- 파일 구조 인덱싱 (repo-indexer 참조)
- 민감 파일 식별 (.env, credentials, keys)

### Phase 2: 코드 분석 + Deep Dive
- 정적 코드 분석 (static-code-analyzer 참조)
  - SQL Injection, XSS, Command Injection
  - 하드코딩된 자격 증명
  - 안전하지 않은 함수 사용
- **Deep Dive 분석** (securityreports-deepdive 참조)
  - 대상: severity ≥ Medium
  - 최대 3단계 재귀 분석
  - status 및 deep_dive_result 추가
- 임시 파일 저장: `.tmp-static-deepdive-{SESSION_ID}.json`

### Phase 3: 민감 정보 탐지 + Deep Dive
- API 키, 토큰, 비밀번호 패턴 (sensitive-pattern-matcher 참조)
- 민감 파일 (.env, *.pem, credentials.*)
- **Deep Dive 분석** (securityreports-deepdive 참조)
  - 대상: severity ≥ Medium
  - 최대 3단계 재귀 분석
  - status 및 deep_dive_result 추가
- 임시 파일 저장: `.tmp-secrets-deepdive-{SESSION_ID}.json`

### Phase 4: 의존성 분석 (SBOM) + Deep Dive
- package.json, requirements.txt, pom.xml 분석 (securityreports-sbom 참조)
- CVE 취약점 매핑
- 라이선스 호환성 검사
- 버전 고정 여부 확인
- **Deep Dive 분석** (securityreports-deepdive 참조)
  - 대상: severity ≥ Medium
  - 최대 3단계 재귀 분석
  - status 및 deep_dive_result 추가
- 임시 파일 저장: `.tmp-sbom-deepdive-{SESSION_ID}.json`

### Phase 5: 최종 보고서 생성
- 모든 Deep Dive 완료된 임시 파일 병합 (report-merger 참조)
- 영문/한글 bilingual JSON 보고서 생성 (bilingual-translator 참조)
- 심각도별 분류 (Critical, High, Medium, Low, Info)
- 최종 레포트 저장: `scanreport-{SESSION_ID}.json`
- 임시 파일 삭제

## ⚠️ 필수: 레포트 파일 관리

### 개별 레포트 (임시 파일)

각 스캔 단계에서 1차 분석 + Deep Dive 완료 후 임시 레포트 생성:

| 단계 | 파일명 |
|------|--------|
| 정적 분석 + Deep Dive | `.tmp-static-deepdive-{SESSION_ID}.json` |
| 민감 정보 + Deep Dive | `.tmp-secrets-deepdive-{SESSION_ID}.json` |
| SBOM + Deep Dive | `.tmp-sbom-deepdive-{SESSION_ID}.json` |

예시 (SESSION_ID = 20260205-143022):
- `.tmp-static-deepdive-20260205-143022.json`
- `.tmp-secrets-deepdive-20260205-143022.json`
- `.tmp-sbom-deepdive-20260205-143022.json`

### 최종 통합 레포트

**Phase 5 완료 후:**

1. **report-merger**가 모든 `.tmp-*-deepdive-{SESSION_ID}.json` 파일을 읽어 통합
2. **bilingual-translator**가 영문/한글 번역 수행
3. 최종 레포트 저장: `scanreport-{SESSION_ID}.json`
4. **임시 파일 삭제**: 모든 `.tmp-*-deepdive-{SESSION_ID}.json` 파일 삭제

```bash
# 삭제할 파일 (SESSION_ID = 20260205-143022 예시)
rm .tmp-static-deepdive-20260205-143022.json
rm .tmp-secrets-deepdive-20260205-143022.json
rm .tmp-sbom-deepdive-20260205-143022.json
```

### 최종 출력

```
=== Security Reports 스캔 완료 ===

📊 발견 사항 요약:
  - Critical: 2건
  - High: 5건  
  - Medium: 6건
  - Low: 2건

📁 레포트 파일: ./scanreport-20260205-143022.json

🗑️ 임시 파일 정리 완료

� 토큰 사용량:
```

**⚠️ 필수: 스캔 완료 후 반드시 토큰 사용량을 출력하세요.**

토큰 사용량을 확인하려면 `/cost` 명령어를 실행하고 그 결과를 위 출력에 포함하세요.

예시:
```
💰 토큰 사용량:
  - 입력 토큰: 45,230
  - 출력 토큰: 12,450
  - 총 비용: $0.42
```

만약 `/cost` 명령어를 직접 실행할 수 없다면:
```
💡 토큰 사용량 확인: /cost 명령어를 입력하세요
```

```
주요 이슈:
1. [STATIC-001] SQL Injection in src/db/query.py:45
2. [SENS-001] AWS Access Key exposed in config/aws.js:12
```

## 출력 형식

⚠️ **필수: JSON Schema V1.2 엄격 준수** - [SCHEMA_V1.2_ENFORCEMENT.md](../../docs/SCHEMA_V1.2_ENFORCEMENT.md) 참조

**임의로 필드를 추가/변경/제거하지 마십시오.**

아래 구조를 **정확하게** 따라야 합니다.

```json
{
  "output_filename": "scanreport-YYYYMMDDhhmmss.json",
  "scan_metadata": {
    "scan_date": "2026-02-05T14:30:22Z",
    "scanner_version": "Claude Threat Scan V2.0",
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
      "description": "...",
      "file_statistics": {
        "total_files": 156,
        "python_files": 12,
        "javascript_files": 8,
        "typescript_tsx": 25,
        "markdown_files": 10,
        "json_files": 5,
        "pem_files": 0,
        "yaml": 3,
        "css": 2,
        "svg": 1,
        "html": 2,
        "other": 88
      },
      "key_components": [],
      "sensitive_files_detected": []
    },
    "static_code_findings": [],
    "binary_analysis_findings": [],
    "skill_risk_findings": [],
    "agent_policy_findings": [],
    "sensitive_patterns": [],
    "prompt_optimization": [],
    "sbom_analysis": {
      "manifest_files_found": [
        {
          "file": "package.json",
          "ecosystem": "npm",
          "direct_dependencies": 25,
          "dev_dependencies": 15
        }
      ],
      "dependency_statistics": {
        "total_direct": 40,
        "total_dev": 15,
        "total_transitive": 450,
        "by_ecosystem": { "npm": 40 }
      },
      "license_summary": { "MIT": 35, "Apache-2.0": 8, "ISC": 5 },
      "vulnerability_findings": [],
      "license_findings": [],
      "version_risk_findings": [],
      "supply_chain_findings": [],
      "sbom_documentation_status": {
        "sbom_file_exists": false,
        "sbom_format": null,
        "ci_sbom_generation": false,
        "completeness": "Missing",
        "recommendation": "Generate SBOM using CycloneDX or SPDX"
      },
      "risk_matrix": {
        "vulnerabilities": { "critical": 0, "high": 0, "medium": 0, "low": 0 },
        "license_issues": { "critical": 0, "high": 0, "medium": 0, "low": 0 },
        "version_risks": { "critical": 0, "high": 0, "medium": 0, "low": 0 },
        "supply_chain": { "critical": 0, "high": 0, "medium": 0, "low": 0 }
      },
      "priority_actions": [
        {
          "rank": 1,
          "category": "Vulnerability",
          "package": "example-pkg",
          "current_version": "1.0.0",
          "action": "Upgrade to 1.0.1",
          "severity": "High",
          "rationale": "Known CVE affecting this version"
        }
      ]
    },
    "recommendations": []
  },
  "korean_report": {
    "repository_summary": {},
    "static_code_findings": [],
    "binary_analysis_findings": [],
    "skill_risk_findings": [],
    "agent_policy_findings": [],
    "sensitive_patterns": [],
    "prompt_optimization": [],
    "sbom_analysis": {
      "manifest_files_found": [],
      "dependency_statistics": {
        "total_direct": 0,
        "total_dev": 0,
        "by_ecosystem": {}
      },
      "license_summary": {},
      "vulnerability_findings": [],
      "license_findings": [],
      "version_risk_findings": [],
      "supply_chain_findings": [],
      "sbom_documentation_status": {},
      "risk_matrix": {},
      "priority_actions": []
    },
    "recommendations": []
  }
}
```

### ❌ 금지 사항 (스키마 위반)

| 하지 마세요 | 올바른 방식 |
|-------------|-------------|
| `findings_summary` 루트에 추가 | 제거 (스키마에 없음) |
| `executive_summary` 추가 | 제거 (스키마에 없음) |
| `findings: []` 단일 배열 | 카테고리별 배열 사용 |
| `positive_findings` 추가 | 제거 (스키마에 없음) |
| `recommendations` 루트 객체 | `english_report.recommendations[]` 배열 |
| `scan_id`, `scan_type`, `target` | `scan_date`, `repository`, `target_repository` 사용 |
| `timestamp` | `scan_date` 사용 |
| `target_info` 중첩 객체 | 플랫 구조 사용 |
| severity 소문자 `"critical"` | 대문자 시작 `"Critical"` |
| `title`, `category`, `cwe`, `owasp` | `issue` 필드 사용 |
| `remediation` | `recommendation` 사용 |
| `code_snippet` | 불필요 (스키마에 없음) |
| `dangerous_files_found` | `sensitive_files_detected` 사용 |
| `sensitive_patterns: {summary, findings}` | `sensitive_patterns: []` 직접 배열 사용 |

### ❌ SBOM 금지 필드 (뷰어 렌더링 실패 원인)

**다음 필드를 사용하면 SBOM 섹션이 뷰어에 표시되지 않습니다:**

| 사용 금지 ❌ | 올바른 필드 ✓ | 적용 섹션 |
|-------------|--------------|-----------|
| `format` | 제거 (스키마에 없음) | root |
| `package_manager` | 제거 (스키마에 없음) | root |
| `total_dependencies` | `dependency_statistics.total_direct` | root |
| `direct_dependencies` (루트 배열) | `manifest_files_found` 배열 사용 | root |
| `version_analysis` | `version_risk_findings` 배열 사용 | root |
| `known_vulnerabilities` | `vulnerability_findings` 배열 사용 | root |
| `vulnerabilities: {count}` | `vulnerability_findings: []` 배열 | root |
| `license_analysis` | `license_summary: {"MIT": 35}` | root |
| `notable_packages` | 제거 | root |
| `version_pinning` | `version_risk_findings` 배열로 | root |
| `priority_actions: ["문자열"]` | `priority_actions: [{rank, category, package, ...}]` 객체 배열 | sbom |
| `current_version` | `version` 사용 | **VULN만** |
| `version` | `current_version` 사용 | **VER만** |
| `description` | `issue` 사용 (Unpinned/Wildcard/Outdated/Deprecated) | **VER만** |
| `cve_id` (단일 문자열) | `cve_ids` 배열 사용 | VULN |
| `deep_dive_result: {객체}` | `deep_dive_result: "문자열"` | 공통 |
| VULN에 `file` 누락 | `file: "package.json"` 필수 | VULN |
| SUPPLY에 `issue` 사용 | `risk_type` 사용 | SUPPLY |
| SUPPLY에 `description` 사용 | `detail` 사용 | SUPPLY |
| SUPPLY에 `package` 누락 | `package` 필수 | SUPPLY |

## Finding ID 규칙

| 접두사 | 스캔 영역 |
|--------|-----------|
| STATIC-NNN | 정적 코드 분석 |
| SENS-NNN | 민감 정보 탐지 |
| VULN-NNN | 의존성 취약점 |
| LIC-NNN | 라이선스 이슈 |
| VER-NNN | 버전 이슈 |
| SKILL-NNN | AI 스킬 보안 |
| AGENT-NNN | 에이전트 정책 |

## 참조 스킬

스캔 시 다음 스킬들의 지침을 참조합니다:
- [repo-indexer](../repo-indexer/SKILL.md)
- [static-code-analyzer](../static-code-analyzer/SKILL.md)
- [sensitive-pattern-matcher](../sensitive-pattern-matcher/SKILL.md)
- [securityreports-sbom](../securityreports-sbom/SKILL.md)
- [bilingual-translator](../bilingual-translator/SKILL.md)
- [report-merger](../report-merger/SKILL.md)
- [securityreports-deepdive](../securityreports-deepdive/SKILL.md) ⭐ Deep Dive 분석

## 번역 용어집

한글 번역 시 [security-terms-en-ko.json](../../dictionary/security-terms-en-ko.json) 참조

## 카테고리별 필수 필드 요약

### static_code_findings
| 필드 | 필수 | 설명 |
|------|------|------|
| `id` | ✓ | STATIC-NNN |
| `file` | ✓ | 파일 경로 (NOT location) |
| `line` | ○ | 라인 번호 (숫자) |
| `issue` | ✓ | 이슈 제목 (NOT title) |
| `description` | ✓ | 상세 설명 |
| `severity` | ✓ | 대문자 시작 |
| `status` | ○ | Confirmed/Mitigated/False Positive |
| `deep_dive_result` | ○ | **문자열** (NOT 객체) |
| `recommendation` | ✓ | 권장 조치 (NOT remediation) |

### vulnerability_findings (SBOM)
| 필드 | 필수 | 설명 |
|------|------|------|
| `id` | ✓ | VULN-NNN |
| `file` | ✓ | 매니페스트 파일 경로 (예: package.json) |
| `package` | ✓ | 패키지명 |
| `version` | ✓ | 현재 버전 (NOT current_version) |
| `cve_ids` | ○ | CVE ID 배열 (NOT cve_id 단일 문자열) |
| `severity` | ✓ | 대문자 시작 |
| `description` | ✓ | 취약점 설명 |
| `fixed_version` | ○ | 패치된 버전 |
| `recommendation` | ✓ | 권장 조치 |

### version_risk_findings (SBOM)
| 필드 | 필수 | 설명 |
|------|------|------|
| `id` | ✓ | VER-NNN |
| `file` | ✓ | 매니페스트 파일 경로 |
| `package` | ✓ | 패키지명 |
| `current_version` | ✓ | 현재 버전 (NOT version) ⚠️ VULN과 반대! |
| `issue` | ✓ | Unpinned/Wildcard/Outdated/Deprecated (NOT description) |
| `severity` | ✓ | 대문자 시작 |
| `recommendation` | ✓ | 권장 조치 |

### sensitive_patterns
| 필드 | 필수 | 설명 |
|------|------|------|
| `id` | ✓ | SENS-NNN |
| `file` | ✓ | 파일 경로 (NOT location) |
| `pattern` | ✓ | 패턴 이름 (NOT issue, NOT type) |
| `detail` | ✓ | 상세 내용 (NOT description) |
| `severity` | ✓ | 대문자 시작 |
| `status` | ○ | 상태 |
| `gitignore_status` | ○ | gitignore 포함 여부 |

### agent_policy_findings
| 필드 | 필수 | 설명 |
|------|------|------|
| `id` | ✓ | AGENT-NNN |
| `file` | ✓ | 파일 경로 (NOT location) |
| `agent` | ✓ | 에이전트 이름 |
| `issue` | ✓ | 이슈 설명 |
| `disallowed_tools` | ○ | 비허용 도구 목록 |
| `severity` | ✓ | 대문자 시작 |
| `recommendation` | ✓ | 권장 조치 |

### supply_chain_findings (SBOM)
| 필드 | 필수 | 설명 |
|------|------|------|
| `id` | ✓ | SUPPLY-NNN |
| `file` | ✓ | 매니페스트 파일 경로 |
| `package` | ✓ | 패키지명 (NOT issue) |
| `risk_type` | ✓ | Typosquatting/UnmaintainedPackage/NonStandardRegistry/GitDependency/LocalPath |
| `severity` | ✓ | 대문자 시작 |
| `detail` | ✓ | 상세 설명 (NOT description) |
| `recommendation` | ✓ | 권장 조치 |

### recommendations
| 필드 | 필수 | 설명 |
|------|------|------|
| `priority` | ✓ | Critical/High/Medium/Low |
| `action` | ✓ | 조치 내용 (뷰어 렌더링) |
| `rationale` | ✓ | 근거 (뷰어 렌더링) |
| `category` | ○ | 카테고리 |
| `affected_files` | ○ | 영향 파일 배열 |
