from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Legislator:
    id: int
    name: str


@dataclass(frozen=True, slots=True)
class Bill:
    id: int
    title: str
    sponsor_id: int | None


@dataclass(frozen=True, slots=True)
class Vote:
    id: int
    bill_id: int


@dataclass(frozen=True, slots=True)
class VoteResult:
    id: int
    legislator_id: int
    vote_id: int
    vote_type: int
