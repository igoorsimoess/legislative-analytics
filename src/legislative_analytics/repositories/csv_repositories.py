from __future__ import annotations

import csv
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

from legislative_analytics.domain.entities import Bill, Legislator, Vote, VoteResult
from legislative_analytics.repositories.interfaces import (
    IBillRepository,
    ILegislatorRepository,
    IVoteRepository,
    IVoteResultRepository,
)


def _parse_int(value: str) -> int:
    return int(value.strip())


def _parse_optional_int(value: str) -> int | None:
    v = value.strip()
    if v == "":
        return None
    return int(v)


@dataclass(frozen=True, slots=True)
class CsvLegislatorRepository(ILegislatorRepository):
    csv_path: Path

    def iter_legislators(self) -> Iterable[Legislator]:
        with self.csv_path.open(newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                yield Legislator(
                    id=_parse_int(row["id"]),
                    name=row["name"].strip(),
                )


@dataclass(frozen=True, slots=True)
class CsvBillRepository(IBillRepository):
    csv_path: Path

    def iter_bills(self) -> Iterable[Bill]:
        with self.csv_path.open(newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                yield Bill(
                    id=_parse_int(row["id"]),
                    title=row["title"].strip(),
                    sponsor_id=_parse_optional_int(row.get("sponsor_id", "")),
                )


@dataclass(frozen=True, slots=True)
class CsvVoteRepository(IVoteRepository):
    csv_path: Path

    def iter_votes(self) -> Iterable[Vote]:
        with self.csv_path.open(newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                yield Vote(
                    id=_parse_int(row["id"]),
                    bill_id=_parse_int(row["bill_id"]),
                )


@dataclass(frozen=True, slots=True)
class CsvVoteResultRepository(IVoteResultRepository):
    csv_path: Path

    def iter_vote_results(self) -> Iterable[VoteResult]:
        with self.csv_path.open(newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                yield VoteResult(
                    id=_parse_int(row["id"]),
                    legislator_id=_parse_int(row["legislator_id"]),
                    vote_id=_parse_int(row["vote_id"]),
                    vote_type=_parse_int(row["vote_type"]),
                )


