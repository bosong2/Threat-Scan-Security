# Phase 3 — OSV 버튼 CVE 모달 + 영향 버전 정규화 (문제 ③)

## 목표

(③a) OSV 조회 결과 CVE 리스트를 **인라인 N개 + 초과 시 반응형 모달**로 표시하고 각 CVE를 `osv.dev/vulnerability/<id>`로 링크한다.
(③b) version 문자열이 스펙 범위(`^4.17.0`, `>=8.17.1`)여도 **concrete 버전으로 정규화**해 OSV에 질의하여 패키지 전체가 아닌 해당 버전 영향 CVE만 반환하도록 **템플릿에서** 보정한다.

## 대상 파일

- `docs/index.html` / `dictionary/security-template.html` — `vulnLinks`(~437), `checkOSV`(~452), `cveLink`(~501), `osv-more` 스타일(~169), 신규 모달 마크업·CSS·`normalizeVersion()`
- (SBOM 스킬은 본 Phase 범위 **외** — 사용자 결정 "템플릿만 보정")

## 작업

### 3-A. version 정규화 (③b)

신규 함수 `normalizeVersion(raw)`:

- 입력 예: `^4.17.0`, `~1.2.3`, `>=8.17.1`, `8.19.0`, `1.0.0 - 2.0.0`, `*`, `latest`.
- 규칙:
  - 선행 범위 연산자(`^ ~ >= <= > < =`)·공백 제거 후 첫 semver 토큰(`\d+\.\d+\.\d+`(-prerelease 허용)) 추출.
  - 추출 성공 → `{version: <concrete>, exact: false|true}` (원문이 순수 semver면 `exact:true`).
  - 추출 실패(`*`/`latest`/빈값) → `{version: null, exact:false}`.
- `checkOSV`는 `body.version`에 **정규화된 concrete 버전**만 넣는다. `version=null`이면 version 없이 패키지+ecosystem만 질의(전체) 하되 버튼/결과에 캐비엇 표시.

### 3-B. 캐비엇 표시 (③b)

- `vulnLinks` 버튼 data에 `data-verexact`(정규화 결과) 추가.
- 비-exact(범위에서 추정) 또는 `version=null`이면 결과 옆에 작은 캐비엇 배지(예: `≈범위` / title="명세 범위에서 추정된 버전 — lock 파일 확정 버전 권장") 노출.
- OSV는 concrete version 질의 시 해당 버전 영향분만 반환하므로, 정규화 자체가 "전체 취약점 표시" 문제를 크게 완화.

### 3-C. CVE 모달 UX (③a)

`checkOSV` 결과 렌더 분기 수정:

1. 수집된 `ids`(CVE/OSV id, dedup)에서:
   - `INLINE_MAX = 5` 이하 → 기존처럼 전부 인라인 클릭형 배지(`cveLink`).
   - 초과 → 상위 5개 인라인 + `+N 더보기` **버튼**(클릭 가능, `osv-more` 정적 텍스트 대체).
2. `+N 더보기` 클릭 → `openCveModal(pkg, version, ids)`:
   - 반응형 모달(오버레이 + 중앙 카드, `max-height` + 내부 스크롤, 모바일 폭 100% 대응).
   - 헤더: `<pkg>@<version>` + 총 CVE 수.
   - 본문: 전체 CVE 리스트, 각 항목 `osv.dev/vulnerability/<id>` 새 탭 링크(`rel="noopener noreferrer"`).
   - 닫기: X 버튼 · 오버레이 클릭 · ESC 키.
3. 모달 마크업은 1개를 재사용(body 끝에 hidden 컨테이너) 하고 내용만 갱신. export(정적 HTML)에서도 동작해야 하므로 외부 의존 없이 순수 JS/CSS.

### 3-D. CSS (양 뷰어 동일)

- `.osv-modal-overlay`, `.osv-modal`, `.osv-modal-hd`, `.osv-modal-list`, `.osv-more`(버튼화) 추가.
- 다크/라이트 변수(`var(--...)`) 재사용, 기존 디자인 토큰 일관성 유지.
- 반응형: `@media (max-width:480px)` 모달 풀폭·리스트 1열.

## 완료 조건 (검증 가능)

- [ ] `normalizeVersion('^4.17.0')` → `4.17.0`, `normalizeVersion('>=8.17.1')` → `8.17.1`, `normalizeVersion('8.19.0')` → `8.19.0(exact)`, `normalizeVersion('*')` → `null`. (브라우저 콘솔/단위 확인)
- [ ] 범위 스펙 패키지 OSV 클릭 시 concrete 버전으로 질의되어 캐비엇 배지 노출.
- [ ] CVE 6건↑ 패키지에서 `+N 더보기` 버튼 노출·클릭 → 모달에 전체 CVE, 각 클릭 시 `osv.dev/vulnerability/<id>` 새 탭.
- [ ] 모달 ESC·오버레이 클릭·X로 닫힘.
- [ ] 모바일 폭(≤480px)에서 모달·버튼 레이아웃 정상.
- [ ] `osv-more`가 정적 텍스트가 아닌 클릭 가능 요소.
- [ ] `diff docs/index.html dictionary/security-template.html` → 빈 출력.

## 주의

- OSV 라이브 질의는 **브라우저 런타임 한정**(스캐너 샌드박스엔 네트워크 없음). 생성 결정론에 영향 주지 않음.
- 네트워크 오류 폴백(기존 `catch` → fallback URL) 유지.
- 모달은 export된 정적 HTML 단독 열람 시에도 동작해야 함(번들 JS 외부 의존 금지).
