# Development Plan Prompt : Compliance Tagging Integration (Threat Scan V2.4.x → V2.5.0)

> Paste this prompt into the development agent (Claude Code) at the root of the `Threat-Scan-Security` repository.
> Input artifacts (place in repo before starting): `compliance-tagmap-distilled.md`, `compliance-tagging-deepdive.md`, `SCHEMA_V1.4_COMPLIANCE_TAGS.md`, `COMPLIANCE_TAGGING_DIRECTIVE_v1.0.md`.

---

You are implementing the Compliance Tagging feature for the `threat-scan-security` skill (Claude Threat Scan), releasing as V2.5.0 with Schema V1.4. Work strictly from the four input artifacts above; where they conflict with this prompt, the artifacts win. Do not invent fields, tags, or behaviors beyond them.

## Ground Rules

1. Non-destructive workflow: create a feature branch; never force-push; never rewrite published schema docs (v1.2/v1.3 stay for backward reference).
2. Schema V1.4 is a strict superset of V1.3: one optional field `compliance_tags`, regex `^#(KISA|AILLM|TA)-[A-Z0-9]+(_[A-Z0-9]+)*$`, 0–4 unique elements, primary-first ordering, EN/KO byte-identical.
3. Stages 1–10 of the pipeline remain inference-only (no code execution); all executable changes are confined to stage-0/stage-11 scripts and repo tooling.
4. Python for all new code. Type hints, no new runtime dependencies beyond the standard library unless already present in the repo.
5. Every phase ends with its acceptance checks passing before the next phase starts. Report progress phase by phase.

## Phase 0 : Repository Intake

- Read `SKILL.md`, `references/docs/SCHEMA_V1.3_ENFORCEMENT.md`, `references/docs/claude-threat-scan-json-schema-v1.3.md`, all files under `references/sub-skills/`, `references/scripts/generate_html_report.py`, `references/dictionary/security-terms-en-ko.json`, and `references/dictionary/security-template.html`.
- Produce a short written map: where finding objects are defined/exemplified, where the HTML generator iterates findings, where the translator rules live.
- Acceptance: the map lists every file you will touch in later phases with a one-line reason.

## Phase 1 : Schema Documents (V1.4)

- Create `references/docs/claude-threat-scan-json-schema-v1.4.md`: copy v1.3 content structure, add `compliance_tags` to every permitted finding example per `SCHEMA_V1.4_COMPLIANCE_TAGS.md` §2, add the governed-namespace table (§2.3) and the AILLM anchor registry (§6) verbatim.
- Create `references/docs/SCHEMA_V1.4_ENFORCEMENT.md`: inherit all v1.3 enforcement rules unchanged, append the tag enforcement rules (format, cardinality, ordering, EN/KO parity, prohibited variants list from §3.1, stage read-only rule from §3.2).
- Update `SKILL.md` schema-reference section to list v1.4 docs first, v1.3/v1.2 as backward references. Bump the JSON example: `scanner_version` → `"Claude Threat Scan V2.5"`, and add `compliance_tags` to one example finding.
- Acceptance: grep confirms no v1.3 doc was modified; v1.4 docs contain the regex exactly once each, character-identical to this prompt's Ground Rule 2.

## Phase 2 : Tagging Directives into the Skill

- Copy `compliance-tagmap-distilled.md` to `references/docs/compliance-tagmap-distilled.md`.
- Copy `compliance-tagging-deepdive.md` to `references/docs/compliance-tagging-deepdive.md`.
- Edit each emitting sub-skill (`static-code-analyzer.md`, `binary-analyzer.md`, `skill-security-analyzer.md`, `sensitive-pattern-matcher.md`, `agent-policy-verifier.md`, `securityreports-sbom.md`, `relationship-graph-analyzer.md`, `model-validity-analyzer.md`) with a single uniform block: an instruction to load `compliance-tagmap-distilled.md`, assign `compliance_tags` at finding emission per its §1 rules, and the stage-specific expected range row from its §2. Keep each edit minimal and diff-style; do not restructure the sub-skill files.
- Edit `securityreports-deepdive.md`: add a "Tag Verification" section that references `compliance-tagging-deepdive.md` and folds V-1…V-7 plus the three cross-finding sweeps into the existing Level 1–3 procedure; extend the output-contract table with the `compliance_tags` delta row.
- Edit `report-merger.md`: tags pass through verbatim, dedup within a finding, never reorder (primary-first is semantic).
- Edit `bilingual-translator.md`: tags are invariant tokens, byte-identical in `korean_report`; control names for prose come from the dictionary, never substituted into tags.
- Acceptance: every emitting sub-skill contains exactly one tagging block; deepdive sub-skill references CTID-V; no sub-skill instructs emitting tags on `prompt_optimization` or `recommendations`.

