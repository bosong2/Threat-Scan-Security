# v2.3.1 — SBOM 명세 파일 전면 확장 + 문서 세트

## 목표 (1문장)

SBOM 스킬이 **지원 가능한 모든 언어의 의존성 명세 파일(매니페스트 + lock 파일)을 빠짐없이 인식**하도록 확장하고(transitive 누락 해소), Apache 2.0 라이선스와 현행 기준 문서 5종(README·INSTALLATION·USER_GUIDE·ARCHITECTURE·CHANGELOG)을 작성한다.

## 배경

v2.2.0 Claude Desktop 스킬로 실제 프로젝트(`DeviceExceptionManager`)를 점검한 결과 **`PyJWT`가 누락**됐다. 원인:

- `securityreports-sbom/SKILL.md`의 지원 파일 목록이 Python을 `requirements.txt, Pipfile, pyproject.toml`로만 한정.
- `PyJWT`는 `msal`의 **transitive 의존성**으로, `requirements-lock.txt`(102개 의존성)에만 존재.
- lock 파일 패턴(`requirements-lock.txt`, `poetry.lock`, `Pipfile.lock` 등)이 목록에 없어 스킬이 lock 파일을 읽지 않음.

근본 원인은 **명세 파일 목록 자체가 불완전**하다는 것. 여러 언어에서 lock 파일·대체 매니페스트가 누락되어 있어 transitive 의존성 점검이 구조적으로 불가능했다.

문서 측면에서는 루트에 README/LICENSE가 없고, `docs/INSTALLATION.md`·`docs/USAGE_GUIDE.md`는 dual-mode 이전(Cursor/Copilot·V2.0) 내용이라 현행과 불일치한다.

## 불변 제약 (계승)

1. **단일 원천**: SBOM 방법론은 `skills/securityreports-sbom/SKILL.md` 하나. Desktop·Code 양 모드가 이 파일을 공유하므로 **한 번 수정 = 양쪽 적용**. (CLAUDE.md Dual-Mode 규칙)
2. **결정론·네트워크 차단 호환**: Desktop 샌드박스는 네트워크 차단. lock 파일 파싱·CVE 점검은 모델 학습 지식 기반, `lookup_links.osv`로 최종 검증 경로 제공.
3. **Schema V1.3 불변**: SBOM 출력 스키마 구조 변경 없음. 파일 인식 범위만 확장.
4. **Desktop 빌드 회귀 없음**: `build_claude_desktop.sh` 정상, zip 구성 유지.

## 완료 정의 (Definition of Done)

- [ ] `securityreports-sbom/SKILL.md`가 17개 생태계의 매니페스트+lock 파일을 모두 명시(아래 Phase 1 매트릭스).
- [ ] **lock 우선 원칙** 명문화: lock 파일이 있으면 우선 파싱(transitive 포함), 없으면 매니페스트 + `scan_notes` 경고.
- [ ] OSV ecosystem 매핑이 확장된 생태계 전부 포함.
- [ ] `repo-indexer/SKILL.md`의 의존성 매니페스트 식별이 lock 파일 인식 포함.
- [ ] 루트에 `LICENSE`(Apache 2.0) + `NOTICE` 존재.
- [ ] 루트에 `README.md`·`INSTALLATION.md`·`USER_GUIDE.md`·`ARCHITECTURE.md`·`CHANGELOG.md` 존재 — Desktop skill·Code plugin 모두 포함, mermaid 다이어그램, 두괄식.
- [ ] 구 `docs/INSTALLATION.md`·`docs/USAGE_GUIDE.md`는 루트 정식 문서로 리다이렉트(드리프트 제거).
- [ ] `VERSION` = 2.3.1, `plugin.json` version 2.3.1.
- [ ] Desktop 빌드 성공, zip에 확장된 SBOM 스킬·문서 반영.

## Phase 구성

| Phase | 문서 | 내용 |
|-------|------|------|
| 1 | `phase-1-sbom-expansion.md` | SBOM 명세 파일 전면 확장(17 생태계) + lock 우선 + repo-indexer 보강 |
| 2 | `phase-2-license-and-docs.md` | Apache 2.0 LICENSE/NOTICE + 문서 5종(mermaid·두괄식·dual-mode) |
| 3 | `phase-3-version-build-validation.md` | VERSION/plugin.json 2.3.1 + 빌드 + 회귀·완결성 검증 |

## 범위 밖

- 실제 lock 파일 파서 코드(샌드박스 네트워크 차단 — 모델 지식 기반 유지).
- 신규 HTML 리포트 `--profile`.
- 구 `claude_threat_scan_prompt_v_2.md`(레거시 단일 프롬프트) 개정.
