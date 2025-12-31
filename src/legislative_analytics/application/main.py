from __future__ import annotations

import argparse
import csv
import logging
from pathlib import Path

from legislative_analytics.repositories.csv_repositories import (
    CsvBillRepository,
    CsvLegislatorRepository,
    CsvVoteRepository,
    CsvVoteResultRepository,
)
from legislative_analytics.repositories.validating_vote_results import ValidatingVoteResultRepository
from legislative_analytics.services.analytics_service import AnalyticsService


def _write_legislator_report(*, out_path: Path, rows) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["id", "name",
                        "num_supported_bills", "num_opposed_bills"],
        )
        writer.writeheader()
        for r in rows:
            writer.writerow(
                {
                    "id": r.legislator_id,
                    "name": r.legislator_name,
                    "num_supported_bills": r.supported_bills,
                    "num_opposed_bills": r.opposed_bills,
                }
            )


def _write_bill_report(*, out_path: Path, rows) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["id", "title", "supporter_count",
                        "opposer_count", "primary_sponsor"],
        )
        writer.writeheader()
        for r in rows:
            writer.writerow(
                {
                    "id": r.bill_id,
                    "title": r.bill_title,
                    "primary_sponsor": r.sponsor_name,
                    "supporter_count": r.supporters,
                    "opposer_count": r.opposers,
                }
            )


def build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Generate voting analytics CSVs from datasets.")
    p.add_argument(
        "--data-dir",
        type=Path,
        default=Path("data"),
        help="Directory containing legislators.csv, bills.csv, votes.csv, vote_results.csv",
    )
    p.add_argument(
        "--out-dir",
        type=Path,
        default=Path("output"),
        help="Directory where reports will be written",
    )
    p.add_argument(
        "--legislator-report",
        type=Path,
        default=None,
        help="Override path for legislator report CSV",
    )
    p.add_argument(
        "--bill-report",
        type=Path,
        default=None,
        help="Override path for bill report CSV",
    )
    p.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        help="Logging level (DEBUG, INFO, WARNING, ERROR). Default: INFO",
    )
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)

    logging.basicConfig(
        level=getattr(logging, str(args.log_level).upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )

    if not args.data_dir.exists():
        raise SystemExit(f"Data directory not found: {args.data_dir}")
    if not args.data_dir.is_dir():
        raise SystemExit(f"Data directory is not a directory: {args.data_dir}")

    legislators_csv = args.data_dir / "legislators.csv"
    bills_csv = args.data_dir / "bills.csv"
    votes_csv = args.data_dir / "votes.csv"
    vote_results_csv = args.data_dir / "vote_results.csv"

    missing = [p for p in (legislators_csv, bills_csv,
                           votes_csv, vote_results_csv) if not p.exists()]
    if missing:
        missing_str = ", ".join(str(p) for p in missing)
        raise SystemExit(f"Missing required input file(s): {missing_str}")

    legislators_repo = CsvLegislatorRepository(legislators_csv)
    bills_repo = CsvBillRepository(bills_csv)
    votes_repo = CsvVoteRepository(votes_csv)
    raw_vote_results_repo = CsvVoteResultRepository(vote_results_csv)

    validating_vote_results_repo = ValidatingVoteResultRepository(
        inner=raw_vote_results_repo,
        legislators=legislators_repo,
        votes=votes_repo,
    )

    service = AnalyticsService(
        legislators=legislators_repo,
        bills=bills_repo,
        votes=votes_repo,
        vote_results=validating_vote_results_repo,
    )

    legislator_out = args.legislator_report or (
        args.out_dir / "legislators_support_oppose.csv")
    bill_out = args.bill_report or (args.out_dir / "bills_support_oppose.csv")

    _write_legislator_report(out_path=legislator_out,
                             rows=service.compute_legislator_support_oppose())
    _write_bill_report(out_path=bill_out,
                       rows=service.compute_bill_support_oppose())

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
