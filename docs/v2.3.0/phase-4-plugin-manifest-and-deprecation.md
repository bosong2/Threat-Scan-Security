# Phase 4 — 플러그인 매니페스트 + 레거시 deprecation + 설정/버전

## 목표

Claude Code가 이 리포지토리를 **로컬 플러그인으로 로드**할 수 있게 매니페스트를 추가하고, 레거시 스킬을 deprecated 처리하며, 실행 권한과 버전을 갱신한다.

> 본 단계는 "로딩 가능"까지가 범위. 버전드 zip 릴리스·마켓플레이스 게시·배포용 INSTALL.md는 **범위 밖**(향후 패키징 버전).

## 변경 1 — `.claude-plugin/plugin.json`

```json
{
  "name": "threat-scan-security",
  "version": "2.3.0",
  "description": "Scan skills/agents/plugins/repos for security threats and model validity; emit bilingual JSON + static HTML report. Dual-mode: Claude Code plugin and Claude Desktop skill.",
  "author": { "name": "Bosung Hong" },
  "keywords": ["security", "skill", "agent", "plugin", "audit", "threat-scan", "html-report"]
}
```

## 변경 2 — `.claude-plugin/marketplace.json`

```json
{
  "name": "threat-scan-security-marketplace",
  "owner": { "name": "Bosung Hong" },
  "metadata": { "description": "Threat-scan-security — security + model-validity scanner with HTML reporting" },
  "plugins": [
    { "name": "threat-scan-security", "source": "./",
      "description": "Full threat-scan pipeline (단계 0–11) → bilingual JSON + KO HTML report." }
  ]
}
```

- 로컬 설치: `/plugin marketplace add <repo-path>` → `/plugin install threat-scan-security@threat-scan-security-marketplace`.

## 변경 3 — 레거시 `securityreports-*` deprecated 표기 (5개)

`securityreports-{scan,sbom,secrets,static,help}/SKILL.md` 각 본문 상단(frontmatter 직후)에 안내 블록 추가:

```markdown
> ⚠️ **DEPRECATED (v2.3.0+)**: 이 명령은 구 SecurityScan 세대입니다.
> v2.1 통합 파이프라인은 `/threat-scan <target>`을 사용하세요.
> (그래프 전파·모델 유효성·심층분석·HTML 리포트 포함)
```

- frontmatter `description` 앞에 `[DEPRECATED]` 접두 추가(목록에서 식별).
- **삭제하지 않음** — 기존 사용자 호환 유지.

## 변경 4 — `.claude/settings.local.json`

`permissions.allow`에 생성기 실행 + 소스 준비 셸 추가:

```json
"Bash(python3 *scripts/generate_html_report.py*)",
"Bash(python3 *generate_html_report.py*)"
```

(기존 git clone/unzip 계열 항목은 source-handler 용도로 유지)

## 변경 5 — `VERSION`

- `2.2.0` → `2.3.0`.

## 완료 조건 (검증 가능)

- [ ] `.claude-plugin/plugin.json`·`marketplace.json` 존재, 유효 JSON, version 2.3.0.
- [ ] `securityreports-*` 5개에 DEPRECATED 블록 + `/threat-scan` 안내, frontmatter description에 `[DEPRECATED]`.
- [ ] `.claude/settings.local.json`에 `generate_html_report.py` 실행 허용 항목.
- [ ] `VERSION` = 2.3.0.

## 검증

```bash
cd Threat-scan-security
python3 -c "import json;json.load(open('.claude-plugin/plugin.json'));json.load(open('.claude-plugin/marketplace.json'));print('JSON OK')"
grep -l "DEPRECATED" skills/securityreports-*/SKILL.md | wc -l   # → 5
grep -q "generate_html_report.py" .claude/settings.local.json && echo "perm OK"
cat VERSION   # → 2.3.0
```
