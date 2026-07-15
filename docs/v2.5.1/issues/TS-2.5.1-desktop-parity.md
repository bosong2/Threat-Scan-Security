# TS-2.5.1 — Desktop Parity 패치 (v2.5.0 Code 강화로 인한 Desktop 품질 회귀 복구)

**Title:** v2.5.0 Code측 강화 과정에서 Desktop 모드의 스키마 준수·번역·커버리지가 회귀한 문제를
Desktop 전용 결정론 장치로 복구
**Component:** `skills/threat-scan-orchestrator/SKILL.md`(공유부·Desktop 섹션) ·
`scripts/enumerate_tree.py`(신규) · `scripts/validate_report_schema.py`(신규) ·
`dictionary/security-template.html` · `skills/bilingual-translator/SKILL.md`
**Severity:** High (Desktop 스캔 결과가 보안 판단 근거로 사용 불가 수준 — 동일 대상에 Code=DISABLE vs Desktop=REVIEW)
**Reporter:** 011.DeviceExceptionManager 동일 대상 양 모드 스캔 대조, 2026-07-15
**증거:** `scanreport-20260715100000-desktop.{json,html}` vs `scanreport-20260715203013-code.{json,html}`

---

## 1. 증상 (동일 저장소 양 모드 스캔 대조)

| 항목 | Desktop | Code |
|------|---------|------|
| 스캔 파일 / markdown 인식 | 112/135 · **md 2개** | 166/166 · md 49개 |
| file_statistics | **자기모순** (항목 합 ≈38 ≠ total 135) | 정합 |
| 모델 유효성 (단계 4.6) | **"ML 아티팩트 없음" 오해** — playbook 모델 pin 9건 전부 미탐 | 9건 (DEGRADED 3건 포함) |
| 프롬프트 최적화 (단계 7) | 0건 | 5건 |
| SBOM verdict | **"APPROVE" (발명 enum)** · lock drift High 미탐 | SUPPLY-001 High → 전파 DISABLE |
| 최종 판정 | Medium / REVIEW | **DISABLE** — 동일 대상 상반 판정 |
| KR 번역 | **역전**: enum 번역됨(금지) + prose 영문 방치(필수) | 계약 준수 |
| HTML 렌더 | 권장조치 본문 공백·code_fix 소실·SBOM 서브섹션 미표시 | 정상 |

단, compliance_tags는 Desktop에서도 형식·EN/KO 동일성 준수 — **스킬 본문에 명시된 규칙은 Desktop에도 전달됨**을 실증.
역으로 Desktop 정적 분석은 9건으로 Code(3건)보다 깊었음 — Code측 정적 커버리지 갭(OAuth 과대 스코프 High 미탐)도 함께 확인.

## 2. 근본 원인 (git 대조 v2.4.1↔v2.5.0으로 실증)

### 2.1 Desktop 상시 컨텍스트 앵커가 stale — 결정적 원인

Desktop dist 메인 SKILL.md(모델이 항상 보유하는 유일 문서 = 오케스트레이터 공유부)에서 확인:

- `### ⚠️ 필수: Schema V1.3 엄격 준수` / `### JSON 구조 (V1.3)` — **v2.5.0에서 V1.4로 미갱신**
- "스키마 및 문서 참조" 목록이 **v1.3/v1.2만 나열** — v1.4 문서·CTID가 references/docs에 복사는 됐으나 목록 미등재 → 모델이 읽을 계기 없음
- 메인 스킬에 **ID prefix 규약·recommendations 필드명·code_fix 객체 구조 앵커가 부재** — 전부 서브스킬에만 존재

v2.5.0 Phase 6가 Code측 참조 표만 갱신하고 양 모드 공유부를 누락. Compliance Tagging만 Desktop 섹션 노트가 있었고 — **앵커가 있던 것(태그)만 준수, 없거나 stale인 것은 전부 드리프트**. 스캔 결과와 정확히 일치.

### 2.2 번역 회귀 메커니즘

- v2.4.1 스펙은 "severity 등급 번역(Critical→심각)" — Desktop은 당시 스펙에 준수했고 품질 양호.
- v2.5.0에서 스펙을 정반대(enum 영문 유지)로 뒤집었으나 **변경이 서브스킬 본문에만 반영**, Desktop 절차에는 미전달(메인 스킬 "번역 참조"는 사전 파일 나열뿐).
- 대형 리포트 단일 컨텍스트 완역은 출력 토큰 압박 → prose 통째 생략(issue 제목만 번역). Code의 fragment 분할에 해당하는 장치가 Desktop에 없음.

### 2.3 파일 열거 도구 부재

Desktop 샌드박스에 Glob 없음 + 열거 스크립트 없음 → 커버리지가 LLM 수동 탐색에 의존.
file_statistics 자기모순·markdown 2/49가 증거. docs/playbooks 계층 발견(GUID 유출·모델 pin·프롬프트 이슈) 통째 누락.