## Phase 3 : Validator

- Create `references/scripts/validate_compliance_tags.py`: standalone, stdlib-only, CLI `python3 validate_compliance_tags.py <report.json>`.
  - Implements the pseudocode from `SCHEMA_V1.4_COMPLIANCE_TAGS.md` §3.3: regex hard-fail, unknown-control-ID warn, cardinality/uniqueness checks, EN/KO parity check across all eight permitted arrays, prohibited-variant detection (fail if `tags`, `kisa_tags`, `control_mapping`, etc. appear on finding objects), and placement check (fail if `compliance_tags` appears on `scan_metadata`, `repository_summary`, `prompt_optimization[]`, `recommendations[]`).
  - Exit codes: 0 clean, 1 errors, 2 warnings-only. Machine-readable JSON summary on `--json`.
- Acceptance: run against (a) a legacy v1.3 report → exit 0; (b) a synthetic v1.4 report with correct tags → exit 0; (c) synthetic violations for each rule class → each individually caught with a distinct message. Commit the three fixtures under `tests/fixtures/`.

## Phase 4 : HTML Renderer (stage 11)

- Extend `generate_html_report.py` and `security-template.html`:
  - Badge per tag next to the severity badge; badge text = raw tag; `title` tooltip = control name in the report language.
  - Namespace colors: `KISA` `#3a7bd5`, `AILLM` `#8a5cd6`, `TA` `#2ea860`; unknown-valid `#5a6173`. Respect existing dark-theme tokens and table-overflow protections (explicit column widths).
  - Absent field or `[]` → no badge row rendered.
  - Optional `--coverage` flag: render-time KISA category coverage table computed from tags; never written back to JSON.
- Extend `references/dictionary/security-terms-en-ko.json` with the `compliance_controls` map for all 59 governed tags (49 KISA + 9 AILLM + 10 TA), `{tag: {"en": ..., "ko": ...}}`. Source EN names from the distilled tag map; KO names must use KISA official Korean weakness names for the KISA namespace.
- Acceptance: generate HTML from fixture (b); visually verify badges, tooltips, and that a finding without tags renders unchanged versus V2.4 output; run the existing HTML quality gates (tag balance, overflow, section completeness, no raw JSON leakage).

## Phase 5 : Orchestrator & Version Wiring

- `SKILL.md`: bump description to v2.5.0; add the two CTID docs to the reference tables; add one line to the 스캔 순서 notes: stage 1–8 assign tags per CTID-D, stage 8.5 verifies per CTID-V, stages 9–11 are tag-read-only.
- Add `validate_compliance_tags.py` invocation guidance to the stage-11 section (validation before HTML generation; stage 11 is already the script-permitted stage, so validation runs there, not in stages 1–10).
- Acceptance: `grep -r "V2.4"` returns only changelog/history mentions; pipeline stage table shows no new stages (tagging is folded into existing stages, not appended).

## Phase 6 : End-to-End Verification & Release Notes

- Run one full scan against a small fixture repo containing at minimum: a hardcoded secret, an eval-on-input sink, an agent YAML without `disallowed_tools`, a Terraform public-ACL bucket, and one benign file. Confirm the produced report:
  1. passes `validate_compliance_tags.py` with exit 0,
  2. tags match CTID-D worked-example expectations,
  3. deep-dive output shows at least one V-rule exercised (add a deliberately misattributable finding to force a V-1 re-attribution),
  4. KO report tags are byte-identical to EN,
  5. HTML renders badges and passes quality gates.
- Write `CHANGELOG` entry for V2.5.0: Schema V1.4 (`compliance_tags`), CTID-D/CTID-V integration, validator, badge rendering, dictionary additions. Note explicitly: backward compatible, absent field = legacy.
- Deliver: branch diff summary, fixture reports (JSON + HTML), validator output, and any deviations from the input artifacts with justification.

## Out of Scope (do not implement)

- New pipeline stages, new finding arrays, `findings_summary`/`executive_summary` (still prohibited), tagging of `prompt_optimization` or `recommendations`, localization of tag strings, live web calls from any script, and any modification to KISA control numbering.
