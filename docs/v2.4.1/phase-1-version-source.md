# Phase 1 — 버전 단일 진실원천화 (문제 ①)

## 목표

HTML 헤더의 버전 표기를 하드코딩(`V2.1`)에서 제거하고 `scan_metadata.scanner_version` 기반 동적 렌더로 전환한다. 동시에 스킬이 emit하는 `scanner_version` 리터럴을 `VERSION`과 동기화한다.

## 대상 파일

- `docs/index.html` (원천 뷰어)
- `dictionary/security-template.html` (배포 템플릿) — **위와 동일하게**
- `skills/report-merger/SKILL.md`
- `skills/threat-scan-orchestrator/SKILL.md`
- `VERSION`, `.claude-plugin/plugin.json`, `commands/threat-scan-help.md`, `CHANGELOG.md`

## 작업

### 1-A. 템플릿 타이틀·배지 동적화 (양 뷰어 동일)

1. `<title>Claude Threat Scan Report Viewer v2.1</title>`(라인 6) → 버전 리터럴 제거: `Claude Threat Scan Report Viewer` (또는 렌더 시 동적 치환). 정적 title은 버전 무관 문구로 고정.
2. `<span class="version-badge">V2.1</span>`(라인 276) → 빈 placeholder(`<span class="version-badge" id="versionBadge"></span>`)로 변경.
3. 렌더 함수(`renderReport`/메타 렌더, 라인 ~529 `scanner_version` 사용처 인근)에서 `scan_metadata.scanner_version`를 파싱해 배지에 주입한다.
   - `scanner_version` 예: `"Claude Threat Scan V2.4"` → 배지에 `V2.4`만 추출 표시(정규식 `/V?\d+(\.\d+)*/i` 매칭, 실패 시 전체 문자열 또는 `-`).
   - `scanner_version` 부재 시 폴백: 배지 숨김 또는 `-`.

### 1-B. 스킬 리터럴 동기화

1. `skills/report-merger/SKILL.md:56` 의 `"scanner_version": "Claude Threat Scan V2.1"` → `"Claude Threat Scan V2.4"`.
2. `skills/report-merger/SKILL.md:234` 의 레거시 예시 `V2.0` → 정합 점검(예시 일관성). 활성 템플릿(라인 56) 우선.
3. `skills/threat-scan-orchestrator/SKILL.md:276` 의 `"scanner_version": "Claude Threat Scan V2.1"` → `"Claude Threat Scan V2.4"`.
4. (선택, 별도 검토) `skills/securityreports-scan/SKILL.md:197`은 deprecated 스킬 → 동기화 대상에서 제외하되 주석으로 deprecated 명시 확인.

> 표기 규약: 마케팅 버전은 메이저.마이너(`V2.4`)로 유지하고 패치(`.1`)는 `VERSION`/`plugin.json`에만 반영(헤더 노이즈 방지). 단, **양쪽이 분리되지 않도록** `scanner_version` 문자열은 `V<major>.<minor>` 규칙을 주석으로 명문화.

### 1-C. 버전 범프

1. `VERSION` → `2.4.1`.
2. `.claude-plugin/plugin.json` `"version"` → `2.4.1`.
3. `commands/threat-scan-help.md` 버전 표기 → 2.4.1.
4. `CHANGELOG.md`에 v2.4.1 항목 추가(본 3종 수정 요약).

## 완료 조건 (검증 가능)

- [ ] `grep -n "V2\.1\|Report Viewer v" docs/index.html dictionary/security-template.html` → 하드코딩 버전 리터럴 0건.
- [ ] happy 리포트 렌더 시 배지에 `V2.4` 표시(스크린샷 또는 생성 HTML 내 `versionBadge` 텍스트 확인).
- [ ] `scanner_version` 없는 합성 JSON 렌더 시 배지가 깨지지 않고 숨김/`-`.
- [ ] `grep -rn '"scanner_version"' skills/report-merger/SKILL.md skills/threat-scan-orchestrator/SKILL.md` → 활성 항목 모두 `V2.4`.
- [ ] `cat VERSION` = `2.4.1`, `plugin.json` version = `2.4.1`.
- [ ] `diff docs/index.html dictionary/security-template.html` → 빈 출력.

## 주의

- 배지 추출 정규식이 `V2.4`·`2.4`·`Claude Threat Scan V2.4` 모두 안전 처리해야 함.
- 정적 `<title>`에 버전을 넣지 말 것(데이터 무관 시점에 렌더되므로 동적화 어려움 → 버전은 배지로 일원화).
