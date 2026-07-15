# 아키텍처

**핵심**: 분석 방법론은 `skills/<name>/SKILL.md` **한 곳**에만 있고, Claude Desktop과 Claude Code 두 모드가 이를 공유합니다. 한 번 수정하면 양쪽에 반영됩니다(드리프트 없음).

```mermaid
flowchart TD
  subgraph SRC[단일 원천]
    SK["skills/*/SKILL.md<br/>(방법론·스키마)"]
    DICT["dictionary/<br/>(용어 사전·HTML 템플릿)"]
    SCR["scripts/<br/>(HTML 생성기)"]
  end

  SK --> DESK
  SK --> CODE
  DICT --> DESK
  DICT --> CODE
  SCR --> DESK
  SCR --> CODE

  subgraph DESK[Claude Desktop 경로]
    BUILD["build_claude_desktop.sh"] --> ZIP["threat-scan-security.zip<br/>references/ 번들"]
  end

  subgraph CODE[Claude Code 경로]
    CMD["commands/threat-scan*.md"] --> AG["agents/tss-*.md<br/>(SKILL.md 참조)"]
    PLG[".claude-plugin/*.json"]
  end
```

## 두 모드의 매핑

| 파이프라인 단계 | 단일 원천 (`skills/`) | Code 에이전트 (`agents/`) |
|-----------------|----------------------|---------------------------|
| 오케스트레이션 | threat-scan-orchestrator | (스킬이 직접 구동) |
| 0 소스 준비 | source-handler | tss-source-handler |
| 1 인덱싱 | repo-indexer | tss-repo-indexer |
| 2 정적 코드 | static-code-analyzer | tss-static-analyzer |
| 3 바이너리 | binary-analyzer | tss-binary-analyzer |
| 4 스킬 보안 | skill-security-analyzer | tss-skill-analyzer |
| 4.5 연관관계 | relationship-graph-analyzer | tss-relationship-graph |
| 4.6 모델 유효성 | model-validity-analyzer | tss-model-validity |
| 5 민감 패턴 | sensitive-pattern-matcher | tss-sensitive-patterns |
| 6 정책 | agent-policy-verifier | tss-policy-verifier |
| 7 프롬프트 | prompt-optimizer | tss-prompt-optimizer |
| 8 SBOM | securityreports-sbom | tss-sbom |
| 8.5 심층 트리아지 | securityreports-deepdive | tss-deepdive |
| 9 병합 | report-merger | tss-report-merger |
| 10 번역 | bilingual-translator | tss-translator |
| 11 HTML | html-report-generator | tss-html-report |

> **오케스트레이션은 스킬 레벨에 있습니다.** Claude Code 서브에이전트는 중첩 호출이 불가하므로, `threat-scan-orchestrator` 스킬이 `allowed-tools: Agent(tss-*)`로 워커 에이전트를 구동합니다.

## 실행 흐름 (Claude Code)

```mermaid
sequenceDiagram
  participant U as 사용자
  participant C as /threat-scan
  participant O as orchestrator (skill)
  participant W as tss-* (agents)
  participant P as generate_html_report.py
  U->>C: /threat-scan <대상>
  C->>O: 오케스트레이터 구동
  O->>W: 단계 0-10 에이전트 호출
  W-->>O: 카테고리별 JSON fragment
  O->>O: 병합 → bilingual JSON 저장
  O->>P: 단계 11 (Bash, python3)
  P-->>O: 정적 HTML 경로
  O-->>U: JSON + KO HTML 보고
```

## 디렉토리 레이아웃

```text
Threat-scan-security/
├── skills/*/SKILL.md        # 단일 원천 (방법론) — 양 모드 공유
├── agents/tss-*.md          # Claude Code 워커 (SKILL.md 참조, Read/Write/Glob/Grep)
├── commands/threat-scan*.md # Claude Code 진입점 (scan · setup · html · help)
├── .claude-plugin/          # plugin.json · marketplace.json
├── hooks/hooks.json         # SubagentStop 훅 (리댁션 · 완료 로깅)
├── dictionary/              # 용어 사전(+compliance_controls) · security-template.html
├── scripts/                 # generate_html_report · validate_compliance_tags · assemble_bilingual (+*.sh 훅)
├── tests/fixtures/          # validator 픽스처 (legacy · valid · violations)
├── build_claude_desktop.sh  # Desktop zip 빌드
└── docs/                    # 스키마 v1.4/v1.3 · CTID-D/V · 버전별 기획문서
```

