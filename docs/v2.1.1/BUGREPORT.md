# Threat-scan-security v2.1.1 — 버그 리포트 & 패치 계획

> 기준선: v2.1.0. 발견 시점: 2026-06-22 정합성 검증 중.

## 발견 경위

v2.1.0 산출 샘플 `scanreport-20260622143000.json`(대상: notebooklm-mcp)을 뷰어(`docs/index.html`)로 검토하던 중, 최종 섹션 **권장 조치(recommendations)** 가 다른 finding 섹션과 달리 추적 불가능하다는 점이 드러났다.

- findings는 20건이 모두 고유 ID 보유: `STATIC-001~007`, `SKILL-001~003`, `AGENT-001~003`, `SENS-001~003`, `REL-001~003`, `MODEL-001`.
- 그러나 recommendations 7건은 `{priority, action, rationale}` 만 가지며, 고유 ID도 없고 어떤 finding에서 파생됐는지 매핑도 없다.
- 추가로 `priority` 값이 정수(1~7)로 출력됨 — 스키마는 문자열 심각도("Critical"/"High")를 기대.

## 버그 분류

| ID | 심각도 | 제목 | 영향 범위 | 담당 Phase |
|----|--------|------|-----------|------------|
| BUG-001 | High | recommendations 추적성 부재 (고유 ID·finding 역참조 없음) | schema §15/§17, report-merger, bilingual-translator, index.html | 1, 2, 3 |
| BUG-002 | Medium | recommendations.priority 타입 불일치 (정수 vs 문자열) | schema §15, SCHEMA_V1.3_ENFORCEMENT, report-merger | 1, 2 |
| BUG-003 | High | Deep Dive(심층 분석) 미실행 — 오케스트레이터 파이프라인에 호출 단계 없음 | orchestrator, securityreports-deepdive, schema, report-merger, bilingual-translator, index.html, build | 5 |

## 근본 원인

1. **스키마 §15 위임 방치** — `docs/claude-threat-scan-json-schema-v1.3.md` §15가 `"V1.2와 동일. 변경 없음."` 으로만 처리되어, recommendations 계약이 V1.2 시절(ID·finding_ids 없음) 그대로 남았다. ID 할당 규칙표(§17)에도 recommendations 행이 없다.
2. **rank/priority 개념 혼동** — 권장조치는 본질적으로 "순서(rank)"와 "등급(severity level)" 두 축을 갖는데, 스키마에 `rank` 필드가 없어 모델이 순번을 `priority`에 정수로 욱여넣었다. "정수 금지" 강제 규칙도 없었다.
3. **report-merger 산정 규칙 부재** — "권장사항 생성" 섹션이 우선순위 기준만 서술하고, 각 권장을 어떤 finding ID에 연결하라는 매핑 규칙이 없었다.

### BUG-003: Deep Dive 미실행

- **현상**: 샘플 레포트에 `deep_dive_result` 필드가 0개(High 5·Medium 10건 존재, `scan_depth=3`인데도). 심층 분석이 전혀 수행되지 않음.
- **근본 원인**: Claude Desktop에 패키징되는 메인 스킬은 `threat-scan-orchestrator`인데, 그 **스캔 순서 표(0~10단계)에 deep-dive 호출 단계가 없다.** Deep Dive는 "분석 전략" 섹션에 **개념으로만** 서술되어 실제 실행으로 연결되지 않았다.
- **이중 경로 문제**: `securityreports-deepdive` 스킬은 존재하지만 **다른 경로(`securityreports-scan`)에만** 연결돼 있고, 메인 오케스트레이터·빌드 Sub-Skill 참조표 어디에서도 호출되지 않아 **죽은 파일** 상태였다.
- **코드블럭 요구**: deep-dive 트리아지는 조치용 수정 코드를 포함할 수 있다. 이 코드가 **JSON 문자열 안에서 깨지지 않도록** 구조화 필드(`code_fix`)로 격리하고, 뷰어에서 **깔끔한 코드블럭**으로 렌더해야 한다.

