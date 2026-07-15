# Phase 2 — 리포지토리 요약/컴포넌트 카드 렌더 복구 (문제 ②)

## 목표

`renderRepoSummary`가 스키마 V1.3 정본 필드(`description`/`key_components`/`risk_summary`/`file_statistics`/`sensitive_files_detected`)를 **그대로** 렌더하되, 비정본 별칭(`overview`/`key_concerns`/`risk_level`)이 와도 **공백 대신 데이터**로 채우도록 폴백을 추가한다. 동시에 생성 스킬이 정본 필드명으로 emit하도록 가이드를 강제한다.

## 대상 파일

- `docs/index.html` / `dictionary/security-template.html` — `renderRepoSummary`(라인 ~746), `renderSummary`의 `graph_verdict` 처리(라인 ~667)
- `skills/repo-indexer/SKILL.md`
- `skills/report-merger/SKILL.md`

## 배경 데이터 (happy 리포트 실측)

```
repository_summary = { overview, risk_level, key_concerns, graph_verdict }   ← 실제
템플릿 기대        = { description, risk_summary, key_components, file_statistics, sensitive_files_detected, graph_verdict }
```

`key_concerns`(보안 우려 목록)와 `key_components`(아키텍처 컴포넌트)는 **의미가 다르다**. 단순 별칭 매핑 시 컴포넌트 카드에 보안 우려가 잘못 들어간다 → **별칭별로 적절한 라벨**로 렌더한다.

## 작업

### 2-A. 템플릿 폴백 (양 뷰어 동일)

`renderRepoSummary(s)` 수정:

1. **설명 카드**:
   - `var desc = s.description || s.overview;` → 있으면 렌더.
   - `var riskSummary = s.risk_summary || s.risk_level;` → 있으면 보조 줄.
2. **컴포넌트/요약 카드**:
   - `key_components`가 있으면 기존대로 컴포넌트 태그.
   - 없고 `key_concerns`가 있으면 **별도 라벨**(예: `t('keyConcerns')` = "주요 우려사항")로 우려 리스트 렌더 — 컴포넌트로 위장하지 말 것.
   - `file_statistics`가 있으면 파일 통계 칩(총 파일/언어별) 렌더(현재 미사용 → 추가). 없으면 생략.
   - `sensitive_files_detected` 기존 유지.
   - 모든 소스가 비면 `noData`.
3. i18n: `keyConcerns` 키를 EN/KO 사전(템플릿 내 `t` 테이블, 라인 ~327/359 인근)에 추가.

### 2-B. graph_verdict 경로 확인

`renderSummary`(라인 667)·`renderGraphVerdictCard`는 이미 `rs.graph_verdict`를 읽음 → happy 리포트의 `graph_verdict`(security_verdict/worst_component/rationale)가 정상 표시되는지만 확인(회귀 점검). 변경 불필요 예상.

### 2-C. 스킬 정본 강제

1. `skills/repo-indexer/SKILL.md`(라인 42~) 출력 예시가 이미 `description`/`key_components`/`sensitive_files_detected`/`file_statistics` 정본 → **출력 가이드에 "필드명 정확히 준수, `overview`/`key_concerns` 사용 금지" 명문 1줄 추가**.
2. `skills/report-merger/SKILL.md`: `repository_summary` 병합 시 정본 필드명 보존 규칙 + "비정본 별칭(`overview`/`key_concerns`/`risk_level`)을 정본으로 정규화" 지침 추가. (생성 측 1차 방어)

## 완료 조건 (검증 가능)

- [ ] happy 리포트 렌더 시 설명 카드에 `overview` 텍스트(slopus/happy ... )가 표시됨.
- [ ] happy 리포트 렌더 시 `key_concerns` 6건이 "주요 우려사항" 라벨로 표시(빈 카드 아님).
- [ ] 정본 필드(`description`/`key_components`/`file_statistics`)로 된 합성 리포트도 정상 렌더(회귀 없음).
- [ ] `graph_verdict`(DISABLE/bash-rpc-handler/rationale) 표시 유지.
- [ ] `keyConcerns` i18n 키가 EN/KO 양쪽 존재.
- [ ] 스킬 2종에 정본 필드명 준수 지침 추가.
- [ ] `diff docs/index.html dictionary/security-template.html` → 빈 출력.

## 주의

- `key_components` vs `key_concerns` 라벨 혼동 금지(레드 플래그).
- `esc()` 누락 없이 — 모든 사용자 데이터 출력에 escape 유지.
