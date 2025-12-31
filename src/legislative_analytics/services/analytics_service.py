from __future__ import annotations

from dataclasses import dataclass

from legislative_analytics.repositories.interfaces import (
    IBillRepository,
    ILegislatorRepository,
    IVoteRepository,
    IVoteResultRepository,
)


@dataclass(frozen=True, slots=True)
class LegislatorVoteCount:
    legislator_id: int
    legislator_name: str
    supported_bills: int
    opposed_bills: int


@dataclass(frozen=True, slots=True)
class BillVoteCount:
    bill_id: int
    bill_title: str
    sponsor_name: str
    supporters: int
    opposers: int


class AnalyticsService:
    """
    Use-case/service layer:
    - O(N) aggregation using hash maps (dicts)
    - no IO here (only repositories)
    """

    def __init__(
        self,
        *,
        legislators: ILegislatorRepository,
        bills: IBillRepository,
        votes: IVoteRepository,
        vote_results: IVoteResultRepository,
    ) -> None:
        self._legislators = legislators
        self._bills = bills
        self._votes = votes
        self._vote_results = vote_results

    def compute_legislator_support_oppose(self) -> list[LegislatorVoteCount]:
        legislator_name_by_id: dict[int, str] = {}
        counts: dict[int, list[int]] = {}

        for leg in self._legislators.iter_legislators():
            legislator_name_by_id[leg.id] = leg.name
            counts[leg.id] = [0, 0]  # [support, oppose]

        # Single pass over vote results. No nested loops.
        for vr in self._vote_results.iter_vote_results():
            if vr.legislator_id not in counts:
                # Requirement: "for every legislator" from legislators.csv.
                # Unknown legislator_ids in vote_results are ignored.
                continue
            if vr.vote_type == 1:
                counts[vr.legislator_id][0] += 1
            elif vr.vote_type == 2:
                counts[vr.legislator_id][1] += 1

        return [
            LegislatorVoteCount(
                legislator_id=leg_id,
                legislator_name=legislator_name_by_id[leg_id],
                supported_bills=support,
                opposed_bills=oppose,
            )
            for leg_id, (support, oppose) in sorted(counts.items(), key=lambda kv: kv[0])
        ]

    def compute_bill_support_oppose(self) -> list[BillVoteCount]:
        legislator_name_by_id: dict[int, str] = {
            leg.id: leg.name for leg in self._legislators.iter_legislators()
        }

        bill_title_by_id: dict[int, str] = {}
        bill_sponsor_id_by_id: dict[int, int | None] = {}
        counts: dict[int, list[int]] = {}

        for bill in self._bills.iter_bills():
            bill_title_by_id[bill.id] = bill.title
            bill_sponsor_id_by_id[bill.id] = bill.sponsor_id
            counts[bill.id] = [0, 0]  # [supporters, opposers]

        vote_id_to_bill_id: dict[int, int] = {v.id: v.bill_id for v in self._votes.iter_votes()}

        for vr in self._vote_results.iter_vote_results():
            bill_id = vote_id_to_bill_id.get(vr.vote_id)
            if bill_id is None or bill_id not in counts:
                continue
            if vr.vote_type == 1:
                counts[bill_id][0] += 1
            elif vr.vote_type == 2:
                counts[bill_id][1] += 1

        result: list[BillVoteCount] = []
        for bill_id, (supporters, opposers) in sorted(counts.items(), key=lambda kv: kv[0]):
            sponsor_id = bill_sponsor_id_by_id.get(bill_id)
            sponsor_name = (
                legislator_name_by_id.get(sponsor_id, "Unknown") if sponsor_id is not None else "Unknown"
            )
            result.append(
                BillVoteCount(
                    bill_id=bill_id,
                    bill_title=bill_title_by_id[bill_id],
                    sponsor_name=sponsor_name,
                    supporters=supporters,
                    opposers=opposers,
                )
            )

        return result


