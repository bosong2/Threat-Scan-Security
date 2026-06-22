# Claude Threat Scan V2.0

## 개요

AI 기반 리포지토리 보안 진단 도구. 최대 3단계 재귀 분석 수행, 영문/한글 병렬 JSON 보고서 생성.

---

## 점검 기능 (9개 영역)

| 구분    | 기능명                | 주요 점검 내용                                         |
| ----- | ------------------ | ------------------------------------------------ |
| 1     | 리포지토리 인덱싱          | 파일 구조, 확장자별 통계, 민감 파일(`.env`, `.pem`, `.key`) 탐지 |
| 2     | 정적 코드 분석           | `os.system`, `exec`, `eval`, 하드코딩 자격증명, 네트워크 통신  |
| 3     | 바이너리 분석            | `.pyc`, `.so`, `.dll` 내 내장 URL, 토큰, 의심 패턴        |
| 4     | Skill/도구 분석        | 민감정보 노출, 권한 상승, 프롬프트 인젝션 취약점                     |
| 5     | 민감 패턴 매칭           | 개인키, API 키, 클라우드 자격증명, `.gitignore` 상태           |
| 6     | 에이전트 정책 검증         | `disallowed_tools` 정책 정의 여부, 정책 일관성              |
| 7     | 포맷 최적화             | 과도한 공백, 중복 프롬프트, 토큰 낭비                           |
| **8** | **SBOM 분석 (V2.0)** | 의존성 취약점, 라이선스 충돌, 공급망 위험, 버전 위험                  |
| **9** | **SBOM 요약 (V2.0)** | 위험 매트릭스, 우선 조치 항목 도출                             |

---

## V2.0 신규: SBOM 분석 상세

| 분석 항목       | 설명                                 |
| ----------- | ---------------------------------- |
| 취약점 평가      | CVE 기반 알려진 취약점 식별                  |
| 라이선스 컴플라이언스 | GPL/MIT 충돌 등 호환성 검증                |
| 버전 위험       | Unpinned, Wildcard, Deprecated 패키지 |
| 공급망 위험      | Typosquatting, 비표준 레지스트리, Git 의존성  |
| SBOM 문서화    | SPDX/CycloneDX 파일 존재 여부            |

**대상 파일**: `package.json`, `requirements.txt`, `pom.xml`, `go.mod`, `Cargo.toml` 등

---

## 출력 형식

- **파일명**: `scanreport-YYYYMMDDhhmmss.json`
- **구조**: 영문/한글 병렬 보고서
- **심각도**: Critical / High / Medium / Low

# Claude Threat Scan V2.0 기능 상세

## 1. 개요

Claude Threat Scan V2.0은 전체 리포지토리에 대해 **다단계 재귀 분석(최대 3단계)**을 수행하여 종합적인 보안 보고서를 생성하는 AI 기반 보안 진단 도구이다. V2.0에서는 **SBOM(Software Bill of Materials) 및 의존성 보안 분석** 기능이 추가되었다.

---

## 2. 분석 전략

|단계|명칭|설명|
|---|---|---|
|Phase 1|Broad Scan (Level 1)|전체 리포지토리 스캔 및 후보 위험 식별|
|Phase 2|Deep Dive (Level 2-3)|중/고위험 항목에 대한 재귀적 심층 분석|

**Deep Dive 수행 기준**

- Severity가 Medium 또는 High인 경우
- 동작이 불명확한 경우
- 민감 정보가 관련된 경우

**최종 판정 분류**: `Confirmed` | `Mitigated` | `False Positive`

---

## 3. 점검 기능 상세

### 3.1 리포지토리 인덱싱 (Section 1)

전체 파일 구조를 재귀적으로 스캔하여 기초 자산 정보를 수집한다.

|점검 항목|설명|
|---|---|
|파일 트리 구조|전체 디렉토리 및 파일 계층 분석|
|확장자별 파일 수|언어별/유형별 파일 분포 통계|
|위험 파일 탐지|`.pem`, `.env`, `.pyc`, `.key`, `.bin` 등 민감 파일 식별|
|버전 관리 부적합 파일|키, 시크릿, 자격 증명 파일 탐지|
|의존성 매니페스트|`package.json`, `requirements.txt` 등 식별|

