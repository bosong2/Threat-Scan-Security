# Phase 1 — SBOM 명세 파일 전면 확장

## 목표

SBOM 스킬이 지원 가능한 **모든 언어 생태계의 의존성 명세 파일**을 인식하게 하여 transitive 의존성 누락(예: PyJWT)을 구조적으로 해소한다.

## 변경 1 — `skills/securityreports-sbom/SKILL.md` 지원 파일 매트릭스

기존 8행 표를 아래 17 생태계 매트릭스로 교체. **lock 파일을 매니페스트와 분리 표기**.

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
| sbt (Scala) | `Maven` | build.sbt | build.sbt(plugins.sbt) |
| Hex (Elixir/Erlang) | `Hex` | mix.exs | mix.lock |
| Conan/vcpkg (C/C++) | (GitHub Advisory) | conanfile.txt, conanfile.py, vcpkg.json | conan.lock |
| CPAN (Perl) | `CPAN` | cpanfile, Makefile.PL | cpanfile.snapshot |
| Hackage/Stack (Haskell) | `Hackage` | *.cabal, package.yaml | cabal.project.freeze, stack.yaml.lock |
| CocoaPods (iOS) | (GitHub Advisory) | Podfile | Podfile.lock |
| CRAN (R) | `CRAN` | DESCRIPTION | renv.lock |

## 변경 2 — lock 우선 원칙 명문화

분석 항목 앞에 신규 절 추가:

> **Lock 파일 우선 원칙**: lock 파일이 존재하면 **반드시 lock 파일을 우선 파싱**한다 — transitive 의존성 전체가 여기에만 명시되기 때문(예: `msal`의 `PyJWT`). 매니페스트만 있으면 직접 의존성만 점검하고, `scan_notes`에 "transitive 미포함 — lock 파일 생성(`pip freeze`, `npm install` 등) 후 재스캔 권장"을 남긴다. `dependency_statistics`의 `total_direct`/`total_transitive`를 구분 집계한다.

## 변경 3 — OSV ecosystem 매핑 갱신

기존 매핑 문장(npm→npm, pip→PyPI...)을 위 매트릭스 전 생태계로 확장. ecosystem 미지원(Conan/vcpkg/CocoaPods)은 GitHub Advisory/일반 검색 링크로 대체 명시.

## 변경 4 — `repo-indexer/SKILL.md` 매니페스트 식별 보강

점검 항목 표의 "의존성 매니페스트" 행을 lock 파일 인식 포함으로 확장:

> `의존성 매니페스트 | package.json, requirements.txt 등 매니페스트 + lock 파일(package-lock.json, poetry.lock, *-lock.txt 등) 식별. lock 파일 우선.`

## 완료 조건 (검증 가능)

- [ ] `securityreports-sbom/SKILL.md`에 17 생태계 매트릭스(매니페스트+lock 분리) 존재.
- [ ] `requirements-lock.txt`·`poetry.lock`·`Pipfile.lock`·`composer.lock`·`Package.resolved`·`pubspec.lock` 등 lock 패턴이 문서에 명시.
- [ ] lock 우선 원칙 절 존재.
- [ ] OSV ecosystem 매핑에 Pub/Hex/CPAN/Hackage/CRAN 등 신규 생태계 포함.
- [ ] `repo-indexer/SKILL.md`가 lock 파일 식별 명시.
- [ ] Schema V1.3 출력 구조 변경 없음(파일 인식 범위만 확장).

## 검증

```bash
cd Threat-scan-security
for p in requirements-lock.txt poetry.lock Pipfile.lock composer.lock Package.resolved pubspec.lock pnpm-lock.yaml packages.lock.json mix.lock Cargo.lock; do
  grep -q "$p" skills/securityreports-sbom/SKILL.md && echo "OK: $p" || echo "MISSING: $p"
done
grep -q "Lock 파일 우선\|lock 파일을 우선" skills/securityreports-sbom/SKILL.md && echo "lock-first OK"
grep -q "lock" skills/repo-indexer/SKILL.md && echo "repo-indexer OK"
```
