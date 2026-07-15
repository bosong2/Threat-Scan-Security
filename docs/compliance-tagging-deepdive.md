# Compliance Tag Verification : Deep-Dive Directive (CTID-V v1.1)

> **Role**: Addendum to `securityreports-deepdive.md`, executed inside pipeline stage 8.5 of `threat-scan-security`.
> **Precondition**: Findings arrive from stages 1–8 already carrying `compliance_tags` assigned per `compliance-tagmap-distilled.md` (CTID-D).
> **Scope**: Same population as deep-dive triage : findings with Severity ≥ Medium, undecided `status`, missing `deep_dive_result`, or ambiguous language ("could/may/potentially"). Low-severity findings are NOT re-tagged; their Phase-1 tags stand as final.

---

## 1. Position in the Deep-Dive Procedure

Tag verification is folded into the existing MAX DEPTH = 3 analysis. It adds no separate pass; it reuses the context already loaded for triage.

| Deep-dive level | Existing task | Added tag task |
|---|---|---|
| Level 1 : direct analysis | confirm risk pattern at file:line | check the primary tag's root-cause trigger (CTID-D §3–§5) actually matches the code |
| Level 2 : context tracing | trace input source, sanitization, call path | detect re-attribution: if the true root cause is a different control, replace the primary tag |
| Level 3 : impact evaluation | exploit scenario, protection efficacy, final grade | add missing secondary tags surfaced by tracing (≤ 4 total); finalize order primary-first |

## 2. Verification Rules

- **V-1 (Re-attribution)**: If Level 2–3 analysis shows the defect's root cause belongs to a different control, replace the primary tag and demote or drop the original. Record the re-attribution in one sentence inside `deep_dive_result` (e.g., "Tag re-attributed #KISA-1_2 → #KISA-2_2: sink unreachable; the exploitable defect is the missing ownership check.").
- **V-2 (Status independence)**: Tags describe the violated control class of the observed pattern; `status` describes exploitability.
  - `Confirmed` → tags retained, corrected if misattributed.
  - `Mitigated` → tags retained unchanged. Mitigation is expressed in `status`/`deep_dive_result`, never by removing tags.
  - `False Positive` → tags retained (they name what the pattern would have violated). Never strip tags to "clean up" a false positive; the exoneration lives in `status`.
- **V-3 (Additions)**: Secondary tags may be added only for controls independently violated by the same evidence, discovered through Level-2 tracing. Ceiling stays at 4; dedup mandatory.
- **V-4 (Namespace discipline)**: Re-check namespace applicability under full context:
  - `AILLM` tags require confirmed LLM/agent features in the traced path. If Phase 1 tagged `#AILLM-*` but tracing shows no LLM involvement, re-attribute to the correct `KISA` control or `[]`.
  - `TA` tags require IaC/config artifact evidence. Application code never carries `TA` tags.
  - Never migrate an `AILLM` finding into a `KISA` number for reporting convenience (framework isolation, CTID P-2).
- **V-5 (Empty is valid)**: If verification concludes no governed control applies, set `compliance_tags: []` and state why in `deep_dive_result`. An empty array after deep dive is a deliberate verdict, not an omission.
- **V-6 (No evidence expansion)**: Tag verification never adds evidence beyond existing masking rules. `masked_value` constraints remain binding.
- **V-7 (Format re-validation)**: On write-back, every tag must still match `^#(KISA|AILLM|TA)-[A-Z0-9]+(_[A-Z0-9]+)*$`, uppercase, unique, ≤ 4, primary-first. A malformed tag introduced at any stage is corrected here; stage 8.5 is the last inference stage before merge.

## 3. Cross-Finding Consistency Checks (once per deep-dive session)

After per-finding verification, run three sweeps over the full finding set:

1. **Duplicate-defect coherence**: Findings pointing at the same file:line defect from different analyzers (e.g., static + sensitive-pattern both flagging one hardcoded key) must carry consistent primary tags. Align them; do not merge the findings themselves (merging is stage 9's job).
2. **Range sanity**: Each finding's tags must be plausible for its source array per CTID-D §2 (e.g., an `agent_policy_findings` entry carrying `#KISA-1_16` is almost certainly misattributed).
3. **AILLM gate coherence**: If ANY finding carries an `AILLM` tag, the target factually has LLM features; if the repository summary says otherwise, resolve the contradiction before merge.

## 4. Interaction with `code_fix`

When a `code_fix` is emitted, the fix must remediate the control named by the **primary tag**. If the fix addresses a different control than the primary tag names, either the tag or the fix is wrong : resolve before write-back. This is a self-consistency gate, not a new field.

## 5. Output Contract (delta over existing deep-dive output)

Existing required fields (`status`, `deep_dive_result`, optional `code_fix`) are unchanged. This directive adds:

| Field | Change |
|---|---|
| `compliance_tags` | verified/corrected in place; never renamed; may become `[]` |
| `deep_dive_result` | one added sentence ONLY when tags changed (re-attribution/addition/emptying rationale) |

No other fields are introduced. Downstream stages then apply the standing invariants: stage 9 preserves and dedups tags, stage 10 treats them as untranslatable invariant tokens (byte-identical in `korean_report`), stage 11 renders them as badges.