---

### 3.2 정적 코드 분석 (Section 2)

소스 코드 내 잠재적 보안 위험 패턴을 식별한다.

|위험 유형|탐지 패턴|
|---|---|
|명령 실행|`os.system`, `subprocess.*`, `exec`, `eval`, `shell=True`|
|파일 시스템 변경|파일 쓰기/삭제 작업|
|원격 코드 실행|외부 코드 다운로드 및 실행|
|하드코딩 자격 증명|코드 내 비밀번호, 토큰, API 키|
|네트워크 통신|HTTP 요청, 소켓 연결|

---

### 3.3 컴파일/바이너리 분석 (Section 3)

컴파일된 아티팩트 내 잠재적 위험 요소를 분석한다.

|대상 파일|분석 내용|
|---|---|
|`.pyc`, `.so`, `.dll`, `.bin`|내장 URL, 토큰, 명령 문자열 탐지|
|바이너리 전반|의심스러운 동작 패턴, 숨겨진 파괴적 로직|

---

### 3.4 SKILL.md / 도구 보안 분석 (Section 4)

AI 도구 정의 및 프롬프트 템플릿의 보안 위험을 평가한다.

|평가 범주|설명|
|---|---|
|민감 정보 노출|도구 정의 내 민감 데이터 노출 위험|
|권한 상승|불필요한 접근 권한 확대|
|명령 실행|시스템 명령 실행 가능 여부|
|외부 데이터 전송|데이터 유출 경로 분석|
|프롬프트 인젝션|규칙 우회, 명령 무시 취약점|

---

### 3.5 민감 패턴 매칭 (Section 5)

코드베이스 전반에서 민감 정보 패턴을 탐지한다.

|탐지 패턴|예시|
|---|---|
|개인키|RSA/EC 개인키, PEM 파일|
|인증 정보|비밀번호, 토큰, API 키|
|환경 파일|`.env` 파일, 내장 시크릿|
|클라우드 자격 증명|AWS, Azure, GCP 키|
|내부 엔드포인트|내부 API URL, 서버 주소|
|개인 데이터|PII 패턴|

**심층 분석 항목**: 사용처 추적, Git 히스토리 검토, `.gitignore` 상태, 로그/테스트 내 유출 여부

---

### 3.6 에이전트 보안 정책 검증 (Section 6)

AI 에이전트의 보안 정책 적용 상태를 검증한다.

|점검 항목|설명|
|---|---|
|`disallowed_tools` 정책|위험 도구 사용 제한 정책 정의 여부|
|암묵적 허용|위험 도구의 암묵적 허용 여부|
|정책 일관성|에이전트 간 정책 불일치|
|중앙 정책 재사용|정책 표준화 권고|

---

### 3.7 프롬프트 및 포맷 최적화 점검 (Section 7)

토큰 낭비 및 비효율적 포맷팅을 식별한다.

|점검 항목|설명|
|---|---|
|과도한 공백|불필요한 공백 및 후행 공백|
|반복 빈 줄|연속된 빈 줄|
|중복 프롬프트 블록|반복되는 프롬프트 내용|
|비효율적 포맷팅|토큰 사용량 증가 요인|

---

### 3.8 SBOM 및 의존성 보안 분석 (Section 8) — V2.0 신규

#### 3.8.1 대상 매니페스트 파일

|생태계|대상 파일|
|---|---|
|Node.js|`package.json`, `package-lock.json`, `yarn.lock`, `pnpm-lock.yaml`|
|Python|`requirements.txt`, `Pipfile`, `Pipfile.lock`, `pyproject.toml`, `poetry.lock`|
|Java/Kotlin|`pom.xml`, `build.gradle`, `build.gradle.kts`|
|Go|`go.mod`, `go.sum`|
|Rust|`Cargo.toml`, `Cargo.lock`|
|Ruby|`Gemfile`, `Gemfile.lock`|
|PHP|`composer.json`, `composer.lock`|
|.NET|`*.csproj`, `packages.config`, `*.nuspec`|

