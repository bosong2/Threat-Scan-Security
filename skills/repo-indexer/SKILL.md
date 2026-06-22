---
name: repo-indexer
description: >
  Recursively scan the full repository file structure to collect baseline asset
  information: file tree, extension stats, risky/sensitive file detection,
  dependency manifest identification.
---

# Repository Indexer Skill

## 개요

리포지토리 전체 파일 구조를 재귀적으로 스캔하여 기초 자산 정보를 수집하는 스킬.

## 역할

1. 전체 파일 트리 구조 분석
2. 확장자별 파일 통계 수집
3. 위험/민감 파일 탐지
4. 의존성 매니페스트 파일 식별

## 호출 방법

```
@repo-indexer <repository-path>
```

## 점검 항목

| 점검 항목 | 설명 |
|-----------|------|
| 파일 트리 구조 | 전체 디렉토리 및 파일 계층 분석 |
| 확장자별 파일 수 | 언어별/유형별 파일 분포 통계 |
| 위험 파일 탐지 | `.pem`, `.env`, `.pyc`, `.key`, `.bin` 등 민감 파일 식별 |
| 버전 관리 부적합 파일 | 키, 시크릿, 자격 증명 파일 탐지 |
| 의존성 매니페스트 | 매니페스트(`package.json`, `requirements.txt`, `pom.xml`, `go.mod` 등) + **lock 파일**(`package-lock.json`, `poetry.lock`, `*-lock.txt`, `Gemfile.lock`, `Cargo.lock` 등) 식별. **lock 파일 우선** — 전이 의존성이 lock에만 존재. monorepo·하위 디렉토리까지 재귀 탐색. |

## 출력 형식

```json
{
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
}
```

## 탐지 대상 위험 파일

| 패턴 | 설명 |
|------|------|
| `.env`, `.env.*` | 환경 변수 파일 |
| `.pem`, `.key`, `.p12` | 인증서/키 파일 |
| `.pyc`, `.pyo` | 컴파일된 Python 파일 |
| `.so`, `.dll`, `.bin` | 바이너리 파일 |
| `id_rsa`, `id_dsa`, `id_ecdsa` | SSH 키 파일 |
| `*.secret`, `*credentials*` | 비밀정보 파일 |

## 의존성 매니페스트 대상

| 생태계 | 대상 파일 |
|--------|-----------|
| Node.js | `package.json`, `package-lock.json`, `yarn.lock`, `pnpm-lock.yaml` |
| Python | `requirements.txt`, `Pipfile`, `Pipfile.lock`, `pyproject.toml`, `poetry.lock` |
| Java/Kotlin | `pom.xml`, `build.gradle`, `build.gradle.kts` |
| Go | `go.mod`, `go.sum` |
| Rust | `Cargo.toml`, `Cargo.lock` |
| Ruby | `Gemfile`, `Gemfile.lock` |
| PHP | `composer.json`, `composer.lock` |
| .NET | `*.csproj`, `packages.config`, `*.nuspec` |

## 제약 사항

- `node_modules`, `venv`, `.git`, `__pycache__` 등 제외
- 파일 내용 분석 없음 (구조만 파악)
- 시스템 명령 실행 금지

## 사용 예시

```
사용자: @repo-indexer /Users/user/project

응답:
[REPOSITORY_INDEX]
Total files: 156
Code files: 42
Sensitive files detected: 3
- .env.local - Environment configuration file
- config/credentials.json - May contain credentials
- certs/server.pem - Private key file

Dependency manifests found:
- package.json (npm)
- requirements.txt (pip)
```
