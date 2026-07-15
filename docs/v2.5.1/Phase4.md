# Phase 4 — HTML 템플릿 읽기측 폴백 (D5)

## 목표

이미 생성된 Desktop 리포트(비정본 필드)를 구제하는 읽기측 관용 폴백을 추가한다.
canonEnum과 동일 원칙 — **생성측이 정본이며, 폴백은 하위호환 표시 장치일 뿐**(신규 산출물은
Phase 2·3이 정본을 강제).

**대상 파일:** `dictionary/security-template.html` (docs/index.html은 심링크 — 자동 동기)

## 4-A. 렌더러 폴백 4곳

1. **`renderRecs`** — Desktop 별칭 폴백:
   - `r.action || r.title`, `r.rationale || r.description`
   - 관련 발견 칩: `r.finding_ids || r.references` (둘 다 배열 — scrollToFinding 동작 동일)
2. **`codeFixBlock`** — 문자열 code_fix 수용:
   - `typeof cf === 'string'` → `codeBlock(t('codeFix'), cf, '', 'cf-after')` 단일 블록으로 렌더
   - 객체 경로는 기존 그대로
3. **`renderSbom`** — 배열명 별칭 + summary:
   - `vf = sbom.vulnerability_findings || sbom.vulnerabilities || []`
   - `lf = sbom.license_findings || sbom.license_issues || []`
   - `scf = sbom.supply_chain_findings || sbom.supply_chain_risks || []`
   - `sbom.summary` 존재 시 `detail()` 렌더 (integrity_check류와 나란히)
4. **graph_verdict rationale 폴백 체인** (`renderSummary`·`renderGraphVerdictCard` 2곳):
   - `gv.rationale || gv.summary || gv.description` → `... || gv.propagation_summary`

## 4-B. 잔결함 2건

1. **푸터 `schemaVer: 'V1.3'` 하드코딩** (`renderFooter`) →
   `compliance_tags` 존재 여부 또는 scanner_version(V2.5+)으로 'V1.4'/'V1.3' 동적 표기
   (단순화 허용: 'V1.4' 고정 + legacy 리포트는 그대로 — 구현 시 판단, 하드코딩 'V1.3'만 제거).
2. **empty-state 문구** "Supports v1.2 and v1.3 schema" → "Supports v1.2–v1.4 schema" (data-en/data-ko 양쪽).

## 완료 조건 (검증 가능)

- [ ] 템플릿 `<script>` 추출 후 `node --check` SYNTAX OK.
- [ ] Desktop 증거 리포트(`scanreport-20260715100000-desktop.json`)를
      `python3 scripts/generate_html_report.py ... --lang ko`로 재렌더:
      - 권장 조치 카드에 본문(title/description 폴백)과 관련 발견 칩(references 폴백) 표시
      - code_fix 문자열이 코드블록으로 렌더
      - SBOM에 Vulnerabilities/License Issues/Supply Chain Risks 서브섹션 표시
      - 최고 위험 컴포넌트 카드에 근거(propagation_summary) 표시
- [ ] Code 증거 리포트 재렌더 — 기존 표시와 회귀 없음(정본 필드 우선 확인).
- [ ] `readlink docs/index.html` 심링크 불변, dist 템플릿에 폴백 반영.