#### 3.8.2 OSS 라이선스 컴플라이언스

|점검 항목|설명|
|---|---|
|라이선스 유형 식별|MIT, Apache-2.0, GPL, LGPL, BSD 등|
|호환성 검증|프로젝트 라이선스와의 충돌 여부|
|미선언 라이선스|라이선스 정보 누락|
|Copyleft 오염|GPL 등 전염성 라이선스 위험|

#### 3.8.3 취약점 평가 (CVE/CWE)

|분석 항목|설명|
|---|---|
|알려진 CVE|특정 버전에 연관된 CVE 식별|
|심각도 등급|Critical, High, Medium, Low|
|취약 버전 범위|영향받는 버전 범위 확인|
|패치 버전|수정된 버전 가용성|

**참고**: 실시간 CVE 데이터베이스 접근 불가. `npm audit`, `pip-audit`, `OWASP Dependency-Check`, `Snyk` 등 외부 도구 연계 권고

#### 3.8.4 의존성 버전 분석

|위험 유형|설명|
|---|---|
|Unpinned|`^1.0.0` 등 범위 지정 버전|
|Wildcard|`*`, `latest` 사용|
|Outdated|최신 안정 버전과의 격차|
|Deprecated|지원 중단 패키지|

#### 3.8.5 공급망 위험 지표

|위험 유형|설명|
|---|---|
|Typosquatting|유명 패키지와 유사한 이름|
|UnmaintainedPackage|관리자 부재, 낮은 다운로드 수|
|NonStandardRegistry|비표준 레지스트리 소스|
|GitDependency|GitHub/GitLab URL 직접 참조|
|LocalPath|로컬 파일 경로 의존성|

#### 3.8.6 SBOM 문서화 상태

|점검 항목|설명|
|---|---|
|SBOM 파일 존재|SPDX, CycloneDX 형식 파일|
|CI/CD 생성 설정|자동 SBOM 생성 파이프라인|
|완전성|Complete, Partial, Missing|

---

### 3.9 SBOM 요약 생성 (Section 9) — V2.0 신규

#### 의존성 통계

|항목|설명|
|---|---|
|직접 의존성 수|Direct dependencies count|
|개발 의존성 수|Dev dependencies count|
|전이 의존성 수|Transitive dependencies count|
|생태계별 분포|npm, pip, maven 등|
|라이선스별 분포|MIT, Apache-2.0 등|

#### 위험 요약 매트릭스

|위험 범주|Critical|High|Medium|Low|
|---|---|---|---|---|
|Vulnerabilities|-|-|-|-|
|License Issues|-|-|-|-|
|Version Risks|-|-|-|-|
|Supply Chain|-|-|-|-|

#### 우선 조치 항목

1. 패치 가능한 Critical CVE
2. 라이선스 비호환성
3. 심각하게 오래된 버전
4. 공급망 우려 사항

---

## 4. 출력 형식

### 파일명 규칙

```
scanreport-YYYYMMDDhhmmss.json
```

### JSON 구조

```
├── output_filename
├── scan_metadata
├── english_report
│   ├── repository_summary
│   ├── static_code_findings
│   ├── binary_analysis_findings
│   ├── skill_risk_findings
│   ├── agent_policy_findings
│   ├── sensitive_patterns
│   ├── prompt_optimization
│   ├── sbom_analysis (V2.0)
│   └── recommendations
└── korean_report (동일 구조)
```

---

## 5. V2.0 주요 변경사항 요약

|항목|V1.x|V2.0|
|---|---|---|
|SBOM 분석|미지원|지원|
|의존성 취약점 분석|미지원|지원|
|라이선스 컴플라이언스|미지원|지원|
|공급망 위험 분석|미지원|지원|
|버전 위험 분석|미지원|지원|
|Finding ID 체계|기존 6종|10종으로 확장|

**신규 Finding ID 체계**: `VULN-NNN`, `LIC-NNN`, `VER-NNN`, `SUPPLY-NNN`