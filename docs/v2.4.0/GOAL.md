# v2.4.0 — 오케스트레이션 장애 방어 재설계 (GOAL)

> 설계 근거: [PROPOSAL.md](PROPOSAL.md). 사용자 확정: **C=병렬 유지**, **D=실패 시 중단(명확한 상황 전달 우선)**.
> A(파일=진실)·B(프로브)·E(완료 로깅 훅)·F(allow-rule 문서화+프로브) 모두 채택.

## 목표 (1문장)

병렬 분석 단계에서 발생하던 권한 hang·무응답 종료·다음 단계 미진행(stuck)을, **"출력 파일=완료 진실"
원칙 + 3계층 장애 방어(사전 프로브·배치 후 체크포인트·완료 로깅 훅)**로 제거하고, 실패 시 명확히
중단·보고한다.

## 불변 제약

1. **Desktop 무영향** — `skills/*/SKILL.md` 본문 불변. Desktop은 단일 컨텍스트라 이 문제 없음.
2. **결정론 우선** — 환경검증·체크포인트·재시도 판정은 순수 Bash(LLM 토큰 0). LLM은 분석에만.
3. **이식성** — Workflow 도구 미사용(배포 플러그인 런타임에서 불가). Skill+Agent+Bash로만 구성.
4. **Schema V1.3 불변** — 출력 JSON 스키마 유지.

## 완료 정의 (검증 가능)

- [ ] `/threat-scan <repo>` 가 Phase 0' → 0 → 1 → 2 → 3 → 4 → 5 를 **중단 없이 완주**한다.
- [ ] Phase 0'가 SCAN_TMP 쓰기가능·git·python3·**서브에이전트 Write 가능 여부**를 배치 전에 검증한다.
- [ ] Phase 1 병렬 배치 후 Bash 체크포인트가 8개 파일의 존재·JSON유효·`_meta`를 검증하고 상태표를 출력한다.
- [ ] MISSING/INVALID 발생 시 해당 에이전트만 1회 재시도하고, 그래도 실패하면 **원인 명시 후 중단**한다.
- [ ] 모든 파일 OK일 때만 다음 Phase로 라우팅한다.
- [ ] SubagentStop 훅이 각 `tss-*` 종료 시 progress.log에 1줄 기록한다.
- [ ] `docs/INSTALLATION.md`에 서브에이전트 Write allow-rule 안내가 있다.
- [ ] 버전 2.4.0 정합(VERSION·plugin.json·help·CHANGELOG).

## Phase

| Phase | 산출 |
|-------|------|
| 1 | 오케스트레이터 SKILL.md Code 섹션 재작성(Phase 0' 환경검증+프로브, Phase 1 병렬+체크포인트+재시도+중단, 라우팅) |
| 2 | hooks.json matcher `tss-*` 완료 로깅 + 로깅 스크립트 + 에이전트 OUTPUT_PATH 계약 정리 |
| 3 | INSTALLATION allow-rule 안내 + CLAUDE.md 패턴 갱신 + 버전 2.4.0 범프 |

## 범위 밖

- Desktop 파이프라인 변경.
- 부분 진행(partial) 모드 — D 확정에 따라 실패 시 중단이 기본.
- 실행 중 라이브 모니터링 — 네이티브 제약(C2)으로 불가, 사전 프로브+배치 후 체크포인트+훅 로그로 대체.
