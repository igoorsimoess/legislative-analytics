from __future__ import annotations

from pathlib import Path

import pytest

from legislative_analytics.application.main import main


@pytest.mark.edge
def test_missing_data_directory_fails_gracefully(tmp_path: Path) -> None:
    missing_data_dir = tmp_path / "does_not_exist"

    with pytest.raises(SystemExit) as excinfo:
        main(["--data-dir", str(missing_data_dir), "--out-dir", str(tmp_path / "out")])

    assert "Data directory not found" in str(excinfo.value)


@pytest.mark.edge
def test_output_directory_is_created_if_missing(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    data_dir.mkdir(parents=True, exist_ok=True)

    (data_dir / "legislators.csv").write_text("id,name\n1,A\n", encoding="utf-8")
    (data_dir / "bills.csv").write_text("id,title,sponsor_id\n10,T1,1\n", encoding="utf-8")
    (data_dir / "votes.csv").write_text("id,bill_id\n100,10\n", encoding="utf-8")
    (data_dir / "vote_results.csv").write_text(
        "id,legislator_id,vote_id,vote_type\n1,1,100,1\n", encoding="utf-8"
    )

    out_dir = tmp_path / "output" / "nested"
    assert not out_dir.exists()

    rc = main(["--data-dir", str(data_dir), "--out-dir", str(out_dir), "--log-level", "ERROR"])
    assert rc == 0

    assert out_dir.is_dir()
    assert (out_dir / "legislators_support_oppose.csv").exists()
    assert (out_dir / "bills_support_oppose.csv").exists()


