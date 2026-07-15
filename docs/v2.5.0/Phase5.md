# Phase 5 — 결정론 도구(validator·사전) + HTML 템플릿 통합 개편

## 목표

① `compliance_tags` 결정론 검증기와 제어명 사전을 신설하고,
② HTML 템플릿에 **3개 출처의 변경을 한 번에 통합**한다 — patch2(enum 정규화·스타일·섹션 재배치),
patch1 PART2(다크 코드뷰), compliance §4(태그 배지).
근거: [issues/SCHEMA_V1.4_COMPLIANCE_TAGS.md](issues/SCHEMA_V1.4_COMPLIANCE_TAGS.md) §3.3–§5,
[issues/TS-2.5.0_patch2.md](issues/TS-2.5.0_patch2.md) §3.5,
[issues/TS-2.5.0-patch1.md](issues/TS-2.5.0-patch1.md) PART 2.

**의존:** Phase 3(스키마 확정)·Phase 4(스킬이 태그를 방출해야 픽스처가 의미 있음).
**주의:** `docs/index.html`은 `dictionary/security-template.html`의 **심링크** — 템플릿만 수정.
patch1 PART2 코드는 캐시 검증본 이식(재발명 금지).

## 5-A. `scripts/validate_compliance_tags.py` (신설 — stdlib-only)

CLI: `python3 scripts/validate_compliance_tags.py <report.json> [--json]`

SCHEMA_V1.4 §3.3 의사코드 기반 구현(KNOWN 셋 그대로):
1. **regex hard-fail**: `^#(KISA|AILLM|TA)-[A-Z0-9]+(_[A-Z0-9]+)*$` 불일치 → error.
2. **unknown-control-ID warn**: 문법은 유효하나 governed 목록(49+9+10) 외 → warning(전방 호환).
3. **개수/유일성**: >4 또는 중복 → error.
4. **EN/KO parity**: 허용 8개 배열 전부에서 english_report와 korean_report의
   `compliance_tags`가 요소·순서까지 동일 → 불일치 error.
5. **금지 변형 탐지**: finding 객체에 `tags`·`kisa_tags`·`kisaTags`·`compliance`·`control`·
   `controls`·`control_mapping`·`owasp_tags` 존재 → error.
6. **배치 검사**: `compliance_tags`가 `scan_metadata`·`repository_summary`·`graph_verdict`·
   `prompt_optimization[]`·`recommendations[]`에 존재 → error.
7. exit code: 0=clean, 1=errors, 2=warnings-only. `--json`이면 기계 판독 요약.

**테스트 픽스처 3종** (`tests/fixtures/`):
- (a) `legacy-v13.json` — 태그 없는 v1.3 리포트 → exit 0.
- (b) `valid-v14.json` — 올바른 태그의 v1.4 리포트 → exit 0.
- (c) `violations-v14.json` — 규칙 클래스별 위반(형식·개수·중복·parity·금지변형·금지배치)
  각 1건 이상 → 각각 구별되는 메시지로 검출, exit 1.

## 5-B. 사전 확장 (`dictionary/security-terms-en-ko.json`)

- 최상위에 `compliance_controls` 키 신설(기존 `metadata`/`categories`/`terms`와 병렬):
  `{ "#KISA-1_1": {"en": "SQL Injection", "ko": "SQL 삽입"}, ... }` — **59태그 전부**
  (KISA 49 + AILLM 9 + TA 10, `A_B1` 포함).
- EN 명칭은 CTID-D 태그맵의 제어명, **KO 명칭은 KISA 공식 한국어 진단항목명**(KISA 소프트웨어
  보안약점 진단가이드 2021 표기)을 사용. AILLM·TA는 태그맵 명칭의 자연스러운 한국어 번역.
- 용도: 템플릿 tooltip·prose 전용. 태그 문자열 치환에 사용 금지.

## 5-C. HTML 템플릿 통합 개편 (`dictionary/security-template.html`)

### (1) patch2 — enum 표시 정규화 + 고정 스타일 (§3.5 명세 그대로)

- `ENUM_DISPLAY` 맵 + `canonEnum()` 함수 신설: 레거시 한글 enum(심각/높음/중간/낮음/정보/
  확인됨/완화됨/제거/비활성화/검토_필요 등)·미래 유입 값을 정본 영문으로 표시 정규화(하위호환).
- 적용 지점 5곳: `sevBadge()`(severity), `verdictBadge()`(verdict/security_verdict),
  findingCard status-badge(status/confidence), `renderRecs` priority, `renderSummary` worstVerdict.
- `verdictBadge` **unknown 폴백**: 정규화 후에도 4종 외 값이면 `verd-unknown` 클래스
  (중립 배경 CSS 신설) — 스타일 누락 구조적 차단.
