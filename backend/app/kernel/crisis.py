"""Crisis floor: the hard-coded contacts shown on every screen (T0-08, R16).

No network call, no model, no rate limit sits in front of these. Re-verify the
numbers against the source registry before each release (governance §9).
"""

from __future__ import annotations

CRISIS_CONTACTS_VERIFIED_ON = "2026-10-20"

CRISIS_CONTACTS: tuple[dict, ...] = (
    {
        "key": "veterans_crisis_line",
        "label": "Veterans Crisis Line",
        "phone": "988",
        "extra": "Press 1",
        "text": "838255",
        "chat_url": "https://www.veteranscrisisline.net/get-help-now/chat/",
    },
    {"key": "988", "label": "988 Suicide & Crisis Lifeline", "phone": "988"},
    {
        "key": "domestic_violence_hotline",
        "label": "National Domestic Violence Hotline",
        "phone": "1-800-799-7233",
        "text": "START to 88788",
    },
    {
        "key": "women_veterans_call_center",
        "label": "VA Women Veterans Call Center",
        "phone": "1-855-829-6636",
        "text": "1-855-829-6636",
    },
    {"key": "homeless_veterans_call_center", "label": "National Call Center for Homeless Veterans", "phone": "1-877-424-3838"},
    {
        "key": "dod_safe_helpline",
        "label": "DoD Safe Helpline (sexual assault support)",
        "phone": "1-877-995-5247",
        "chat_url": "https://www.safehelpline.org/",
    },
)
