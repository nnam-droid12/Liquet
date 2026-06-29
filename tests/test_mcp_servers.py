"""Integration tests for MCP server tools (in-process calls)."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from mcp_servers.order_service.server import get_order, list_buyer_orders
from mcp_servers.logistics_service.server import get_tracking, was_delivered
from mcp_servers.listing_service.server import get_listing
from mcp_servers.comms_service.server import get_messages, get_message_summary
from mcp_servers.policy_engine.server import evaluate_policy, get_policy_text
from mcp_servers.resolution_service.server import deny_claim, get_ledger


class TestOrderService:
    def test_get_existing_order(self):
        result = get_order("ORD-001")
        assert result["order_id"] == "ORD-001"
        assert result["price"] == 89.99
        assert "buyer_id" in result

    def test_get_nonexistent_order(self):
        result = get_order("ORD-FAKE-999")
        assert "error" in result

    def test_list_buyer_orders(self):
        orders = list_buyer_orders("USR-B001")
        assert any(o["order_id"] == "ORD-001" for o in orders)


class TestLogisticsService:
    def test_get_tracking_delivered(self):
        result = get_tracking("ORD-001")
        assert result["status"] == "delivered"
        assert len(result["events"]) > 0

    def test_was_delivered_true(self):
        result = was_delivered("ORD-001")
        assert result["delivered"] is True
        assert result["evidence_quality"] == "carrier_scan"

    def test_was_delivered_missing(self):
        result = was_delivered("ORD-FAKE-999")
        assert result["delivered"] is False


class TestListingService:
    def test_get_listing(self):
        result = get_listing("PROD-001")
        assert "brown" in result["description"].lower() or "leather" in result["title"].lower()

    def test_get_listing_missing(self):
        result = get_listing("PROD-FAKE")
        assert "error" in result


class TestCommsService:
    def test_get_messages(self):
        msgs = get_messages("ORD-001")
        assert len(msgs) > 0
        assert any(m["from"] == "buyer" for m in msgs)

    def test_get_message_summary(self):
        summary = get_message_summary("ORD-001")
        assert summary["total_messages"] == 4

    def test_empty_messages(self):
        msgs = get_messages("ORD-FAKE-999")
        assert msgs == []


class TestPolicyEngine:
    def test_never_arrived_no_tracking_full_refund(self):
        result = evaluate_policy({
            "order_value": 89.99,
            "dispute_type": "never_arrived",
            "delivered": False,
            "tracking_missing": False,
            "damage_in_photos": False,
            "color_mismatch": False,
            "wrong_item": False,
        })
        assert "full_refund" in result["eligible_resolutions"]
        assert not result["requires_escalation"]

    def test_high_value_requires_escalation(self):
        result = evaluate_policy({
            "order_value": 649.0,
            "dispute_type": "not_as_described",
            "delivered": True,
            "tracking_missing": False,
            "damage_in_photos": False,
            "color_mismatch": True,
            "wrong_item": False,
        })
        assert result["requires_escalation"] is True
        assert "V-001" in result["hard_blocks"][0]

    def test_policy_text_loads(self):
        text = get_policy_text()
        assert "LIQUET" in text or "P-001" in text


class TestResolutionService:
    def test_deny_claim_records_in_ledger(self):
        result = deny_claim("TEST-D001", "ORD-001", "USR-B001", "Insufficient evidence")
        assert result["action"] == "deny"
        assert result["status"] == "executed"

        ledger = get_ledger("TEST-D001")
        assert any(e["action"] == "deny" for e in ledger)