## 패치 전략

확정 설계: **rank + priority 분리** + **finding_ids 역참조** + **REC-NNN ID**. 모든 신규 필드 optional → v1.2/v1.3 하위호환. 스키마 메이저 승급 없이 v1.3 보강.

| Phase | 작업 | 핵심 파일 |
|-------|------|-----------|
| 1 | 스키마 §15 계약 명문화, §17 REC-NNN 추가, enforcement 규칙·체크리스트 | `claude-threat-scan-json-schema-v1.3.md`, `SCHEMA_V1.3_ENFORCEMENT.md` |
| 2 | report-merger 생성 로직·ID표, bilingual-translator 번역 비대상 명시, 사전 라벨 | `report-merger/SKILL.md`, `bilingual-translator/SKILL.md`, `dictionary/*.json` |
| 3 | 뷰어 REC 뱃지·finding_ids 칩·앵커 스크롤, findingCard 앵커 id | `docs/index.html` |
| 5 | Deep Dive 파이프라인 편입 + code_fix 필드 + 코드블럭 안전/렌더 | `orchestrator`, `securityreports-deepdive`, schema, `index.html`, `build` |
| 4 | VERSION 2.1.1, 빌드 재생성, 회귀·스키마·EN/KO 검증 | `VERSION`, `build_claude_desktop.sh` |

### Deep Dive 코드 격리 계약 (BUG-003)

수정 코드는 finding의 **`code_fix` 구조화 필드**에만 둔다 (자유서술 prose에 섞지 않음):

```json
{
  "id": "STATIC-001",
  "status": "Confirmed",
  "deep_dive_result": "Level 1: ... Level 2: 입력 추적 ... Level 3: 악용 시나리오 ... 결론: Confirmed.",
  "code_fix": {
    "language": "typescript",
    "before": "const cmd = `mmdc -i ${userInput}`;\nexec(cmd);",
    "after": "execFile('mmdc', ['-i', userInput]);",
    "note": "Use execFile to avoid shell interpolation."
  }
}
```

- 모든 코드는 **JSON 문자열 값**으로만 존재 → 줄바꿈 `\n`, 큰따옴표 `\"`, 백슬래시 `\\` 표준 이스케이프.
- 마크다운 코드펜스(```` ``` ````)를 JSON 문자열에 넣지 않는다 — 뷰어가 자체적으로 `<pre><code>`로 렌더.
- 기존 금지 필드 `code_snippet`(자유서술)과 구분: `code_fix`는 deep-dive 전용 **승인된 구조화 필드**.

## 신규 recommendations 계약 (요약)

```json
{
  "id": "REC-001",
  "rank": 1,
  "priority": "Critical",
  "category": "Secret Management",
  "action": "Remove plaintext credential auto-login",
  "rationale": "...",
  "finding_ids": ["STATIC-001", "SENS-001"],
  "affected_files": [".cursor/config.json"]
}
```

- `priority` = 참조 finding들의 **최고 severity** (문자열, 정수 금지)
- `rank` = priority 내림차순 정렬 순번 (정수, 1=최우선)
- `finding_ids` = 근거 finding ID (기존 ID만, 최소 1개)

## 변경 파일 요약

| 계층 | 파일 |
|------|------|
| 스키마 | `docs/claude-threat-scan-json-schema-v1.3.md`, `docs/SCHEMA_V1.3_ENFORCEMENT.md` |
| 스킬 | `skills/report-merger/SKILL.md`, `skills/bilingual-translator/SKILL.md` |
| 사전 | `dictionary/security-terms-en-ko.json`, `dictionary/translation-rules-ko.json` |
| 뷰어 | `docs/index.html` |
| 빌드 | `VERSION`, `build_claude_desktop.sh` |
| Deep Dive (BUG-003) | `skills/threat-scan-orchestrator/SKILL.md`, `skills/securityreports-deepdive/SKILL.md` |
