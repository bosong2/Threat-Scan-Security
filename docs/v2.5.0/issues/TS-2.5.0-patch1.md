# threat-scan-security 패치 종합 — TS-1.4.3

작성: 2026-07-15 · 대상 캐시: `~/.claude/plugins/cache/threat-scan-security-marketplace/threat-scan-security/2.4.1/`
백업: 같은 상위 디렉터리 `tss-plugin-backup-<timestamp>/`

> **적용 완료 — 캐시에 즉시 반영됨.** 이 문서는 지금까지 적용한 모든 커스텀 패치를 하나로 모은 종합본이다
> (① 자율 완주/커버리지/번역 안정화, ② HTML 리포트 코드뷰 개선, ③ AI 에이전트 구성요소 스캔범위 확인 게이트).
> ⚠️ **플러그인 업데이트/재설치 시 벤더 캐시가 덮어써지므로 백업에서 재적용 필요.**
> ⚠️ **에이전트/스킬 정의는 세션 시작 시 캐시**되므로, Glob/Grep 등 에이전트 변경을 실제로 적용하려면
> `/reload-plugins` 후 **새 세션**에서 실행해야 한다.
> (파일명은 v1.4.2 시점 그대로 유지 — 내용은 v1.4.3까지의 전체 변경을 포함하는 누적 문서.)

---

## PART 1 — 자율 완주 · 커버리지 · 번역 안정화 (기존 v2.4.1-auto)

### 배경 — reviewOS-security 스캔에서 관찰된 중단점
1. repo-indexer가 중첩 프로젝트(`.../reviewOS-security/reviewOS-security/`)를 "empty"로 오탐.
2. 분석 에이전트가 `Read,Write`만 가져 파일을 열거 못 하고 경로를 추측 → API 라우트 대부분 누락(수동 보충 필요).
3. 단계 10 번역 hang(영문 재출력 + 단일 거대 Write). 사용자가 말한 "jira 확인 단계 멈춤"이 이 조각.
4. 런타임이 Agent를 async로 실행하는데 SKILL은 blocking 가정 → 오케스트레이터가 수동 babysitting.

### A. 분석 에이전트에 읽기 전용 탐색 도구 부여
`agents/tss-*.md` frontmatter `tools:`에 **`Glob, Grep` 추가** — 9개 소스 검사 에이전트
(`repo-indexer, static, binary, skill, sensitive, policy, prompt, sbom, deepdive`).
본문에 "전체 트리 완전 열거(경로 추측 금지)" 지시 추가. Glob/Grep은 셸/코드 실행이 아닌 읽기 전용 도구라
"단계 1–10 코드 실행 금지" 제약과 상충하지 않음.

### B. 번역기 ANTI-HANG + JSON-SAFETY CONTRACT (`agents/tss-translator.md`)
- 영문 원문 재출력 금지, `korean_report{}` 조각 하나만 단일 Write, 시작 즉시 Read→번역→Write→1줄 반환.
- `ITEM_RANGE`(예: `0-8`) 옵션 — 배열 슬라이스만 번역(대형 배열 재분할용).
- **JSON SAFETY**: 값 문자열 내부에 원시 `"` 금지(홑따옴표/낫표/이스케이프), 개행·탭 이스케이프, 코드펜스 금지.

### C. 오케스트레이터 자율 완주 + 자가 복구 (`skills/threat-scan-orchestrator/SKILL.md`)
- **AUTONOMOUS-COMPLETION CONTRACT**: 시작 후 사용자 확인 없이 Phase 5까지 완주. 하드 실패에서만 중단.
- Agent 실행 모델 불문 완료 판정 = OUTPUT_PATH 파일. async면 `Monitor`(`until [ -f ]`) 대기. `allowed-tools`에 `Monitor, TaskStop` 추가.
- **Phase 0(c)**: 0-파일 시 매니페스트 위치로 중첩 루트 자동 하강 후 재인덱싱.
- **Phase 3-B**: **"카테고리당 조각 1개"가 기본값**(단일 카테고리 조각은 30–120초에 안정 완료). `ITEM_RANGE`
  슬라이싱은 최후 백스톱(워커가 end-exclusive 미준수 시 경계 중복 발생). 스톨 시 `TaskStop`→재분할.
- **Phase 3-C**: 조립 전 조각별 **JSON 유효성 검증**(깨진 카테고리 자동 재번역), 조립은 **`SCAN_TMP` env
  auto-glob**로 수행(zsh는 `--frags $(ls)` unquoted를 단어분할 안 해 실패 — 실측 확인). 최종 EN/KR parity 검증.

