# Phase 4 — 모델·권한 차등 정합성 + 효율 모니터링

## 목표

(1) 에이전트별 **모델·권한**을 역할에 맞게 정합화하고, (2) 런타임 토큰 조회가 불가능한
제약 아래에서 **자기보고 메트릭 + 사후 트랜스크립트 분석**으로 효율 모니터링을 도입한다.

## Part A — 모델·권한 차등 정합성

### 현황 점검

이미 에이전트별 `model`/`tools`가 부분 설정돼 있다(v2.3.0~). 이를 역할 기준으로
정합화한다.

| 에이전트 | 현재 model | 권장 model | tools | 근거 |
|----------|-----------|-----------|-------|------|
| (오케스트레이터 스킬) | 세션 모델 | **opus** | Agent/Bash/Read/Write | 라우팅·검증 판단력, 얇은 컨텍스트(Phase 2) |
| tss-source-handler | haiku | haiku | Bash, Read | 단순 clone/unzip |
| tss-repo-indexer | (확인) | haiku | Read | 인덱싱 |
| tss-static-analyzer | sonnet | sonnet | **Read** | 코드 패턴 추론 |
| tss-binary-analyzer | (확인) | sonnet | Read | |
| tss-skill-analyzer | (확인) | sonnet | Read | prompt-injection 추론 |
| tss-sensitive-patterns | sonnet | sonnet | **Read** | 마스킹 계약(Phase 1) |
| tss-policy-verifier | (확인) | sonnet | Read | |
| tss-prompt-optimizer | (확인) | haiku | Read | 포맷·토큰 점검 |
| tss-relationship-graph | (확인) | sonnet | Read | 그래프 위험 전파 추론 |
| tss-model-validity | (확인) | haiku | Read | 룰 기반 판정 |
| tss-sbom | (확인) | sonnet | Read | CVE·라이선스 |
| tss-deepdive | sonnet | **opus** | Read | 최고 난도 트리아지(오탐/RCE 판단) |
| tss-report-merger | (확인) | haiku | Read | 결정론적 병합 |
| tss-translator | (확인) | sonnet | Read | 번역 품질 |
| tss-html-report | (확인) | haiku | Bash, Read | 결정론적 생성 |

### 권한 통제 원칙

- **탐지·분석 워커는 `tools: Read`만** → 셸·쓰기·네트워크 구조적 차단(유출 불가).
- **셸 허용은 3개만**: source-handler(clone/unzip), html-report(스크립트), (오케스트레이터).
- `disallowedTools`로 마스터가 워커에 위험 도구를 상속시키지 않도록 명시(필요 시).
- settings.json `deny`는 항상 우선 — 2중 방어.

### 작업

각 `agents/tss-*.md` frontmatter의 `model`/`tools`를 위 표대로 통일. 누락된 `model`이
있으면 추가. `tss-deepdive`를 sonnet→opus로 상향(고난도 판단).

## Part B — 효율 모니터링 (라이브 불가 → 2가지 대안)

### 검증된 제약

런타임에 서브에이전트 토큰을 조회하는 API는 **없다**. 따라서:

### B-1. 자기보고 `_meta` footer (워커 → 마스터 집계)

각 워커가 반환 JSON에 소형 메트릭을 부착(토큰 직접값은 아니나 효율 프록시):

```json
{
  "sensitive_patterns": [ ... ],
  "_meta": {
    "agent": "tss-sensitive-patterns",
    "files_scanned": 128,
    "findings": 3,
    "depthReached": 1,
    "notes": "skipped node_modules"
  }
}
```

- 공유 방법론 각 `skills/*/SKILL.md` 산출 규약에 `_meta` footer 1줄 추가.
- 마스터는 Phase 1 체크포인트에서 `_meta`를 집계해 "에이전트별 스캔 범위·산출량" 요약 생성.
- `_meta`는 Schema V1.3 **optional** — report-merger가 최종 리포트에서 제외(내부 메트릭).

### B-2. 사후 트랜스크립트 분석 (선택적 산출)

스캔 종료 후, 서브에이전트 트랜스크립트(`~/.claude/projects/.../subagents/agent-*.jsonl`)를
파싱해 per-agent 토큰·turn 수를 추출하는 선택적 스크립트를 제공:

```
scripts/agent_efficiency.sh <session-id>
→ 에이전트별 input/output 토큰, turn 수, 소요시간 표 출력
```

- Phase 5 보고에 "효율 요약(선택)" 으로 포함. 기본 스캔 흐름엔 영향 없음.
- 경로·스키마가 Claude Code 버전에 의존하므로 **best-effort**(미존재 시 graceful skip).

## Dual-Mode 영향

- `_meta` footer 규약은 공유 방법론(`skills/*/SKILL.md`)에 → 양 모드 반영. 단 Desktop은
  서브에이전트가 없으므로 단일 컨텍스트의 단계별 메트릭으로만 의미.
- 모델·권한 frontmatter(`agents/tss-*.md`)는 Claude Code 전용.
- 트랜스크립트 분석(B-2)은 Claude Code 전용.

## 완료 조건 (검증 가능)

- [ ] 모든 `agents/tss-*.md`에 `model` frontmatter 존재, Part A 표와 일치.
- [ ] 탐지·분석 워커 12개+가 `tools: Read`(셸·쓰기 없음). 셸 허용은 3개로 한정.
- [ ] `tss-deepdive` model = `opus`.
- [ ] 공유 방법론에 `_meta` footer 규약 존재, report-merger가 최종 리포트에서 `_meta` 제외.
- [ ] `scripts/agent_efficiency.sh` 존재(best-effort, 미존재 환경서 graceful skip).
- [ ] 마스터가 Phase 1 체크포인트에서 `_meta` 집계 요약 생성.

## 검증

```bash
cd Threat-scan-security
# 모든 워커에 model 존재
for f in agents/tss-*.md; do grep -q "^model:" "$f" || echo "MISSING model: $f"; done   # 출력 없어야 함
# 셸 허용은 3개만
grep -l "tools:.*Bash" agents/tss-*.md | wc -l        # 3 (source-handler, html-report, + 필요시)
# deepdive opus
grep -A1 "name: tss-deepdive" agents/tss-deepdive.md | grep -c "opus"   # 1
# _meta 규약
grep -rc "_meta" skills/sensitive-pattern-matcher/SKILL.md             # ≥ 1
test -f scripts/agent_efficiency.sh && echo "efficiency script present"
```
