from __future__ import annotations

from pathlib import Path

import pytest

from legislative_analytics.repositories.csv_repositories import (
    CsvBillRepository,
    CsvLegislatorRepository,
    CsvVoteRepository,
    CsvVoteResultRepository,
)
from legislative_analytics.services.analytics_service import AnalyticsService


@pytest.mark.edge
def test_missing_sponsor_id_is_unknown(tmp_path: Path) -> None:
    (tmp_path / "legislators.csv").write_text("id,name\n1,A\n", encoding="utf-8")
    (tmp_path / "bills.csv").write_text("id,title,sponsor_id\n10,T1,\n", encoding="utf-8")
    (tmp_path / "votes.csv").write_text("id,bill_id\n100,10\n", encoding="utf-8")
    (tmp_path / "vote_results.csv").write_text(
        "id,legislator_id,vote_id,vote_type\n1,1,100,1\n", encoding="utf-8")

    svc = AnalyticsService(
        legislators=CsvLegislatorRepository(tmp_path / "legislators.csv"),
        bills=CsvBillRepository(tmp_path / "bills.csv"),
        votes=CsvVoteRepository(tmp_path / "votes.csv"),
        vote_results=CsvVoteResultRepository(tmp_path / "vote_results.csv"),
    )

    (row,) = svc.compute_bill_support_oppose()
    assert row.sponsor_name == "Unknown"


@pytest.mark.edge
def test_legislators_with_zero_votes_are_present(tmp_path: Path) -> None:
    (tmp_path / "legislators.csv").write_text("id,name\n1,A\n2,B\n", encoding="utf-8")
    (tmp_path / "bills.csv").write_text("id,title,sponsor_id\n10,T1,1\n", encoding="utf-8")
    (tmp_path / "votes.csv").write_text("id,bill_id\n100,10\n", encoding="utf-8")
    (tmp_path / "vote_results.csv").write_text(
        "id,legislator_id,vote_id,vote_type\n1,1,100,1\n", encoding="utf-8")

    svc = AnalyticsService(
        legislators=CsvLegislatorRepository(tmp_path / "legislators.csv"),
        bills=CsvBillRepository(tmp_path / "bills.csv"),
        votes=CsvVoteRepository(tmp_path / "votes.csv"),
        vote_results=CsvVoteResultRepository(tmp_path / "vote_results.csv"),
    )

    rows = svc.compute_legislator_support_oppose()
    assert [(r.legislator_id, r.supported_bills, r.opposed_bills)
            for r in rows] == [(1, 1, 0), (2, 0, 0)]


@pytest.mark.edge
def test_bills_with_no_votes_are_present(tmp_path: Path) -> None:
    (tmp_path / "legislators.csv").write_text("id,name\n1,A\n", encoding="utf-8")
    (tmp_path / "bills.csv").write_text("id,title,sponsor_id\n10,T1,1\n20,T2,1\n", encoding="utf-8")
    (tmp_path / "votes.csv").write_text("id,bill_id\n100,10\n", encoding="utf-8")
    (tmp_path / "vote_results.csv").write_text(
        "id,legislator_id,vote_id,vote_type\n1,1,100,2\n", encoding="utf-8")

    svc = AnalyticsService(
        legislators=CsvLegislatorRepository(tmp_path / "legislators.csv"),
        bills=CsvBillRepository(tmp_path / "bills.csv"),
        votes=CsvVoteRepository(tmp_path / "votes.csv"),
        vote_results=CsvVoteResultRepository(tmp_path / "vote_results.csv"),
    )

    rows = svc.compute_bill_support_oppose()
    assert [(r.bill_id, r.supporters, r.opposers)
            for r in rows] == [(10, 0, 1), (20, 0, 0)]
