---
name: securityreports-secrets
description: "[DEPRECATED v2.3.0+] 민감 정보 패턴 탐지. /threat-scan 으로 마이그레이션하세요."
disable-model-invocation: true
argument-hint: <file-or-directory-path>
---

> ⚠️ **DEPRECATED (v2.3.0+)**: 이 명령은 구 SecurityScan 세대입니다.
> v2.1 통합 파이프라인은 `/threat-scan <target>`을 사용하세요.

# Security Reports - Sensitive Pattern Detection

**$ARGUMENTS** 에서 민감 정보 패턴을 탐지합니다.

## 탐지 대상

### API Keys & Tokens
| 패턴 | 예시 |
|------|------|
| AWS Access Key | `AKIA...` |
| AWS Secret Key | `aws_secret_access_key = ...` |
| GitHub Token | `ghp_...`, `gho_...`, `ghu_...` |
| GitLab Token | `glpat-...` |
| Slack Token | `xoxb-...`, `xoxp-...` |
| Stripe Key | `sk_live_...`, `pk_live_...` |
| Google API Key | `AIza...` |
| Firebase Key | `AAAA...` |
| SendGrid Key | `SG....` |
| Twilio Key | `SK...` |

### 자격 증명
| 패턴 | 예시 |
|------|------|
| Password in Code | `password = "..."` |
| Database URL | `postgresql://user:pass@host` |
| Connection String | `mongodb://...` |
| JWT Secret | `jwt_secret = ...` |
| Private Key | `-----BEGIN RSA PRIVATE KEY-----` |
| SSH Key | `-----BEGIN OPENSSH PRIVATE KEY-----` |

### 민감 파일
| 파일명 | 위험도 |
|--------|--------|
| `.env` | Critical |
| `.env.local` | Critical |
| `credentials.json` | Critical |
| `serviceAccountKey.json` | Critical |
| `id_rsa`, `id_ed25519` | Critical |
| `.htpasswd` | High |
| `wp-config.php` | High |
| `config.yml` (with secrets) | Medium |

### 개인정보 (PII)
| 패턴 | 예시 |
|------|------|
| 이메일 주소 | `user@example.com` |
| 전화번호 | `010-1234-5678` |
| 주민등록번호 | `123456-1234567` |
| 신용카드 번호 | `4111-1111-1111-1111` |
| IP 주소 (하드코딩) | `192.168.1.1` |

## 출력 형식

⚠️ **필수: Schema V1.2 준수** - [SCHEMA_V1.2_ENFORCEMENT.md](../../docs/SCHEMA_V1.2_ENFORCEMENT.md) 참조

민감 정보 탐지 결과는 최종 레포트의 `sensitive_patterns` 배열에 포함됩니다.

```json
{
  "sensitive_patterns": [
    {
      "id": "SENS-001",
      "file": "src/config/aws.js",
      "pattern": "AWS Access Key",
      "detail": "AKIA...[REDACTED] - AWS access key exposed in source code",
      "severity": "Critical",
      "status": "Confirmed",
      "gitignore_status": "Not in .gitignore - CRITICAL"
    },
    {
      "id": "SENS-002",
      "file": ".env",
      "pattern": "Sensitive File",
      "detail": "Environment file with secrets committed to repository",
      "severity": "Critical",
      "status": "Confirmed",
      "gitignore_status": "Add to .gitignore immediately"
    }
  ]
}
```

### ❌ 금지 필드
- `finding_id` → `id` 사용
- `type` → `pattern` 사용
- `description` → `detail` 사용
- `findings` 배열 → `sensitive_patterns` 사용
- severity 소문자 → 대문자 시작
- `sensitive_patterns: {summary, findings}` → `sensitive_patterns: []` 직접 배열
- `summary` 객체 추가 금지 → 직접 배열에 finding 객체들만 포함

## Finding ID 규칙

| 접두사 | 의미 |
|--------|------|
| SENS-NNN | 민감 정보 탐지 |

## ⚠️ 필수: 레포트 파일 저장

### 단독 실행 시
파일명: `secrets-report-{YYYYMMDD}-{HHMMSS}.json`

### securityreports-scan에서 호출 시
SESSION_ID를 전달받아 임시 파일로 저장:
```
.tmp-secrets-{SESSION_ID}.json
```
예시: `.tmp-secrets-20260205-143022.json`

이 파일은 report-merger가 통합 후 삭제합니다.

### 단독 실행 시 출력
```
✅ 민감 정보 탐지 완료! 레포트: ./secrets-report-20260205-143022.json

검사: 156개 파일
발견: 3건 (Critical 2, High 1)
```

## 참조

- [sensitive-pattern-matcher skill](../sensitive-pattern-matcher/SKILL.md) - 상세 패턴 로직