### 2.4 Desktop JSON 스키마 위반 → HTML 렌더 실패 매핑

| 위반 | 정본 | 렌더 영향 |
|------|------|-----------|
| recommendations `title/description/references` | `action/rationale/finding_ids/rank` | 권장조치 본문 공백, 관련 발견 칩 소실 |
| `code_fix` 문자열 | 객체 `{language,before,after,note}` | codeFixBlock `typeof!=='object'` → 전부 소실 |
| sbom `vulnerabilities/license_issues/supply_chain_risks` | `vulnerability_findings/license_findings/supply_chain_findings` | 서브섹션 미표시(Version Risks만 렌더) |
| `graph_verdict.propagation_summary` | `rationale` | 최고위험 카드 근거 미표시 |
| ID `SCED-/SPT-/AGNT-/SBOM-` | `STATIC-/SENS-/AGENT-/VULN-·VER-·SUPPLY-` | 추적성 붕괴 |
| repository_summary `name/tech_stack/risk_level/counts` | 임의 필드 금지 | tech_stack 미렌더 등 |
| sbom `verdict:"APPROVE"`(KR "승인") | verdict 4종 화이트리스트 | 발명 enum — MASK 유형 재발 |

**HTML 템플릿 자체는 양 모드 동일 v2.5.0 최신본으로 무결** (canonEnum·배지·섹션순서 모두 존재).
템플릿 잔결함 2건: 푸터 `schemaVer:'V1.3'` 하드코딩, empty-state "v1.2 and v1.3" 문구.

## 3. 수정 명세 — 대책 D1~D5

> 원칙: 기존 LLM·셸 경계(단계 0·10.5·11만 셸 허용)를 **바꾸지 않고**, 그 안에서 결정론 장치를 Desktop에 이식한다.
> Desktop도 단계 0(clone/unzip)·11(HTML 생성)은 이미 스크립트를 실행한다.

### D1. 결정론 파일 열거 — `scripts/enumerate_tree.py` 신설 (공용)

- 단계 0 확장: 소스 준비 직후 `python3 references/scripts/enumerate_tree.py <target> --out file-manifest.json` 실행 (Desktop·Code 공통, repo에서는 `scripts/` 경로).
- 산출(stdlib-only·결정론): 파일 전체 목록(제외: node_modules/.git/.next/dist/build/vendor), **`file_statistics` 정본 포맷 직접 산출**, 민감/위험 파일 후보 플래그(.env·*.pem·키워드), 매니페스트·lock 파일 식별, AI 구성요소 경로 목록(게이트 입력 재사용).
- 소비 계약: 단계 1(repo-indexer)은 manifest 통계를 **그대로** repository_summary에 사용(LLM 산수 금지 → 자기모순 해소). 단계 2–8은 "manifest에 있는 파일만·전부"를 커버리지 기준으로 분석.
- Code 모드: Glob과 병행, `_meta.files_total` 정본·프로브 보조로 재사용.

### D2. Desktop 출력 계약 앵커 복구 — 오케스트레이터 공유부·Desktop 섹션

1. **stale 앵커 갱신 (공유부)**: `출력 형식` 절 V1.3→**V1.4**(compliance_tags·ai_agent_scope 반영), "스키마 및 문서 참조" 목록에 v1.4 2종+CTID 2종 등재(v1.3/v1.2는 legacy 표기).
2. **단계별 출력 계약 카드 신설** (~10줄, 공유 출력형식 절): 단계→ID prefix→필수 필드/구조 컴팩트 표
   — `recommendations{action,rationale,finding_ids,rank,priority}` · `code_fix=객체` · sbom 배열명 4종 정본 ·
   `graph_verdict{security_verdict,rationale,worst_component}` · enum 13종 영문 · ID prefix 전표.
3. **재독 의무 (Desktop 섹션)**: 각 단계 시작 시 해당 `references/sub-skills/<name>.md` 재독 + 산출 직전 계약 카드 대조.
4. **자기검증 3줄 (Desktop 섹션)**: 단계 산출 후 ID prefix / 필수 필드 / enum 영문 self-check.
   ※ BUG-02 준수: Code 전용 명칭(tss-·SCAN_TMP) 사용 금지, 공유부/Desktop 섹션에만 반영.

### D3. 결정론 스키마 검증기 — `scripts/validate_report_schema.py` 신설 (공용)

