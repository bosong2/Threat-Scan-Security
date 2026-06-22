---
name: sensitive-pattern-matcher
description: >
  Detect sensitive information patterns across the codebase: API keys, tokens,
  PII, internal endpoints, and hardcoded credentials.
---

# Sensitive Pattern Matcher Skill

## 개요

코드베이스 전반에서 민감 정보 패턴을 탐지하는 스킬.

## 역할

1. 개인키 및 인증서 탐지
2. API 키/토큰 식별
3. 클라우드 자격 증명 탐지
4. 개인 데이터(PII) 패턴 매칭
5. .gitignore 상태 검증

## 호출 방법

```
@sensitive-pattern-matcher <repository-path>
```

## 탐지 패턴

### 1. 개인키 및 인증서
```regex
-----BEGIN (RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----
-----BEGIN CERTIFICATE-----
-----BEGIN PGP PRIVATE KEY BLOCK-----
```

### 2. API 키 및 토큰
| 서비스 | 패턴 |
|--------|------|
| AWS Access Key | `AKIA[0-9A-Z]{16}` |
| AWS Secret Key | `[0-9a-zA-Z/+]{40}` |
| GitHub Token | `ghp_[0-9a-zA-Z]{36}` |
| GitLab Token | `glpat-[0-9a-zA-Z\-]{20}` |
| Slack Token | `xox[baprs]-[0-9a-zA-Z-]+` |
| Stripe Key | `sk_live_[0-9a-zA-Z]{24}` |
| Google API | `AIza[0-9A-Za-z\-_]{35}` |
| OpenAI API | `sk-[0-9a-zA-Z]{48}` |

### 3. 클라우드 자격 증명
```
# AWS
aws_access_key_id
aws_secret_access_key

# Azure
azure_client_id
azure_client_secret
azure_tenant_id

# GCP
type: service_account
private_key_id
private_key
```

### 4. 일반 비밀 패턴
```regex
password\s*[=:]\s*["'][^"']+["']
secret\s*[=:]\s*["'][^"']+["']
api[_-]?key\s*[=:]\s*["'][^"']+["']
token\s*[=:]\s*["'][^"']+["']
bearer\s+[a-zA-Z0-9\-._~+/]+=*
```

### 5. 개인 데이터 (PII)
| 유형 | 패턴 설명 |
|------|-----------|
| 이메일 | 표준 이메일 형식 |
| 전화번호 | 국제/국내 전화번호 |
| 주민번호 | 한국 주민등록번호 패턴 |
| 신용카드 | 주요 카드사 번호 패턴 |
| IP 주소 | 내부 IP 주소 (10.x, 192.168.x) |

## 출력 형식

⚠️ **필수: Schema V1.2 엄격 준수** - [SCHEMA_V1.2_ENFORCEMENT.md](../../docs/SCHEMA_V1.2_ENFORCEMENT.md) 참조

```json
{
  "sensitive_patterns": [
    {
      "id": "SENS-001",
      "file": ".env.production",
      "pattern": "AWS Secret Key",
      "detail": "AWS_SECRET_ACCESS_KEY=***masked***",
      "severity": "Critical",
      "status": "Confirmed",
      "gitignore_status": "Not in .gitignore - RISK"
    }
  ]
}
```

### ❌ 절대 금지 필드
| 사용 금지 | 올바른 필드 |
|-----------|-------------|
| `finding_id` | `id` |
| `location` | `file` |
| `issue` | `pattern` |
| `type` | `pattern` |
| `description` | `detail` |
| severity 소문자 | 대문자 시작 |
```

## Deep Dive 기준

Medium/High severity 항목에 대해 심층 분석 수행:

### 분석 항목
1. **사용처 추적**: 해당 값이 어디서 사용되는지
2. **Git 히스토리 검토**: 커밋 이력에 노출 여부
3. **.gitignore 상태**: 버전 관리 제외 여부
4. **로그/테스트 내 유출**: 로그, 테스트 데이터에 노출 여부

### 분석 경로 (최대 3단계)
```
민감 파일 → 사용처 → .gitignore → 히스토리 → 로그/테스트
```

## gitignore 상태 분류

| 상태 | 설명 |
|------|------|
| `Protected` | .gitignore에 포함됨 |
| `Not in .gitignore - RISK` | .gitignore에 미포함, 위험 |
| `Already Committed - CRITICAL` | 이미 커밋된 상태 |
| `Pattern Mismatch` | 불완전한 gitignore 패턴 |

## Severity 기준

| Severity | 기준 |
|----------|------|
| Critical | 클라우드 자격 증명, 프로덕션 시크릿 |
| High | API 키, 인증 토큰 |
| Medium | 개발 환경 시크릿, 내부 엔드포인트 |
| Low | 플레이스홀더, 테스트 데이터 |
| Info | 형식만 매칭, 실제 값 아님 |

## 마스킹 규칙

출력 시 민감 값은 마스킹 처리:
```
실제 값: AKIAIOSFODNN7EXAMPLE
마스킹: AKIA***************LE

실제 값: ghp_1234567890abcdefghijklmnopqrstuvwxyz
마스킹: ghp_************************************
```

## 제외 패턴

다음은 분석에서 제외:
- `node_modules/`, `vendor/`, `venv/`
- `.git/` 디렉토리 내용
- 테스트 fixtures 내 명시적 더미 데이터
- 문서 내 예시 코드

## 제약 사항

- Git 히스토리 직접 접근 불가 (구조 분석만)
- 암호화된 파일 분석 불가
- 대용량 바이너리 파일 제외

## 사용 예시

```
사용자: @sensitive-pattern-matcher /Users/user/project

응답:
[SENSITIVE_PATTERN]
file: config/secrets.yaml
pattern: AWS Credentials
detail: 
  - aws_access_key_id: AKIA***LE
  - aws_secret_access_key: ***masked***
severity: Critical
status: Confirmed
gitignore_status: Not in .gitignore - RISK

Deep Dive 결과:
- 사용처: src/aws/client.py (line 23)
- Git 상태: 파일이 커밋됨 - 키 로테이션 필요
- 권장: 
  1. 즉시 AWS 키 로테이션
  2. config/secrets.yaml을 .gitignore에 추가
  3. git filter-branch로 히스토리 정리
```
