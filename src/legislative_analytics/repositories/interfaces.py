from __future__ import annotations

from collections.abc import Iterable
from typing import Protocol

from legislative_analytics.domain.entities import Bill, Legislator, Vote, VoteResult


class ILegislatorRepository(Protocol):
    def iter_legislators(self) -> Iterable[Legislator]: ...


class IBillRepository(Protocol):
    def iter_bills(self) -> Iterable[Bill]: ...


class IVoteRepository(Protocol):
    def iter_votes(self) -> Iterable[Vote]: ...


class IVoteResultRepository(Protocol):
    def iter_vote_results(self) -> Iterable[VoteResult]: ...


