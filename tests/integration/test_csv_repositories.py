from __future__ import annotations

import csv
from pathlib import Path

import pytest

from legislative_analytics.repositories.csv_repositories import (
    CsvBillRepository,
    CsvLegislatorRepository,
    CsvVoteRepository,
    CsvVoteResultRepository,
)


@pytest.mark.integration
def test_csv_legislator_repository_reads_rows(tmp_path: Path) -> None:
    p = tmp_path / "legislators.csv"
    p.write_text("id,name\n1,A\n2,B\n", encoding="utf-8")
    repo = CsvLegislatorRepository(p)
    rows = list(repo.iter_legislators())
    assert [(r.id, r.name) for r in rows] == [(1, "A"), (2, "B")]


@pytest.mark.integration
def test_csv_bill_repository_parses_optional_sponsor_id(tmp_path: Path) -> None:
    p = tmp_path / "bills.csv"
    p.write_text("id,title,sponsor_id\n10,T1,1\n20,T2,\n", encoding="utf-8")
    repo = CsvBillRepository(p)
    rows = list(repo.iter_bills())
    assert [(r.id, r.title, r.sponsor_id)
            for r in rows] == [(10, "T1", 1), (20, "T2", None)]


@pytest.mark.integration
def test_csv_vote_and_vote_result_repositories(tmp_path: Path) -> None:
    votes = tmp_path / "votes.csv"
    vote_results = tmp_path / "vote_results.csv"

    votes.write_text("id,bill_id\n100,10\n", encoding="utf-8")
    vote_results.write_text(
        "id,legislator_id,vote_id,vote_type\n1,2,100,1\n", encoding="utf-8")

    assert [(v.id, v.bill_id)
            for v in CsvVoteRepository(votes).iter_votes()] == [(100, 10)]
    assert [
        (vr.id, vr.legislator_id, vr.vote_id, vr.vote_type)
        for vr in CsvVoteResultRepository(vote_results).iter_vote_results()
    ] == [(1, 2, 100, 1)]


@pytest.mark.integration
def test_csv_output_compatibility_with_standard_csv_reader(tmp_path: Path) -> None:
    """
    Not testing the app layer directly here
    just asserting our repo fixtures look like normal CSVs.
    This is a "sanity integration" test to catch newline/encoding issues across platforms.
    """

    p = tmp_path / "sample.csv"
    with p.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["a", "b"])
        w.writeheader()
        w.writerow({"a": 1, "b": 2})

    with p.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    assert rows == [{"a": "1", "b": "2"}]
