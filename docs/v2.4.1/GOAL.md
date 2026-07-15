# v2.4.1 — HTML 리포트 출력 결함 3종 + 파이프라인 내구성 수정

## 목표 (1문장)

스캔 결과 HTML 리포트의 **① 버전 헤더 미범핑, ② 리포지토리 요약/컴포넌트 카드 미출력, ③ OSV 버튼의 CVE 리스트·영향 버전 부정확** 세 결함을 뷰어 원천(`docs/index.html`)→배포 템플릿(`dictionary/security-template.html`)→스킬까지 연계 해소하고, **④ v2.4.0 실제 스캔에서 드러난 파이프라인 내구성 결함(translator 출력 토큰 상한 초과로 36분 허비 후 실패·총 1h23m 소요)**을 크기 게이트 분할 번역·결정론 조립으로 제거한다.

## 배경

`scanreport-20260624044705-happy.json`(slopus/happy 스캔)을 HTML로 렌더한 결과 3가지 결함이 동시에 관찰됐다. 세 결함 모두 **데이터는 정상 생성됐으나 표시 계층(템플릿·버전 원천)에서 누락·오판**된다.

- **뷰어 이원 구조**: `docs/index.html`(원천 뷰어, 1311줄)과 `dictionary/security-template.html`(생성기 `generate_html_report.py`가 사용하는 배포 템플릿)은 **동일 복제본**이다. 한쪽만 고치면 모드 간 불일치 → **양쪽을 동일하게 수정**해야 한다.
- **Dual-Mode 영향**: 템플릿·스크립트·스킬은 Claude Desktop·Claude Code 양 모드 공유 자산이다. 따라서 본 수정은 두 모드에 동시 반영되며 버전은 v2.4.1로 범프한다.
- **v2.4.0 실제 스캔 로그(slopus/happy, 1h23m)**: 단계 10 `tss-translator`가 전체 bilingual JSON을 단일 Write로 emit하려다 32K 출력 토큰 상한에 걸려 **36m59s 허비 후 실패** → 오케스트레이터가 즉석 5-fragment 분할+Python 조립으로 복구. 단계 9 `tss-report-merger`도 9m56s(상한 임박). **단일 에이전트·단일 Write로 전체 리포트 출력**하는 구조가 리포트 크기에 따라 실패·지연을 유발. 검증된 복구책이 스킬에 코드화되지 않음(재발 시 또 허비).

## 검토로 확정된 근본 원인

| 문제 | 근본 원인 | 증거 |
|------|-----------|------|
| **① 버전 헤더 미범핑** | 버전이 3곳에 하드코딩(`V2.1`)되어 `VERSION`(2.4.0)과 분리. 단일 진실원천 부재 | `security-template.html:6`(title), `:276`(badge); `scan_metadata.scanner_version="Claude Threat Scan V2.2"` (report-merger/orchestrator SKILL 리터럴) |
| **② 요약/컴포넌트 카드 미출력** | 생성 단계가 스키마 V1.3 필드명 위반(`overview`/`key_concerns`/`risk_level` emit) + 템플릿에 폴백 부재 → 카드 전체 공백 | 템플릿 `renderRepoSummary`(`:746`)는 `description`/`key_components`/`risk_summary`/`file_statistics`를 읽음. happy 리포트엔 해당 필드 없음 |
| **③a OSV 리스트/링크** | 상위 4개만 클릭형 배지, 초과분 `+N`은 **정적 텍스트**(클릭 불가). 모달·확장 없음 | `checkOSV`(`:452`), `osv-more`(`:486`) |
| **③b OSV 영향 버전 오판** | `version_risk_findings.current_version`이 `^4.17.0`류 스펙 범위면 OSV 질의가 파싱 실패 → 패키지 전체 취약점으로 폴백 | `checkOSV` POST body `version`(`:457`), fallback `list?q=`(`:441`) |
| **④ 파이프라인 내구성** | 단계 9·10이 전체 리포트를 단일 에이전트·단일 Write로 출력 → 출력 토큰 상한·직렬 생성시간이 리포트 크기에 비례 폭증 | `tss-translator` step4(단일 Write), `tss-report-merger` step4; v2.4.0 로그 36m59s 실패 |

## 사용자 확정 결정

