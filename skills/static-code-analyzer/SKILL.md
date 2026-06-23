---
name: static-code-analyzer
description: >
  Statically analyze source code for potential security risk patterns:
  injection, secrets, unsafe APIs, hardcoded credentials, insecure configurations.
---

# Static Code Analyzer Skill

## 개요

소스 코드 내 잠재적 보안 위험 패턴을 정적으로 분석하는 스킬.

## 역할

1. 위험한 함수 호출 패턴 탐지
2. 하드코딩된 자격 증명 식별
3. 네트워크 통신 패턴 분석
4. 파일 시스템 조작 감지

## 호출 방법

```
@static-code-analyzer <repository-path>
```

## 점검 항목

| 위험 유형 | 탐지 패턴 |
|-----------|-----------|
| 명령 실행 | `os.system`, `subprocess.*`, `exec`, `eval`, `shell=True` |
| 파일 시스템 변경 | 파일 쓰기/삭제 작업 |
| 원격 코드 실행 | 외부 코드 다운로드 및 실행 |
| 하드코딩 자격 증명 | 코드 내 비밀번호, 토큰, API 키 |
| 네트워크 통신 | HTTP 요청, 소켓 연결 |

## 탐지 패턴 상세

### Python
```python
# 명령 실행
os.system("...")
subprocess.call(...)
subprocess.Popen(..., shell=True)
eval("...")
exec("...")

# 위험한 import
import pickle  # 역직렬화 취약점
import marshal

# 네트워크
requests.get/post(...)
urllib.request.urlopen(...)
socket.socket(...)
```

### JavaScript/TypeScript
```javascript
// 명령 실행
child_process.exec(...)
child_process.spawn(...)
eval("...")
new Function("...")

// 동적 require
require(variable)
import(variable)

// 네트워크
fetch(...)
axios.get/post(...)
```

### Java
```java
// 명령 실행
Runtime.getRuntime().exec(...)
ProcessBuilder(...)

// 위험 패턴
Class.forName(...)  // 동적 클래스 로딩
ObjectInputStream  // 역직렬화
```

## MASKING CONTRACT — 하드코딩 자격 증명 (필수 — v2.3.3)

하드코딩 패스워드·토큰·API 키가 finding으로 탐지될 때, **raw 값을 절대 출력하지 않는다.**

- `masked_value`: 앞 4자 + 나머지 마스킹 (`AKIA****************`, `sk-l****`).
- `value` / `secret` / `raw` / `snippet` 키를 절대 사용하지 않는다.
- 자세한 마스킹 규약은 `skills/sensitive-pattern-matcher/SKILL.md` § MASKING CONTRACT.

## 출력 형식

⚠️ **필수: Schema V1.3 엄격 준수** - [SCHEMA_V1.3_ENFORCEMENT.md](../../docs/SCHEMA_V1.3_ENFORCEMENT.md) 참조

```json
{
  "static_code_findings": [
    {
      "id": "STATIC-001",
      "file": "src/utils/shell.py",
      "line": 45,
      "issue": "Command Injection Risk",
      "description": "os.system() called with user-controllable input",
      "severity": "High",
      "status": "Confirmed",
      "deep_dive_result": "Input is passed from HTTP request without sanitization",
      "recommendation": "Use subprocess with shell=False and sanitize inputs"
    },
    {
      "id": "STATIC-002",
      "file": "src/config.py",
      "line": 12,
      "issue": "Hardcoded API Key",
      "description": "OpenAI API key hardcoded in source",
      "masked_value": "sk-l****",
      "severity": "High",
      "status": "Confirmed",
      "recommendation": "Use environment variables or secrets manager"
    }
  ],
  "_meta": {
    "agent": "tss-static-analyzer",
    "files_scanned": 64,
    "findings": 2,
    "depthReached": 1,
    "notes": ""
  }
}
```

### ❌ 절대 금지 필드
| 사용 금지 | 올바른 필드 |
|-----------|-------------|
| `finding_id` | `id` |
| `location` | `file` |
| `title` | `issue` |
| `type` | `issue` |
| `remediation` | `recommendation` |
| `code_snippet` | 제거 |
| `cwe`, `owasp` | 제거 |
| `value`, `secret`, `raw`, `snippet` (자격증명 맥락) | `masked_value` |
| severity 소문자 | 대문자 시작 |

### `_meta` footer 규약

모든 반환 JSON에 `_meta` 객체를 포함한다(report-merger가 최종 리포트에서 제외):

| 필드 | 설명 |
|------|------|
| `agent` | `tss-static-analyzer` |
| `files_scanned` | 실제 점검한 파일 수 |
| `findings` | 발견된 finding 수 |
| `depthReached` | 분석 깊이 |
| `notes` | 제외 경로 등 메모 (optional) |

## Deep Dive 기준

다음 조건에서 심층 분석 수행:
- Severity가 Medium 또는 High
- 사용자 입력과 연결된 경우
- 동적으로 구성된 명령/쿼리

### Deep Dive 분석 항목
1. 입력 소스 추적 (최대 3단계)
2. 검증/새니타이징 여부
3. 실행 컨텍스트 분석
4. 공격 시나리오 평가

## Severity 기준

| Severity | 기준 |
|----------|------|
| Critical | 원격 코드 실행 가능, 인증 우회 |
| High | 명령 주입, 하드코딩 자격 증명 |
| Medium | 잠재적 파일 조작, 불안전한 역직렬화 |
| Low | 정보 노출 가능성, 로깅 이슈 |

## 제약 사항

- 코드 실행 금지 (정적 분석만)
- 외부 API 호출 금지
- 3단계 이상 참조 추적 금지

## 사용 예시

```
사용자: @static-code-analyzer /Users/user/project

응답:
[STATIC_FINDING]
file: src/api/handler.py
line: 127
issue: Command Injection
description: subprocess.call with user input, shell=True
severity: High
status: Requires Deep Dive

Deep Dive 결과:
- 입력 소스: HTTP POST body
- 검증: 없음
- 권장: subprocess.run(args, shell=False) 사용
```
