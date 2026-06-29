"""
Synthetic case generator for Liquet eval harness.

Generates a labeled dataset covering all dispute types and difficulty levels:
- Clear cases → should auto-resolve (LIQUET)
- Borderline cases → may or may not escalate
- Engineered 50/50 → must escalate (NON_LIQUET)
- High-value cases → must escalate on value even if confident

Run: python data/generate_cases.py
"""

from __future__ import annotations

import json
import random
from pathlib import Path

CASES_DIR = Path(__file__).parent / "cases"
CASES_DIR.mkdir(exist_ok=True)

CASES = [
    # ── CLEAR: never arrived, carrier confirms no delivery → FULL_REFUND ────────
    {
        "id": "CASE-001",
        "label": "clear_never_arrived",
        "expected_resolution": "full_refund",
        "expected_gate": "LIQUET",
        "difficulty": "clear",
        "dispute": {
            "order_id": "ORD-CLEAR-001",
            "dispute_type": "never_arrived",
            "buyer_id": "USR-B001",
            "seller_id": "USR-S001",
            "buyer_narrative": "I ordered a phone case 3 weeks ago and it has never arrived. Tracking shows it was picked up but has been stuck 'in transit' for 20 days with no delivery scan.",
            "seller_narrative": "I shipped the item on time. The carrier must have lost it. I can't control what happens after pickup.",
            "metadata": {"evidence_images": []},
        },
        "synthetic_tracking": {
            "status": "in_transit",
            "delivered_at": None,
            "days_stalled": 20,
        },
    },

    # ── CLEAR: carrier confirms delivery + signed receipt → DENY ────────────────
    {
        "id": "CASE-002",
        "label": "clear_delivered_deny",
        "expected_resolution": "deny",
        "expected_gate": "LIQUET",
        "difficulty": "clear",
        "dispute": {
            "order_id": "ORD-CLEAR-002",
            "dispute_type": "never_arrived",
            "buyer_id": "USR-B002",
            "seller_id": "USR-S002",
            "buyer_narrative": "I never received my jacket. I want a full refund.",
            "seller_narrative": "FedEx tracking shows delivery at 2:32pm with signature J. DOE at the buyer's address.",
            "metadata": {"evidence_images": []},
        },
        "synthetic_tracking": {
            "status": "delivered",
            "delivered_at": "2025-11-08T14:32:00Z",
            "signed_by": "J. DOE",
        },
    },

    # ── CLEAR: broken ceramics with photos → PARTIAL_REFUND ─────────────────────
    {
        "id": "CASE-003",
        "label": "clear_damaged_partial",
        "expected_resolution": "partial_refund",
        "expected_gate": "LIQUET",
        "difficulty": "clear",
        "dispute": {
            "order_id": "ORD-CLEAR-003",
            "dispute_type": "damaged",
            "buyer_id": "USR-B003",
            "seller_id": "USR-S003",
            "buyer_narrative": "3 of the 6 ceramic cups arrived broken. The box was clearly crushed. I have photos showing the damage and crushed packaging.",
            "seller_narrative": "I packaged everything carefully with bubble wrap. USPS must have dropped the package. I'm not responsible for carrier damage.",
            "metadata": {"evidence_images": ["https://example.com/broken_cups_damage.jpg"]},
        },
        "synthetic_vision": {
            "damage_detected": True,
            "observations": ["3 ceramic cups show clear breakage", "Package exterior shows impact deformation"],
        },
    },

    # ── CLEAR: wrong item shipped → FULL_REFUND ──────────────────────────────────
    {
        "id": "CASE-004",
        "label": "clear_wrong_item",
        "expected_resolution": "full_refund",
        "expected_gate": "LIQUET",
        "difficulty": "clear",
        "dispute": {
            "order_id": "ORD-CLEAR-004",
            "dispute_type": "wrong_item",
            "buyer_id": "USR-B004",
            "seller_id": "USR-S004",
            "buyer_narrative": "I ordered a size Medium blue dress but received a size XXL red shirt. Completely wrong item. Photos attached.",
            "seller_narrative": "I may have mixed up the orders. I'll need to investigate my inventory.",
            "metadata": {"evidence_images": []},
        },
        "synthetic_tracking": {"status": "delivered", "delivered_at": "2025-11-10T10:00:00Z"},
    },

    # ── BORDERLINE: color mismatch — lighting defense is plausible ───────────────
    {
        "id": "CASE-005",
        "label": "borderline_color_mismatch",
        "expected_resolution": "partial_refund",
        "expected_gate": "NON_LIQUET",
        "difficulty": "borderline",
        "dispute": {
            "order_id": "ORD-BORDER-001",
            "dispute_type": "not_as_described",
            "buyer_id": "USR-B005",
            "seller_id": "USR-S005",
            "buyer_narrative": "The leather jacket I received is dark grey. The listing shows brown leather. This is a clear misrepresentation. I have photos of what I received next to the listing photo.",
            "seller_narrative": "The jacket IS brown — it photographs differently under different lighting conditions. Leather color perception varies widely. This is the same jacket from the listing. No refund is warranted.",
            "metadata": {"evidence_images": ["https://example.com/grey_jacket_buyer_photo.jpg"]},
        },
        "synthetic_vision": {
            "damage_detected": False,
            "color_observed": "grey/charcoal",
            "observations": ["Jacket appears grey-charcoal in this lighting", "No visible damage"],
            "confidence": 0.70,
        },
    },

    # ── ENGINEERED 50/50: symmetric conflicting evidence → MUST be NON_LIQUET ────
    {
        "id": "CASE-006",
        "label": "engineered_fifty_fifty",
        "expected_resolution": "escalate",
        "expected_gate": "NON_LIQUET",
        "difficulty": "fifty_fifty",
        "notes": "DEMO SHOWSTOPPER: buyer has unboxing video showing scratch; seller has pre-ship inspection photo showing no scratch. Neither can be verified as authentic. Carrier delivered. Camera lens at $649.",
        "dispute": {
            "order_id": "ORD-5050-001",
            "dispute_type": "not_as_described",
            "buyer_id": "USR-B006",
            "seller_id": "USR-S006",
            "buyer_narrative": "I recorded my unboxing on video. The moment I removed the lens from the box it was visibly scratched on the front element. The scratch was there before I touched it. $649 for a damaged lens — I need a full refund.",
            "seller_narrative": "I have detailed inspection photos taken on the day of shipping, one hour before I handed it to DHL. The glass was perfect. I've been selling cameras for 8 years with zero complaints. The buyer must have dropped it after unboxing and is staging a claim. I refuse any refund.",
            "metadata": {
                "evidence_images": [
                    "https://example.com/buyer_unboxing_scratch.jpg",
                    "https://example.com/seller_preship_no_scratch.jpg",
                ],
                "hard_contradiction": True,
            },
        },
        "synthetic_vision": {
            "photo_1": {
                "damage_detected": True,
                "observations": ["Scratch visible on front lens element"],
                "confidence": 0.78,
            },
            "photo_2": {
                "damage_detected": False,
                "observations": ["Lens element appears clean and undamaged in this photo"],
                "confidence": 0.75,
            },
        },
        "hard_contradiction": "Buyer's unboxing video shows scratch present; seller's pre-ship photo shows no scratch. Both sources have moderate reliability. Cannot determine which is authentic.",
    },

    # ── HIGH VALUE: high confidence but must escalate on value (V-001) ──────────
    {
        "id": "CASE-007",
        "label": "high_value_escalate",
        "expected_resolution": "full_refund",
        "expected_gate": "NON_LIQUET",
        "difficulty": "high_value",
        "notes": "Clear case but order value $649 triggers V-001 policy escalation.",
        "dispute": {
            "order_id": "ORD-HIGH-001",
            "dispute_type": "never_arrived",
            "buyer_id": "USR-B007",
            "seller_id": "USR-S007",
            "buyer_narrative": "I paid $649 for a camera lens and tracking has been stuck for 25 days. Never delivered.",
            "seller_narrative": "I shipped it. The carrier must have lost it.",
            "metadata": {"evidence_images": [], "order_value_override": 649.0},
        },
        "synthetic_tracking": {"status": "in_transit", "delivered_at": None, "days_stalled": 25},
    },

    # ── CLEAR: DOA electronics, seller tested pre-ship claim unverified → REPLACEMENT
    {
        "id": "CASE-008",
        "label": "clear_doa_electronics",
        "expected_resolution": "replacement",
        "expected_gate": "LIQUET",
        "difficulty": "clear",
        "dispute": {
            "order_id": "ORD-CLEAR-008",
            "dispute_type": "not_as_described",
            "buyer_id": "USR-B008",
            "seller_id": "USR-S008",
            "buyer_narrative": "The gaming headset arrived dead on arrival. Will not power on despite trying USB 3.0, different computers, and a 10-second reset. The item was listed as 'brand new' but it clearly has a defect.",
            "seller_narrative": "I tested it before shipping and it worked. This must be user error or damage the buyer caused.",
            "metadata": {"evidence_images": []},
        },
        "synthetic_tracking": {"status": "delivered", "delivered_at": "2025-11-12T10:15:00Z"},
    },

    # ── BORDERLINE: tracking stalled 10 days but still within uncertainty window ──
    {
        "id": "CASE-009",
        "label": "borderline_stalled_tracking",
        "expected_resolution": "escalate",
        "expected_gate": "NON_LIQUET",
        "difficulty": "borderline",
        "dispute": {
            "order_id": "ORD-BORDER-002",
            "dispute_type": "never_arrived",
            "buyer_id": "USR-B009",
            "seller_id": "USR-S009",
            "buyer_narrative": "My yoga mat has been stuck 'in transit' for 10 days. The tracking hasn't updated and the estimated delivery was 5 days ago.",
            "seller_narrative": "Tracking shows it was picked up and is in transit. USPS sometimes has delays. Please wait a few more days before escalating.",
            "metadata": {"evidence_images": []},
        },
        "synthetic_tracking": {"status": "in_transit", "days_stalled": 10, "delivered_at": None},
    },

    # ── CLEAR: counterfeit item → FULL_REFUND mandatory ──────────────────────────
    {
        "id": "CASE-010",
        "label": "clear_counterfeit",
        "expected_resolution": "full_refund",
        "expected_gate": "LIQUET",
        "difficulty": "clear",
        "dispute": {
            "order_id": "ORD-CLEAR-010",
            "dispute_type": "counterfeit",
            "buyer_id": "USR-B010",
            "seller_id": "USR-S010",
            "buyer_narrative": "I received what appears to be a counterfeit luxury watch. The serial number doesn't exist in the brand's database, the logo font is wrong, and the movement sounds wrong. I have expert verification photos.",
            "seller_narrative": "It's genuine. I bought it from a trusted wholesaler.",
            "metadata": {"evidence_images": ["https://example.com/counterfeit_evidence.jpg"]},
        },
    },
]


def generate() -> None:
    for case in CASES:
        path = CASES_DIR / f"{case['id']}.json"
        path.write_text(json.dumps(case, indent=2))
        print(f"  Generated {path.name}: {case['label']} (expected: {case['expected_gate']} -> {case['expected_resolution']})")

    index = {"cases": [c["id"] for c in CASES], "total": len(CASES)}
    (CASES_DIR / "index.json").write_text(json.dumps(index, indent=2))
    print(f"\nGenerated {len(CASES)} cases in {CASES_DIR}")


if __name__ == "__main__":
    generate()
