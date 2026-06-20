"""Unit tests for the deterministic, credential-free logic (scoring + age parsing)."""
from __future__ import annotations

from app.models.results import CriterionVerdict, TrialMatch
from app.services.clinicaltrials import parse_age
from app.services.scoring import aggregate, rank_key


def _v(type_, status):
    return CriterionVerdict(type=type_, text="x", status=status, reason="r")


def test_exclusion_met_is_disqualifying():
    verdicts = [_v("inclusion", "met"), _v("exclusion", "met")]
    eligibility, confidence = aggregate(verdicts)
    assert eligibility == "ineligible"
    assert confidence == 1.0


def test_inclusion_not_met_is_disqualifying():
    eligibility, _ = aggregate([_v("inclusion", "not_met")])
    assert eligibility == "ineligible"


def test_unknown_drives_needs_more_info_and_confidence():
    verdicts = [_v("inclusion", "met"), _v("inclusion", "unknown")]
    eligibility, confidence = aggregate(verdicts)
    assert eligibility == "needs_more_info"
    assert confidence == 0.5


def test_all_met_is_likely_eligible():
    eligibility, confidence = aggregate([_v("inclusion", "met"), _v("exclusion", "not_met")])
    assert eligibility == "likely_eligible"
    assert confidence == 1.0


def test_empty_is_needs_more_info():
    assert aggregate([]) == ("needs_more_info", 0.0)


def test_rank_orders_eligible_then_confidence():
    def tm(elig, conf):
        return TrialMatch(
            nct_id="NCT", brief_title=None, url="u", eligibility=elig, confidence=conf, criteria=[]
        )

    items = [tm("ineligible", 1.0), tm("likely_eligible", 0.5), tm("likely_eligible", 0.9)]
    items.sort(key=rank_key)
    assert [i.confidence for i in items] == [0.9, 0.5, 1.0]
    assert items[-1].eligibility == "ineligible"


def test_parse_age():
    assert parse_age("18 Years") == 18.0
    assert parse_age("6 Months") == 0.5
    assert parse_age("N/A") is None
    assert parse_age(None) is None
