# Phase 2 — Desktop 출력 계약 앵커 복구 + 번역 회귀 복구 (D2 + D4)

## 목표

Desktop 드리프트의 결정적 원인인 **stale 앵커**(메인 스킬의 V1.3 출력 형식·v1.3-only 참조 목록·
산출 계약 부재)를 갱신하고, 번역 계약(enum 영문·prose 완역)을 Desktop 절차에 명시적으로 이식한다.

**대상 파일:** `skills/threat-scan-orchestrator/SKILL.md` (공유부 + Desktop 섹션),
`skills/bilingual-translator/SKILL.md` (1줄)

## 2-A. stale 앵커 갱신 (공유부 — Desktop dist에 살아남는 영역)

1. `## 출력 형식` 절: `### ⚠️ 필수: Schema V1.3 엄격 준수` → **V1.4** (v1.4 enforcement 참조로 교체),
   `### JSON 구조 (V1.3 — v1.2 완전 호환)` → **V1.4** — 구조 예시에 `compliance_tags`(finding 1곳)·
   `repository_summary.ai_agent_scope` 반영. 기존 금지 필드 목록 유지 + 태그 금지 변형 추가.
2. `## 스키마 및 문서 참조` 목록 갱신:
   - `references/docs/SCHEMA_V1.4_ENFORCEMENT.md` · `claude-threat-scan-json-schema-v1.4.md` (정본)
   - `references/docs/compliance-tagmap-distilled.md` · `compliance-tagging-deepdive.md` (CTID)
   - v1.3/v1.2 문서는 "(legacy 참조)" 표기로 유지.

## 2-B. 단계별 출력 계약 카드 신설 (공유 출력형식 절 — ~10줄 컴팩트 앵커)

```markdown
### 단계별 출력 계약 (요약 카드 — 산출 직전 반드시 대조)

| 단계 | ID prefix | 필수 구조 |
|------|-----------|-----------|
| 2 정적 | STATIC-NNN | severity/status 영문, code_fix는 객체 {language,before,after,note} |
| 3 바이너리 | BIN-NNN | 〃 |
| 4 스킬 | SKILL-NNN | verdict ∈ {INSTALL_OK,REVIEW,DISABLE,REMOVE} |
| 4.5 그래프 | REL-NNN | graph_verdict{security_verdict,worst_component,rationale} |
| 4.6 모델 | MODEL-NNN | model_effectiveness ∈ {VALID,DEGRADED,OBSOLETE,MODEL_LOCKED} |
| 5 민감 | SENS-NNN | masked_value만, verdict 4종만(MASK 금지) |
| 6 정책 | AGENT-NNN | — |
| 7 프롬프트 | OPT-NNN | 태그 금지 |
| 8 SBOM | VULN-/LIC-/VER-/SUPPLY-NNN | 배열명: vulnerability_findings/license_findings/version_risk_findings/supply_chain_findings. verdict 필드 발명 금지(APPROVE 등) |
| 9 병합 | REC-NNN | recommendations{action,rationale,finding_ids,rank,priority} — title/description/references 금지 |
| 10 번역 | — | enum 13종+compliance_tags 원형 유지, 서술 필드 완역 |
```

(정확한 표 내용은 v1.4 스키마 문서와 대조해 구현 시 확정 — 위 표가 기준 초안)

## 2-C. Desktop 섹션 — 재독 의무 + 자기검증

Desktop 실행 절차에 추가:

- **재독 의무**: "각 단계를 시작할 때 해당 `references/sub-skills/<name>.md`를 **다시 읽는다**.
  긴 스캔에서 앞서 읽은 내용에 의존하지 않는다."
- **자기검증 3줄**: "각 단계 산출 직후 확인 — ① ID prefix가 계약 카드와 일치하는가,
  ② 필수 필드가 존재하는가, ③ enum 값이 영문 정본인가. 불일치 시 즉시 교정 후 다음 단계로."

## 2-D. 번역 회귀 복구 (D4)

1. **Desktop 섹션 단계 10 전용 지시** 신설:
   - "모든 finding의 `description`/`recommendation`/`deep_dive_result`/`detail`/`issue`와
     repository_summary·graph_verdict의 서술 필드를 한국어로 **완역**한다. 영문 문장 잔존 = 실패."
   - "enum 13종(severity·status·verdict·security_verdict·priority·confidence·model_effectiveness·
     edge_type·component_type·target_type·pattern_type·risk_level·gitignore_status)과
     `compliance_tags`·ID·경로·코드·CVE는 원형 유지."
   - **카테고리 단위 순차 번역**: "english_report의 최상위 카테고리를 하나씩 — 한 카테고리를 완역해
     korean_report에 기록한 뒤 다음 카테고리로 진행한다. 전체를 한 번에 출력하려다 생략하지 않는다."
2. `skills/bilingual-translator/SKILL.md` 완역 의무 1줄 추가(양 모드 공유):
   "서술 필드의 부분 번역·생략은 실패로 간주한다 — 출력이 길면 카테고리별로 나눠서라도 전량 번역한다."

## 완료 조건 (검증 가능)

- [ ] `bash build_claude_desktop.sh` 후 dist 메인 SKILL.md에서:
      `grep -c "Schema V1.3 엄격"` = 0, `grep -c "V1.4"` ≥ 4, v1.4/CTID 4종이 참조 목록에 존재,
      "단계별 출력 계약" 카드 존재, "다시 읽는다" 재독 의무 존재, 완역·순차 번역 지시 존재.
- [ ] BUG-02: dist `tss-`=0, `SCAN_TMP`=0, `AskUserQuestion`=0.
- [ ] Code 섹션 동작 무변경(이 Phase는 공유부·Desktop 섹션·translator 스킬만 수정) — git diff로 확인.
