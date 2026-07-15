# v2.4.1 실행 프롬프트 (goal-mode)

> 아래 블록을 그대로 goal-mode 세션 입력으로 사용한다. 작업은 **`Threat-scan-security/` 프로젝트 폴더**에서 진행한다(워크스페이스 루트 아님).

---

## GOAL

`Threat-scan-security`의 HTML 리포트 출력 결함 3종 + 파이프라인 내구성 결함을 v2.4.1로 수정한다. 계획서는 `docs/v2.4.1/`에 있다(`GOAL.md`, `phase-1..5`). 계획을 변경하지 말고 **그대로 구현**하되, 구현 중 계획과 실제 코드가 다르면 멈추고 보고한다.

## 불변 제약 (위반 시 중단·보고)

1. `docs/index.html`과 `dictionary/security-template.html`은 **모든 변경에서 바이트 동일**을 유지한다. 각 Phase 끝에 `diff docs/index.html dictionary/security-template.html`이 빈 출력이어야 한다.
2. 스키마 V1.3에 **신규 출력 필드를 추가하지 않는다**(④ 분할/조립도 최종 스키마 동일). 별칭 폴백은 읽기 측 호환.
3. ①②③은 LLM·셸 경계·파이프라인 단계를 바꾸지 않는다. **④ Phase 5에 한해 단계 10.5 조립(결정론 Python)을 셸 허용 예외로 신규 분류**하며, 이때 CLAUDE.md·docs 경계 문구를 **반드시 함께** 갱신한다.
4. SBOM 스킬의 출력 스키마/lock 해석은 **이번 범위 밖**(③b는 템플릿 정규화만).
5. Desktop 빌드 동작·zip 구성은 회귀 없어야 한다. 오케스트레이터 Code 섹션 수정이 Desktop 섹션을 오염시키면 안 된다(BUG-02).

## 실행 순서

Phase 1→2→3은 **뷰어 동일 파일** 충돌 회피로 **순차**. Phase 5는 **파이프라인 계층**(뷰어와 파일 비중복)이라 1–3과 **독립·병렬 가능**. Phase 4는 1–3,5 누적 검증.

1. **Phase 1** (`phase-1-version-source.md`): 버전 배지 동적화 + 스킬 `scanner_version` → `V2.4` + 버전 범프(2.4.1). → diff 0 확인.
2. **Phase 2** (`phase-2-repo-summary.md`): `renderRepoSummary` 폴백(`overview`/`key_concerns`→"주요 우려사항"/`risk_level`/`file_statistics`) + i18n 키 + 스킬 정본 강제. → diff 0 확인.
3. **Phase 3** (`phase-3-osv.md`): `normalizeVersion()` + 캐비엇 + CVE 모달(인라인 5 + `+N 더보기`) + CSS/반응형. → diff 0 확인.
4. **Phase 5** (`phase-5-pipeline-resilience.md`): 크기 게이트 분할 번역/병합 + `scripts/assemble_bilingual.py` + 오케스트레이터 Phase 3 분기 + LLM/셸 경계 문서 갱신 + 폴링 정리.
5. **Phase 4** (`phase-4-validation.md`): happy 리포트 E2E·**재스캔(④)**·회귀·Desktop 빌드·버전 정합 전수 검증.

## 작업 규칙

- 양 뷰어 수정은 **동일 패치를 두 파일에 각각** 적용한다(자동 복사 금지 — 둘 다 추적 대상). 단, 한쪽 완성 후 `cp`로 다른쪽 동기화하고 diff로 확인하는 방식 허용.
- 각 Phase의 "완료 조건" 체크리스트를 모두 만족해야 다음 Phase로 진행한다.
- 검증은 실제 명령 실행 결과로 보고한다(추정 금지). happy 리포트 경로: `~/Downloads/scanreport-20260624044705-happy.json`.
- 커밋·푸시는 Phase 4 통과 후 **사용자 승인**을 받고 수행한다.

## 완료 보고 형식

각 Phase 종료 시: 변경 파일 목록 + 완료 조건 체크 결과 + diff 0 여부. 전체 종료 시: happy 리포트 렌더 스크린샷/육안 확인 결과 3종(①②③) + Desktop 빌드 회귀 결과.

---

## 참고 — 핵심 코드 좌표 (v2.4.0 기준, 라인은 근사)

| 대상 | 위치 |
|------|------|
| title 하드코딩 | `security-template.html:6` / `docs/index.html:6` |
| version-badge 하드코딩 | `:276` |
| 메타 렌더(`scanner_version` 사용) | `:529` 인근 |
| `renderRepoSummary` | `:746` |
| `renderSummary`/graph_verdict | `:667` |
| i18n `t` 테이블 EN/KO | `:327` / `:359` 인근 |
| `vulnLinks` | `:437` |
| `checkOSV` | `:452` |
| `cveLink` | `:501` |
| `osv-more` CSS | `:169` |
| 스킬 scanner_version | `report-merger/SKILL.md:56`, `threat-scan-orchestrator/SKILL.md:276` |
| repo_summary 스키마 정본 | `repo-indexer/SKILL.md:42~`, `docs/claude-threat-scan-json-schema-v1.3.md:79~` |
| translator 단일 Write (④) | `agents/tss-translator.md` step4 |
| merger 단일 Write (④) | `agents/tss-report-merger.md` step4 |
| 오케스트레이터 Phase 3 (단계 9→10) | `threat-scan-orchestrator/SKILL.md:168~184` |
| LLM/셸 경계 문구 | 루트·프로젝트 `CLAUDE.md`, `skills/threat-scan-orchestrator/SKILL.md:233` |
| 신규 조립 스크립트 | `scripts/assemble_bilingual.py` (신규) |
