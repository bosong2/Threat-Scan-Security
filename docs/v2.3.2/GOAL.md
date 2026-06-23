# v2.3.2 — 오케스트레이터 실행 버그 수정

## 목표 (1문장)

Claude Code 플러그인 실행 시 **에이전트 스폰 후 조기 종료**되던 오케스트레이터 버그와, 수정 과정에서 발생한 **dual-mode 교차 오염** 버그를 수정한다.

## 배경

v2.3.1에서 Claude Code 플러그인을 실제 실행한 결과 두 가지 버그가 확인됐다:

1. **오케스트레이터 조기 종료** (BUG-01): 8개 에이전트를 병렬 실행한다고 알린 뒤 에이전트가 완료되자 스캔이 그대로 종료됐다. 단계 4.5(연관관계)·4.6(모델 유효성)·8.5(심층 트리아지)·9(병합)·10(번역)·11(HTML)이 전혀 실행되지 않았다.

2. **Dual-mode 교차 오염** (BUG-02): BUG-01 수정을 위해 추가한 Phase 0-5 실행 절차가 `tss-*` 에이전트 이름(Code 전용)을 모드 구분 없이 사용해, Desktop SKILL.md 에도 그대로 포함될 상태였다.

3. **SBOM description 오염** (BUG-03): `securityreports-sbom/SKILL.md` description에 `tss-sbom`(Code 전용 이름)이 포함되어 Desktop dist에도 복사됐다.

## 버그 상세

### BUG-01 — 오케스트레이터 조기 종료

| 항목 | 내용 |
|------|------|
| 파일 | `skills/threat-scan-orchestrator/SKILL.md` |
| 원인 | 본문이 파이프라인 **설명 문서** 형식(표·서술). Claude가 에이전트를 스폰한 뒤 "할 일 없음"으로 판단해 턴 종료 |
| 참조 | SkillScan의 `skillscan/SKILL.md`는 "Phase A: invoke in parallel — **Phase B: after all return**, join" 명시적 지시 형태 |
| 증상 | "Steps 1~8 실행 중" 출력 → 에이전트 완료 → 스캔 종료. 4.5~11 미실행 |

### BUG-02 — Dual-mode 교차 오염

| 항목 | 내용 |
|------|------|
| 파일 | `skills/threat-scan-orchestrator/SKILL.md` |
| 원인 | BUG-01 수정 시 추가한 Phase 0-5 섹션이 `tss-source-handler` 등 Code 전용 에이전트명 사용. Desktop 빌드 시 그대로 포함 |
| 영향 | Desktop에서 `tss-*` 스킬 참조 시 미존재 에이전트 호출 오류 가능 |

### BUG-03 — SBOM description 오염

| 항목 | 내용 |
|------|------|
| 파일 | `skills/securityreports-sbom/SKILL.md` line 5 |
| 원인 | description에 "Used by tss-sbom agent (step 8)" — Code 전용 에이전트명 |
| 영향 | Desktop dist `references/sub-skills/securityreports-sbom.md`에 복사. 기능 영향 없으나 오염 |

## 수정 내용

| 버그 | 수정 파일 | 내용 |
|------|-----------|------|
| BUG-01 | `skills/threat-scan-orchestrator/SKILL.md` | Phase 0-5 명시적 실행 절차 추가(SkillScan 패턴). "전부 반환될 때까지 기다린다", "Phase 완료 후" 명시 |
| BUG-02 | `skills/threat-scan-orchestrator/SKILL.md` | 실행 절차를 `## 실행 절차 — Claude Code Plugin` / `## 실행 절차 — Claude Desktop` 으로 분리 |
| BUG-03 | `skills/securityreports-sbom/SKILL.md` | description에서 `tss-sbom` 제거 → "Used by threat-scan-orchestrator pipeline (step 8)" |
| 추가 | `commands/threat-scan.md` | "Do not stop until Phase 5 is done" 완주 지시 추가 |

## 완료 정의

- [ ] `/threat-scan <대상>` 실행 시 Phase 0→1→2→3→4→5 순서대로 완주, JSON+HTML 산출.
- [ ] Desktop SKILL.md에 `tss-*` 이름이 `## 실행 절차 — Claude Code Plugin` 섹션 **안에만** 존재.
- [ ] `securityreports-sbom` description에 `tss-sbom` 미포함.
- [ ] `VERSION` = 2.3.2, `plugin.json` version 2.3.2.
- [ ] Desktop 빌드 성공, 회귀 없음.

## Phase 구성

| Phase | 문서 | 내용 |
|-------|------|------|
| 1 | `phase-1-bug-fixes.md` | BUG-01·02·03 수정 상세 |
| 2 | `phase-2-version-and-release.md` | 버전 범프·빌드·커밋·태그 |
