"""ClinicalTrials.gov v2 API client + field extraction.

Public API, no key required. We fetch recruiting trials for a condition, pull the
fields we care about out of the nested `protocolSection`, and normalize age strings
into years for the SQL prefilter.

Docs / field definitions: https://clinicaltrials.gov/data-api/api
"""
from __future__ import annotations

from typing import Any

from curl_cffi.requests import AsyncSession

BASE_URL = "https://clinicaltrials.gov/api/v2/studies"
_RECRUITING = "RECRUITING|NOT_YET_RECRUITING"
# clinicaltrials.gov is fronted by Akamai Bot Manager, which 403s vanilla Python
# HTTP clients on TLS/HTTP-2 fingerprint (a browser User-Agent is not enough).
# curl_cffi impersonates a real browser's handshake so the request passes.
_IMPERSONATE = "chrome"
_UNIT_TO_YEARS = {
    "year": 1.0,
    "month": 1 / 12,
    "week": 1 / 52,
    "day": 1 / 365,
}


def parse_age(value: str | None) -> float | None:
    """'18 Years' -> 18.0, '6 Months' -> 0.5, 'N/A'/None -> None."""
    if not value:
        return None
    parts = value.strip().split()
    if len(parts) < 2:
        return None
    try:
        amount = float(parts[0])
    except ValueError:
        return None
    unit = parts[1].lower().rstrip("s")  # "Years" -> "year"
    factor = _UNIT_TO_YEARS.get(unit)
    return round(amount * factor, 3) if factor else None


def parse_study(study: dict[str, Any]) -> dict[str, Any]:
    """Flatten a CT.gov study record into our `trials` row shape (no embedding yet)."""
    protocol = study.get("protocolSection", {})
    ident = protocol.get("identificationModule", {})
    status = protocol.get("statusModule", {})
    conditions_mod = protocol.get("conditionsModule", {})
    elig = protocol.get("eligibilityModule", {})

    return {
        "nct_id": ident.get("nctId"),
        "brief_title": ident.get("briefTitle"),
        "conditions": conditions_mod.get("conditions", []),
        "overall_status": status.get("overallStatus"),
        "sex": elig.get("sex"),
        "min_age_years": parse_age(elig.get("minimumAge")),
        "max_age_years": parse_age(elig.get("maximumAge")),
        "healthy_volunteers": _coerce_bool(elig.get("healthyVolunteers")),
        "eligibility_criteria": elig.get("eligibilityCriteria"),
        "raw_json": study,
    }


def _coerce_bool(value: Any) -> bool | None:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"yes", "true", "y"}
    return None


async def fetch_studies(condition: str, max_trials: int = 200) -> list[dict[str, Any]]:
    """Fetch up to `max_trials` recruiting studies for a condition, paginated.

    Returns parsed rows (see `parse_study`). Rows without an nct_id or eligibility
    text are dropped — they cannot be ingested usefully.
    """
    rows: list[dict[str, Any]] = []
    page_token: str | None = None
    page_size = min(max_trials, 1000)  # CT.gov caps pageSize at 1000

    async with AsyncSession() as client:
        while len(rows) < max_trials:
            params: dict[str, Any] = {
                "query.cond": condition,
                "filter.overallStatus": _RECRUITING,
                "pageSize": page_size,
                "countTotal": "true",
            }
            if page_token:
                params["pageToken"] = page_token

            resp = await client.get(
                BASE_URL, params=params, impersonate=_IMPERSONATE, timeout=30.0
            )
            resp.raise_for_status()
            data = resp.json()

            for study in data.get("studies", []):
                parsed = parse_study(study)
                if parsed["nct_id"] and parsed["eligibility_criteria"]:
                    rows.append(parsed)
                if len(rows) >= max_trials:
                    break

            page_token = data.get("nextPageToken")
            if not page_token:
                break

    return rows[:max_trials]
