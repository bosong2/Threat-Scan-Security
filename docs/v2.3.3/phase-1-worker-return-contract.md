# Phase 1 — 탐지 워커 반환 계약: 마스킹 + locator-only

## 목표

탐지 워커가 raw secret/PII 값을 **반환·에코하지 못하도록** 반환 스키마를 강제한다.
프롬프트 권고("mask with `***`")를 **구조화된 반환 계약**으로 격상한다.

## 근본 원인

`agents/tss-sensitive-patterns.md`에 다음 권고가 있으나 강제력이 없다:

```
- Do NOT log or echo actual secret values — mask with `***`.
```

문제점:
1. **권고일 뿐 스키마가 아니다** — finding 객체에 `value`/`evidence` 필드로 raw 값이
   담기면 그대로 통과한다.
2. **단일 원천이 아니다** — Code 에이전트(`tss-*`)에만 있고, 공유 방법론
   `skills/sensitive-pattern-matcher/SKILL.md`에는 마스킹 규약이 명문화돼 있지 않다.
   Desktop 모드는 이 보호를 받지 못한다.

## 수정 — 공유 방법론에 마스킹 규약 명문화 (단일 원천)

### 1. `skills/sensitive-pattern-matcher/SKILL.md`

`sensitive_patterns[]` 산출 규약에 **MASKING CONTRACT** 절을 추가한다:

```markdown
## MASKING CONTRACT (필수 — v2.3.3)

탐지된 secret/PII의 **raw 값을 절대 산출하지 않는다.** 다음 규칙을 강제한다:

- `masked_value`: 앞 4자 + 나머지 마스킹. 예) `AKIA****************`, `ghp_****`,
  이메일 `j***@***.com`. 원본 길이를 유지하지 말 것(길이도 정보 누출).
- `value`/`secret`/`raw`/`snippet` 등 **원문 필드 금지**.
- 위치는 `file` + `line` + `rule`(예: `aws-access-key`)로만 식별한다.
- 컨텍스트가 꼭 필요하면 raw 줄 대신 `±0 라인의 마스킹된 발췌`만 허용.

### 산출 객체 (각 sensitive_patterns[] 항목)
| 필드 | 예시 | 비고 |
|------|------|------|
| `issue` | "AWS access key in source" | |
| `severity` | "High" | 대문자 시작 |
| `file` | "src/config.py" | |
| `line` | 42 | |
| `rule` | "aws-access-key" | 탐지 분류 |
| `masked_value` | "AKIA****************" | **raw 금지** |
| `recommendation` | "..." | |
```

### 2. `skills/static-code-analyzer/SKILL.md`

정적 분석에서 하드코딩 크리덴셜을 발견할 때도 동일 규약 적용 — `static_code_findings[]`
의 증거 필드에 raw 값 대신 `masked_value`를 쓰도록 동일 MASKING CONTRACT 참조 추가.

## 수정 — Code 에이전트 반환 계약 강화

### `agents/tss-sensitive-patterns.md`

`## Rules` 를 권고에서 **계약**으로 격상:

```markdown
## Rules

- Read-only. No file writes, no code execution.
- MASKING CONTRACT (강제): raw secret/PII 값을 **절대** 반환하지 않는다.
  - 각 finding은 `masked_value`(앞 4자 + 마스킹)만 포함한다.
  - `value`/`secret`/`raw`/`snippet` 키를 절대 사용하지 않는다.
  - 자세한 규약은 `skills/sensitive-pattern-matcher/SKILL.md` § MASKING CONTRACT.
- 반환 JSON은 `sensitive_patterns[]` 배열 + `_meta` footer(Phase 4)만 포함한다.
```

### `agents/tss-static-analyzer.md`

하드코딩 크리덴셜 finding에 동일하게 `masked_value` 사용 규약 1줄 추가.

## Schema V1.3 호환성

- `masked_value`는 **신규 optional 필드**로, 기존 뷰어 호환성을 깨지 않는다
  (`docs/SCHEMA_V1.3_ENFORCEMENT.md`의 금지 필드 목록에 추가 항목 없음 — 추가만).
- 기존 `value`/`snippet` 류 필드를 **금지 필드 목록**에 명시적으로 추가하여
  스키마 검증 단계(report-merger)에서 누출을 차단한다.

## 완료 조건 (검증 가능)

- [ ] `skills/sensitive-pattern-matcher/SKILL.md`에 `MASKING CONTRACT` 절 존재.
- [ ] `skills/static-code-analyzer/SKILL.md`가 동일 규약 참조.
- [ ] `agents/tss-sensitive-patterns.md` Rules가 `masked_value` 강제, `value`/`raw` 금지 명시.
- [ ] `docs/SCHEMA_V1.3_ENFORCEMENT.md` 금지 필드에 `value`/`secret`/`raw`/`snippet`(secret 맥락) 추가.
- [ ] Desktop 빌드 시 마스킹 규약이 `dist_claude_desktop`의 sub-skill에도 복사됨.

## 검증

```bash
cd Threat-scan-security
# 공유 방법론에 규약 존재
grep -c "MASKING CONTRACT" skills/sensitive-pattern-matcher/SKILL.md   # ≥ 1
grep -c "masked_value" skills/sensitive-pattern-matcher/SKILL.md       # ≥ 1
# Code 에이전트 계약 강화
grep -c "masked_value" agents/tss-sensitive-patterns.md               # ≥ 1
grep -E "value|secret|raw|snippet" agents/tss-sensitive-patterns.md | grep -i "절대\|never\|금지"  # 금지 명시
# 빌드 후 Desktop 반영
bash build_claude_desktop.sh >/dev/null && \
  grep -c "MASKING CONTRACT" dist_claude_desktop/threat-scan-security/references/sub-skills/sensitive-pattern-matcher.md  # ≥ 1
```

## 비고

Phase 1은 **가장 우선순위 높은 보안 수정**이다. Phase 3(훅)이 2차 방어선이지만, 1차
방어선인 반환 계약을 먼저 세워야 한다(훅은 보강이지 대체가 아님). 두 계층이 모두 있어야
"depth-in-defense"가 성립한다.
