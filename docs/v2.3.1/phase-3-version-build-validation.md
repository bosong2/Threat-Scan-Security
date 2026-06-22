# Phase 3 — 버전·빌드·검증

## 목표

버전을 2.3.1로 올리고, Desktop 빌드 회귀가 없는지, SBOM 확장과 문서가 패키지에 반영됐는지 검증한다.

## 변경

1. `VERSION`: `2.3.0` → `2.3.1`.
2. `.claude-plugin/plugin.json`: version `2.3.0` → `2.3.1`, description에 "광범위 의존성 명세 인식" 반영(선택).
3. `build_claude_desktop.sh`: 설명 버전 문자열 동기화(있으면). 루트 문서(README/LICENSE 등)는 Desktop zip 필수 아님 — 포함 여부는 선택(LICENSE/NOTICE는 포함 권장).
4. 빌드 재실행 → `threat-scan-security.zip` 갱신.

## 완료 조건 (검증 가능)

- [ ] `VERSION` = 2.3.1, `plugin.json` version 2.3.1.
- [ ] `bash build_claude_desktop.sh` 성공, 로그 `VERSION=2.3.1`.
- [ ] zip 내 `references/sub-skills/securityreports-sbom.md`에 확장 매트릭스(lock 파일) 반영.
- [ ] Desktop 빌드 구성 회귀 없음(기존 파일 모두 유지).
- [ ] LICENSE/NOTICE zip 포함(포함 선택 시).

## 검증

```bash
cd Threat-scan-security
cat VERSION                                   # 2.3.1
grep '"version"' .claude-plugin/plugin.json   # 2.3.1
out=$(bash build_claude_desktop.sh 2>&1); echo "$out" | grep "VERSION="
unzip -p threat-scan-security.zip threat-scan-security/references/sub-skills/securityreports-sbom.md | grep -c "poetry.lock\|requirements-lock"
```

## 최종 완결성 점검 (GOAL DoD 매핑)

- SBOM 17 생태계 + lock 우선 → Phase 1 검증.
- LICENSE/문서 5종 + mermaid + dual-mode → Phase 2 검증.
- 버전·빌드 회귀 → 본 Phase.
- 단일 원천 1회 수정으로 Desktop·Code 동시 반영 확인(securityreports-sbom는 tss-sbom 에이전트가 참조).
