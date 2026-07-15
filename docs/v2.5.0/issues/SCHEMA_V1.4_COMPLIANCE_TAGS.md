# Claude Threat Scan JSON Schema V1.4 : Compliance Tags Amendment

> **Audience**: scanner developer (Claude Threat Scan V2.4.x → V2.5.0)
> **Baseline**: Schema V1.3 (`claude-threat-scan-json-schema-v1.3.md`, `SCHEMA_V1.3_ENFORCEMENT.md`)
> **Compatibility**: V1.4 is a strict superset of V1.3. Every valid V1.3 report is a valid V1.4 report. The single addition is one optional field.
> **Status**: Specification for implementation · 2026-07-15

---

## 1. Change Summary

| # | Change | Type |
|---|---|---|
| 1 | New optional field `compliance_tags` on all finding objects | Addition |
| 2 | Enforcement rules for the field (format, cardinality, ordering, casing) | Addition |
| 3 | New prohibited field variants (`tags`, `compliance`, `kisa_tags`, `control`, `control_mapping`) | Enforcement extension |
| 4 | HTML generator (stage 11) badge rendering for tags | Renderer extension |
| 5 | Translation invariance rule for tags (stage 10) | Pipeline rule |

Nothing in V1.3 is removed, renamed, or retyped. `scan_metadata.scanner_version` becomes `"Claude Threat Scan V2.5"` when this schema ships.

## 2. Field Definition

### 2.1 `compliance_tags`

```json
{
  "id": "STATIC-001",
  "file": "src/api/user.py",
  "line": 42,
  "issue": "SQL Injection",
  "description": "External input concatenated into query. Ref: CWE-89; OWASP Top 10 A03.",
  "severity": "High",
  "status": "Confirmed",
  "compliance_tags": ["#KISA-1_1"],
  "recommendation": "Use parameterized queries."
}
```

| Property | Rule |
|---|---|
| Name | `compliance_tags` : exact, lowercase, plural. No variants. |
| Type | `array` of `string` |
| Presence | **Optional.** Absent field = legacy/untagged finding (valid). Present-but-empty `[]` = "verified: no governed control applies" (also valid, and semantically distinct from absent). |
| Element pattern | `^#(KISA\|AILLM\|TA)-[A-Z0-9]+(_[A-Z0-9]+)*$` |
| Cardinality | 0–4 elements |
| Uniqueness | elements unique within the array |
| Ordering | primary (root-cause) tag first; order is semantic, preserve it |
| Localization | **None.** `korean_report` carries the array byte-identical to `english_report`. Tags are invariant tokens. |

### 2.2 Placement

The field is permitted on every element of:

- `static_code_findings[]`
- `binary_analysis_findings[]`
- `skill_risk_findings[]`
- `agent_policy_findings[]`
- `sensitive_patterns[]`
- `relationship_findings[]`
- `model_validity_findings[]`
- finding objects inside `sbom_analysis`

It is **not** permitted on `scan_metadata`, `repository_summary`, `graph_verdict`, `prompt_optimization[]` (quality items, not compliance findings), or `recommendations[]`.

### 2.3 Governed namespaces (closed set)

| Namespace | Governing framework | Valid control IDs |
|---|---|---|
| `KISA` | KISA Software Security Weakness Diagnosis Guide (Nov 2021), fixed | `1_1`–`1_17`, `2_1`–`2_16`, `3_1`–`3_2`, `4_1`–`4_3`, `5_1`–`5_5`, `6_1`–`6_4`, `7_1`–`7_2` |
| `AILLM` | CTID AI/LLM control set v1.1 (anchored: OWASP LLM Top 10 2025 / CWE-1426, CWE-1427 / MITRE ATLAS) | `8_1`–`8_9` |
| `TA` | Technical/Administrative checklist, statically assessable subset | `T_A1`, `T_C3`, `T_D1`–`T_D3`, `T_E1`, `T_I1`–`T_I3`, `A_B1` |

Validators SHOULD warn (not fail) on a syntactically valid tag whose control ID is outside these lists, to allow forward-compatible appends. The regex itself MUST fail hard.

## 3. Enforcement Rules (append to SCHEMA enforcement doc)

### 3.1 Prohibited variants (schema violations)

- `tags`, `compliance`, `kisa_tags`, `kisaTags`, `control`, `controls`, `control_mapping`, `owasp_tags`
- lowercase namespaces (`#kisa-1_1`), missing `#`, `§`/`.`/`-` separators inside control IDs (`#KISA-1.1`, `#KISA-1-1`)
- tags embedded in `issue` or `severity` strings
- CWE/OWASP/ATLAS identifiers formatted as `#`-tags (`#CWE-89` is a violation; CWE belongs in `description`/`recommendation` prose)

### 3.2 Cross-report invariants

- EN/KO parity: for every finding, `english_report` and `korean_report` carry identical `compliance_tags` (same elements, same order).
- Merge (stage 9): tags pass through verbatim; dedup within a finding only; never dedup/reorder across findings.
- Deep dive (stage 8.5) is the only stage permitted to modify tags after emission; stages 9–11 are read-only with respect to tag content.

