# Phase 3 — 뷰어 추적성 UI (Goal Prompt)

> 선행 의존성: **Phase 1**. 관련 버그: BUG-001.

## 🎯 목표 (Objective)

`docs/index.html` 뷰어가 권장조치 카드에 REC-id·rank·priority 뱃지와 finding_ids 칩을 렌더하고, 칩 클릭 시 해당 finding 카드로 스크롤·섹션 자동 펼침하게 한다.

## 📥 참조 입력 (Inputs)

- `docs/index.html`: `renderRecs()`(~L806-818), `findingCard()`(~L535), `toggleSection()`(~L870), `t()` 라벨(~L262/291), `.rec-*`/`.finding-id` CSS
- 검증 샘플: `scanreport-20260622143000.json`

## 🔧 작업 (Tasks)

1. **`findingCard()`**: 카드 래퍼에 `id="finding-"+esc(f.id)` 앵커 속성 추가 (현재 id가 텍스트로만 노출, DOM 앵커 부재).
2. **`renderRecs()`**: 각 카드에 REC `id` 뱃지 + `rank` + `priority` 뱃지 + `finding_ids`를 클릭 가능한 칩으로 렌더. priority는 이미 `String()` 처리되어 정수/문자열 모두 견고. id/rank/finding_ids 부재 시 graceful(미표시).
3. **신규 `scrollToFinding(id)`**: 대상 finding 앵커(`#finding-<id>`)가 속한 섹션을 먼저 펼친 뒤(`section-content` 표시 — `toggleSection` 로직 재사용) `scrollIntoView({behavior:'smooth'})` + 일시 하이라이트.
4. **CSS**: rec id/rank/finding-ref 칩 스타일 (기존 `.finding-id`·`.rec-*` 팔레트 재사용). 클릭 칩에 hover/cursor 표시.
5. **`t()` 라벨**: `rank`(EN "Rank"/KO "순위"), `relatedFindings`(EN "Related Findings"/KO "관련 발견") 추가.
6. 내보내기(`exportHTML`)는 `renderReport()` 재렌더 경로라 자동 반영 — 추가 변경 없음.

## ✅ 완료 조건 (Acceptance) — 검증 가능

- index.html 단일 script 블록이 `new Function()` 파싱 통과(구문 무결).
- `scanreport-20260622143000.json` 로드 시 권장조치 카드에 REC-id·rank·priority 뱃지 표시(이 구파일은 finding_ids 없음 → 칩 미표시가 정상, 오류 없음).
- finding_ids를 수기 주입한 샘플에서 칩 클릭 → 해당 STATIC-001 카드로 스크롤 + 섹션 자동 펼침 동작.
- id/rank/finding_ids 없는 v2.1.0 페이로드 로드 시 콘솔 오류 0.

## 🔗 선행 의존성

Phase 1 (필드 계약). Phase 2와 병행 가능(독립 계층).
