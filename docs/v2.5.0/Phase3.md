# Phase 3 — Schema V1.4 문서 세트 + CTID 디렉티브 정식 배치

## 목표

Schema V1.4(`compliance_tags` 추가)를 **문서로 확정**한다. v1.3 문서는 무수정 보존하고
v1.4 문서를 신설한다(v1.2→v1.3 관례). CTID 디렉티브 2건을 issues/에서 docs/ 정식 위치로 배치한다.
근거: [issues/SCHEMA_V1.4_COMPLIANCE_TAGS.md](issues/SCHEMA_V1.4_COMPLIANCE_TAGS.md) 전체.

> **경로 매핑 주의**: compliance PROMPT의 `references/docs/...`는 플러그인 캐시(Desktop dist)
> 기준 경로다. upstream repo에서는 `docs/`가 정본이며, Desktop 빌드가 `references/docs/`로 복사한다.

## 3-A. `docs/claude-threat-scan-json-schema-v1.4.md` (신설)

1. v1.3 문서(`docs/claude-threat-scan-json-schema-v1.3.md`) 구조를 복제해 기반으로.
2. **`compliance_tags` 필드 정의** — SCHEMA_V1.4 §2를 그대로 반영:
   - 필드명 `compliance_tags` 정확·소문자·복수형, `array of string`, optional
     (부재=legacy, `[]`=검증 후 해당 없음 — 의미 구분).
   - 요소 패턴 `^#(KISA|AILLM|TA)-[A-Z0-9]+(_[A-Z0-9]+)*$` (문자 그대로, 1회).
   - 0–4개, 유일, primary(근본원인) 우선 순서(순서는 의미론적 — 보존).
   - 로컬라이즈 없음 — korean_report byte-identical.
3. 허용 배치 8곳: `static_code_findings[]`·`binary_analysis_findings[]`·`skill_risk_findings[]`·
   `agent_policy_findings[]`·`sensitive_patterns[]`·`relationship_findings[]`·
   `model_validity_findings[]`·`sbom_analysis` 내 finding 객체.
   금지 배치: `scan_metadata`·`repository_summary`·`graph_verdict`·`prompt_optimization[]`·`recommendations[]`.
4. **Governed namespace 표(§2.3)와 AILLM 앵커 레지스트리(§6)를 verbatim 수록**
   (KISA 49·AILLM 9·TA 10, CWE-250/284 (assumed) 주석 포함).
5. 허용 배열별 finding 예시 각 1건에 `compliance_tags` 추가.
6. **`repository_summary.ai_agent_scope` optional 필드 등재** (Phase 2 연동):
   `"included" | "excluded"`, optional, 부재=게이트 미발동(legacy). 번역 비대상.
7. `scan_metadata.scanner_version` 예시 → `"Claude Threat Scan V2.5"`.

## 3-B. `docs/SCHEMA_V1.4_ENFORCEMENT.md` (신설)

1. v1.3 enforcement 규칙 **전부 무변경 승계** 선언 + v1.4 추가분 append 구조.
2. 태그 강제 규칙 (SCHEMA_V1.4 §3):
   - 형식·개수·유일·순서·대문자.
   - **금지 변형(§3.1)**: `tags`·`compliance`·`kisa_tags`·`kisaTags`·`control`·`controls`·
     `control_mapping`·`owasp_tags`, 소문자 네임스페이스, `#` 누락, `.`/`-` 구분자,
     issue/severity 문자열 내 태그 삽입, `#CWE-89`류(CWE/OWASP/ATLAS는 prose 전용).
   - **단계 규칙(§3.2)**: 태그 수정은 단계 8.5만 허용, 9–11 읽기전용. EN/KO parity.
     병합(9)은 verbatim 패스스루 + finding 내 dedup만.
3. **korean_report enum 불변 규칙 통합** (patch2 §3.3 — v1.3 개정 대신 v1.4에 흡수):
   - "priority는 등급 번역" 규칙 **폐지** 선언(v1.3의 해당 행은 legacy — v1.4에서 무효).
   - enum 필드 13종(severity·status·verdict·security_verdict·priority·confidence·
     model_effectiveness·edge_type·component_type·target_type·pattern_type·risk_level·
     gitignore_status) 값은 EN/KO 리포트 모두 영어 원문 — "EN/KO enum 값 diff = 0" 검증 항목.
   - verdict 정본 4종(INSTALL_OK/REVIEW/DISABLE/REMOVE) 화이트리스트 — `MASK`/`KEEP` 등
     발명 값은 스키마 위반, 병합 시 REVIEW 정규화.
4. V1.3.1 recommendations 추적성(id/rank/finding_ids) 규칙 승계 유지.

## 3-C. CTID 디렉티브 정식 배치

- `docs/v2.5.0/issues/compliance-tagmap-distilled.md` → **`docs/compliance-tagmap-distilled.md`** 복사.
- `docs/v2.5.0/issues/compliance-tagging-deepdive.md` → **`docs/compliance-tagging-deepdive.md`** 복사.
- issues/ 원본은 보존(이슈 이력). docs/가 스킬 참조 대상 정본.
- 스킬에서의 참조 경로: `${CLAUDE_PLUGIN_ROOT}/docs/compliance-tagmap-distilled.md`
  (env 미설정 시 repo `docs/`) — Desktop 빌드는 references/docs/로 복사됨.

## 3-D. `CLAUDE.md` 스키마 참조 갱신

- "Schema V1.3 불변 규칙" 절 → "Schema V1.4 불변 규칙"으로: v1.4 문서 2종을 정본으로,
  v1.3은 legacy 참조. `compliance_tags`는 유일한 v1.4 추가 필드(그 외 임의 필드 금지 유지).
- 금지 필드 목록에 태그 금지 변형(`tags`·`control_mapping` 등) 추가.

## 완료 조건 (검증 가능)

- [ ] `docs/claude-threat-scan-json-schema-v1.4.md`·`docs/SCHEMA_V1.4_ENFORCEMENT.md` 존재.
- [ ] v1.3 문서 2종 무수정: `git diff docs/claude-threat-scan-json-schema-v1.3.md docs/SCHEMA_V1.3_ENFORCEMENT.md` = 빈 출력.
- [ ] 태그 regex `^#(KISA|AILLM|TA)-[A-Z0-9]+(_[A-Z0-9]+)*$`가 두 v1.4 문서에 각각 정확히 1회.
- [ ] `docs/compliance-tagmap-distilled.md`·`docs/compliance-tagging-deepdive.md` 존재(issues/ 원본과 동일 내용).
- [ ] v1.4 스키마에 `ai_agent_scope` optional 등재.
- [ ] CLAUDE.md가 v1.4를 정본으로 참조.
