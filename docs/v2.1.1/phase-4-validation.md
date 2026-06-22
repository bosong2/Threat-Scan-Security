# Phase 4 — 버전·빌드·검증 (Goal Prompt)

> 선행 의존성: **Phase 1–3**.

## 🎯 목표 (Objective)

VERSION을 2.1.1로 올리고 배포 패키지를 재생성하며, 전 계층 일관성·하위호환·EN/KO를 회귀 검증한다.

## 📥 참조 입력 (Inputs)

- `VERSION`, `build_claude_desktop.sh`
- Phase 1–3 산출물 전체
- 회귀 기준: v2.1.0 산출 페이로드

## 🔧 작업 (Tasks)

1. **`VERSION`**: `2.1.0` → `2.1.1`.
2. **`build_claude_desktop.sh`**: VERSION 자동 참조 — 구조 변경 불필요. 빌드 실행으로 검증.
3. **회귀 검증**: 신규 필드(id/rank/finding_ids)만 추가됐는지, 금지 필드 0, EN/KO 병행, finding_ids가 실제 존재하는 finding만 참조하는지.

## ✅ 완료 조건 (Acceptance) — 검증 가능

- **스키마 일관성**: `grep "REC-NNN"` 이 스키마 §17·report-merger 표·enforcement에 모두 존재. §15 "정수 금지" 문구 확인.
- **뷰어**: index.html script `new Function()` 파싱 통과. 샘플 로드 무오류.
- **하위호환**: id/rank/finding_ids 없는 v2.1.0 페이로드 정상 렌더.
- **빌드**: `bash build_claude_desktop.sh` 성공, 로그 `VERSION=2.1.1`, `threat-scan-security.zip` 재생성.
- **EN/KO**: 한글 보고서에서 action/rationale/category만 번역, id/rank/finding_ids 원형 유지.

## 🔗 선행 의존성

Phase 1–3 완료.
