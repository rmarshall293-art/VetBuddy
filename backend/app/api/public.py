"""Guest routes (Privacy Mode A): no sign-in, nothing stored, no database write.

These compute from the request body and fixed rules only. The guest-preview
test counts every table before and after to prove nothing persists.
"""

from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Request

from .. import reference
from ..governance import language
from ..kernel import crisis, ratings, router as kernel, vocab
from ..kernel.jurisdictions import JURISDICTIONS
from .errors import ApiError
from .schemas import RatingsRequest, RouterRequest

router = APIRouter(prefix="/api/v1")


def today(request: Request) -> date:
    return request.app.state.clock()


@router.get("/health/live")
def live():
    return {"status": "ok"}


@router.get("/health/ready")
def ready(request: Request):
    db = request.app.state.db
    database = "not_configured" if db is None else ("ok" if db.ping() else "unavailable")
    return {
        "status": "ok" if database != "unavailable" else "degraded",
        "database": database,
        "sign_in": "dev_mock" if request.app.state.settings.auth_mode == "dev" else "off",
        "model_gateway": "not_present",
        "benefit_rules_verified": 0,
    }


@router.get("/crisis-resources")
def crisis_resources():
    return {"contacts": crisis.CRISIS_CONTACTS, "verified_on": crisis.CRISIS_CONTACTS_VERIFIED_ON,
            "emergency": "If you are in immediate danger, call 911."}


@router.get("/jurisdictions")
def jurisdictions():
    verified = sum(1 for j in JURISDICTIONS if j["verification_status"] == "verified")
    return {"jurisdictions": JURISDICTIONS, "verified": verified, "total": len(JURISDICTIONS),
            "unverified_disclaimer": vocab.UNVERIFIED_DISCLAIMER}


@router.get("/policy/language")
def policy_language():
    return {"version": language.LANGUAGE_VERSION, "ai_disclosure": language.AI_DISCLOSURE,
            "standard_disclaimer": language.STANDARD_DISCLAIMER, "vso_referral": language.VSO_REFERRAL,
            "find_rep_url": language.FIND_REP_URL}


@router.get("/reference")
def reference_index():
    data = reference.load()
    tl = data["transition_timeline"]
    verified = sum(1 for w in tl["windows"] if w.get("status", tl["default_status"]) == "VERIFIED")
    return {"datasets": {name: (data[name].get("_meta") or {}).get("note", "") for name in reference.DATASETS},
            "verified_rows": verified,
            "notice": "Reference material for explanation. Nothing here is a determination; unverified rows are leads."}


@router.get("/reference/{dataset}")
def reference_dataset(dataset: str):
    if dataset not in reference.DATASETS:
        raise ApiError(404, "NOT_FOUND", "Not found.")
    return reference.load()[dataset]


@router.post("/mission-router/evaluate")
def evaluate(body: RouterRequest, request: Request):
    try:
        out = kernel.route(body.to_input(), today(request))
    except kernel.RouterInputError as e:
        raise ApiError(422, "INVALID_INPUT", str(e)) from None
    return {**out, "privacy_mode": "A", "stored": False, "as_of": today(request),
            "facts": {"source": "DECLARED"}, "readiness": kernel.readiness(
                [{"readiness_dimension": t["dimension"], "status": "todo"} for t in out["tasks"]]),
            "disclosure": language.AI_DISCLOSURE, "disclaimer": language.STANDARD_DISCLAIMER}


@router.post("/ratings/combine")
def combine(body: RatingsRequest):
    try:
        res = ratings.combine_ratings(body.ratings, body.bilateral)
    except ValueError as e:
        raise ApiError(422, "INVALID_INPUT", str(e)) from None
    return {**res, "educational_only": True,
            "notice": "Arithmetic on the numbers you entered, following 38 CFR 4.25 (and 4.26 for ratings you marked "
                      "as affecting both arms or both legs). Not a prediction of what VA will rate. VA decides your rating.",
            "vso_referral": language.VSO_REFERRAL}
