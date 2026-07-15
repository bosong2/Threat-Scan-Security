# v2.5.1 — GOAL (goal-mode 마스터 프롬프트)

> **이 문서는 /goal 모드 실행 진입점이다.** 아래 목표·제약·Phase 순서에 따라
> `Phase1.md`~`Phase5.md`의 상세 명세를 차례로 구현한다. 각 Phase의 "완료 조건"이
> 전부 통과해야 다음 Phase로 진행하며, Phase 단위로 커밋한다.

## 목표 (1문장)

v2.5.0의 Code측 강화 과정에서 회귀한 **Desktop 모드의 스키마 준수·한글 번역·파일 커버리지**를,
기존 LLM·셸 경계(단계 0·10.5·11만 스크립트 허용)를 바꾸지 않고 **결정론 장치의 Desktop 이식**
(파일 열거 스크립트 + 출력 계약 앵커 + 스키마 검증기 + 번역 절차 + 템플릿 폴백)으로 복구해
양 모드 결과 동등성(parity)을 확보한다.

## 근거 문서 (구현 시 정본)

| 문서 | 내용 |
|------|------|
| [issues/TS-2.5.1-desktop-parity.md](issues/TS-2.5.1-desktop-parity.md) | 증상·근본원인(실측)·대책 D1~D5 상세 명세 — **충돌 시 이 문서가 우선** |

증거 리포트: `~/Downloads/scanreport-20260715100000-desktop.json`(Desktop 회귀 실증),
`~/sec/20260609-reviewOS-security/` 및 사용자 제공 `scanreport-20260715203013-code.json`(Code 기준).

## 대책 → Phase 추적 표 (누락 0 검증)

| 대책 | 내용 | Phase |
|------|------|-------|
| D1 | `enumerate_tree.py` 결정론 파일 열거 + 단계 0 배선 (양 모드) | 1 |
| D2 | Desktop 출력 계약 앵커 (V1.4 앵커·참조 목록·계약 카드·재독·자기검증) | 2 |
| D4 | 번역 회귀 복구 (Desktop 단계 10 완역 지시·카테고리 순차·공유 스킬 1줄) | 2 |
| D3 | `validate_report_schema.py` 결정론 스키마 검증기 + 단계 11 배선 (양 모드) | 3 |
| D5 | 템플릿 읽기측 폴백 (recommendations·code_fix·sbom·graph_verdict·푸터) | 4 |
| — | 버전 2.5.1 배선 + Desktop 빌드 회귀 + 증거 리포트 검증 | 5 |

## 불변 제약

1. **LLM·셸 경계 불변** — 단계 1–10 추론 전용 유지. 신규 스크립트 2종은 기존 셸 허용 단계(0·11)에서만 실행.
2. **BUG-02 (Dual-mode 교차 오염)** — 오케스트레이터 공유부·Desktop 섹션 수정 시 Code 전용 명칭
   (`tss-`, `SCAN_TMP`, `AskUserQuestion`) 사용 금지. 빌드 후 dist 오염 0 검증 필수.
3. **Schema V1.4 불변** — 신규 출력 필드 추가 없음. D1~D5는 전부 준수 강제·읽기측 관용 장치.
4. **생성측이 정본** — D5 템플릿 폴백은 이미 생성된 리포트 구제용(canonEnum 원칙). 신규 산출물은
   D2·D3로 정본을 강제한다.
5. **템플릿-뷰어 심링크 불변** — `docs/index.html`은 심링크. 템플릿만 수정.
6. **v1.3/v1.2 문서 무수정 보존** (legacy 참조).

## Phase 구성·의존

| Phase | 내용 | 의존 |
|-------|------|------|
| 1 | [Phase1.md](Phase1.md) `enumerate_tree.py` + 단계 0 배선 | — |
| 2 | [Phase2.md](Phase2.md) Desktop 앵커·계약 카드·재독·자기검증 + 번역 복구 | 1 (manifest 소비 계약 참조) |
| 3 | [Phase3.md](Phase3.md) `validate_report_schema.py` + 단계 11 배선 | 2 (계약 카드와 검사 항목 동일 원천) |
| 4 | [Phase4.md](Phase4.md) 템플릿 읽기측 폴백 + 푸터/문구 | — (병행 가능하나 순차 권장) |
| 5 | [Phase5.md](Phase5.md) 버전 2.5.1 배선 + 회귀·증거 검증 | 1–4 전부 |

**실행 순서: 1 → 2 → 3 → 4 → 5 (순차).** 오케스트레이터 SKILL.md는 Phase 1·2·3이 연속 수정하므로 순차 필수.

## 완료 정의 (Definition of Done)

- [ ] **P1** `enumerate_tree.py`가 이 repo 대상 실행에서 정합한 file_statistics·AI 구성요소 목록 산출.
      Desktop·Code 단계 0 절차에 실행+소비 계약 명문화.
- [ ] **P2** dist 메인 SKILL.md에 V1.4 앵커·v1.4 참조 목록·단계별 출력 계약 카드·재독 의무·자기검증·
      단계 10 완역/순차 지시가 존재. `grep "Schema V1.3 엄격"` = 0 (dist).
- [ ] **P3** `validate_report_schema.py`가 Desktop 증거 리포트에서 위반 전 클래스(ID·recommendations·
      code_fix·sbom 배열명·graph_verdict·발명 verdict·KR 미번역)를 구별 검출, Code 리포트에서는 경미 2건만,
      정상 픽스처 exit 0. 양 모드 단계 11 직전 배선.
- [ ] **P4** Desktop 증거 리포트 재렌더 시 권장조치 본문·code_fix·SBOM 서브섹션·최고위험 근거 표시 복구.
      푸터 V1.3 하드코딩 제거. node --check OK.
- [ ] **P5** 버전 2.5.1 정합(VERSION·plugin.json·help·CHANGELOG), Desktop 빌드 회귀 전부 통과
      (`tss-`=0/`SCAN_TMP`=0/신규 py 2종 dist 포함), 커밋·태그 v2.5.1 (push는 사용자 승인 후).
- [ ] 최종: Desktop 실스캔 재검증은 사용자 항목으로 명시(커버리지·판정·KR 완역).

## 범위 밖 (구현 금지)

- LLM·셸 경계 변경, 신규 파이프라인 단계, Schema 필드 추가.
- Code측 정적 분석 커버리지 갭(OAuth 스코프 미탐) 보완 — 별도 이슈로 이관.
- Desktop fragment 병렬 번역(도구 없음 — 순차 지침으로 갈음).
- 과거 생성 JSON 데이터 정정(D5 읽기측 폴백으로 흡수).
