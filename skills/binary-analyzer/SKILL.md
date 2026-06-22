---
name: binary-analyzer
description: >
  Analyze compiled artifacts and binary files for surface-level security risks:
  suspicious signatures, embedded strings, and obfuscation indicators.
---

# Binary Analyzer Skill

## 개요

컴파일된 아티팩트 및 바이너리 파일 내 잠재적 위험 요소를 분석하는 스킬.

## 역할

1. 바이너리 내 문자열 패턴 탐지
2. 내장 URL, 토큰, 명령 문자열 식별
3. 의심스러운 동작 패턴 분석
4. 숨겨진 파괴적 로직 탐지

## 호출 방법

```
@binary-analyzer <repository-path>
```

## 분석 대상 파일

| 확장자 | 설명 |
|--------|------|
| `.pyc`, `.pyo` | 컴파일된 Python 파일 |
| `.so` | Linux 공유 라이브러리 |
| `.dll` | Windows 동적 라이브러리 |
| `.bin` | 일반 바이너리 파일 |
| `.exe` | Windows 실행 파일 |
| `.class`, `.jar` | 컴파일된 Java 파일 |
| `.wasm` | WebAssembly 모듈 |

## 탐지 패턴

### 의심 문자열 패턴
```
# URL 패턴
http://, https://
ftp://, ssh://
ws://, wss://

# 자격 증명 패턴
password=, passwd=
secret=, token=
api_key=, apikey=
auth=, authorization=

# 명령 패턴
/bin/sh, /bin/bash
cmd.exe, powershell
wget, curl, nc
chmod, chown

# C2 패턴
callback, beacon
reverse_shell, bind_shell
```

### 행위 지표
| 행위 | 설명 |
|------|------|
| Network communication | 외부 통신 기능 |
| File system access | 파일 읽기/쓰기 |
| Process execution | 프로세스 생성/실행 |
| Registry access | 레지스트리 조작 (Windows) |
| Encryption routines | 암호화/복호화 기능 |
| Anti-debugging | 디버깅 방지 기법 |

## 출력 형식

```json
{
  "binary_analysis_findings": [
    {
      "id": "BIN-001",
      "file": "dist/app.pyc",
      "behaviors": ["Network communication", "File system access"],
      "risk_summary": "Compiled Python file with network capabilities detected.",
      "severity": "Medium"
    }
  ]
}
```

## Deep Dive 기준

다음 조건에서 심층 분석 수행:
- 네트워크 통신 패턴 발견
- 명령 실행 문자열 발견
- 하드코딩된 자격 증명 의심
- 난독화된 코드 패턴

### Deep Dive 분석 항목
1. 문자열 테이블 전체 분석
2. Import/Export 테이블 분석
3. 의심 패턴 컨텍스트 분석
4. 연관 파일 추적

## Severity 기준

| Severity | 기준 |
|----------|------|
| Critical | C2 패턴, 백도어 의심 |
| High | 하드코딩 자격 증명, 의심 네트워크 패턴 |
| Medium | 네트워크 기능, 프로세스 실행 |
| Low | 일반 바이너리, 명확한 목적 |

## 제약 사항

- 바이너리 실행 금지
- 디컴파일러 실행 금지 (문자열 분석만)
- 대용량 파일 (>10MB) 제한적 분석

## 분석 방법

바이너리 분석은 다음 방법으로 수행:
1. **문자열 추출**: 가독 문자열 패턴 식별
2. **패턴 매칭**: 알려진 악성 패턴과 비교
3. **엔트로피 분석**: 암호화/패킹 여부 추정
4. **구조 분석**: 파일 헤더 및 섹션 분석

## 사용 예시

```
사용자: @binary-analyzer /Users/user/project

응답:
[BINARY_FINDING]
file: lib/native.so
behaviors: 
  - Network communication (socket, connect)
  - Process execution (execve)
  - File system access (open, write)
risk_summary: Native library with system-level capabilities. Contains embedded URL pattern.
severity: High

Embedded strings found:
- "http://api.internal.corp/callback"
- "/bin/sh -c"
```
