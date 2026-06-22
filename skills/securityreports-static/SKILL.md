---
name: securityreports-static
description: "[DEPRECATED v2.3.0+] 정적 코드 보안 분석. /threat-scan 으로 마이그레이션하세요."
disable-model-invocation: true
argument-hint: <file-or-directory-path>
---

> ⚠️ **DEPRECATED (v2.3.0+)**: 이 명령은 구 SecurityScan 세대입니다.
> v2.1 통합 파이프라인은 `/threat-scan <target>`을 사용하세요.

# Security Reports - Static Code Analysis

**$ARGUMENTS** 에 대해 정적 코드 보안 분석을 수행합니다.

## 지원 언어

Python, JavaScript, TypeScript, Java, Go, Ruby, PHP, C#, Rust, Swift, Kotlin

## 탐지 항목

### Injection 취약점
| ID | 유형 | 심각도 |
|----|------|--------|
| STATIC-001 | SQL Injection | Critical |
| STATIC-002 | Command Injection | Critical |
| STATIC-003 | XSS (Cross-Site Scripting) | High |
| STATIC-004 | LDAP Injection | High |
| STATIC-005 | XML Injection (XXE) | High |
| STATIC-006 | NoSQL Injection | High |

### 인증/인가 취약점
| ID | 유형 | 심각도 |
|----|------|--------|
| STATIC-010 | Hardcoded Credentials | Critical |
| STATIC-011 | Weak Password Policy | Medium |
| STATIC-012 | Missing Authentication | High |
| STATIC-013 | Insecure Session Management | Medium |

### 암호화 취약점
| ID | 유형 | 심각도 |
|----|------|--------|
| STATIC-020 | Weak Cryptographic Algorithm | High |
| STATIC-021 | Hardcoded Encryption Key | Critical |
| STATIC-022 | Insufficient Key Length | Medium |
| STATIC-023 | Missing SSL/TLS Verification | High |

### 데이터 노출 취약점
| ID | 유형 | 심각도 |
|----|------|--------|
| STATIC-030 | Path Traversal | High |
| STATIC-031 | Information Disclosure | Medium |
| STATIC-032 | Sensitive Data in Logs | Medium |
| STATIC-033 | Debug Mode Enabled | Low |

### 기타 취약점
| ID | 유형 | 심각도 |
|----|------|--------|
| STATIC-040 | Insecure Deserialization | Critical |
| STATIC-041 | Race Condition | Medium |
| STATIC-042 | Resource Leak | Low |
| STATIC-043 | Unsafe Reflection | Medium |

## 출력 형식

⚠️ **필수: Schema V1.2 준수** - [SCHEMA_V1.2_ENFORCEMENT.md](../../docs/SCHEMA_V1.2_ENFORCEMENT.md) 참조

정적 코드 분석 결과는 최종 레포트의 `static_code_findings` 배열에 포함됩니다.

```json
{
  "static_code_findings": [
    {
      "id": "STATIC-001",
      "file": "src/db/query.py",
      "line": 45,
      "issue": "SQL Injection",
      "description": "User input directly interpolated into SQL query",
      "severity": "Critical",
      "status": "Confirmed",
      "deep_dive_result": "Input from HTTP request directly used in query without sanitization",
      "recommendation": "Use parameterized queries: cursor.execute(\"SELECT * FROM users WHERE id = ?\", (user_id,))"
    }
  ]
}
```

### ❌ 금지 필드
- `finding_id` → `id` 사용
- `type` → `issue` 사용
- `code_snippet` → 스키마에 없음
- `column` → 스키마에 없음
- `cwe_id`, `owasp` → 스키마에 없음
- severity 소문자 → 대문자 시작
- `findings` 배열 → `static_code_findings` 사용

## ⚠️ 필수: 레포트 파일 저장

### 단독 실행 시
파일명: `static-report-{YYYYMMDD}-{HHMMSS}.json`

### securityreports-scan에서 호출 시
SESSION_ID를 전달받아 임시 파일로 저장:
```
.tmp-static-{SESSION_ID}.json
```
예시: `.tmp-static-20260205-143022.json`

이 파일은 report-merger가 통합 후 삭제합니다.

### 단독 실행 시 출력
```
✅ 정적 분석 완료! 레포트: ./static-report-20260205-143022.json

분석: 89개 파일, 12,450 라인
발견: 5건 (Critical 1, High 2, Medium 2)
```

## 참조

- [static-code-analyzer skill](../static-code-analyzer/SKILL.md) - 상세 분석 로직
- OWASP Top 10 (2021)
- CWE/SANS Top 25
