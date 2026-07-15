# Phase 5 — 파이프라인 내구성: 대용량 리포트 분할 번역·조립 (실행 시간/에러)

## 목표

단계 9(병합)·10(번역)의 **단일 에이전트·단일 Write 전체 출력** 구조가 대용량 리포트에서 32K 출력 토큰 상한에 걸려 실패(v2.4.0: translator 36m59s 허비 후 실패)하는 것을 제거한다. **크기 게이트 기반 카테고리 분할 → 병렬 처리 → 결정론 Python 조립**을 스킬·오케스트레이터에 코드화한다.

## v2.4.0 로그 실측 근거

- `tss-translator`가 전체 bilingual JSON 단일 Write 시도 → 32,000 출력 토큰 상한 → **36m59s 후 실패**.
- 오케스트레이터가 즉석으로 5-fragment 분할 + Python 조립으로 복구(동작은 했으나 비코드화·수동).
- `tss-report-merger` 단계 9: 78 findings 단일 Write 9m56s — 동일 상한 임박.

## 사용자 확정 결정

1. **분할 시점** = **크기 게이트**. `step9-english.json` 크기/finding 수가 임계치 초과 시에만 분할. 소규모는 단일 호출 유지(오버헤드 회피).
2. **조립 방식** = **결정론 Python 스크립트** `scripts/assemble_bilingual.py` 신규. 단계 0·11과 동일하게 "결정론·셸 허용 예외"로 분류(LLM 추론 아님). → **LLM/셸 경계 문서 갱신 필요**.

## 대상 파일

- `agents/tss-translator.md` (크기 게이트 + fragment self-write 분기)
- `agents/tss-report-merger.md` (동일 패턴, 게이트 적용)
- `skills/bilingual-translator/SKILL.md` / `skills/report-merger/SKILL.md` (방법론 본문에 분할·조립 규칙)
- `skills/threat-scan-orchestrator/SKILL.md` Phase 3 (단계 9→10 분기 절차 + 조립 단계)
- `scripts/assemble_bilingual.py` (신규, 양 모드 공유)
- `CLAUDE.md`(루트·프로젝트) / `docs/` — LLM·셸 경계에 "조립(assemble)" 예외 추가
- `.claude-plugin/plugin.json` `allowed-tools`/오케스트레이터 frontmatter (분할 translator 병렬 호출 반영)

## 작업

### 5-A. 임계치 정의

- 게이트 기준(택1·문서화): `step9-english.json` 바이트 ≥ **40KB** **또는** 총 finding 수 ≥ **40**.
- 이하 → 단일 호출(현행 유지). 초과 → 분할 모드.
- 임계치는 오케스트레이터가 단계 9 산출 직후 Bash로 측정(`wc -c`, finding 카운트).

### 5-B. 분할 단위 (카테고리)

`english_report{}` 최상위 키를 5묶음으로 그룹핑(v2.4.0 복구와 동일 검증된 분할):

1. `repository_summary`
2. `static_code_findings` + `binary_analysis_findings`
3. `skill_risk_findings` + `agent_policy_findings`
4. `sensitive_patterns` + `prompt_optimization` + `sbom_analysis`
5. `relationship_findings` + `model_validity_findings` + `recommendations`

각 묶음 → `tss-translator` 1개가 **fragment 파일**(`step10-frag-N.json`)에 korean 부분만 self-write. 병렬 5개.

### 5-C. 결정론 조립 스크립트

`scripts/assemble_bilingual.py`:

- 입력: `step9-english.json` + `step10-frag-*.json`(korean fragment들) + scan_metadata.
- 출력: `{ scan_metadata, english_report, korean_report }` 최종 bilingual JSON.
- 검증 내장: EN/KR 카테고리별 항목 수 일치, 누락 키 검출 → 불일치 시 비-0 종료(파일=진실).
- 표준 라이브러리만, 외부 의존·네트워크 없음, 결정론.

### 5-D. 오케스트레이터 Phase 3 절차 (Code 모드)