1. **버전 주입(①)** = **데이터 기반 + 스킬 동기화**. 헤더 배지·타이틀을 `scan_metadata.scanner_version`에서 동적 렌더하고, 스킬 프롬프트의 `scanner_version` 리터럴을 `VERSION`과 동기화한다. 하드코딩 `V2.1` 제거.
2. **요약 필드(②)** = **스키마 정본 + 템플릿 폴백**. 스키마 V1.3 필드명(`description`/`key_components`/`risk_summary`/`file_statistics`)을 정본으로 유지하고 스킬이 정확히 그 이름으로 emit하도록 강제 + 템플릿에 `overview`/`key_concerns`/`risk_level` 별칭 폴백을 추가해 기존 리포트도 렌더되게 한다.
3. **OSV UX(③a)** = **인라인 N개 + 초과 시 모달**. 상위 ~5개는 클릭형 배지 인라인, 초과분은 `+N 더보기` 버튼 → 전체 CVE 반응형 모달(각 항목 `osv.dev/vulnerability` 링크).
4. **OSV 버전 정확도(③b)** = **템플릿만 보정**. SBOM 스킬은 건드리지 않고, 템플릿에서 version 문자열을 정규화(캐럿/틸드/범위 제거 → concrete 버전)해 OSV에 질의하고, 비-concrete면 캐비엇 표시. (스킬 측 lock 해석은 본 버전 범위 외 — 후속 검토로 이관)
5. **파이프라인 분할(④)** = **크기 게이트 + 결정론 Python 조립**. `step9-english.json`이 임계치(40KB/40 findings) 초과 시에만 단계 9·10을 카테고리별 병렬 분할 후 `scripts/assemble_bilingual.py`로 결정론 조립. 소규모는 단일 호출 유지. 조립은 단계 0·11과 동일한 "결정론·셸 허용 예외"로 분류(LLM/셸 경계 문서 갱신 동반).

## 불변 제약

1. **뷰어 동기화 불변**: `docs/index.html`과 `dictionary/security-template.html`은 **바이트 동일**을 유지한다(버전 헤더 동적화 포함 모든 변경 양쪽 동일 적용). 검증: `diff docs/index.html dictionary/security-template.html` → 빈 출력.
2. **스키마 V1.3 불변**: 임의 필드 추가 금지. 본 버전은 신규 출력 필드를 추가하지 않는다(③b는 템플릿 표시 로직만, ④는 분할/조립이며 최종 스키마 동일). 별칭 폴백은 *읽기* 측 호환이며 스키마 변경 아님.
3. **LLM·셸 경계 — ④에서 한정 확장**: 단계 1–10 추론 전용 원칙 유지하되, **단계 10.5 조립(결정론 Python)을 단계 0·11과 동일한 셸 허용 예외로 신규 분류**한다(분할 모드 한정). 이 경계 변경은 CLAUDE.md·docs 동시 갱신을 **필수** 동반한다(불일치 시 BUG 재발). ①②③은 템플릿/프롬프트 수정만으로 처리.
4. **Dual-Mode 동시 수정**: 스킬·템플릿·버전 변경 시 Desktop·Code 양 계층 반영. `build_claude_desktop.sh` 회귀 없음.
5. **결정론**: `generate_html_report.py`는 동일 입력 → 동일 출력 유지(외부 네트워크 의존 없음; OSV 라이브 질의는 브라우저 런타임 한정, 생성 결정론과 무관).

## 완료 정의 (Definition of Done)

