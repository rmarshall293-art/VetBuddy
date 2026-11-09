"""Pull providers over slice 03 stores (VD06, owner decision 2026-10-29; ADR 0006).

A provider is another agent's store, seen by the vault only through the pull
broker, under a grant the person gave, logged by key and never by value. This
module wires the one holder whose facts slice 03 actually records:
``service_profile_agent``, over ``service_record`` (what the person declared at
onboarding).

It provides only what that record says without guessing:

* ``component``: active, guard or reserve, when the declared status is one of
  active duty, National Guard or Reserve. Retired and separated people did not
  say which component they served in, so nothing is provided.
* ``service_status``: retired for "retired"; separated for "separated" and
  "medically separated"; serving for active duty, Guard or Reserve whose
  declared end date is unknown or in the future. A serving component with a
  past end date is ambiguous and is not provided.

Deliberately not provided, although the manifest exposes them:

* ``residence_state``: onboarding asks where the person lives now, which is
  not their legal residence (the state definition trap).
* ``guard_state``, ``duty_station_state``, ``on_active_duty_orders``,
  ``active_duty_days``, ``wartime_service``, ``discharge`` and the awards:
  slice 03 never asks for them.

A key the provider cannot answer is simply absent from what it returns: the
broker delivers the rest, the pull ledger records only the keys delivered, and
the matcher keeps asking the person for the others. Nothing here runs without
the person's grant.
"""
from __future__ import annotations

from datetime import date
from typing import Any, Callable, Dict, FrozenSet, Mapping, Optional

SERVING_COMPONENT = {"active_duty": "active", "national_guard": "guard", "reserve": "reserve"}
STATUS_BY_COMPONENT = {"retired": "retired", "separated": "separated", "medically_separated": "separated"}
PROVIDED_KEYS = frozenset({"component", "service_status"})


class ServiceProfileProvider:
    """``service_profile_agent`` over slice 03's ``service_record`` (fact_status DECLARED)."""

    agent_id = "service_profile_agent"

    def __init__(self, connect: Callable, today: Callable[[], date] = date.today):
        self._connect, self._today = connect, today

    def _record(self, tenant: str) -> Optional[tuple]:
        with self._connect() as conn:
            with conn.transaction():
                conn.execute("SELECT set_config('vetbuddy.tenant_id', %s, true)", (tenant,))
                return conn.execute(
                    "SELECT sr.component, sr.service_end FROM service_record sr"
                    " JOIN person_profile pp ON pp.person_id = sr.person_id AND pp.relationship = 'self'"
                    " ORDER BY sr.service_record_id LIMIT 1").fetchone()

    def provide(self, tenant_ref: str, keys: FrozenSet[str]) -> Mapping[str, Any]:
        wanted = frozenset(keys) & PROVIDED_KEYS
        if not wanted:
            return {}
        row = self._record(tenant_ref)
        if row is None:
            return {}
        return {k: v for k, v in derive(row[0], row[1], self._today()).items() if k in wanted}


def derive(component: str, service_end: Optional[date], today: date) -> Dict[str, str]:
    """The facts a declared component and end date support, and nothing more."""
    out: Dict[str, str] = {}
    if component in SERVING_COMPONENT:
        out["component"] = SERVING_COMPONENT[component]
        if service_end is None or service_end >= today:
            out["service_status"] = "serving"
    elif component in STATUS_BY_COMPONENT:
        out["service_status"] = STATUS_BY_COMPONENT[component]
    return out