```
단계 9 (merger) → step9-english.json
  ↓ Bash: 크기/카운트 측정
  ├─ 임계 이하 → 단계 10 단일 translator (현행)
  └─ 임계 초과 → 단계 10' 분할:
       5개 tss-translator 병렬 → step10-frag-1..5.json
       ↓ 각 fragment 존재·JSON유효 체크포인트(파일=진실)
       단계 10.5 assemble: python3 scripts/assemble_bilingual.py ... → 최종 JSON
       ↓ EN/KR 카운트 일치 검증
```

> Desktop 모드: Desktop 섹션에 동일 취지의 "리포트가 크면 카테고리별로 나눠 번역 후 합본" 지침만 서술(셸 없음 — 모델이 순차 조립). Code 섹션 오염 금지(BUG-02).

### 5-E. report-merger 동일 적용 (5-B와 대칭)

- 단계 9도 finding 총량이 임계 초과면 카테고리별 fragment self-write + 동일 조립으로 영문 병합. (9m56s 단일 Write 위험 제거)

### 5-F. LLM·셸 경계 문서 갱신

- `CLAUDE.md`(루트·프로젝트)·`docs/`의 "단계 0·11만 셸/파일 허용" 문구에 **"단계 10.5 조립(결정론 Python) 예외"** 추가.

### 5-G. (부수) 오케스트레이터 대기 패턴 정리

- 단계 복귀 후 체크포인트는 **단일 존재 확인**(`test -f`)으로 통일. sleep 폴링 루프·백그라운드 Bash 대기 금지(v2.4.0의 `Invalid tool parameters`·stale wait-loop 혼선 제거). CLAUDE.md "Monitor/폴링 금지" 원칙 재확인.

### 5-H. (부수·선택) source-handler ballast 자동 제외

- 100MB 초과 시 `.git` 히스토리·well-known 번들 바이너리(ripgrep/difftastic 등)를 **자동 식별·제외**하고 그 사실을 supply-chain finding + scan_note로 기록. (v2.4.0의 수동 ballast 제거를 코드화 — 시간/개입 절감)
- 범위 부담 시 본 항목은 v2.4.2로 이관 가능(GOAL에 표기).

## 완료 조건 (검증 가능)

- [ ] happy 리포트(≥40 findings) 재스캔 시 단계 10이 분할 경로로 진입, **단일 translator 36분 허비 없이** 완주(목표: 단계 10 총 ≤ 8분).
- [ ] `scripts/assemble_bilingual.py`가 fragment+english → 최종 bilingual 조립, EN/KR 카운트 불일치 시 비-0 종료.
- [ ] 소규모 리포트(< 임계)는 단일 호출 경로 유지(회귀 없음).
- [ ] 오케스트레이터 Phase 3에 게이트 분기·조립·체크포인트 절차 명문화(Code 섹션), Desktop 섹션 미오염(`diff`로 경계 확인).
- [ ] `allowed-tools`에 분할 translator 병렬 호출 반영, frontmatter 유효.
- [ ] CLAUDE.md·docs의 LLM/셸 경계에 단계 10.5 조립 예외 반영.
- [ ] 체크포인트가 `test -f` 단일 확인으로 통일, sleep/백그라운드 폴링 제거.
- [ ] `bash build_claude_desktop.sh` 성공 + `assemble_bilingual.py`가 Desktop dist에 미포함(Code 전용 — `scripts/*.sh` 비복사 규칙과 별개로 `.py`는 references에 복사됨 → 조립 스크립트는 Code 파이프라인 전용임을 빌드에서 분기 확인).

## 주의·리스크

- **빌드 분기 주의**: `build_claude_desktop.sh`는 `scripts/*.py`를 references로 복사한다(현행). `assemble_bilingual.py`가 Desktop에 들어가도 무해해야 하며, Desktop은 호출하지 않음 — 빌드 검증에 포함.
- **경계 변경 신중**: 단계 10.5 조립 예외는 LLM/셸 경계를 건드리므로 문서·CLAUDE.md 동시 갱신 필수(불일치 시 BUG 재발).
- **임계치 튜닝**: 40KB/40 findings는 초기값. happy(67 findings) 기준 분할 경로 검증 후 조정.