### 3.3 Validator pseudocode (Python, for `generate_html_report.py` or a standalone check)

```python
import re

TAG_RE = re.compile(r"^#(KISA|AILLM|TA)-[A-Z0-9]+(_[A-Z0-9]+)*$")

KNOWN = {
    "KISA": {f"1_{i}" for i in range(1, 18)} | {f"2_{i}" for i in range(1, 17)}
          | {"3_1", "3_2", "4_1", "4_2", "4_3"}
          | {f"5_{i}" for i in range(1, 6)} | {f"6_{i}" for i in range(1, 5)}
          | {"7_1", "7_2"},
    "AILLM": {f"8_{i}" for i in range(1, 10)},
    "TA": {"T_A1", "T_C3", "T_D1", "T_D2", "T_D3", "T_E1",
           "T_I1", "T_I2", "T_I3", "A_B1"},
}

def validate_tags(tags: list[str]) -> list[str]:
    errors: list[str] = []
    if len(tags) > 4:
        errors.append(f"cardinality>{4}: {len(tags)}")
    if len(set(tags)) != len(tags):
        errors.append("duplicate tags")
    for t in tags:
        m = TAG_RE.match(t)
        if not m:
            errors.append(f"format violation: {t}")
            continue
        ns, cid = m.group(1), t.split("-", 1)[1]
        if cid not in KNOWN[ns]:
            errors.append(f"warn: unknown control id {t}")  # warn, not fail
    return errors
```

## 4. Renderer Requirements (stage 11, `generate_html_report.py`)

- Render each tag as a badge adjacent to the severity badge; badge text is the raw tag string.
- Tooltip (`title` attribute) shows the control name; Korean control names load from `security-terms-en-ko.json` (new `compliance_controls` section, see §5).
- Namespace badge colors (dark theme tokens): `KISA` `#3a7bd5`, `AILLM` `#8a5cd6`, `TA` `#2ea860`. Unknown-but-valid tags render in muted `#5a6173`.
- Absent field → no badge row. Empty array → no badge row (do not render "no tags").
- Optional coverage summary (KISA category × Pass/Vulnerable-style table) is computed at render time from tags; it MUST NOT be written back into the JSON (`findings_summary` remains prohibited).

## 5. Dictionary Additions (`security-terms-en-ko.json`)

Add a `compliance_controls` map: tag → `{ "en": "<control name>", "ko": "<제어 항목명>" }` for all 59 governed tags (49 KISA + 9 AILLM + 10 TA + `A_B1` included in the 10). Used for tooltips/prose only; never substituted into the tag itself.

## 6. AILLM Anchor Registry (normative reference table)

Verified against primary sources, access date 2026-07-15: OWASP Top 10 for LLM Applications 2025 (genai.owasp.org), CWE v4.20 (cwe.mitre.org : CWE-1426 "Improper Validation of Generative AI Output", CWE-1427 "Improper Neutralization of Input Used for LLM Prompting"), MITRE ATLAS (atlas.mitre.org, 2025-10 agentic update).

| Tag | Control | OWASP LLM 2025 | CWE | ATLAS |
|---|---|---|---|---|
| `#AILLM-8_1` | Prompt Injection (direct) | LLM01 | CWE-1427 | AML.T0051.000 |
| `#AILLM-8_2` | Indirect Prompt Injection | LLM01 | CWE-1427 | AML.T0051.001 |
| `#AILLM-8_3` | Trusting LLM Output | LLM05 | CWE-1426 | : |
| `#AILLM-8_4` | Sensitive Data in Context | LLM02 · LLM07 | CWE-200 | AML.T0056 · AML.T0057 |
| `#AILLM-8_5` | Unbounded Output / Cost DoS | LLM10 | CWE-400/770 | : |
| `#AILLM-8_6` | Missing LLM Audit Logging | : | CWE-778 | : |
| `#AILLM-8_7` | Excessive Agency | LLM06 | CWE-250 (assumed) | AML.T0110 |
| `#AILLM-8_8` | Vector & Embedding Weaknesses | LLM08 | CWE-284 (assumed) | AML.T0070 |
| `#AILLM-8_9` | AI Supply Chain | LLM03 | CWE-502/494 · CWE-1357 | AML.T0010 |

Two CWE anchors are marked (assumed): CWE-250 for 8_7 and CWE-284 for 8_8 are logical mappings without an official OWASP↔CWE assignment at spec time; revisit when OWASP publishes updated CWE cross-references.

## 7. Migration & Versioning

- Readers: treat missing `compliance_tags` as legacy; no backfill required.
- Writers: emit the field on all new findings once analyzers ship CTID-D; partial rollout (some stages tagging, others not) is valid under the optional-field rule but MUST NOT persist past one release.
- Version bump: schema docs `claude-threat-scan-json-schema-v1.4.md` + `SCHEMA_V1.4_ENFORCEMENT.md`; keep v1.3 docs for backward reference, mirroring the existing v1.2/v1.3 convention.
