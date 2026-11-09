"""Egress guard: where the vault may go on the network, and what it may say.

Two rules:

1. A URL may be fetched or shown only if it is https and its host is on the
   allowlist. The allowlist is every host of a page the research read or an
   official link it recorded (built into the registry).
2. A discovery query may be built only from a fixed template filled with V0
   vocabulary: jurisdiction names, category labels and group labels. Raw
   facts and the person's own words never reach a query, so nothing about the
   person can leave through a search engine.
"""
from __future__ import annotations

import re
import string
from typing import AbstractSet, Dict, Iterable, Mapping, Optional, Tuple
from urllib.parse import urlsplit

from ..vocab import CATEGORY_LABELS, GROUP_LABELS, JURISDICTIONS


class EgressBlocked(PermissionError):
    def __init__(self, reason: str, detail: str):
        super().__init__(f"{reason}: {detail}")
        self.reason = reason


V0_VOCABULARY: Dict[str, frozenset] = {
    "jurisdiction": frozenset(JURISDICTIONS.values()),
    "category": frozenset(CATEGORY_LABELS.values()),
    "group": frozenset(GROUP_LABELS.values()),
}


def url_problem(url: Optional[str], allowlist: AbstractSet[str]) -> Optional[Tuple[str, str]]:
    """None when ``url`` is plain https on an allowed host, else (reason, detail).

    Shared by the egress guard (fetching) and the citation validator (showing
    a link), so a link can be shown exactly when it could be fetched.
    """
    try:
        parts = urlsplit(url or "")
        port = parts.port
    except ValueError:
        return "URL_NOT_PLAIN", "malformed URL"
    if parts.scheme != "https":
        return "NOT_HTTPS", url or ""
    host = (parts.hostname or "").lower()
    if host not in allowlist:
        return "HOST_NOT_ALLOWED", host
    if parts.username or parts.password or port not in (None, 443):
        return "URL_NOT_PLAIN", host
    return None


class EgressGuard:
    def __init__(self, allowlist: Iterable[str], templates: Mapping[str, str]):
        self.allowlist = frozenset(h.lower() for h in allowlist)
        self.templates: Dict[str, str] = {}
        for template_id, template in templates.items():
            fields = {f for _, f, _, _ in string.Formatter().parse(template) if f}
            unknown = fields - set(V0_VOCABULARY)
            if unknown:
                raise ValueError(f"template {template_id} uses non-V0 fields {sorted(unknown)}")
            self.templates[template_id] = template

    @classmethod
    def from_registry(cls, registry) -> "EgressGuard":
        governance = registry.governance
        return cls(governance["egress_allowlist"], governance["discovery"]["templates"])

    def check_url(self, url: str) -> str:
        problem = url_problem(url, self.allowlist)
        if problem:
            raise EgressBlocked(*problem)
        return url

    def allowed(self, url: str) -> bool:
        try:
            self.check_url(url)
        except EgressBlocked:
            return False
        return True

    def build_query(self, template_id: str, **tokens: str) -> str:
        template = self.templates.get(template_id)
        if template is None:
            raise EgressBlocked("UNKNOWN_TEMPLATE", template_id)
        fields = {f for _, f, _, _ in string.Formatter().parse(template) if f}
        if set(tokens) != fields:
            raise EgressBlocked("TEMPLATE_FIELDS", f"{template_id} needs {sorted(fields)}")
        for name, value in tokens.items():
            if value not in V0_VOCABULARY[name]:
                raise EgressBlocked("NOT_V0", f"{name} value is not in the fixed vocabulary")
        query = template.format(**tokens)
        if re.search(r"\d{3,}|@", query):
            raise EgressBlocked("NOT_V0", "a query may not carry numbers or addresses")
        return query