- [ ] **①** 타이틀·`version-badge`에 하드코딩 `V2.1` 없음. 헤더가 `scan_metadata.scanner_version`(없으면 기본값)에서 동적 렌더. 양 뷰어 동일.
- [ ] **①** 스킬(`report-merger`, `threat-scan-orchestrator`)의 `scanner_version` 리터럴이 `Claude Threat Scan V2.4`로 동기화.
- [ ] **②** happy 리포트(`overview`/`key_concerns`/`risk_level`)로 렌더 시 설명 카드·요약/컴포넌트 카드가 **공백이 아니라 데이터로 채워짐**.
- [ ] **②** 스키마 정본 필드(`description`/`key_components`/`risk_summary`)로 된 리포트도 정상 렌더(회귀 없음). 스킬 출력 가이드가 정본 필드명으로 강제.
- [ ] **③a** CVE가 N개(예: 6개) 초과인 패키지에서 `+N 더보기` 버튼 클릭 → 전체 CVE 모달, 각 항목 클릭 시 `osv.dev/vulnerability/<id>` 새 탭. 모바일 폭에서 레이아웃 깨지지 않음.
- [ ] **③b** version이 `^4.17.0`/`>=8.17.1`류여도 OSV 질의가 concrete 버전으로 정규화되어 패키지 전체가 아닌 해당 버전 영향 CVE를 반환. 정규화 불가 시 버튼에 캐비엇(범위 표시) 노출.
- [ ] **④** happy 리포트(≥40 findings) 재스캔 시 단계 10이 분할 경로로 진입, **단일 translator 36분 허비 없이** 완주(단계 10 총 ≤ 8분 목표). `scripts/assemble_bilingual.py`가 EN/KR 카운트 불일치 시 비-0 종료.
- [ ] **④** 소규모 리포트(< 임계)는 단일 호출 경로 유지(회귀 없음). 오케스트레이터 Phase 3에 게이트 분기·조립·체크포인트 명문화, Desktop 섹션 미오염.
- [ ] **④** CLAUDE.md·docs LLM/셸 경계에 단계 10.5 조립 예외 반영.
- [ ] `VERSION` = 2.4.1, `.claude-plugin/plugin.json` version = 2.4.1, `commands/threat-scan-help.md`·`CHANGELOG.md` 동기화.
- [ ] `diff docs/index.html dictionary/security-template.html` 빈 출력.
- [ ] `python3 scripts/generate_html_report.py scanreport-...-happy.json --lang ko` 성공, 세 결함 모두 해소된 HTML 산출.
- [ ] `bash build_claude_desktop.sh` 성공, Desktop zip 구성 회귀 없음.

## Phase 구성

| Phase | 문서 | 내용 | 주요 파일 |
|-------|------|------|-----------|
| 1 | `phase-1-version-source.md` | 버전 동적 렌더 + 스킬 리터럴 동기화 + 버전 범프 | 양 뷰어, `report-merger`/`orchestrator` SKILL, `VERSION`, `plugin.json` |
| 2 | `phase-2-repo-summary.md` | 요약/컴포넌트 카드 폴백 렌더 + 스킬 정본 강제 | 양 뷰어 `renderRepoSummary`, `repo-indexer`/`report-merger` SKILL |
| 3 | `phase-3-osv.md` | OSV CVE 모달 UX + version 정규화/필터 | 양 뷰어 `vulnLinks`/`checkOSV`/신규 모달·정규화 |
| 5 | `phase-5-pipeline-resilience.md` | **④** 크기 게이트 분할 번역/병합 + `assemble_bilingual.py` 결정론 조립 + 경계 문서 | `tss-translator`/`tss-report-merger` 에이전트·스킬, 오케스트레이터 Phase 3, 신규 스크립트, CLAUDE.md |
| 4 | `phase-4-validation.md` | 양 뷰어 diff, happy 리포트 E2E·재스캔, Desktop 빌드 회귀, 모바일 확인 | 검증 전용 |

## 실행 순서·의존

Phase 1 → 2 → 3은 **템플릿/뷰어** 동일 파일을 만지므로 **순차** 진행(머지 충돌 회피). 각 Phase 종료 시 `docs/index.html`↔`security-template.html` diff를 0으로 맞춘 뒤 다음 Phase로.

Phase 5는 **파이프라인(에이전트·오케스트레이터·스크립트)** 계층으로 1–3(뷰어)과 파일이 겹치지 않아 **독립·병렬 가능**. 단, 검증(Phase 4)은 5까지 완료 후 수행한다(happy 재스캔으로 ④ 검증 필요).

Phase 4는 전 Phase(1–3,5) 누적 검증.

> 실행 진입은 `docs/v2.4.1/EXEC_PROMPT.md`의 goal-mode 프롬프트를 사용한다.

## 후속 이관 (v2.4.1 범위 밖)

- **5-E report-merger 동일 적용 보류**: `tss-report-merger`(단계 9)의 Mode B(카테고리 fragment)는
  agents/skills 문서에 정의됐으나 오케스트레이터 Phase 3가 아직 이를 호출하지 않는다. 단계 9는
  현재 항상 단일 호출(Mode A)이다. v2.4.0 로그상 단계 9는 9m56s(상한 임박, 미실패)였으나 본
  버전의 완료 정의(④)는 단계 10(실제 실패 사례)만 요구하므로 범위에서 제외했다. 단계 9도 상한에
  걸리는 리포트가 관측되면 다음 버전에서 동일한 크기 게이트를 Phase 3에 추가해 Mode B를 연결한다.
