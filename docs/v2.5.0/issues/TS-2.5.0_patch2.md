# TS-2.5.0 Patch 2 — Bilingual 리포트 enum 표기 비일관 + 섹션 순서 변경

**Title:** korean_report enum 값 번역 비일관(섹션별 혼재) 제거 — "enum = 영어 고유명사 + 템플릿 고정 스타일" 원칙 확립 + 권장 조치 섹션 재배치
**Component:** `dictionary/security-template.html`(공유 템플릿) · `skills/bilingual-translator/SKILL.md`(공유 방법론) · `agents/tss-translator.md`(Code) · `docs/SCHEMA_V1.3_ENFORCEMENT.md` · `skills/sensitive-pattern-matcher/SKILL.md` · `skills/report-merger/SKILL.md`
**Severity:** Medium (기능 동작하나 리포트 신뢰성·가독성 저하 — 동일 리포트 안에서 등급 표기가 언어·스타일 혼재)
**Reporter:** ReviewOS-security 스캔 리포트 육안 검수, 2026-07-15
**증거 리포트:** `scanreport-20260715150007.json`(V2.4.1) · `scanreport-20260715135851.json` · `scanreport-20260715104652.json`

---

## 1. 증상 (사용자 관찰 8건)

| # | 섹션 | 관찰 | 기대 |
|---|------|------|------|
| 1 | 위험요소 대시보드 → 최고 위험 컴포넌트 카드 | verdict가 "제거"로 표기, 배지 배경 스타일 없음 | `REMOVE` + verd-remove 스타일 |
| 2 | 정적 코드 분석 | `CRITICAL` / `Confirmed` — **올바른 기준 표기**(영어 고유명사 + 고정 스타일) | (기준) |
| 3 | 스킬 보안 | "중간" / "확인됨" 한글 표기 | #2와 동일: `MEDIUM` / `Confirmed` |
| 4 | 민감 패턴 | `MASK` 라벨 — 스키마에 없는 임의 verdict, 배지 배경 스타일 누락 | 정본 verdict enum만 + 미지값 폴백 스타일 |
| 5 | 프롬프트 최적화 | "낮음" 한글 표기 | `LOW` (#2 컨셉) |
| 6 | SBOM | "우선 조치·취약점·라이선스 이슈·버전 위험·공급망 위험" 한글 서브헤딩 | 영어 고유명사 레이블(Priority Actions / Vulnerabilities / License Issues / Version Risks / Supply Chain Risks) + #2와 동일한 고정 스타일 |
| 7 | 연관관계 그래프 | "심각" 한글 표기 | `CRITICAL` (#2 컨셉) |
| 8 | 권장 조치 | "우선순위: 심각" | 값은 영어 고유명사: "우선순위: Critical" |

## 2. 근본 원인 (확정 — 실측 기반)

### 2.1 데이터 실측: korean_report 안에서 enum이 **부분 번역·혼재**

`scanreport-20260715150007.json`(V2.4.1) korean_report 실측:

```
severity: ['Critical','High','Info','Low','Medium','낮음','높음','심각','중간']   ← 혼재!
status:   ['Confirmed','확인됨']                                                  ← 혼재!
priority: ['낮음','높음','심각','중간']                                            ← 전부 번역됨
security_verdict: ['제거']                                                        ← 번역됨 (EN은 REMOVE)
verdict:  ['DISABLE','MASK','REMOVE','REVIEW']                                    ← MASK는 EN 원본에도 존재
```

`scanreport-20260715135851.json`은 verdict까지 번역됨: `['검토_필요','비활성화','제거']`.

**혼재가 생기는 메커니즘:** v2.4.1 분할 번역(Mode B)은 카테고리 5묶음을 **병렬 5개 translator**로 처리한다. 각 fragment가 enum 번역 여부를 독자적으로 판단 → 같은 리포트 안에서 카테고리(=화면 섹션)별로 언어가 갈린다. 증상 #2(영문 유지)와 #3/#5/#7(한글)의 차이가 정확히 fragment 경계와 일치한다.

### 2.2 지침 자체의 모순 — 번역기 잘못이 아니라 **명세가 번역을 지시**

`skills/bilingual-translator/SKILL.md`(양 모드 공유 단일 원천):

| 행 | 현행 지침 | 문제 |
|----|-----------|------|
| :72 | "recommendations.priority는 severity처럼 **등급 번역(Critical→심각)**" | 증상 #8의 직접 원인 — 명세 준수 결과 |
| :78 | "verdict 값: INSTALL_OK, REVIEW, DISABLE, REMOVE (대문자 그대로 유지)" | `security_verdict`(graph_verdict 내부)는 자구상 미포함 → 증상 #1 |
| :100 | 용어 사전 표: `Critical → 심각` | enum 값에도 적용되는 것으로 해석됨 |
| :217, :306 | 출력 예시가 `"severity": "높음"` | **예시 자체가 enum 번역을 시연** |
| :241 | 체크리스트 "모든 severity 값 일관되게 번역" | 증상 #3/#5/#7의 직접 원인 |

`docs/SCHEMA_V1.3_ENFORCEMENT.md:164`도 동일: "`priority`는 severity처럼 등급 번역(Critical→심각)".

`agents/tss-translator.md`(Code 전용)의 Rules는 "번역은 value 텍스트만, key 불변"뿐 — enum 값 예외를 명시하지 않아 fragment별 임의 판단을 유발.

즉 **severity/priority는 번역하라, verdict는 남겨라**는 이중 규칙 + fragment 병렬화가 겹쳐 섹션별 비일관을 만든다. LLM 번역의 자연 편차까지 더해져 같은 규칙조차 fragment마다 다르게 적용됐다.

### 2.3 `MASK` verdict — 번역 문제가 아닌 **생성 단계 스키마 위반**

`scanreport-20260715150007.json` **english_report**에서 `sensitive_patterns` SENS-002/004/005/006이 `verdict: "MASK"`를 가짐(다른 리포트에선 `KEEP`도 발명됨). Schema V1.3 verdict enum은 `INSTALL_OK / REVIEW / DISABLE / REMOVE` 4종뿐. `skills/sensitive-pattern-matcher/SKILL.md:110`은 verdict를 optional로 정의하며 예시는 `"REMOVE"`지만 **enum 화이트리스트를 명시하지 않아** LLM이 "마스킹하라"는 의미의 `MASK`를 발명했다.

### 2.4 템플릿 스타일 누락의 구조

`dictionary/security-template.html`:

- `sevBadge()`(:567): 원문 그대로 출력 + `sevClass()`로 색상 클래스. `sevClass`(:419)는 한글 별칭(심각/높음/중간/낮음)을 **방어적으로 매핑**해두어 한글 severity도 배경색은 입혀짐 — 텍스트만 한글로 노출 (#3/#5/#7).
- `verdictBadge()`(:572): `verd-<소문자 원문>` 클래스 생성. CSS에는 `verd-install_ok/review/disable/remove` 4종만 존재 → `verd-제거`, `verd-mask`는 **미정의 클래스 → 배경 스타일 없는 배지** (#1, #4).
- `.severity-badge` CSS(:129)에 `text-transform:uppercase` → 영문 값이면 "CRITICAL"로 표기 (#2의 기준 스타일).
- SBOM 서브헤딩(:1130~1160)은 `t('vulns')` 등 **템플릿 i18n 레이블**(ko 로케일 시 한글) — 데이터가 아니라 템플릿 설계 (#6).
- `renderRecs`(:1183): `t('priority')+': '+r.priority` — 값은 데이터 원문 그대로 → korean_report의 번역된 `심각`이 노출 (#8).

### 2.5 원인 매트릭스 (증상 → 원인 → 수정 계층)

| # | 원인 | 수정 계층 |
|---|------|-----------|
| 1 | 번역기가 `security_verdict` 번역(:78 자구 공백) + `verd-제거` 클래스 부재 | 번역 가드레일 + 템플릿 정규화·폴백 |
| 3, 5, 7 | 명세(:241)가 severity 번역 지시 + fragment별 편차 | 번역 가드레일(명세 개정) + 템플릿 정규화 |
| 4 | 생성 단계 verdict enum 미강제(`MASK` 발명) + `verd-mask` 클래스 부재 | 생성 가드레일(화이트리스트) + 템플릿 폴백 스타일 |
| 6 | 템플릿 i18n 설계(도메인 서브헤딩까지 한글화) | 템플릿 레이블 정책 변경 |
| 8 | 명세(:72)가 priority 등급 번역 지시 | 번역 가드레일(명세 개정) + 템플릿 정규화 |

## 3. 수정 명세

### 원칙 (사용자 확정)

1. **enum 값은 어떤 계층에서도 번역하지 않는다** — 영어 고유명사가 정본. 번역 가드레일로 원천 차단.
2. **표시 스타일은 템플릿이 고정** — 데이터에 뭐가 오든(구버전 리포트의 한글 enum 포함) 템플릿이 정규화·폴백해 항상 동일 스타일로 렌더.
3. 권장 조치 섹션을 **리포지토리 요약 바로 다음**으로 이동.

### 3.1 번역 가드레일 — `skills/bilingual-translator/SKILL.md` (양 모드 공유 원천)

**"번역하지 않는 항목"(§64)에 enum 통합 규칙 신설:**

```markdown
### 번역 금지 — 구조·등급 enum 값 (v2.5.0 가드레일)

아래 필드의 **값**은 등급/판정 enum으로, EN/KO 리포트 모두 영어 원문 그대로 유지한다.
korean_report에서도 절대 번역하지 않는다 (표시 언어 처리는 HTML 템플릿 계층의 책임):

severity · status · verdict · security_verdict · priority · confidence ·
model_effectiveness · edge_type · component_type · target_type · pattern_type ·
risk_level · gitignore_status

예: "severity": "Critical" → (KO에서도) "severity": "Critical"   ← "심각" 금지
    graph_verdict.security_verdict: "REMOVE" → "REMOVE"          ← "제거" 금지
    recommendations[].priority: "High" → "High"                  ← "높음" 금지
```

**동반 개정(모순 제거) — 반드시 함께:**

| 위치 | 현행 | 개정 |
|------|------|------|
| :72 | "priority는 severity처럼 등급 번역(Critical→심각)" | "priority는 enum — 번역 금지, 원문 유지" |
| :78 | "verdict 값: … 대문자 그대로 유지" | 위 통합 규칙으로 흡수(`security_verdict` 포함 명시) |
| :100 용어 표 | `Critical → 심각` | 표에 주석: "**서술 문장 내 단어 번역용**. JSON enum 값에는 적용 금지" |
| :217, :306 예시 | `"severity": "높음"` | `"severity": "High"` 로 예시 교체 |
| :241 체크리스트 | "모든 severity 값 일관되게 번역" | "모든 enum 값(severity 등)이 EN/KO 동일(영문 원문)인지 확인" |

### 3.2 Code 에이전트 — `agents/tss-translator.md`

Rules에 추가 (Mode A/B 공통, fragment별 편차 차단):

```markdown
- **enum 번역 금지(강제)**: severity/status/verdict/security_verdict/priority/confidence/
  model_effectiveness/edge_type/component_type/pattern_type 값은 영어 원문 그대로 출력한다.
  korean_report에서도 동일. (표시 언어는 템플릿 책임 — SKILL.md § 번역 금지 참조)
```

### 3.3 스키마 강제 문서 — `docs/SCHEMA_V1.3_ENFORCEMENT.md`

- §2.6(:164) "priority는 severity처럼 등급 번역(Critical→심각)" → "**priority는 enum — 번역 비대상**"으로 개정.
- 신규 절 "korean_report enum 불변 규칙": 위 3.1 필드 목록 + "EN/KO enum 값 diff = 0" 검증 항목 추가.

### 3.4 생성 가드레일 — verdict 화이트리스트 (`MASK`/`KEEP` 발명 차단)

- `skills/sensitive-pattern-matcher/SKILL.md`(:110 근처): "verdict는 `INSTALL_OK / REVIEW / DISABLE / REMOVE` **4종만 허용**. `MASK`·`KEEP` 등 임의 값 금지. '마스킹 필요' 의미는 verdict가 아니라 `recommendation` 텍스트로 서술."
- `skills/report-merger/SKILL.md` 체크리스트: "모든 finding.verdict ∈ {INSTALL_OK, REVIEW, DISABLE, REMOVE} — 비정본 값은 병합 시 `REVIEW`로 정규화하고 원값을 recommendation에 보존" 추가. (병합이 최종 게이트)

### 3.5 템플릿 고정 스타일 — `dictionary/security-template.html`

> `docs/index.html`은 이 파일의 **심링크**이므로 자동 동기화(별도 수정 불필요·불변식 자동 성립).

**(a) enum 표시 정규화 — 구버전 리포트 하위호환.** 이미 생성된 리포트(한글 enum 포함)도 항상 정본 표기로 렌더되도록 표시 계층 정규화 함수 신설:

```javascript
// Display normalization: legacy Korean/invented enum values → canonical English.
var ENUM_DISPLAY={
  '심각':'Critical','높음':'High','중간':'Medium','낮음':'Low','정보':'Info',
  '확인됨':'Confirmed','완화됨':'Mitigated','미확인':'Unconfirmed',
  '거짓 양성':'False Positive','검증 필요':'Needs Verification',
  '제거':'REMOVE','비활성화':'DISABLE','검토':'REVIEW','검토_필요':'REVIEW','설치_가능':'INSTALL_OK'
};
function canonEnum(v){ if(v===null||v===undefined) return v; var s=String(v).trim(); return ENUM_DISPLAY[s]||s; }
```

적용 지점(값 표시 전 `canonEnum()` 통과):
- `sevBadge()` — severity (findingCard 경유 전 섹션 공통)
- `verdictBadge()` — verdict/security_verdict (#1, 연관관계·그래프 카드 포함)
- findingCard의 `status-badge`(:882) — status/confidence
- `renderRecs`의 priority(:1183) — #8
- `renderSummary` 최고 위험 컴포넌트 카드(worstVerdict) — #1

**(b) 미지 verdict 폴백 스타일** — 정규화 후에도 4종 외 값이면(`MASK` 등 미래 유입 대비) 중립 배경 클래스로 폴백해 **스타일 누락이 구조적으로 불가능**하게:

```javascript
function verdictBadge(v,extraCls){
  if(v===null||v===undefined||v==='') return '';
  var cv=canonEnum(v);
  var known={'install_ok':1,'review':1,'disable':1,'remove':1};
  var cls=String(cv).toLowerCase();
  if(!known[cls]) cls='unknown';                        // ← 폴백
  return '<span class="verdict-badge verd-'+esc(cls)+(extraCls?' '+extraCls:'')+'">'+esc(cv)+'</span>';
}
```

```css
.verd-unknown{background:var(--bg-tertiary);color:var(--text-secondary);border:1px solid var(--border)}
```

**(c) SBOM 서브헤딩 영어 고정 레이블 (#6)** — 도메인 고유명사는 로케일 무관 영어 고정. i18n `t()` 경유를 제거하고 리터럴 사용:

| 위치 | 현행 | 변경 |
|------|------|------|
| :1130 | `t('vulns')` | `'Vulnerabilities'` |
| :1144 | `t('licenseIssues')` | `'License Issues'` |
| :1152 | `t('versionRisks')` | `'Version Risks'` |
| :1160 | `t('supplyChain')` | `'Supply Chain Risks'` |
| (우선 조치 헤딩) | `t('priorityActions')` | `'Priority Actions'` |

스타일은 기존 `.sub-heading` 유지(템플릿 고정 스타일 원칙). ko i18n 사전의 해당 키는 다른 참조가 없으면 제거, 있으면 존치(§4 검증에서 확인).
※ 섹션 제목·안내문 등 **UI 크롬 i18n은 유지** — 영어 고정 대상은 도메인 고유명사 서브헤딩과 enum 값에 한정.

**(d) 섹션 순서 변경 — 권장 조치를 리포지토리 요약 다음으로.** `renderReport()`(:1306):

```diff
     renderScanMeta(meta)+
     renderSummary(report)+
     renderRepoSummary(data.repository_summary)+
+    renderRecs(data.recommendations)+
     renderStatic(data.static_code_findings)+
     ...
     renderModelValidity(data.model_validity_findings)+
-    renderRecs(data.recommendations);
+    '';
```

**영향 범위 검토 결과 (누락 방지):**

| 영역 | 영향 | 판정 |
|------|------|------|
| `scrollToFinding` finding-ref 링크 | id 앵커 기반 — 순서 무관. 권장 조치가 위로 가면 링크가 아래 방향 스크롤로 동작 | ✅ 수정 불필요 |
| `countSev`/`initRiskChart`/도넛 | 데이터 집계 — DOM 순서 무관 | ✅ 수정 불필요 |
| 섹션 접기(collapse)·`section()` | 섹션 단위 독립 | ✅ 수정 불필요 |
| 인쇄(print CSS) | DOM 순서 따라 인쇄 — 의도된 변경 | ✅ 수정 불필요 |
| `exportHTML` | 템플릿 재직렬화 — renderReport 순서 자동 반영 | ✅ 수정 불필요 |
| 기존 생성된 HTML | 과거 순서 유지(재생성 시 신규 순서) | ✅ 허용 |
| Desktop/Code 양 모드 | 템플릿 공유 자산 — 1회 수정으로 동시 반영, Desktop zip 재빌드 필요 | ⚠️ §5 체크 |

## 4. 검증 절차

```bash
# 1. 뷰어 동기(심링크 확인)
test -L docs/index.html && readlink docs/index.html   # ../dictionary/security-template.html

# 2. 증거 리포트 재렌더 — 한글/미지 enum이 정본 표기+스타일로 정규화되는지
python3 scripts/generate_html_report.py \
  ~/sec/20260609-reviewOS-security/scanreport-20260715150007.json --lang ko --out /tmp/patch2-check.html
# 브라우저 육안: ①REMOVE 배지 스타일 ②전 섹션 CRITICAL/Confirmed 통일 ④MASK → verd-unknown 스타일
# ⑥SBOM 영어 서브헤딩 ⑧우선순위: Critical ⑨권장 조치가 리포지토리 요약 직후

# 3. i18n 잔존 참조 확인 (제거한 키를 다른 곳에서 안 쓰는지)
grep -n "t('vulns')\|t('licenseIssues')\|t('versionRisks')\|t('supplyChain')\|t('priorityActions')" dictionary/security-template.html  # 0건

# 4. 번역 지침 모순 제거 확인
grep -n "등급 번역\|일관되게 번역" skills/bilingual-translator/SKILL.md docs/SCHEMA_V1.3_ENFORCEMENT.md  # 0건
grep -c '"severity": "높음"' skills/bilingual-translator/SKILL.md  # 0

# 5. 신규 스캔 E2E — korean_report enum이 영문 유지되는지 (fragment 모드 포함 대형 리포트로)
#    EN/KO enum diff = 0 확인:
python3 - <<'PY'
import json; d=json.load(open('<신규 scanreport.json>'))
KEYS=('severity','status','verdict','security_verdict','priority','confidence','model_effectiveness')
def enums(r):
    out=set()
    def w(o):
        if isinstance(o,dict):
            for k,v in o.items():
                if k in KEYS and isinstance(v,str): out.add((k,v))
                w(v)
        elif isinstance(o,list): [w(x) for x in o]
    w(r); return out
en,kr=enums(d['english_report']),enums(d['korean_report'])
assert en==kr, f"EN/KR enum mismatch: {en^kr}"
print("ENUM PARITY OK")
PY

# 6. Desktop 빌드 회귀
bash build_claude_desktop.sh
grep -c "tss-" dist_claude_desktop/threat-scan-security/SKILL.md            # 0
grep -c "canonEnum" dist_claude_desktop/threat-scan-security/references/dictionary/security-template.html  # ≥1 (수정 반영)
```

## 5. Dual-Mode 반영 체크리스트 (양쪽 누락 방지 — 필수)

| 파일 | 계층 | Desktop 반영 경로 | Code 반영 경로 |
|------|------|-------------------|----------------|
| `dictionary/security-template.html` | **공유** | 빌드가 references/dictionary로 복사 | `generate_html_report.py`가 직접 사용 |
| `skills/bilingual-translator/SKILL.md` | **공유 원천** | 빌드가 references/sub-skills로 복사 → Desktop 단계 10 | `tss-translator`가 Read로 참조 |
| `skills/sensitive-pattern-matcher/SKILL.md` | **공유 원천** | 동일 | `tss-sensitive-patterns`가 참조 |
| `skills/report-merger/SKILL.md` | **공유 원천** | 동일 | `tss-report-merger`가 참조 |
| `agents/tss-translator.md` | Code 전용 | 해당 없음(빌드 미포함) | 직접 |
| `docs/SCHEMA_V1.3_ENFORCEMENT.md` | 문서 | 빌드가 references/docs로 복사 | repo 직접 |
| Desktop zip 재빌드 + 재배포 | — | **필수** (구 zip은 구 지침 유지) | 해당 없음 |
| 플러그인 버전 범프(2.5.0) 후 `/plugin update` | — | — | **필수** (플러그인 캐시는 릴리스 시점 고정) |

## 6. 범위 밖 (본 패치에서 다루지 않음)

- korean_report에서 enum 필드를 아예 **생략**하고 english_report만 정본으로 두는 구조 개편(중복 제거) — Schema V1.3 구조 변경이라 별도 버전에서 검토.
- 과거 생성 JSON의 데이터 정정(마이그레이션) — 템플릿 표시 정규화(3.5a)로 렌더 계층에서 흡수.
- `우선순위:` 등 UI 크롬 레이블의 언어 정책 전면 재검토 — 현행 i18n 유지.
