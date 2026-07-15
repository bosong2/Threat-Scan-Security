# Phase 3 — 결정론 스키마 검증기: `validate_report_schema.py` + 단계 11 배선 (D3)

## 목표

Desktop의 "결정론 강제 계층 부재"를 메우는 핵심. 단계 11(셸 허용) 직전에 리포트 전체 스키마를
기계 검증하고, 위반 시 모델이 교정 후 재검증하는 게이트를 양 모드에 배선한다.

## 3-A. `scripts/validate_report_schema.py` (신규 — stdlib-only)

CLI: `python3 scripts/validate_report_schema.py <report.json> [--json]` · exit 0=clean / 1=errors / 2=warnings-only

검사 항목 (Desktop 증거 리포트의 위반 클래스 전체를 커버):

| # | 검사 | 수준 |
|---|------|------|
| 1 | finding ID prefix 규약 (배열→prefix 매핑: static→STATIC-, sensitive→SENS-, agent_policy→AGENT-, relationship→REL-, model_validity→MODEL-, prompt→OPT-, sbom vuln/lic/ver/supply→VULN-/LIC-/VER-/SUPPLY-, recommendations→REC-) | error |
| 2 | recommendations 필수 필드: `action`·`rationale`·`finding_ids`(비어있지 않음) 존재, `title`/`description`/`references` 사용 시 error(비정본 별칭) | error |
| 3 | `code_fix`가 문자열이면 error (객체 {language?,before?,after,note?} 요구) | error |
| 4 | sbom 비정본 배열명(`vulnerabilities`/`license_issues`/`supply_chain_risks`) 존재 시 error | error |
| 5 | `graph_verdict`에 `security_verdict` 부재(+`verdict`만 존재) 또는 `rationale` 부재(+`propagation_summary`만 존재) → error | error |
| 6 | verdict 화이트리스트: finding verdict ∈ 4종, sbom verdict 필드는 존재 자체 경고+비정본 값 error (APPROVE/MASK/KEEP 차단) | error |
| 7 | enum 13종 영문 검사(한글 값 감지) + EN/KO enum 동일성 | error |
| 8 | **KR prose 완역 휴리스틱**: korean_report의 `description`/`recommendation`/`deep_dive_result`/`detail` 문자열에서 한글 문자 비율 계산 — 전체 서술 텍스트의 한글 비율 < 30% → error("korean_report prose not translated"), 30–60% → warning | error/warn |
| 9 | repository_summary 임의 필드(`name`/`tech_stack`/`total_findings`/`critical~low` 카운트) | warn |
| 10 | scan_date가 `T00:00:00Z`/`T10:00:00Z` 같은 정각 의심값 | warn |

구현 노트:
- compliance_tags 검사는 기존 `validate_compliance_tags.py` 소관 — 중복 구현하지 않음(별도 실행).
- 한글 비율: `len([c for c in text if '가'<=c<='힣']) / max(1, len([c for c in text if c.isalpha()]))` 방식.
- `--json` 기계 판독 출력(오류 클래스별 카운트) — 오케스트레이터가 교정 대상 파악에 사용.

## 3-B. 테스트 픽스처

`tests/fixtures/`에 추가:
- `schema-valid.json` — 정본 준수 소형 리포트 → exit 0 (기존 `valid-v14.json` 확장 재사용 가능)
- `schema-violations.json` — 위 검사 1~8 클래스별 위반 각 1건 → 각각 구별 메시지로 검출, exit 1
- 실증 검증: Desktop 증거 리포트(`scanreport-20260715100000-desktop.json`)로 실행 시
  ID·recommendations·code_fix·sbom 배열명·graph_verdict·APPROVE·KR 미번역이 전부 검출되어야 함
  (픽스처로 커밋하지 않고 검증 절차로만 사용 — 실데이터 포함 금지).

## 3-C. 단계 11 배선 (양 모드)

**Code 섹션** — Phase 4(a)를 확장:
```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/validate_report_schema.py" "<최종 scanreport JSON>"
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/validate_compliance_tags.py" "<최종 scanreport JSON>"
# 둘 중 하나라도 exit 1 → 위반 클래스를 보고, 해당 단계 산출물(주로 9/10) 교정 후 1회 재검증.
# 재실패 → 위반 목록과 함께 중단. exit 2(warn-only) → 경고 요약 후 진행.
```

**Desktop 섹션** — 단계 11 절차에 동일 지시(references/scripts 경로):
"HTML 생성 전 `python3 references/scripts/validate_report_schema.py <report.json>` 와
`validate_compliance_tags.py`를 실행한다. 오류 발견 시 지적된 단계 산출물을 교정하고 1회 재검증
후 진행한다. 이 검증은 결정론 스크립트로 단계 0·11과 동일한 셸 허용 예외다."

## 완료 조건 (검증 가능)

- [ ] `schema-valid.json` exit 0 / `schema-violations.json` 클래스별 구별 메시지 + exit 1.
- [ ] Desktop 증거 리포트 실행 → §3-A 표의 1~8 전 클래스 검출 (특히 KR prose 미번역).
- [ ] Code 증거 리포트(20260715203013) 실행 → 경미 항목만(REL-002 severity "Unknown" 등) — 대량 오탐 없음.
- [ ] 오케스트레이터 Code·Desktop 양 섹션에 배선 존재, BUG-02 오염 0.
- [ ] dist에 `references/scripts/validate_report_schema.py` 포함.