### 실사 재현 검증 (2026-07-15, 캐시 적용본 재실행)
Phase 0–5 완주, `scanreport-20260715135851.{json,html}` 생성, graph_verdict=REMOVE, EN=KR parity OK.
- 각 단일 카테고리 번역 조각 **36–120초** 완료(과거 12분+ → 무hang).
- nested-root 자동 해석·zsh-safe 조립 정상.
- parity-check가 신규 결함 2건(ITEM_RANGE 경계 중복, 번역 JSON 파손)을 사용자 개입 없이 자동 복구.

---

## PART 2 — HTML 리포트 코드뷰 개선 (신규, TS-1.4.2)

**대상 파일:** `dictionary/security-template.html` (뷰어 겸 export 템플릿. `scripts/generate_html_report.py`가
이 템플릿을 그대로 임베드하고, 브라우저에서 내장 JS가 `code_fix`를 렌더).

요청: `code_fix`(수정 코드) 블록을 **전문 코드뷰**로 — 언어별 구문 강조, 더 작은 글꼴, **검은 배경**.

### 제약과 선택
리포트는 **오프라인·무의존·결정론**이 원칙(외부 CDN/네트워크 금지). 따라서 highlight.js/Prism 같은 외부
라이브러리를 끌어오지 않고, **템플릿 내장 경량 하이라이터**(정규식 토크나이저)를 새로 심었다. 코드 스니펫이
짧고(주로 TS/JS/JSON/bash) 결정론적이라 이 방식이 적합.

### 변경 내용
1. **다크 코드 테마 (CSS, VS Code Dark+ 팔레트)** — `.code-block`을 라이트→**다크**로 교체:
   - 배경 `#1e1e1e`, 테두리 `#30363d`, 기본 텍스트 `#d4d4d4`.
   - **글꼴 12px → 10.5px**, line-height 1.55, 폰트 `JetBrains Mono`/`SF Mono`/`Fira Code` 우선.
   - `.code-block code`에 배경 제거 오버라이드(인라인 코드 칩 스타일과 격리).
   - 토큰 색상 클래스 추가: `tk-key`#569cd6, `tk-str`#ce9178, `tk-com`#6a9955(이탤릭),
     `tk-num`#b5cea8, `tk-fn`#dcdcaa, `tk-prop`#9cdcfe, `tk-bool`#4fc1ff, `tk-punc`#808080.
   - `.code-lang` 배지를 다크 톤으로(대문자·파랑 텍스트). before/after 좌측 컬러 보더 유지.
2. **경량 구문 하이라이터 (JS)** — `highlightCode(raw, lang)` + 헬퍼(`hlEsc`, `hlLang`, `HL_KW`, `HL_LIT`) 추가.
   - 언어 감지: ts/tsx/js/jsx/json/node→`js`, py→`py`, sh/bash/zsh→`sh`, 그 외→하이라이트 없이 다크 테마만.
   - 정규식 토크나이저로 주석/문자열(단·이중·백틱)/숫자/식별자/공백/기타를 분류. 식별자는 키워드·리터럴·
     함수호출(`(` 선행)·프로퍼티(`.` 후행)로 세분.
   - **하이라이트만 수행, 재포맷/재들여쓰기 절대 안 함**(수정 코드는 원문 그대로 유지해야 하므로).
3. **`codeBlock()`** 이 `esc(code)` 대신 `highlightCode(code, lang)`를 호출하도록 변경.

### 안전성 (XSS)
기존엔 `esc()`로 통째 이스케이프했으나 이제 HTML(span)을 생성하므로, 하이라이터가 **모든 토큰 텍스트를
`hlEsc`로 이스케이프**한다(`<`,`>`,`&`). node 테스트로 검증:
- ts/tsx/py/bash/js/미지정 6개 샘플에서 **원시 `<` 누출 0건**(span 태그 외 `<` 없음).
- `</script><img onerror>` 등 주입 시도 문자열이 `&lt;/script&gt;…`로 안전하게 이스케이프됨.
- `codeBlock`이 keyword/function/comment 토큰을 정상 강조.

### 검증
- `highlightCode` 단위 테스트(node) 전부 통과(정확성 + XSS-safety).
- 템플릿 `<script>` 블록 `node --check` **SYNTAX OK**.
- `generate_html_report.py`로 실제 리포트 재생성 성공 → 임베드 확인:
  `highlightCode`(2회), `background:#1e1e1e`, `font-size:10.5px`, `.tk-key{color:#569cd6}`.
- 사용자 리포트 `scanreport-20260715135851.html` 새 테마로 재생성 완료(230KB).

### 참고 / 한계
- 하이라이팅은 브라우저 렌더 시 실행되므로, 생성된 HTML 파일을 열어야 색상이 보인다(파일 grep으로는 토큰 span 안 보임 — 정상).
- 지원 언어 외(예: go/rust)는 다크 테마 + 이스케이프만 적용(무채색). 필요 시 `HL_KW`에 키워드셋 추가로 확장 가능.
- 프린트/PDF 시에도 다크 배경 유지(요청대로 "전문가용 검은 배경"). 잉크 절약이 필요하면 별도 print 미디어쿼리 추가 검토.

