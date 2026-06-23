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

---

## MASKING CONTRACT (필수 — v2.3.3)

탐지된 secret/PII의 **raw 값을 절대 산출하지 않는다.** 다음 규칙을 강제한다:

- `masked_value`: 앞 4자 + 나머지 전체 마스킹. 예: `AKIA****************`, `ghp_****`, 이메일 `j***@***.com`. 원본 길이를 유지하지 말 것(길이도 정보 누출).
- `value` / `secret` / `raw` / `snippet` 등 **원문 필드 금지**. 이 필드들을 출력에 포함하는 것은 스키마 위반이다.
- 위치는 `file` + `line` + `rule`(예: `aws-access-key`)로만 식별한다.
- 컨텍스트가 꼭 필요하면 raw 줄 대신 `±0 라인의 마스킹된 발췌`만 허용 — `detail` 필드에 마스킹 형태로 기재.

### 산출 객체 필드 (각 sensitive_patterns[] 항목)

| 필드 | 예시 | 필수 |
|------|------|------|
| `id` | `"SENS-001"` | ✅ |
| `file` | `"src/config.py"` | ✅ |
| `line` | `42` | ✅ |
| `rule` | `"aws-access-key"` | ✅ |
| `pattern` | `"AWS Access Key"` | ✅ |
| `masked_value` | `"AKIA****************"` | ✅ (**raw 금지**) |
| `severity` | `"Critical"` | ✅ (대문자 시작) |
| `status` | `"Confirmed"` | ✅ |
| `gitignore_status` | `"Not in .gitignore - RISK"` | optional |
| `detail` | `"aws_access_key_id=AKIA****"` | optional (마스킹만 허용) |
| `recommendation` | `"Rotate key immediately"` | optional |
| `verdict` | `"REMOVE"` | optional |

---

## 출력 형식

⚠️ **필수: Schema V1.3 엄격 준수** - [SCHEMA_V1.3_ENFORCEMENT.md](../../docs/SCHEMA_V1.3_ENFORCEMENT.md) 참조

```json
{
  "sensitive_patterns": [
    {
      "id": "SENS-001",
      "file": "config/secrets.yaml",
      "line": 12,
      "rule": "aws-access-key",
      "pattern": "AWS Access Key",
      "masked_value": "AKIA****************",
      "severity": "Critical",
      "status": "Confirmed",
      "gitignore_status": "Not in .gitignore - RISK",
      "recommendation": "Rotate key immediately and add file to .gitignore",
      "verdict": "REMOVE"
    }
  ],
  "_meta": {
    "agent": "tss-sensitive-patterns",
    "files_scanned": 128,
    "findings": 1,
    "depthReached": 1,
    "notes": "skipped node_modules, .git"
  }
}
```

### ❌ 절대 금지 필드
| 사용 금지 | 이유 |
|-----------|------|
| `value` | raw secret 노출 |
| `secret` | raw secret 노출 |
| `raw` | raw secret 노출 |
| `snippet` (secret 맥락) | raw secret 노출 |
| `finding_id` | `id` 사용 |
| `location` | `file` 사용 |
| `issue` | `pattern` 사용 |
| `type` | `pattern` 사용 |
| `description` | `detail` 사용 |
| severity 소문자 | 대문자 시작 필수 |

### `_meta` footer 규약

모든 반환 JSON에 `_meta` 객체를 포함한다(internal metric — report-merger가 최종 리포트에서 제외):

| 필드 | 설명 |
|------|------|
| `agent` | 에이전트 이름 (`tss-sensitive-patterns`) |
| `files_scanned` | 실제 점검한 파일 수 |
| `findings` | 발견된 finding 수 |
| `depthReached` | 분석 깊이 (1=Level 1만) |
| `notes` | 제외 경로 등 메모 (optional) |

---

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