- **SBOM 서브헤딩 영어 고정 5개**: `t('vulns')`→`'Vulnerabilities'`,
  `t('licenseIssues')`→`'License Issues'`, `t('versionRisks')`→`'Version Risks'`,
  `t('supplyChain')`→`'Supply Chain Risks'`, `t('priorityActions')`→`'Priority Actions'`.
  ko i18n 사전의 해당 키는 잔존 참조 없으면 제거. UI 크롬 i18n(섹션 제목 등)은 유지.
- **섹션 순서**: `renderReport()`에서 `renderRecs(...)`를 `renderRepoSummary(...)` 직후로 이동
  (영향 7개 영역 patch2에서 검토 완료 — 이 1곳 수정으로 충분. finding-ref 링크는 id 앵커 기반).

### (2) patch1 PART2 — 다크 코드뷰 (캐시 검증본 이식)

- `.code-block` 다크 테마 CSS: 배경 `#1e1e1e`, 테두리 `#30363d`, 텍스트 `#d4d4d4`,
  글꼴 10.5px, JetBrains Mono 우선. 토큰 색상 8종(`tk-key`#569cd6, `tk-str`#ce9178,
  `tk-com`#6a9955, `tk-num`#b5cea8, `tk-fn`#dcdcaa, `tk-prop`#9cdcfe, `tk-bool`#4fc1ff,
  `tk-punc`#808080). `.code-lang` 배지 다크 톤.
- `highlightCode(raw, lang)` 경량 하이라이터 + 헬퍼(`hlEsc`·`hlLang`·`HL_KW`·`HL_LIT`):
  js/ts/py/sh/json 감지, 정규식 토크나이저, **모든 토큰 텍스트 `hlEsc` 이스케이프(XSS-safe)**,
  재포맷/재들여쓰기 절대 금지. 미지원 언어는 다크 테마+이스케이프만.
- `codeBlock()`이 `esc(code)` 대신 `highlightCode(code, lang)` 호출.

### (3) compliance §4 — 태그 배지

- finding 카드의 severity 배지 인접에 태그별 배지: 텍스트=원시 태그 문자열,
  `title` tooltip=사전 `compliance_controls`의 제어명(리포트 표시 언어 기준 en/ko).
- 네임스페이스 색: `KISA` `#3a7bd5`, `AILLM` `#8a5cd6`, `TA` `#2ea860`,
  unknown-but-valid `#5a6173`. 기존 다크테마 토큰·표 오버플로 보호 준수.
- 필드 부재 또는 `[]` → 배지 행 자체를 렌더하지 않음("no tags" 표기 금지).
- 적용 렌더러: `findingCard`(공통) + `renderRelationship`·`renderSbom` finding 카드.

## 5-D. `scripts/generate_html_report.py` — `--coverage` 플래그

- 옵션 지정 시 태그로부터 **렌더 타임** KISA 카테고리 커버리지 표(§1–§7 × 발견/해당없음)를
  계산해 HTML에 섹션 추가. **JSON에 재기록 금지**(`findings_summary` 금지 원칙 유지).
- 미지정 시 기존 출력과 동일(회귀 없음).

## 완료 조건 (검증 가능)

- [ ] validator: 픽스처 (a)(b) exit 0, (c) 위반 클래스별 구별 메시지 + exit 1. `--json` 동작.
- [ ] 사전 `compliance_controls` 59개: `python3 -c "...len(d['compliance_controls'])"` = 59.
- [ ] 템플릿 JS `node --check` SYNTAX OK.
- [ ] 증거 리포트 재렌더(`python3 scripts/generate_html_report.py
      ~/sec/20260609-reviewOS-security/scanreport-20260715150007.json --lang ko`):
      patch2 8개 증상 전부 해소(REMOVE 스타일·전 섹션 영문 enum·MASK→verd-unknown·
      SBOM 영어 서브헤딩·우선순위 Critical) + 권장 조치가 리포지토리 요약 직후 + 다크 코드뷰.
- [ ] 픽스처 (b) 렌더: 태그 배지·tooltip·네임스페이스 색 표시, 태그 없는 finding은
      v2.4 출력과 동일(배지 행 없음).
- [ ] XSS: 하이라이터 출력에 span 태그 외 원시 `<` 0건(주입 샘플 테스트).
- [ ] `grep -n "t('vulns')\|t('licenseIssues')\|t('versionRisks')\|t('supplyChain')\|t('priorityActions')"
      dictionary/security-template.html` = 0건.
- [ ] `readlink docs/index.html` = `../dictionary/security-template.html` (심링크 불변).
