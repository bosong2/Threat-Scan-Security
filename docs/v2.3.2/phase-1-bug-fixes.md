# Phase 1 — 버그 수정

## BUG-01 수정 — 오케스트레이터 조기 종료

### 근본 원인

`skills/threat-scan-orchestrator/SKILL.md` 본문이 파이프라인 **설명 문서** 형식이었다.
Claude가 에이전트를 스폰한 후 다음 지시가 없어 턴을 종료했다.

SkillScan(`skillscan/SKILL.md`) 비교:
```
# SkillScan (올바른 패턴)
Phase A: Invoke in parallel (launch in ONE message)
Phase B: Join + synthesize (after all three return)  ← 명시적 대기·수집
Phase C: Relay to user
```

### 수정

오케스트레이터 SKILL.md 상단에 `## 실행 절차 — Claude Code Plugin` 섹션 추가:

```
Phase 0  tss-source-handler 호출 → 준비된 경로 반환
Phase 1  8개 에이전트를 ONE message로 병렬 호출, 전부 반환될 때까지 기다린다
Phase 2  4.5(연관관계)→4.6(모델유효성)→8.5(심층트리아지) 순차 실행
Phase 3  9(병합)→10(번역) 순차 실행
Phase 4  11(HTML) 실행
Phase 5  산출 파일 경로·verdict 보고 (모든 단계 완료 후)
```

핵심 문구: **"전부 반환될 때까지 기다린다"**, **"Phase N 완료 후"**, **"Phase 5 완료 후에만 보고"**

`commands/threat-scan.md`에도 추가:
```
Do not stop until Phase 5 is complete — all agents must finish before you report back.
```

## BUG-02 수정 — Dual-mode 교차 오염

### 근본 원인

BUG-01 최초 수정 시 Phase 0-5 섹션이 `tss-source-handler`, `tss-repo-indexer` 등
Claude Code 전용 에이전트명을 모드 구분 없이 포함. Desktop 빌드가 이 본문을 그대로 복사.

Desktop에는 `tss-*` 에이전트가 존재하지 않으므로 실행 시 에러 가능.

### 수정

실행 절차 섹션을 두 개로 분리:

```markdown
## 실행 절차 — Claude Code Plugin
> 이 섹션은 Claude Code Plugin 모드 전용입니다.
> Claude Desktop은 아래 실행 절차 — Claude Desktop 섹션을 따릅니다.
[Phase 0-5, tss-* 에이전트명 사용]

## 실행 절차 — Claude Desktop
Claude Desktop에서는 아래 스캔 순서 표에 따라 각 @sub-skill 을 순서대로 호출한다.
```

### 검증

```bash
grep -n "Claude Code Plugin\|Claude Desktop" dist_claude_desktop/threat-scan-security/SKILL.md
# → 두 섹션 모두 존재, tss-* 는 Code Plugin 섹션 안에만
grep -c "tss-" dist_claude_desktop/threat-scan-security/SKILL.md
# → Code Plugin 섹션 내부에만 카운트
```

## BUG-03 수정 — SBOM description 오염

### 근본 원인

```yaml
# skills/securityreports-sbom/SKILL.md — 수정 전
description: >
  ... Used by tss-sbom agent (step 8)
```

`tss-sbom`은 Claude Code 전용 에이전트명. Desktop dist에 복사되어 오염.

### 수정

```yaml
# 수정 후
description: >
  ... Used by threat-scan-orchestrator pipeline (step 8).
  Supports 17 ecosystems with lock-file-first transitive detection.
```

## 완료 조건 (검증 가능)

- [ ] Desktop SKILL.md 재빌드 시 `tss-*` 가 `Claude Code Plugin` 섹션 안에만 존재.
- [ ] `securityreports-sbom/SKILL.md` description에 `tss-sbom` 미포함.
- [ ] `commands/threat-scan.md`에 "Phase 5" 완주 지시 존재.

## 검증

```bash
# BUG-01/02
grep -c "전부 반환될 때까지" skills/threat-scan-orchestrator/SKILL.md   # ≥ 1
grep -n "Claude Code Plugin\|Claude Desktop" skills/threat-scan-orchestrator/SKILL.md
# BUG-03
grep "tss-sbom" skills/securityreports-sbom/SKILL.md   # → 없어야 함
# 빌드 후 dist 확인
bash build_claude_desktop.sh && \
  grep -c "tss-" dist_claude_desktop/threat-scan-security/SKILL.md
```
