"""Guard & Reserve Benefit Vault: the v8 Guard/Reserve role of Benefits Intelligence (ADR 0011).

National Guard, Reserve and AGR members get a vault view built for them: they
answer in their own terms (component, duty status, the authorities on their
orders, qualifying days), and the role turns those answers into the vault's
facts, checks the Operation Sentinel rule leads, and puts the Guard and
Reserve records first.

What the role is not:

- not a second registry: every record is a Benefit Vault registry record;
- not a second matcher: every outcome comes from ``vault.matcher``;
- not a second puller: pulls run through ``benefits_intelligence_agent`` and
  the broker, under the person's grant (only that agent may pull);
- not a decider: duty-status classification restates the Sentinel dataset
  (data/reference/guard_reserve.json); it is not a benefit determination.

Modules: ``policy`` (the authored policy and the Sentinel dataset, validated),
``profile`` (Guard & Reserve facts, classification, derived vault facts and
rule-lead checks), ``agent`` (the role over the parent agent) and ``api``
(routes under /api/v1/vault/guard-reserve).
"""

ROLE_ID = "guard_reserve_agent"
ROLE_VERSION = "1.0.0"