---

## PART 3 — AI 에이전트 구성요소 스캔범위 확인 게이트 (신규, TS-1.4.3)

**요청:** 초기 스캐닝 시작 시, 대상 소스 폴더 내에 `.claude/`와 같은 AI 에이전트 관련 구성요소가 있으면
스캔 범위에 포함할지 여부를 먼저 물어보고 시작하도록.

### 배경
`.claude/`, `.cursor/`, `agents/**`, `.mcp.json` 같은 경로는 애플리케이션 소스코드가 아니라 **AI 도구
자체의 설정·프롬프트·권한 구성**이다. 이미 단계 4(`tss-skill-analyzer`)와 단계 6(`tss-policy-verifier`)이
이런 경로를 검사하도록 설계돼 있지만, 지금까지는 **사용자 동의 없이 자동으로 포함**됐다. 이런 구성요소에는
내부 인프라 정보·팀 전용 프롬프트·권한 구조가 담길 수 있어, 스캔 범위 포함 여부는 자동 판단이 아니라
**사용자가 직접 결정할 사안**이다.

### 변경 내용 (`skills/threat-scan-orchestrator/SKILL.md`)
1. **`allowed-tools`에 `AskUserQuestion` 추가** — 이 게이트에서만 사용, 다른 곳에서는 쓰지 않음.
2. **AUTONOMOUS-COMPLETION CONTRACT에 유일한 예외 명시**: 이 질문 하나만 예외이며, 답을 받은 즉시 다시
   묻지 않고 Phase 5까지 완주한다(전체 자율완주 원칙은 그대로 유지).
3. **Phase 0(d) 신규 단계** (Phase 0(c) 중첩루트 해석 직후, Phase 1 병렬분석 직전에 삽입):
   - `RESOLVED_TARGET_ROOT` 하위를 Python `os.walk`로 순회해 `.claude/`, `.cursor/`, `agents/`,
     `prompts/` 디렉터리와 `AGENTS.md`, `SKILL.md`, `.mcp.json`/`mcp.json`,
     `copilot-instructions.md` 파일을 탐지(`node_modules`/`.git`/`.next`/`dist`/`build`/`vendor` 제외).
   - **미발견(`NONE`)이면 질문 없이 조용히 진행** — 대다수 프로젝트는 이 게이트를 인지하지 못함.
   - **발견되면 Phase 1 배치 발주 전에 `AskUserQuestion`으로 정확히 1회 질문**: "포함(권장)" vs "제외".
   - **제외 선택 시**: 해당 경로를 `tss-skill-analyzer`/`tss-policy-verifier`(및 기타 분석 에이전트)
     프롬프트에 `EXCLUDE_PATHS`로 명시해 내용 분석을 금지(존재만 인지, 내용 미분석).
   - 어느 쪽이든 `repository_summary.ai_agent_scope`에 `"included"`/`"excluded"`를 기록해 최종
     리포트에 이 결정이 투명하게 남도록 함.

### 검증
- 탐지 스니펫을 실제 대상(`reviewOS-security/`)에 실행 → `.claude/` 정확히 탐지(기존 스캔에서 확인된
  `.claude/launch.json`과 일치).
- 빈 프로젝트(매니페스트만 있고 AI 관련 경로 없음)에 실행 → `NONE` 정상 반환, 오탐 없음.
- SKILL.md 임베디드 Python 블록(신규 포함 4개) 전부 `ast.parse` OK.

### 참고
- 이 게이트는 **AI 도구 구성요소가 실제로 존재할 때만** 발동하므로, 일반적인 웹앱/서비스 리포지토리
  스캔에서는 아무 영향이 없다(질문 없이 그대로 진행).
- "제외" 선택 시에도 단계 5(`tss-sensitive-patterns`) 등 다른 카테고리 분석은 정상 수행되며, 배제는
  AI 에이전트 구성요소의 **내용 분석**에만 적용된다(코드 전체 스캔을 막지 않음).

---

## 변경 파일 요약
| 파일 | 변경 |
|------|------|
| `agents/tss-{repo-indexer,static,binary,skill,sensitive,policy,prompt,sbom,deepdive}-analyzer.md` | `tools:` + `Glob, Grep`, 파일 열거 지시 |
| `agents/tss-translator.md` | ANTI-HANG + ITEM_RANGE + JSON-SAFETY 계약 |
| `skills/threat-scan-orchestrator/SKILL.md` | 자율완주·nested-root·카테고리분할·zsh-safe 조립·parity검증, `allowed-tools`에 Monitor/TaskStop/AskUserQuestion, **Phase 0(d) AI 에이전트 구성요소 스캔범위 확인 게이트 신규** |
| `dictionary/security-template.html` | 다크 코드뷰 CSS + 경량 구문 하이라이터 JS + `codeBlock` 연결 |
