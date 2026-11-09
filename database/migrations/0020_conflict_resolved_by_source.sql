-- 0020 — A conflict may be resolved by reading the primary source (additive in effect).
--
-- 'resolved_by_primary_source': the readings disagreed, and the tier-1 source
-- (e.g. VA.gov's own rate table) was read and shows which is right. The
-- resolution must name that source and the date it was read. This is not a
-- reviewer's approval: the values it settles stay SOURCE_CHECKED, never VERIFIED.
-- Only the CHECK constraints widen; no row changes.

ALTER TABLE ref.conflict DROP CONSTRAINT conflict_status_check;
ALTER TABLE ref.conflict ADD CONSTRAINT conflict_status_check
  CHECK (status IN ('contested_unresolved', 'resolved_by_design', 'resolved_by_primary_source'));
ALTER TABLE ref.conflict ADD CONSTRAINT conflict_primary_source_resolution
  CHECK (status <> 'resolved_by_primary_source' OR resolution IS NOT NULL);
