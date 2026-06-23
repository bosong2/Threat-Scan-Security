# Phase 2 — 버전 범프·빌드·릴리스

## 변경 파일

| 파일 | 변경 내용 |
|------|-----------|
| `VERSION` | `2.3.1` → `2.3.2` |
| `.claude-plugin/plugin.json` | `"version": "2.3.2"` |
| `build_claude_desktop.sh` | description 문자열 `v2.3.1` → `v2.3.2` |
| `commands/threat-scan-help.md` | `(v2.3.0)` → `(v2.3.2)` |
| `CHANGELOG.md` | `[2.3.2]` 항목 추가 |

## 완료 조건 (검증 가능)

- [ ] `cat VERSION` → `2.3.2`
- [ ] `grep '"version"' .claude-plugin/plugin.json` → `2.3.2`
- [ ] `bash build_claude_desktop.sh` 성공, 로그 `VERSION=2.3.2`
- [ ] `unzip -p threat-scan-security.zip .../SKILL.md | grep "v2.3.2"`
- [ ] `git tag v2.3.2` 푸시 → GitHub Actions 릴리스 성공

## 검증

```bash
cat VERSION
grep '"version"' .claude-plugin/plugin.json
out=$(bash build_claude_desktop.sh 2>&1); echo "$out" | grep "VERSION="
git log --oneline -3
GH_HOST=github.com gh run list --repo bosong2/Threat-Scan-Security --workflow release.yml --limit 1
```