- 단계 11(HTML 생성) 직전 실행 — Desktop 최초의 결정론 강제 게이트. Code Phase 4(a)에도 태그 validator와 나란히 추가.
- 검사 항목: ① finding ID prefix 규약, ② recommendations 필수 필드, ③ code_fix 객체 구조,
  ④ sbom 정본 배열명(비정본 감지), ⑤ graph_verdict 정본 필드, ⑥ verdict 화이트리스트(finding·sbom —
  APPROVE/MASK/KEEP류 발명 차단), ⑦ enum 13종 영문+EN/KO 동일, ⑧ **KR prose 완역 휴리스틱**
  (korean_report의 description/recommendation/deep_dive_result 한글 문자 비율 < 임계(예: 30%) → 실패),
  ⑨ repository_summary 임의 필드 경고.
- exit 0/1/2 + `--json`. 위반 시 모델이 단계 9/10 산출물 교정 후 재검증(1회 루프), 재실패 시 위반 목록과 함께 보고.

### D4. 번역 회귀 복구

- **Desktop 섹션 단계 10 전용 지시** 신설: "모든 finding의 description/recommendation/deep_dive_result/detail을
  한국어로 **완역**(영문 문장 잔존 금지). enum 13종·compliance_tags·코드·경로·ID는 원형 유지."
- **카테고리 단위 순차 번역** 지침(Code fragment의 Desktop 이식): 한 카테고리를 번역·확정한 뒤 다음 카테고리로 —
  대형 리포트에서 출력 압박으로 인한 통째 생략 방지.
- `skills/bilingual-translator/SKILL.md`에 "완역 의무" 1줄 강조(양 모드 공유): "서술 필드의 부분 번역·생략은 실패로
  간주 — 카테고리별로 나눠서라도 전량 번역한다."
- D3-⑧이 미번역을 기계적으로 검출.

### D5. 템플릿 읽기측 폴백 (이미 생성된 리포트 구제 — canonEnum과 동일 원칙, 생성측이 정본)

- `renderRecs`: `r.action||r.title`, `r.rationale||r.description`, `r.finding_ids||r.references`
- `codeFixBlock`: 문자열 code_fix → 단일 코드블록(after)으로 렌더
- `renderSbom`: `vulnerability_findings||vulnerabilities` · `license_findings||license_issues` ·
  `supply_chain_findings||supply_chain_risks` + `sbom.summary` detail 렌더
- graph_verdict rationale 폴백 체인에 `||gv.propagation_summary`
- 푸터 `schemaVer` 'V1.3' 하드코딩 → scanner_version 기반 동적(또는 V1.4), empty-state 문구 "v1.2–v1.4" 갱신
- `docs/index.html`은 심링크 — 자동 동기.

## 4. 호환성 판정 (v2.5.0 신규 기능 ↔ Desktop)

| 항목 | 판정 |
|------|------|
| Compliance Tagging | Desktop 호환 **정상**(이번 스캔 실증) — 변경 불요 |
| Schema V1.4 | strict superset이라 호환 문제 없음. Desktop 앵커 stale이 문제 → D2 |
| HTML 템플릿 | 양 모드 동일본 확인 — 무결. D5는 방어적 폴백 |

## 5. 검증

1. `enumerate_tree.py`: 이 repo 대상 실행 → file_statistics 합계 정합, AI 구성요소 목록이 Phase 0(d) 탐지와 일치.
2. `validate_report_schema.py`: (a) Code 리포트(20260715203013) → REL-002 "Unknown" severity·ai_agent_scope 번역 2건만 검출,
   (b) Desktop 리포트(20260715100000) → §2.4 위반 전체 클래스별 검출 + KR prose 미번역 검출, (c) 정상 픽스처 → exit 0.
3. Desktop 빌드 회귀: dist 메인 SKILL.md에 V1.4 앵커·계약 카드·v1.4 참조 목록 존재, `tss-`=0/`SCAN_TMP`=0.
4. Desktop 증거 리포트를 신 템플릿으로 재렌더 → 권장조치 본문·code_fix·SBOM 서브섹션·최고위험 근거 표시 복구(D5).
5. Desktop 실스캔 1회(사용자): 커버리지(markdown 수)·판정·KR 완역·validator 통과 확인.

## 6. Dual-Mode 반영 체크리스트

| 파일 | 계층 | 비고 |
|------|------|------|
| `scripts/enumerate_tree.py` · `validate_report_schema.py` | 🟢 공용 신규 | 빌드 `*.py` 복사 규칙으로 dist 자동 포함 |
| `skills/threat-scan-orchestrator/SKILL.md` | 공유부+Desktop 섹션+Code 섹션 | 공유부(출력형식·참조)·Desktop 섹션(재독·자기검증·번역·순차) 수정, Code 섹션은 단계 0/11 스크립트 배선만 |
| `skills/bilingual-translator/SKILL.md` | 🟢 공용 | 완역 의무 1줄 |
| `dictionary/security-template.html` | 🟢 공용 | D5 폴백 (docs/index.html 심링크 자동) |
| Desktop zip 재빌드·재업로드 | — | **필수** |
| 버전 | — | 2.5.1 (VERSION·plugin.json·help·CHANGELOG) |
