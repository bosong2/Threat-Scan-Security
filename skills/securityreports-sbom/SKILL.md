---
name: securityreports-sbom
description: >
  Analyze software bill of materials and dependency security: CVE detection, license
  compliance, supply-chain risk, outdated packages. Used by threat-scan-orchestrator
  pipeline (step 8). Supports 17 ecosystems with lock-file-first transitive detection.
disable-model-invocation: true
argument-hint: <project-path>
---

# Security Reports - SBOM Analysis

**$ARGUMENTS** 의 소프트웨어 의존성을 분석합니다.

## 지원 패키지 매니저 (전 생태계)

**매니페스트(직접 의존성)와 lock 파일(전이 의존성 포함)을 구분**한다. 프로젝트 내 아래 파일을 **재귀적으로 모두 탐색**한다.

| 생태계 | OSV ecosystem | 매니페스트 | Lock 파일 |
|--------|---------------|-----------|-----------|
| npm/yarn/pnpm/bun | `npm` | package.json | package-lock.json, npm-shrinkwrap.json, yarn.lock, pnpm-lock.yaml, bun.lockb |
| pip/pipenv/poetry/pdm/uv/conda | `PyPI` | requirements*.txt, setup.py, setup.cfg, pyproject.toml, Pipfile, environment.yml | requirements-lock.txt, poetry.lock, Pipfile.lock, pdm.lock, uv.lock |
| Maven/Gradle (Java/Kotlin) | `Maven` | pom.xml, build.gradle, build.gradle.kts, settings.gradle(.kts) | gradle.lockfile |
| Go modules | `Go` | go.mod | go.sum |
| Cargo (Rust) | `crates.io` | Cargo.toml | Cargo.lock |
| RubyGems | `RubyGems` | Gemfile, *.gemspec | Gemfile.lock |
| NuGet (.NET C#/F#/VB) | `NuGet` | *.csproj, *.fsproj, *.vbproj, packages.config, Directory.Packages.props | packages.lock.json |
| Composer (PHP) | `Packagist` | composer.json | composer.lock |
| SwiftPM | `SwiftURL` | Package.swift | Package.resolved |
| Pub (Dart/Flutter) | `Pub` | pubspec.yaml | pubspec.lock |
| sbt (Scala) | `Maven` | build.sbt, project/plugins.sbt | build.sbt |
| Hex (Elixir/Erlang) | `Hex` | mix.exs | mix.lock |
| Conan/vcpkg (C/C++) | (GitHub Advisory) | conanfile.txt, conanfile.py, vcpkg.json | conan.lock |
| CPAN (Perl) | `CPAN` | cpanfile, Makefile.PL | cpanfile.snapshot |
| Hackage/Stack (Haskell) | `Hackage` | *.cabal, package.yaml | cabal.project.freeze, stack.yaml.lock |
| CocoaPods (iOS) | (GitHub Advisory) | Podfile | Podfile.lock |
| CRAN (R) | `CRAN` | DESCRIPTION | renv.lock |

### ⚠️ Lock 파일 우선 원칙 (필수)

**lock 파일이 존재하면 반드시 lock 파일을 우선 파싱한다.** 전이(transitive) 의존성은 lock 파일에만 명시되기 때문이다. (예: `requirements.txt`의 `msal`만 보면 그 하위 `PyJWT`를 놓치지만, `requirements-lock.txt`에는 `PyJWT==2.12.1`이 명시된다.)

- **lock 파일 있음** → lock 파일을 점검 기준으로 삼아 직접+전이 의존성 전체를 점검. `dependency_statistics.total_transitive`를 집계.
- **매니페스트만 있음** → 직접 의존성만 점검하고, `scan_notes`에 다음을 남긴다:
  > "전이 의존성 미포함 — lock 파일 생성(`pip freeze > requirements-lock.txt`, `npm install`, `poetry lock` 등) 후 재스캔 권장."
- **동일 생태계에 매니페스트+lock 공존** → lock 파일 기준으로 점검하되, 매니페스트는 직접 의존성 식별(`direct_dependencies`)에 사용.

> 같은 디렉토리뿐 아니라 하위 디렉토리(monorepo)·`backend/`·`frontend/` 등 모든 위치의 명세 파일을 탐색한다.

## 분석 항목

### 1. 취약점 분석 (Vulnerability)
- CVE 매핑 (아래 **인터넷 차단 환경 방법론** 참조)
- CVSS 점수 기반 심각도 분류
- 패치 가능 버전 제안

## ⚠️ 인터넷 차단 환경에서의 CVE 점검 방법론 (필수)

Claude Desktop 샌드박스는 **네트워크가 차단**되어 NVD/OSV 등 실시간 CVE DB를
조회할 수 없습니다. 데이터 소스는 **모델 학습 지식뿐**입니다. 따라서:

1. **모델 학습 지식 범위 내에서 반드시 점검을 시도한다.**
   각 의존성의 이름·버전을 학습 지식과 대조하여 알려진 CVE를
   `vulnerability_findings[]`에 **개별 구조화 항목**으로 출력한다.
2. **"No CVEs" 같은 한 줄 자유서술로 회피하지 않는다.**
   금지 필드 `known_vulnerabilities`(루트 문자열)는 **절대 사용 금지**.
   취약점이 없다고 판단되면 `vulnerability_findings: []`(빈 배열)로 두고,
   점검 사실·한계를 `scan_notes`에 남긴다.
3. **불확실성을 반드시 표기한다.** 각 finding에 `confidence` 필드를 둔다:
   - `Confirmed` — 학습 지식상 명확히 알려진 CVE
   - `Needs Verification` — 가능성은 있으나 버전 매칭/패치 여부 불확실
   - 학습 컷오프 이후 출시 버전은 **항상** `Needs Verification`로 표기한다.
4. **모든 의존성에 OSV 조회 링크(`lookup_links.osv`)를 생성한다.**
   리포트 뷰어는 사용자 브라우저에서 열리므로 링크는 실제로 동작한다.
   사용자가 클릭하여 OSV.dev에서 직접 최종 검증할 수 있게 한다.

생태계(ecosystem) 지정이 매칭 정확도의 핵심이다. 탐지된 명세 파일로
ecosystem을 결정한다 — 위 **지원 패키지 매니저** 표의 `OSV ecosystem` 열을 사용:
npm→`npm`, pip/poetry/pipenv→`PyPI`, maven/gradle/sbt→`Maven`, go→`Go`,
cargo→`crates.io`, gem→`RubyGems`, composer→`Packagist`, nuget→`NuGet`,
swift→`SwiftURL`, pub→`Pub`, hex→`Hex`, cpan→`CPAN`, hackage→`Hackage`, cran→`CRAN`.
OSV ecosystem이 없는 생태계(Conan/vcpkg/CocoaPods)는 GitHub Advisory 검색
링크(`https://github.com/advisories?query=<package>`)로 대체한다.
`@scope/pkg` 같은 네임스페이스 패키지는 ecosystem 없이는 검색이 실패한다.

```
OSV: https://osv.dev/list?q=<package>&ecosystem=<Ecosystem>
```
> 패키지명은 URL 인코딩한다 (`@`→`%40`, `/`→`%2F`).

> 핵심: 점검 결과의 **신뢰도와 한계를 투명하게 밝히고**, 최종 검증 경로를
> 사용자에게 제공하는 것. 단정적 "안전" 선언은 금지한다.

### 2. 라이선스 분석 (License)
- 라이선스 유형 식별 (MIT, GPL, Apache 등)
- 라이선스 호환성 검사
- 상업적 사용 제한 경고

### 3. 버전 분석 (Version)
- Unpinned 버전 탐지 (`^`, `~`, `*`)
- 오래된 버전 경고
- 메이저 버전 업데이트 권고

### 4. 공급망 위험 (Supply Chain)
- Typosquatting 의심 패키지
- 유지보수 중단 패키지
- 최근 소유권 변경 패키지

## 출력 형식

⚠️ **필수: Schema V1.2 준수**

SBOM 분석 결과는 최종 레포트의 `sbom_analysis` 객체 내에 포함됩니다.

```json
{
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
    "license_summary": {
      "MIT": 35,
      "Apache-2.0": 8,
      "ISC": 5
    },
    "vulnerability_findings": [
      {
        "id": "VULN-001",
        "file": "package.json",
        "package": "lodash",
        "version": "4.17.15",
        "cve_ids": ["CVE-2020-8203"],
        "severity": "High",
        "description": "Prototype pollution vulnerability",
        "fixed_version": "4.17.21",
        "confidence": "Confirmed",
        "lookup_links": {
          "osv": "https://osv.dev/list?q=lodash&ecosystem=npm"
        },
        "recommendation": "Upgrade to 4.17.21 or later"
      }
    ],
    "direct_dependencies": [
      {
        "name": "lodash",
        "version": "4.17.15",
        "license": "MIT",
        "risk": "High",
        "lookup_links": {
          "osv": "https://osv.dev/list?q=lodash&ecosystem=npm"
        }
      }
    ],
    "scan_notes": "모델 학습 지식(컷오프 기준)으로 점검함. 컷오프 이후 버전 및 Needs Verification 항목은 lookup_links로 최종 검증 권장. 번들 바이너리(예: Chromium)는 추적 사각지대.",
    "license_findings": [
      {
        "id": "LIC-001",
        "file": "package.json",
        "package": "some-gpl-lib",
        "version": "1.0.0",
        "license": "GPL-3.0",
        "issue": "Copyleft",
        "project_license": "MIT",
        "severity": "High",
        "recommendation": "Consider alternative package"
      }
    ],
    "version_risk_findings": [
      {
        "id": "VER-001",
        "file": "package.json",
        "package": "express",
        "current_version": "^4.17.0",
        "issue": "Unpinned",
        "severity": "Low",
        "recommendation": "Pin to exact version"
      }
    ],
    "supply_chain_findings": [],
    "sbom_documentation_status": {
      "sbom_file_exists": false,
      "sbom_format": null,
      "ci_sbom_generation": false,
      "completeness": "Missing",
      "recommendation": "Generate SBOM using CycloneDX or SPDX"
    },
    "risk_matrix": {
      "vulnerabilities": {"critical": 0, "high": 2, "medium": 5, "low": 3},
      "license_issues": {"critical": 0, "high": 1, "medium": 2, "low": 0},
      "version_risks": {"critical": 0, "high": 0, "medium": 8, "low": 15},
      "supply_chain": {"critical": 0, "high": 0, "medium": 1, "low": 2}
    },
    "priority_actions": [
      {
        "rank": 1,
        "category": "Vulnerability",
        "package": "lodash",
        "current_version": "4.17.15",
        "action": "Upgrade to 4.17.21",
        "severity": "High",
        "rationale": "Multiple prototype pollution CVEs"
      }
    ]
  }
}
```

### ❌ 절대 금지 필드 (Schema V1.2 위반)

**다음 필드를 사용하면 뷰어에서 SBOM 섹션이 렌더링되지 않습니다:**

| 사용 금지 | 올바른 필드 |
|-----------|-------------|
| `known_vulnerabilities` (루트 문자열) | `vulnerability_findings` (배열) — 없으면 빈 배열 + `scan_notes` |
| `total_dependencies` | `dependency_statistics.total_direct` |
| `direct_dependencies` (root) | `dependency_statistics.total_direct` |
| `dev_dependencies` (root) | `dependency_statistics.total_dev` |
| `vulnerabilities` (카운트 객체) | `vulnerability_findings` (배열) |
| `license_analysis` | `license_summary` (카운트 객체) |
| `notable_packages` | 제거 |
| `version_pinning` | `version_risk_findings` 배열로 |
| `finding_id` | `id` |
| `cve_id` | `cve_ids` (배열) |
| `cvss_score` | 제거 |
| `current_version` | `version` 사용 |
| VULN에 `file` 누락 | `file: "package.json"` 필수 |
| SUPPLY에 `issue` 사용 | `risk_type` 사용 |
| SUPPLY에 `description` 사용 | `detail` 사용 |
| SUPPLY에 `package` 누락 | `package` 필수 |
| severity 소문자 | 대문자 시작 (Critical, High, Medium, Low) |
| `priority_actions: ["문자열"]` | `priority_actions: [{rank, category, package, action, severity, rationale}]` |

### ⚠️ 필수 구조 검증

출력 전 다음 필드가 모두 존재하는지 확인:
```
□ sbom_analysis.manifest_files_found (배열)
□ sbom_analysis.dependency_statistics.total_direct (숫자)
□ sbom_analysis.dependency_statistics.total_dev (숫자)
□ sbom_analysis.dependency_statistics.by_ecosystem (객체)
□ sbom_analysis.license_summary (카운트 객체: {"MIT": 35, ...})
□ sbom_analysis.vulnerability_findings (배열)
□ sbom_analysis.license_findings (배열)
□ sbom_analysis.version_risk_findings (배열)
□ sbom_analysis.supply_chain_findings (배열)
□ sbom_analysis.sbom_documentation_status (객체)
□ sbom_analysis.risk_matrix (객체)
□ sbom_analysis.priority_actions (배열)
□ vulnerability_findings 점검 시도 완료 (없으면 빈 배열 + scan_notes)
□ known_vulnerabilities 루트 문자열 미사용 확인
□ 각 finding/의존성에 lookup_links(osv) 존재
□ 불확실 항목에 confidence: "Needs Verification" 표기
```

## Finding ID 규칙

| 접두사 | 의미 |
|--------|------|
| VULN-NNN | 알려진 취약점 (CVE) |
| LIC-NNN | 라이선스 이슈 |
| VER-NNN | 버전 관련 이슈 |
| SUPPLY-NNN | 공급망 위험 |

## ⚠️ 필수: 레포트 파일 저장

### 단독 실행 시
파일명: `sbom-report-{YYYYMMDD}-{HHMMSS}.json`

### securityreports-scan에서 호출 시
SESSION_ID를 전달받아 임시 파일로 저장:
```
.tmp-sbom-{SESSION_ID}.json
```
예시: `.tmp-sbom-20260205-143022.json`

이 파일은 report-merger가 통합 후 삭제합니다.

### 단독 실행 시 출력
```
✅ SBOM 분석 완료! 레포트: ./sbom-report-20260205-143022.json

통계: 45개 의존성 (직접 12, 간접 33)
취약점: 2건 (Critical 1, High 1)
라이선스 이슈: 1건
```

## 참조


