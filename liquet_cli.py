#!/usr/bin/env python
"""
Liquet CLI — batch and single dispute processing.

Usage examples
--------------
# Investigate a single dispute (creates it if it doesn't exist yet)
  python liquet_cli.py investigate ORD-001

# Run a batch job over all known seed orders
  python liquet_cli.py batch

# List all disputes and their outcomes
  python liquet_cli.py list

# Run the eval harness (offline, no API needed)
  python liquet_cli.py eval

# Smoke-test the QwenCloud API connection
  python liquet_cli.py smoke
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))

from backend.core.logging_config import configure_logging
configure_logging()

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from backend.repositories.database import AsyncSessionLocal, init_db
from backend.repositories.dispute_repo import (
    AuditRepository, DecisionRepository, DisputeRepository,
)
from backend.services.orchestrator import DisputeOrchestrator
from backend.core.models import Dispute, DisputeCreate, DisputeStatus, DisputeType

log = structlog.get_logger("liquet.cli")

# ── Seed profiles for the 10 synthetic test cases ─────────────────────────────

SEED_DISPUTES: list[dict] = [
    {
        "order_id": "ORD-001",
        "dispute_type": DisputeType.NOT_AS_DESCRIBED,
        "buyer_id": "BUYER-001",
        "seller_id": "SELLER-001",
        "buyer_narrative": "I ordered a blue mug but received a grey one. The listing clearly showed blue.",
        "seller_narrative": "We shipped exactly what was ordered. Color might look different in photos.",
    },
    {
        "order_id": "ORD-002",
        "dispute_type": DisputeType.NEVER_ARRIVED,
        "buyer_id": "BUYER-002",
        "seller_id": "SELLER-002",
        "buyer_narrative": "My package never arrived. Tracking shows delivered but I have nothing.",
        "seller_narrative": "Tracking confirms delivery. Not our responsibility after confirmed delivery.",
    },
    {
        "order_id": "ORD-003",
        "dispute_type": DisputeType.DAMAGED,
        "buyer_id": "BUYER-003",
        "seller_id": "SELLER-003",
        "buyer_narrative": "The vase arrived completely shattered. Poor packaging.",
        "seller_narrative": "Item was packed carefully. Damage must have occurred in transit.",
    },
    {
        "order_id": "ORD-004",
        "dispute_type": DisputeType.NOT_AS_DESCRIBED,
        "buyer_id": "BUYER-004",
        "seller_id": "SELLER-004",
        "buyer_narrative": "Received a camera body but ordered a lens. Completely wrong item.",
        "seller_narrative": "We shipped the lens as ordered. Buyer may be confused.",
    },
    {
        "order_id": "ORD-005",
        "dispute_type": DisputeType.NEVER_ARRIVED,
        "buyer_id": "BUYER-005",
        "seller_id": "SELLER-005",
        "buyer_narrative": "Order never arrived. Tracking shows it is still in transit after 3 weeks.",
        "seller_narrative": "Carrier delays are out of our control. Package is still moving.",
    },
    {
        "order_id": "ORD-006",
        "dispute_type": DisputeType.DAMAGED,
        "buyer_id": "BUYER-006",
        "seller_id": "SELLER-006",
        "buyer_narrative": "Laptop screen cracked on arrival. Photos show the damage.",
        "seller_narrative": "We cannot verify damage claims without evidence from carrier.",
    },
    {
        "order_id": "ORD-007",
        "dispute_type": DisputeType.NOT_AS_DESCRIBED,
        "buyer_id": "BUYER-007",
        "seller_id": "SELLER-007",
        "buyer_narrative": "Received size M instead of size L as ordered.",
        "seller_narrative": "We ship based on order details. Order record shows size M.",
    },
    {
        "order_id": "ORD-008",
        "dispute_type": DisputeType.NEVER_ARRIVED,
        "buyer_id": "BUYER-008",
        "seller_id": "SELLER-008",
        "buyer_narrative": "Package marked as delivered but not at my address.",
        "seller_narrative": "GPS confirms delivery at buyer's address.",
    },
    {
        "order_id": "ORD-009",
        "dispute_type": DisputeType.NOT_AS_DESCRIBED,
        "buyer_id": "BUYER-009",
        "seller_id": "SELLER-009",
        "buyer_narrative": "Product quality is far below listing description.",
        "seller_narrative": "Product matches our listing specifications.",
    },
    {
        "order_id": "ORD-HIGH-001",
        "dispute_type": DisputeType.DAMAGED,
        "buyer_id": "BUYER-010",
        "seller_id": "SELLER-010",
        "buyer_narrative": "High-value watch arrived with a cracked face. Need full refund.",
        "seller_narrative": "Watch was insured and packed with care. Dispute the carrier claim.",
    },
]


# ── Helpers ────────────────────────────────────────────────────────────────────

def _fmt_row(label: str, value: str, width: int = 20) -> str:
    return f"  {label:<{width}} {value}"


def _gate_color(gate: str) -> str:
    if gate == "LIQUET":
        return f"\033[32m{gate}\033[0m"
    return f"\033[33m{gate}\033[0m"


async def _get_or_create_dispute(
    repo: DisputeRepository, profile: dict, session: AsyncSession
) -> Dispute:
    existing = await repo.get_by_order_id(profile["order_id"])
    if existing:
        return existing
    data = DisputeCreate(**profile)
    return await repo.create(data)


# ── Commands ───────────────────────────────────────────────────────────────────

async def cmd_investigate(order_id: str) -> None:
    """Investigate a single dispute end-to-end."""
    async with AsyncSessionLocal() as session:
        repo = DisputeRepository(session)
        profile = next((p for p in SEED_DISPUTES if p["order_id"] == order_id), None)

        dispute = await repo.get_by_order_id(order_id)
        if dispute is None:
            if profile is None:
                print(f"[ERROR] No dispute or seed profile found for {order_id}")
                sys.exit(1)
            print(f"Creating dispute for {order_id}…")
            dispute = await repo.create(DisputeCreate(**profile))
        else:
            print(f"Found existing dispute {dispute.id} for {order_id} (status: {dispute.status.value})")

        if dispute.status not in (DisputeStatus.OPEN, DisputeStatus.INVESTIGATING):
            print(f"Dispute already resolved ({dispute.status.value}) — skipping.")
            return

        print(f"\nRunning Liquet autopilot on {order_id}…\n")
        orch = DisputeOrchestrator(session)
        decision = await orch.run(dispute)

    print("\n" + "─" * 60)
    print("RESULT")
    print("─" * 60)
    print(_fmt_row("Gate:", _gate_color(decision.gate_result.value)))
    print(_fmt_row("Resolution:", decision.verdict.resolution.value.replace("_", " ")))
    print(_fmt_row("Confidence:", f"{decision.verdict.confidence:.0%}"))
    print(_fmt_row("Value at stake:", f"${decision.verdict.value_at_stake:.2f}"))
    if decision.abstention_reason:
        print(_fmt_row("NON LIQUET reason:", decision.abstention_reason))
    print("\nRationale:")
    print(f"  {decision.verdict.rationale}")
    if decision.verdict.policy_clauses:
        print(_fmt_row("Policy clauses:", ", ".join(decision.verdict.policy_clauses)))
    print("─" * 60)


async def cmd_batch() -> None:
    """Run all 10 seed disputes sequentially and print a summary table."""
    results = []
    async with AsyncSessionLocal() as session:
        repo = DisputeRepository(session)
        for profile in SEED_DISPUTES:
            order_id = profile["order_id"]
            print(f"  [{order_id}] investigating…", end=" ", flush=True)
            try:
                dispute = await _get_or_create_dispute(repo, profile, session)
                if dispute.status in (DisputeStatus.RESOLVED, DisputeStatus.ESCALATED):
                    dec_repo = DecisionRepository(session)
                    existing_dec = await dec_repo.get_by_dispute(dispute.id)
                    if existing_dec:
                        results.append({
                            "order_id": order_id,
                            "gate": existing_dec.gate_result.value,
                            "resolution": existing_dec.verdict.resolution.value,
                            "confidence": existing_dec.verdict.confidence,
                            "status": "cached",
                        })
                        print(f"cached ({existing_dec.gate_result.value})")
                        continue

                orch = DisputeOrchestrator(session)
                decision = await orch.run(dispute)
                results.append({
                    "order_id": order_id,
                    "gate": decision.gate_result.value,
                    "resolution": decision.verdict.resolution.value,
                    "confidence": decision.verdict.confidence,
                    "status": "ok",
                })
                print(f"done ({decision.gate_result.value}, {decision.verdict.confidence:.0%})")
            except Exception as exc:
                results.append({"order_id": order_id, "gate": "ERROR", "resolution": str(exc)[:40], "confidence": 0.0, "status": "error"})
                print(f"ERROR: {exc}")

    print("\n" + "─" * 72)
    print(f"{'Order':<18} {'Gate':<14} {'Resolution':<22} {'Conf':>6}")
    print("─" * 72)
    liquet_n = 0
    for r in results:
        gate_str = r["gate"]
        if gate_str == "LIQUET":
            liquet_n += 1
        conf_str = f"{r['confidence']:.0%}" if r["confidence"] else "—"
        print(f"{r['order_id']:<18} {gate_str:<14} {r['resolution']:<22} {conf_str:>6}")
    print("─" * 72)
    total = len(results)
    print(f"LIQUET (auto-resolved): {liquet_n}/{total}   NON LIQUET (escalated): {total - liquet_n}/{total}")


async def cmd_list() -> None:
    """List all disputes in the database."""
    async with AsyncSessionLocal() as session:
        repo = DisputeRepository(session)
        dec_repo = DecisionRepository(session)
        disputes = await repo.list_all()

    if not disputes:
        print("No disputes in database. Run: python liquet_cli.py batch")
        return

    print(f"\n{'ID':<10} {'Order':<15} {'Type':<20} {'Status':<15} {'Gate':<14} {'Conf':>6}")
    print("─" * 84)
    for d in disputes:
        async with AsyncSessionLocal() as session:
            dec_repo = DecisionRepository(session)
            dec = await dec_repo.get_by_dispute(d.id)
        gate = dec.gate_result.value if dec else "—"
        conf = f"{dec.verdict.confidence:.0%}" if dec else "—"
        disp_type = d.dispute_type.value.replace("_", " ")
        print(f"{d.id[:8]:<10} {d.order_id:<15} {disp_type:<20} {d.status.value:<15} {gate:<14} {conf:>6}")
    print()


async def cmd_smoke() -> None:
    """Smoke-test the QwenCloud API connection."""
    from backend.core.llm_client import smoke_test
    print("Testing QwenCloud connection…")
    result = await smoke_test()
    if result.get("status") == "ok":
        print(f"  Connection OK. Response: {result.get('response')}")
    else:
        print(f"  FAILED: {result}")
        sys.exit(1)


def cmd_eval() -> None:
    """Run the offline eval harness."""
    import importlib.util, subprocess
    eval_script = ROOT / "eval" / "run_eval.py"
    if not eval_script.exists():
        print("eval/run_eval.py not found")
        sys.exit(1)
    subprocess.run([sys.executable, str(eval_script)], check=True)


# ── Entry point ────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        prog="liquet_cli",
        description="Liquet dispute resolution CLI",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_inv = sub.add_parser("investigate", help="Investigate a single order dispute")
    p_inv.add_argument("order_id", help="e.g. ORD-001")

    sub.add_parser("batch", help="Run all 10 seed disputes")
    sub.add_parser("list", help="List all disputes in DB")
    sub.add_parser("smoke", help="Smoke-test QwenCloud API")
    sub.add_parser("eval", help="Run offline eval harness")

    args = parser.parse_args()

    asyncio.run(init_db())

    if args.command == "investigate":
        asyncio.run(cmd_investigate(args.order_id))
    elif args.command == "batch":
        asyncio.run(cmd_batch())
    elif args.command == "list":
        asyncio.run(cmd_list())
    elif args.command == "smoke":
        asyncio.run(cmd_smoke())
    elif args.command == "eval":
        cmd_eval()


if __name__ == "__main__":
    main()
