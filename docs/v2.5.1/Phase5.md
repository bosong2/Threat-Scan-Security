# Phase 5 — 버전 2.5.1 배선 + 회귀·증거 검증

## 목표

전 Phase 산출물을 v2.5.1로 배선하고, Desktop 빌드 회귀와 증거 리포트 기반 검증으로 릴리스를 확정한다.

## 5-A. 버전 배선

| 파일 | 변경 |
|------|------|
| `VERSION` | `2.5.1` |
| `.claude-plugin/plugin.json` | `"version": "2.5.1"` |
| `commands/threat-scan-help.md` | `(v2.5.1)` |
| `build_claude_desktop.sh` | Desktop description `v2.5.1` |
| `CHANGELOG.md` | 아래 항목 |

CHANGELOG `[2.5.1]` 구성:
- **Fixed — Desktop 품질 회귀 (TS-2.5.1)**: v2.5.0 Code 강화 시 Desktop 앵커 미갱신으로 발생한
  스키마 드리프트(ID·recommendations·code_fix·sbom 배열명·발명 verdict)·번역 역전(enum 번역+prose 미번역)·
  커버리지 붕괴 복구.
- **Added**: `scripts/enumerate_tree.py`(단계 0 결정론 파일 열거·file_statistics 정본 산출),
  `scripts/validate_report_schema.py`(단계 11 스키마 게이트 — ID/필드/구조/enum/KR 완역 검사),
  Desktop 단계별 출력 계약 카드·재독 의무·자기검증, Desktop 단계 10 완역·카테고리 순차 번역 지시.
- **Changed**: 오케스트레이터 공유부 출력 형식·스키마 참조 V1.4 갱신, 템플릿 읽기측 폴백
  (recommendations/code_fix/sbom/graph_verdict), 푸터 스키마 표기.

## 5-B. CLAUDE.md 갱신 (1곳)

"장애 방어 모델" 또는 Desktop 관련 절에 1단락:
"**Desktop parity (v2.5.1):** Desktop은 결정론 강제를 단계 0(`enumerate_tree.py` 열거)과
단계 11(`validate_report_schema.py`+`validate_compliance_tags.py` 게이트)에서 수행한다.
스키마·계약 변경 시 오케스트레이터 **공유부의 출력 계약 카드와 스키마 참조 목록을 반드시 함께
갱신**할 것 — v2.5.0에서 이를 누락해 Desktop 회귀(TS-2.5.1)가 발생했다."

## 5-C. Desktop 빌드 회귀 (최종)

```bash
bash build_claude_desktop.sh
```
- [ ] `tss-`=0 / `SCAN_TMP`=0 / `AskUserQuestion`=0 / `*.sh`=0 (기존 회귀 셋)
- [ ] dist에 신규 py 2종(`enumerate_tree.py`·`validate_report_schema.py`) 포함
- [ ] dist 메인 SKILL.md: "Schema V1.3 엄격" 0건, V1.4 앵커·계약 카드·재독·완역 지시 존재
- [ ] Desktop 게이트·Compliance 노트 등 기존 섹션 보존

## 5-D. 증거 기반 통합 검증

1. **validator 삼중 검증**:
   - Desktop 증거 리포트 → schema validator가 위반 전 클래스 검출(exit 1)
   - Code 증거 리포트 → 경미 항목만(대량 오탐 없음)
   - `tests/fixtures/schema-valid.json` → exit 0
2. **템플릿 구제 확인**: Desktop 증거 리포트 재렌더 → Phase 4 완료 조건 4항목 재확인.
3. **enumerate 정합**: 이 repo 대상 실행 → 통계 정합 + `ai_agent_paths` 게이트 스니펫과 일치.
4. `git grep "v2.5.0"` 버전 리터럴 잔존 확인(문서 이력 제외).

## 5-E. 마무리

- [ ] goal.md "대책 → Phase 추적 표" 전 행 구현 대조 (D1~D5 누락 0).
- [ ] Phase별 커밋 확인 후 릴리스 커밋 + 태그 `v2.5.1`.
- [ ] **push는 사용자 승인 후.**
- [ ] 사용자 검증 항목 안내: Desktop zip 재업로드 후 동일 대상 실스캔 1회 —
      ① markdown 인식 수(≈49), ② SBOM/graph 판정이 Code와 동급(DISABLE 계열),
      ③ KR prose 완역, ④ validator 통과, ⑤ HTML 권장조치·code_fix 정상 렌더.
