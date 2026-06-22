# Phase 3 — 스킬 + 오케스트레이터 통합

## 목표

신규 스킬 `@html-report-generator`를 추가하고, 오케스트레이터 스캔 순서에 단계 11로 편입하며, "스크립트/파일 생성 허용 단계" 제약을 갱신한다.

## 변경

### 신규 스킬 — `skills/html-report-generator/SKILL.md`

- 개요/역할/호출방법(CLI 옵션표)/프로파일 매핑표/입출력/워크플로우/동작원리(exportHTML 재현)/제약/버전.
- "LLM 미사용, 결정론, Desktop 샌드박스에서 번들 스크립트 실행(단계 0과 동일 성격의 예외)" 명시.
- 향후 `--profile`(it-staff/dev/advanced) 로드맵 표 포함.

### 오케스트레이터 — `skills/threat-scan-orchestrator/SKILL.md`

- 스캔 순서 표에 **단계 11 `@html-report-generator`** 행 추가(단계 10 뒤).
- 단계 11 설명 문단: 단계 10 산출 JSON 후 수행, 스크립트 실행 예외 단계, **별도 요구 없으면 JSON + KO HTML 함께 출력**.
- 참조 목록에 `references/sub-skills/html-report-generator.md` 추가.
- 제약 §:
  - "단계 0만 셸 허용" → **"단계 0·11만 스크립트/파일 생성 허용"**.
  - "파일 생성 금지(JSON 출력만)" → **단계 1–10으로 한정**. 단계 11은 HTML 파일 생성(입력 JSON 무변형 임베드).

## 완료 조건 (검증 가능)

- [x] `skills/html-report-generator/SKILL.md` 존재.
- [x] 오케스트레이터 스캔 순서에 `| **11** | **\`@html-report-generator\`** |` 행 존재.
- [x] 제약 §에 "단계 0·11" 셸/파일 허용 문구, 단계 1–10 한정 문구 존재.

## 검증

```bash
test -f skills/html-report-generator/SKILL.md && echo OK
grep -q "html-report-generator" skills/threat-scan-orchestrator/SKILL.md && echo OK
grep -q "단계 0·11" skills/threat-scan-orchestrator/SKILL.md && echo OK
```
