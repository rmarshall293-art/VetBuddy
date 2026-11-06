"""Career Navigator (ADR 0007; v6 §8).

Rebuilt from "VeteranOS Career Navigator — Architecture" (a reverse-engineered
specification of the separate veteranos-career-navigator repository, whose
source was not supplied: SOURCE_NOT_AVAILABLE). One Python implementation,
carrying all ten documented fixes, with the rule tables in
config/career_rules.json.

The thesis, unchanged: generators propose; a deterministic gate disposes.
Generators may over-propose; the gate refuses anything not traceable to
verified evidence, and every refusal is shown to the person with its reason.

- ``enforcement``: audit, consent broker (field-level allowlist; wellness
  structurally severed; health and protected fields never grantable),
  protected-content guard, evidence bank, fabrication guard, assembly gate.
- ``analysis``: announcement extraction, tokenizer and stemmer, qualification
  matrix (absences never support; legally required credentials block),
  per-category competitiveness labels (no composite score).
- ``documents``: resume, cover letter and STAR proposals, all through the gate.

Pure library: no I/O beyond reading the rules file, no persistence, no
network, no model. Persistence and routes come after G17 (see ADR 0007).
"""

ENGINE_NAME = "vetbuddy.career.core"
ENGINE_VERSION = "1.0.0"
