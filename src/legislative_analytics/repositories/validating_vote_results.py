from __future__ import annotations

import logging
from collections.abc import Iterable
from dataclasses import dataclass

from legislative_analytics.domain.entities import VoteResult
from legislative_analytics.repositories.interfaces import (
    ILegislatorRepository,
    IVoteRepository,
    IVoteResultRepository,
)


@dataclass(frozen=True, slots=True)
class ValidatingVoteResultRepository(IVoteResultRepository):
    """
    Defensive Data Ingestion:
    - Enforces referential integrity and business rules in-memory
    - Logs failures and skips invalid records (fail fast and loud, but don't crash)
    """

    inner: IVoteResultRepository
    legislators: ILegislatorRepository
    votes: IVoteRepository
    logger: logging.Logger = logging.getLogger(
        "legislative_analytics.ingestion")

    def iter_vote_results(self) -> Iterable[VoteResult]:
        self.logger.info("ingestion.entry", extra={
                         "component": "ValidatingVoteResultRepository"})

        legislator_ids = {l.id for l in self.legislators.iter_legislators()}
        vote_id_to_bill_id = {v.id: v.bill_id for v in self.votes.iter_votes()}

        seen_legislator_bill: set[tuple[int, int]] = set()

        processed = 0
        accepted = 0
        rejected = 0

        for vr in self.inner.iter_vote_results():
            processed += 1
            self.logger.debug(
                "ingestion.validation.start",
                extra={
                    "vote_result_id": vr.id,
                    "legislator_id": vr.legislator_id,
                    "vote_id": vr.vote_id,
                },
            )

            # Extra safety: vote_id must exist to identify bill_id.
            bill_id = vote_id_to_bill_id.get(vr.vote_id)
            if bill_id is None:
                rejected += 1
                self.logger.warning(
                    "ingestion.validation.fail.missing_vote_id",
                    extra={
                        "vote_result_id": vr.id,
                        "vote_id": vr.vote_id,
                    },
                )
                continue

            # Check 1: legislator_id exists
            if vr.legislator_id not in legislator_ids:
                rejected += 1
                self.logger.warning(
                    "ingestion.validation.fail.unknown_legislator",
                    extra={
                        "vote_result_id": vr.id,
                        "legislator_id": vr.legislator_id,
                        "bill_id": bill_id,
                        "vote_id": vr.vote_id,
                    },
                )
                continue

            # Check 2: no double-voting per bill
            key = (vr.legislator_id, bill_id)
            if key in seen_legislator_bill:
                rejected += 1
                self.logger.error(
                    "ingestion.validation.fail.double_vote",
                    extra={
                        "vote_result_id": vr.id,
                        "legislator_id": vr.legislator_id,
                        "bill_id": bill_id,
                        "vote_id": vr.vote_id,
                    },
                )
                continue

            seen_legislator_bill.add(key)
            accepted += 1
            self.logger.debug(
                "ingestion.validation.ok",
                extra={
                    "vote_result_id": vr.id,
                    "legislator_id": vr.legislator_id,
                    "bill_id": bill_id,
                    "vote_id": vr.vote_id,
                },
            )

            # "Persistence" in this pipeline is yielding to downstream processing.
            self.logger.debug(
                "ingestion.persistence.emit",
                extra={
                    "vote_result_id": vr.id,
                    "legislator_id": vr.legislator_id,
                    "bill_id": bill_id,
                    "vote_id": vr.vote_id,
                },
            )
            yield vr

        self.logger.info(
            "ingestion.exit",
            extra={
                "component": "ValidatingVoteResultRepository",
                "processed": processed,
                "accepted": accepted,
                "rejected": rejected,
            },
        )
