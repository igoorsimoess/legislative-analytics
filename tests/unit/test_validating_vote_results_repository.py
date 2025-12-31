from __future__ import annotations

import logging
from dataclasses import dataclass

import pytest

from legislative_analytics.domain.entities import Legislator, Vote, VoteResult
from legislative_analytics.repositories.validating_vote_results import ValidatingVoteResultRepository


@dataclass(frozen=True)
class _StubLegislatorsRepo:
    legislators: list[Legislator]

    def iter_legislators(self):
        return iter(self.legislators)


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


def test_validating_repo_skips_unknown_legislator_and_double_vote_and_missing_vote_id(caplog) -> None:
    caplog.set_level(logging.DEBUG, logger="legislative_analytics.ingestion")

    repo = ValidatingVoteResultRepository(
        inner=_StubVoteResultsRepo(
            [
                VoteResult(id=1, legislator_id=1, vote_id=100, vote_type=1),  # ok
                VoteResult(id=2, legislator_id=999, vote_id=100, vote_type=1),  # unknown legislator
                VoteResult(id=3, legislator_id=1, vote_id=100, vote_type=2),  # double vote on same bill
                VoteResult(id=4, legislator_id=1, vote_id=9999, vote_type=1),  # missing vote_id -> bill_id
            ]
        ),
        legislators=_StubLegislatorsRepo([Legislator(id=1, name="A")]),
        votes=_StubVotesRepo([Vote(id=100, bill_id=10)]),
    )

    rows = list(repo.iter_vote_results())
    assert [r.id for r in rows] == [1]

    messages = [rec.message for rec in caplog.records]
    # Step-by-step flow
    assert "ingestion.entry" in messages
    assert "ingestion.validation.start" in messages
    assert "ingestion.validation.ok" in messages
    assert "ingestion.persistence.emit" in messages
    assert "ingestion.exit" in messages
    # Failure modes
    assert "ingestion.validation.fail.unknown_legislator" in messages
    assert "ingestion.validation.fail.double_vote" in messages
    assert "ingestion.validation.fail.missing_vote_id" in messages


def test_validating_repo_double_vote_is_per_bill_not_per_vote_id(caplog) -> None:
    """
    Same legislator voting on the same bill twice (even under different vote_ids)
    should be rejected by the (legislator_id, bill_id) rule.
    """
    caplog.set_level(logging.ERROR, logger="legislative_analytics.ingestion")

    repo = ValidatingVoteResultRepository(
        inner=_StubVoteResultsRepo(
            [
                VoteResult(id=1, legislator_id=1, vote_id=100, vote_type=1),
                VoteResult(id=2, legislator_id=1, vote_id=101, vote_type=1),
            ]
        ),
        legislators=_StubLegislatorsRepo([Legislator(id=1, name="A")]),
        votes=_StubVotesRepo(
            [
                Vote(id=100, bill_id=10),
                Vote(id=101, bill_id=10),  # same bill, different vote
            ]
        ),
    )

    rows = list(repo.iter_vote_results())
    assert [r.id for r in rows] == [1]
    assert any(rec.message == "ingestion.validation.fail.double_vote" for rec in caplog.records)


