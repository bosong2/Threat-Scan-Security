# Phase 2 — Apache 2.0 라이선스 + 문서 세트

## 목표

Apache 2.0 라이선스를 적용하고, 현재 버전 기준의 깔끔한 문서 5종을 루트에 작성한다. **Claude Desktop skill·Claude Code plugin 양쪽**을 모두 다룬다.

## 공통 문서 원칙

- **두괄식**: 각 문서·섹션은 결론/핵심을 먼저.
- **현재 버전만**: 과거 히스토리 서술 금지(CHANGELOG 제외).
- **간결**: 불필요하게 길지 않게, 표·다이어그램 활용.
- **mermaid**: 구조·흐름은 mermaid 코드 블록으로 시각화.
- **dual-mode 명시**: 모든 문서에 Desktop/Code 두 경로를 병기.

## 변경 1 — `LICENSE` (Apache 2.0)

표준 Apache License 2.0 전문. Copyright: `Copyright 2026 Bosung Hong`.

## 변경 2 — `NOTICE`

Apache 2.0 NOTICE 파일. 프로젝트명·저작권·외부 의존 고지(Chart.js CDN — MIT, 리포트 뷰어 한정).

## 변경 3 — `README.md`

- 한 줄 소개 + 핵심 가치(보안+모델 유효성+연관관계+HTML 리포트).
- **Dual-mode 배지/표**: Desktop skill vs Code plugin.
- 빠른 시작(두 모드 각각 3줄 이내).
- 파이프라인 mermaid `flowchart` (단계 0–11).
- 기능 요약표, 라이선스(Apache 2.0), 문서 링크.

## 변경 4 — `INSTALLATION.md`

- **결론 먼저**: 두 가지 설치 경로 표.
- Claude Desktop: `build_claude_desktop.sh` → zip → Settings▸Skills▸Upload.
- Claude Code: `/plugin marketplace add <path>` → `/plugin install`.
- 요구사항(Python 3, 네트워크 선택), 검증 방법, 제거 방법.
- mermaid `flowchart` 설치 결정 트리.

## 변경 5 — `USER_GUIDE.md`

- **결론 먼저**: `/threat-scan <target>` 한 줄이 전부.
- 입력 유형(로컬/GitHub/ZIP), 출력물(JSON + KO HTML), 커맨드 표(`/threat-scan`, `/threat-scan-html`, `/threat-scan-help`).
- Desktop 사용법(오케스트레이터 호출)·Code 사용법(슬래시 커맨드) 병기.
- verdict/severity/model_effectiveness 의미표.
- HTML 리포트 보기(EN/KO 토글·프린트), SBOM lock 파일 권장 팁.

## 변경 6 — `ARCHITECTURE.md`

- **결론 먼저**: dual-mode 단일 원천 구조 1문단 + mermaid.
- mermaid `flowchart`: 단일 원천(`skills/*/SKILL.md`) → Desktop 빌드 경로 / Code 에이전트 참조 경로.
- 컴포넌트 매핑표(skill ↔ tss-agent ↔ command).
- 파이프라인 단계 시퀀스(mermaid `sequenceDiagram` 또는 flowchart).
- 디렉토리 레이아웃, 공유 자산(dictionary/scripts), 제약(LLM 경계·결정론).

## 변경 7 — `CHANGELOG.md`

- Keep a Changelog 형식, 최신순. SemVer.
- `2.3.1`(SBOM 확장+문서), `2.3.0`(dual-mode), `2.2.0`(HTML 리포트), `2.1.x`(그래프·모델·deepdive), `2.0.0`(기준선) 요약.

## 변경 8 — 구 문서 리다이렉트

`docs/INSTALLATION.md`·`docs/USAGE_GUIDE.md`를 짧은 리다이렉트 스텁으로 교체(루트 정식 문서 가리킴) — 드리프트/혼동 제거.

## 완료 조건 (검증 가능)

- [ ] `LICENSE`(Apache 2.0 전문)·`NOTICE` 존재.
- [ ] `README.md`·`INSTALLATION.md`·`USER_GUIDE.md`·`ARCHITECTURE.md`·`CHANGELOG.md` 루트 존재.
- [ ] 각 문서에 Desktop·Code 두 경로 모두 언급.
- [ ] README·ARCHITECTURE·INSTALLATION에 mermaid 블록 존재.
- [ ] 구 `docs/INSTALLATION.md`·`docs/USAGE_GUIDE.md` 리다이렉트 스텁.

## 검증

```bash
cd Threat-scan-security
ls LICENSE NOTICE README.md INSTALLATION.md USER_GUIDE.md ARCHITECTURE.md CHANGELOG.md
head -1 LICENSE   # Apache License 흔적
for f in README.md INSTALLATION.md ARCHITECTURE.md; do grep -q '```mermaid' "$f" && echo "mermaid OK: $f"; done
for f in README.md INSTALLATION.md USER_GUIDE.md ARCHITECTURE.md; do grep -qiE "desktop" "$f" && grep -qiE "claude code|plugin" "$f" && echo "dual OK: $f"; done
```
