# Phase 1 — 워커 에이전트 세트 (`agents/tss-*.md`)

## 목표

Desktop 파이프라인의 각 분석 단계를 Claude Code **서브에이전트**로 노출한다. 단, 분석 방법론은 복제하지 않고 대응하는 `skills/<name>/SKILL.md`를 참조한다(단일 원천).

## 에이전트 목록·매핑·모델 배정

`agents/` 디렉토리에 다음 15개 생성. 모델은 작업 성격에 맞춰 비용 최적화(기계적=haiku, 추론=sonnet).

| 에이전트 파일 | 참조 SKILL | model | tools | 비고 |
|---|---|---|---|---|
| `tss-source-handler.md` | source-handler | haiku | Bash, Read | 소스 준비(clone/unzip) — 셸 허용 단계 |
| `tss-repo-indexer.md` | repo-indexer | haiku | Read | 파일 트리·통계 |
| `tss-static-analyzer.md` | static-code-analyzer | sonnet | Read | 정적 코드 분석 |
| `tss-binary-analyzer.md` | binary-analyzer | haiku | Read | 바이너리 표면 검사 |
| `tss-skill-analyzer.md` | skill-security-analyzer | sonnet | Read | Skill/도구 보안 |
| `tss-relationship-graph.md` | relationship-graph-analyzer | sonnet | Read | 연관관계 그래프·전파 |
| `tss-model-validity.md` | model-validity-analyzer | sonnet | Read | 모델 유효성/진부화 |
| `tss-sensitive-patterns.md` | sensitive-pattern-matcher | sonnet | Read | 민감 패턴 |
| `tss-policy-verifier.md` | agent-policy-verifier | sonnet | Read | 에이전트 정책 |
| `tss-prompt-optimizer.md` | prompt-optimizer | sonnet | Read | 프롬프트/포맷 |
| `tss-sbom.md` | securityreports-sbom | sonnet | Read | SBOM/의존성 |
| `tss-deepdive.md` | securityreports-deepdive | sonnet | Read | 심층분석(트리아지) |
| `tss-report-merger.md` | report-merger | haiku | Read | 영문 보고서 병합 |
| `tss-translator.md` | bilingual-translator | haiku | Read | 한글 번역·bilingual JSON |
| `tss-html-report.md` | html-report-generator | haiku | Bash | python3 생성기 실행 |

> 오케스트레이터는 에이전트가 아니라 **스킬**(Phase 3)로 둔다 — 서브에이전트는 다른 서브에이전트를 호출(중첩)할 수 없기 때문.

## 에이전트 본문 표준 형식 (중복 최소화)

각 `tss-*.md`는 thin wrapper로 구성한다. frontmatter + 단계 역할 1–2문장 + **SKILL.md 참조 지시**.

```markdown
---
name: tss-static-analyzer
description: >
  Run the Threat-scan static code analysis step. Reads the canonical
  static-code-analyzer methodology and emits Schema V1.3 static_code_findings.
  Use as step 2 of the threat-scan pipeline.
model: sonnet
tools: Read
---

You are the static code analysis worker of the Threat-scan pipeline.

1. Read the canonical methodology:
   `${CLAUDE_PLUGIN_ROOT}/skills/static-code-analyzer/SKILL.md`
   (개발 환경에서 env 미설정 시 repo의 `skills/static-code-analyzer/SKILL.md`).
2. Apply it to the target path you were given.
3. Return ONLY the `static_code_findings[]` fragment as Schema V1.3 JSON.
   No file writes (단계 1–10 제약). No code execution.
```

### 단계별 본문 특이사항

- `tss-source-handler` (단계 0): Bash 허용. clone/unzip 수행 후 **준비된 경로**를 반환. SKILL.md의 100MB 제한·소스 유형 감지 로직 참조.
- `tss-html-report` (단계 11): Bash로 `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/generate_html_report.py" <merged.json> --lang ko` 실행. 산출 HTML 경로를 stdout으로 반환. LLM 추론 없음.
- 단계 1–10 워커: **출력은 해당 카테고리 JSON fragment만**(파일 생성 금지). 오케스트레이터가 수집·병합.

## 완료 조건 (검증 가능)

- [ ] `agents/tss-*.md` 15개 존재.
- [ ] 각 파일 frontmatter에 `name`(파일명과 일치)·`description`·`model`·`tools` 존재.
- [ ] 본문에 대응 `skills/<name>/SKILL.md` 참조 경로 포함(복제된 분석 본문 없음).
- [ ] `tss-source-handler`·`tss-html-report`만 Bash 포함, 나머지는 Read만.
- [ ] 모델 배정이 위 표와 일치.

## 검증

```bash
cd Threat-scan-security
ls agents/tss-*.md | wc -l                       # → 15
for f in agents/tss-*.md; do head -1 "$f" | grep -q '^---$' && echo "FM OK: $f"; done
grep -l "CLAUDE_PLUGIN_ROOT" agents/tss-*.md | wc -l   # → 15 (모두 SKILL.md 참조)
grep -L "Bash" agents/tss-*.md | wc -l           # → 13 (Bash 미포함 워커)
```
