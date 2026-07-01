"""Comms Service MCP server â€” buyer-seller message history."""


import json
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("comms_service")

_DATA_FILE = Path(__file__).parent.parent.parent / "data" / "messages.json"
_messages: dict[str, list] = {}


def _load_data() -> None:
    global _messages
    if _DATA_FILE.exists():
        _messages = json.loads(_DATA_FILE.read_text())
    else:
        _messages = {
            "ORD-001": [
                {"ts": "2025-11-08T18:00:00Z", "from": "buyer", "text": "I just received the jacket but the color is dark grey, not brown like in the listing photos."},
                {"ts": "2025-11-08T20:15:00Z", "from": "seller", "text": "That's impossible â€” I shipped the exact item from the photos. The color is brown leather, it may look different under indoor lighting."},
                {"ts": "2025-11-09T09:00:00Z", "from": "buyer", "text": "I've attached photos. This is clearly grey, not brown. I want a refund."},
                {"ts": "2025-11-09T11:30:00Z", "from": "seller", "text": "I see your photo. This is the same jacket. Lighting and camera settings make leather look different. No refund warranted."},
            ],
            "ORD-002": [
                {"ts": "2025-11-13T10:00:00Z", "from": "buyer", "text": "Received the headset but it won't connect. Tried both USB and 3.5mm. Dead on arrival."},
                {"ts": "2025-11-13T14:00:00Z", "from": "seller", "text": "Sorry to hear that. Please try holding the power button for 10 seconds to reset. Also ensure USB dongle is plugged into USB 3.0 port."},
                {"ts": "2025-11-13T16:30:00Z", "from": "buyer", "text": "Tried everything. Still completely dead. I need a replacement or full refund."},
                {"ts": "2025-11-13T18:00:00Z", "from": "seller", "text": "I tested this item before shipping and it worked perfectly. I believe you may have damaged it."},
            ],
            "ORD-003": [
                {"ts": "2025-11-05T12:00:00Z", "from": "buyer", "text": "The ceramic set arrived â€” 3 of the 6 cups are broken. The packaging wasn't adequate for fragile items."},
                {"ts": "2025-11-05T15:00:00Z", "from": "seller", "text": "I'm so sorry! I packaged everything carefully but USPS must have damaged it in transit. I have insurance. Please file a claim and I'll help."},
                {"ts": "2025-11-05T17:00:00Z", "from": "buyer", "text": "I've taken photos of all broken pieces and the packaging. What do we do next?"},
                {"ts": "2025-11-06T09:00:00Z", "from": "seller", "text": "Please send the photos. I'll contact USPS and we'll get you a partial refund for the broken items."},
            ],
            "ORD-004": [
                {"ts": "2025-11-18T09:00:00Z", "from": "buyer", "text": "The lens arrived but there is a large scratch on the front element that wasn't disclosed. This significantly affects image quality."},
                {"ts": "2025-11-18T11:00:00Z", "from": "seller", "text": "There was NO scratch when I shipped it. I inspected it carefully. The listing says 'excellent condition' and that was accurate."},
                {"ts": "2025-11-18T14:00:00Z", "from": "buyer", "text": "I have unboxing video showing the scratch was there when I opened it. $649 and I got a damaged lens."},
                {"ts": "2025-11-18T16:00:00Z", "from": "seller", "text": "A video can be staged. I won't issue a refund for damage you may have caused."},
            ],
            "ORD-005": [
                {"ts": "2025-11-25T08:00:00Z", "from": "buyer", "text": "It's been 10 days and my yoga mat hasn't arrived. Tracking hasn't updated in 5 days."},
                {"ts": "2025-11-25T10:00:00Z", "from": "seller", "text": "Tracking shows it's in transit. Sometimes USPS is slow. Please wait a few more days."},
                {"ts": "2025-11-28T09:00:00Z", "from": "buyer", "text": "Still nothing. Tracking still frozen. I want a refund."},
                {"ts": "2025-11-28T12:00:00Z", "from": "seller", "text": "According to tracking it's been shipped and is on the way. I am not responsible for carrier delays."},
            ],
        }


@mcp.tool()
def get_messages(order_id: str) -> list:
    """Get the full buyer-seller message thread for an order."""
    _load_data()
    msgs = _messages.get(order_id)
    if msgs is None:
        return []
    return msgs


@mcp.tool()
def get_message_summary(order_id: str) -> dict:
    """Get a structured summary of the message thread: key claims by each party."""
    _load_data()
    msgs = _messages.get(order_id, [])
    buyer_msgs = [m["text"] for m in msgs if m["from"] == "buyer"]
    seller_msgs = [m["text"] for m in msgs if m["from"] == "seller"]
    return {
        "order_id": order_id,
        "total_messages": len(msgs),
        "buyer_messages": buyer_msgs,
        "seller_messages": seller_msgs,
        "first_message_ts": msgs[0]["ts"] if msgs else None,
        "last_message_ts": msgs[-1]["ts"] if msgs else None,
    }


if __name__ == "__main__":
    import os
    port = int(os.getenv("COMMS_SERVICE_PORT", "8004"))
    mcp.run(transport="sse", host="0.0.0.0", port=port)