## 디렉토리 용도 분류 (공용 / Desktop / Code / 로컬)

> 분류 기준: **🟢 공용** = 양 모드가 사용하는 단일 원천. **🔵 Code 전용** = Claude Code 플러그인 런타임만 사용.
> **🟠 Desktop 전용** = Desktop zip 빌드·배포에만 관여. **⚪ 로컬 전용** = 개발 머신 세션 설정 — **git 비추적**(.gitignore).

| 경로 | 분류 | 용도 | Desktop 반영 경로 | Code 반영 경로 |
|------|------|------|-------------------|----------------|
| `skills/*/SKILL.md` | 🟢 공용 | 분석 방법론·스키마 단일 원천 | 빌드가 `references/sub-skills/`로 복사 | `tss-*` 에이전트가 Read로 참조 |
| `dictionary/` | 🟢 공용 | 번역 사전(JSON)·HTML 리포트 템플릿 | 빌드가 `references/dictionary/`로 복사 | `generate_html_report.py`가 직접 사용 |
| `scripts/*.py` | 🟢 공용 | 결정론 스크립트 — HTML 생성기·bilingual 조립 | 빌드가 `references/scripts/`로 복사 | 단계 10.5·11에서 직접 실행 |
| `docs/` (스키마·CTID 정본) | 🟢 공용 | Schema V1.4 정의·enforcement + CTID-D/V 태깅 디렉티브 — 양 모드 방법론이 참조 | 빌드가 `references/docs/`로 복사 | repo 직접 참조 |
| `docs/vX.Y.Z/` | 📄 개발 문서 | 버전별 기획(GOAL·phase)·이슈 패치 문서 | 미포함 | 개발 시 참조 |
| `VERSION` | 🟢 공용 | 버전 동기화 단일 기준 (빌드·plugin.json·help) | 빌드가 읽음 | 범프 시 plugin.json과 동기화 |
| `agents/tss-*.md` | 🔵 Code 전용 | 파이프라인 워커 정의 (방법론은 SKILL.md 참조) | 미포함 (빌드 비복사) | 플러그인 런타임이 로드 |
| `commands/threat-scan*.md` | 🔵 Code 전용 | `/threat-scan` 등 슬래시 커맨드 진입점 | 미포함 | 플러그인 런타임이 로드 |
| `hooks/hooks.json` | 🔵 Code 전용 | SubagentStop 훅(리댁션·완료 로깅) — 런타임 자동 로드 | 미포함 | 플러그인 런타임이 로드 |
| `scripts/*.sh` | 🔵 Code 전용 | 훅 스크립트(redact_secrets·log_completion)·유틸(agent_efficiency) | **의도적 비복사** (Desktop 샌드박스에 셸 없음) | 훅이 실행 |
| `.claude-plugin/` | 🔵 Code 전용 | **배포 매니페스트** — plugin.json(버전)·marketplace.json(마켓 정의). `/plugin marketplace add`가 이 리포지토리에서 읽는 설치 진입점 | 미포함 | 설치·업데이트의 기준 |
| `build_claude_desktop.sh` | 🟠 Desktop 전용 | zip 빌드 도구 — frontmatter 스트립·Code 섹션 제거·references 번들 | 빌드 실행 주체 | 사용 안 함 |
| `dist_claude_desktop/` · `*.zip` | 🟠 Desktop 전용 | 빌드 산출물 — **git 비추적** (태그 시 CI가 생성) | 배포물 그 자체 | 사용 안 함 |
| `.github/workflows/` | 🟠 Desktop 전용 | 태그 push 시 Desktop zip 릴리스 CI | 릴리스 자동화 | 사용 안 함 |
| `CLAUDE.md` | 📄 개발 가이드 | 이 리포지토리를 Claude Code로 **개발**할 때의 규칙 (플러그인 기능 아님 — 추적 유지) | — | — |
| `README` · `INSTALLATION` · `USER_GUIDE` · `ARCHITECTURE` · `CHANGELOG` | 📄 문서 | 사용자·기여자 문서 | 미포함 | — |
| `LICENSE` · `NOTICE` | 📄 라이선스 | Apache-2.0 | 빌드가 패키지 루트로 복사 | repo 포함 |
| `.claude/` | ⚪ 로컬 전용 | 이 머신의 세션 설정(권한 allowlist 등) — **비추적** | — | — |
| `.gemini/` `.cursor/` `.codex/` 등 | ⚪ 로컬 전용 | 타 AI 도구 로컬 가드레일 — **비추적** | — | — |

