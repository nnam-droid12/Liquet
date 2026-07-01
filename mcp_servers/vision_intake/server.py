"""
Vision Intake MCP server â€” wraps qwen-vl-plus (qwen3.6-plus) for dispute photo analysis.

Perception is cleanly separated from judgment:
- This server does ONLY visual observation (what does the image show?)
- The reasoning core (qwen3.7-max / orchestrator) interprets observations against claims.
"""


import asyncio
from typing import Any, Optional

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("vision_intake")

VISION_PROMPT = """You are a neutral evidence analyst reviewing a dispute photo.
Describe what you observe with precision:
1. Identify the item in the photo
2. Note the condition: any damage, discoloration, missing parts, or anomalies
3. Note the color(s) visible
4. If packaging is visible, note its condition
5. Do NOT interpret or assign fault â€” only describe what you see

Respond with a JSON object:
{
  "observations": ["list of specific factual observations"],
  "damage_detected": true/false,
  "damage_description": "description of damage if any",
  "color_observed": "primary color(s) observed",
  "item_identified": "what item is this",
  "packaging_condition": "condition of packaging if visible, or null",
  "confidence": 0.0-1.0,
  "raw_description": "one paragraph natural language description"
}"""


@mcp.tool()
def analyze_image(image_url: str, listing_description: str = "") -> dict:
    """
    Analyze a dispute evidence image using the vision model.
    Returns structured observations: damage, color, condition mismatch signals.
    """
    return asyncio.get_event_loop().run_until_complete(
        _analyze_image_async(image_url, listing_description)
    )


async def _analyze_image_async(image_url: str, listing_description: Optional[str]) -> dict:
    try:
        import sys
        import os
        sys.path.insert(0, str(__file__).split("mcp_servers")[0])
        from backend.core.llm_client import vision_completion
        from config import settings

        prompt = VISION_PROMPT
        if listing_description:
            prompt += f"\n\nThe listing described this item as: {listing_description}\nNote any discrepancies."

        raw = await vision_completion(prompt, image_url, model=settings.model_vision)

        import json
        try:
            result = json.loads(raw)
        except json.JSONDecodeError:
            result = {
                "observations": [raw],
                "damage_detected": False,
                "raw_description": raw,
                "confidence": 0.5,
                "parse_error": True,
            }
        result["image_url"] = image_url
        result["model_used"] = settings.model_vision
        return result

    except Exception as exc:
        return {
            "error": str(exc),
            "image_url": image_url,
            "observations": [],
            "damage_detected": False,
            "confidence": 0.0,
            "raw_description": f"Vision analysis failed: {exc}",
        }


@mcp.tool()
def analyze_image_mock(image_url: str, listing_description: str = "") -> dict:
    """Mock vision analysis for offline testing â€” returns deterministic results based on URL keywords."""
    url_lower = image_url.lower()

    if "damage" in url_lower or "broken" in url_lower or "crack" in url_lower:
        return {
            "observations": ["Item shows visible damage", "Cracking on surface", "Color matches listing"],
            "damage_detected": True,
            "damage_description": "Visible cracks or breakage consistent with impact damage",
            "color_observed": "as listed",
            "item_identified": "disputed item",
            "packaging_condition": "packaging appears insufficient for fragile item",
            "confidence": 0.85,
            "raw_description": "The item shows clear physical damage. Cracking is visible.",
            "image_url": image_url,
            "model_used": "mock",
        }
    elif "grey" in url_lower or "gray" in url_lower or "wrong_color" in url_lower:
        return {
            "observations": ["Item color appears grey/charcoal", "Item appears to be a jacket", "No visible damage"],
            "damage_detected": False,
            "color_observed": "grey/charcoal",
            "item_identified": "leather jacket",
            "packaging_condition": None,
            "confidence": 0.72,
            "raw_description": "The jacket in this photo appears grey or charcoal in color.",
            "image_url": image_url,
            "model_used": "mock",
        }
    else:
        return {
            "observations": ["Item appears to match described condition", "No obvious damage visible"],
            "damage_detected": False,
            "color_observed": "as expected",
            "item_identified": "disputed item",
            "packaging_condition": None,
            "confidence": 0.65,
            "raw_description": "Item appears to be in the described condition based on visible features.",
            "image_url": image_url,
            "model_used": "mock",
        }


if __name__ == "__main__":
    import os
    port = int(os.getenv("VISION_INTAKE_PORT", "8005"))
    mcp.run(transport="sse", host="0.0.0.0", port=port)
