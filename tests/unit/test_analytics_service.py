from __future__ import annotations

from dataclasses import dataclass

import pytest

from legislative_analytics.domain.entities import Bill, Legislator, Vote, VoteResult
from legislative_analytics.services.analytics_service import AnalyticsService


@dataclass(frozen=True)
class _StubLegislatorsRepo:
    legislators: list[Legislator]

    def iter_legislators(self):
        return iter(self.legislators)


@dataclass(frozen=True)
class _StubBillsRepo:
    bills: list[Bill]

    def iter_bills(self):
        return iter(self.bills)


@dataclass(frozen=True)
class _StubVotesRepo:
    votes: list[Vote]

    def iter_votes(self):
        return iter(self.votes)


@dataclass(frozen=True)
class _StubVoteResultsRepo:
    vote_results: list[VoteResult]

    def iter_vote_results(self):
        return iter(self.vote_results)


def test_legislator_support_oppose_includes_zero_vote_legislators_and_ignores_unknown_ids() -> None:
    service = AnalyticsService(
        legislators=_StubLegislatorsRepo(
            [
                Legislator(id=1, name="A"),
                Legislator(id=2, name="B"),
                Legislator(id=3, name="C (no votes)"),
            ]
        ),
        bills=_StubBillsRepo([]),
        votes=_StubVotesRepo([]),
        vote_results=_StubVoteResultsRepo(
            [
                VoteResult(id=10, legislator_id=1, vote_id=100, vote_type=1),
                VoteResult(id=11, legislator_id=1, vote_id=101, vote_type=2),
                VoteResult(id=12, legislator_id=2, vote_id=100, vote_type=2),
                VoteResult(id=13, legislator_id=999, vote_id=100, vote_type=1),  # unknown legislator_id
                VoteResult(id=14, legislator_id=2, vote_id=100, vote_type=0),  # ignored vote type
            ]
        ),
    )

    rows = service.compute_legislator_support_oppose()
    assert [(r.legislator_id, r.supported_bills, r.opposed_bills) for r in rows] == [
        (1, 1, 1),
        (2, 0, 1),
        (3, 0, 0),
    ]


@pytest.mark.parametrize(
    ("vote_type", "expected_support", "expected_oppose"),
    [(1, 1, 0), (2, 0, 1), (0, 0, 0), (99, 0, 0)],
)
def test_legislator_vote_type_mapping(vote_type: int, expected_support: int, expected_oppose: int) -> None:
    service = AnalyticsService(
        legislators=_StubLegislatorsRepo([Legislator(id=1, name="A")]),
        bills=_StubBillsRepo([]),
        votes=_StubVotesRepo([]),
        vote_results=_StubVoteResultsRepo([VoteResult(id=1, legislator_id=1, vote_id=1, vote_type=vote_type)]),
    )
    (row,) = service.compute_legislator_support_oppose()
    assert (row.supported_bills, row.opposed_bills) == (expected_support, expected_oppose)


def test_bill_support_oppose_includes_no_vote_bills_and_unknown_sponsors() -> None:
    service = AnalyticsService(
        legislators=_StubLegislatorsRepo(
            [
                Legislator(id=1, name="Sponsor"),
                Legislator(id=2, name="Voter"),
            ]
        ),
        bills=_StubBillsRepo(
            [
                Bill(id=10, title="Bill With Votes", sponsor_id=1),
                Bill(id=20, title="Bill No Votes", sponsor_id=None),
                Bill(id=30, title="Bill Sponsor Missing", sponsor_id=999),
            ]
        ),
        votes=_StubVotesRepo([Vote(id=100, bill_id=10), Vote(id=101, bill_id=30)]),
        vote_results=_StubVoteResultsRepo(
            [
                VoteResult(id=1, legislator_id=2, vote_id=100, vote_type=1),
                VoteResult(id=2, legislator_id=2, vote_id=100, vote_type=2),
                VoteResult(id=3, legislator_id=2, vote_id=101, vote_type=1),
                VoteResult(id=4, legislator_id=2, vote_id=9999, vote_type=1),  # vote_id missing in votes
            ]
        ),
    )

    rows = service.compute_bill_support_oppose()
    assert [(r.bill_id, r.sponsor_name, r.supporters, r.opposers) for r in rows] == [
        (10, "Sponsor", 1, 1),
        (20, "Unknown", 0, 0),
        (30, "Unknown", 1, 0),
    ]