> **혼동 주의:** `.claude/`(로컬 세션 설정, 비추적)와 `.claude-plugin/`(배포 매니페스트, 추적 필수)은 이름만 비슷할 뿐 정반대 성격이다. `.claude-plugin/`이 없으면 마켓플레이스 설치가 불가능하다.

## 설계 원칙

- **단일 원천**: 에이전트는 방법론을 복제하지 않고 `${CLAUDE_PLUGIN_ROOT}/skills/<name>/SKILL.md`를 참조.
- **결정론·LLM 경계**: 단계 1–10은 코드 실행·파일 생성 없이 Claude 추론(읽기 전용 `Glob`/`Grep` 탐색은 허용). 셸 예외는 단계 0·10.5(분할 조립)·11(HTML+검증).
- **파일=진실 자율완주**: 완료 판정은 리턴 메시지가 아니라 OUTPUT_PATH 파일. async 런타임에선 `Monitor`로 파일 출현 대기. 사용자 개입은 권한 셋업 승인·AI 구성요소 게이트 2회로 한정.
- **오프라인 호환**: CVE는 모델 지식 + OSV 링크. HTML 차트는 CDN 실패 시 SVG 폴백. 컴플라이언스 제어명은 템플릿에 인라인 임베드(무의존).
- **스키마 불변**: 출력은 Schema V1.4 고정(`docs/SCHEMA_V1.4_ENFORCEMENT.md`, v1.3의 strict superset). 유일한 추가 필드는 `compliance_tags`(optional) + `ai_agent_scope`(optional). v1.2/v1.3 문서는 legacy 참조로 보존.

## 컴플라이언스 태깅 파이프라인 (v2.5.0 / Schema V1.4)

```mermaid
flowchart LR
  E[단계 1-8<br/>emitting 스킬] -->|CTID-D 방출| T1[compliance_tags 부여]
  T1 --> V[단계 8.5 deepdive<br/>CTID-V 검증·교정]
  V -->|read-only| M[단계 9 병합]
  M -->|read-only<br/>EN=KO 불변| TR[단계 10 번역]
  TR -->|validate_compliance_tags.py| H[단계 11 HTML 배지]
```

- **CTID-D**(`docs/compliance-tagmap-distilled.md`): 단계 1–8 방출 규칙 — KISA 49 + AILLM 9 + TA 10.
- **CTID-V**(`docs/compliance-tagging-deepdive.md`): 단계 8.5 검증(V-1~V-7 + cross-finding sweep) — 태그 수정 가능한 유일 단계.
- 단계 9–11은 태그 읽기전용. 번역은 태그·enum을 EN/KO byte-identical로 유지, HTML은 네임스페이스 배지로 렌더.

## 공유 자산

| 자산 | 역할 |
|------|------|
| `dictionary/security-template.html` | HTML 리포트 템플릿(뷰어 = 생성기 원천). `docs/index.html`은 이 파일의 심링크 |
| `dictionary/security-terms-en-ko.json` | 보안 용어 번역 사전 + `compliance_controls`(68 제어명 EN/KO) |
| `scripts/generate_html_report.py` | 표준 라이브러리만, `CLAUDE_PLUGIN_ROOT`/repo/dist 경로 자동 해석. `--coverage` KISA 커버리지 |
| `scripts/validate_compliance_tags.py` | Schema V1.4 태그 결정론 검증기(단계 11 직전 실행) |
| `scripts/assemble_bilingual.py` | 분할 번역 조각 결정론 조립(단계 10.5) |
| `docs/claude-threat-scan-json-schema-v1.4.md` · `SCHEMA_V1.4_ENFORCEMENT.md` | 스키마 정본(v1.3 legacy 보존) |
| `VERSION` | Desktop 빌드·플러그인 버전 동기화 기준 |
