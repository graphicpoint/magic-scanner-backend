"""
Claude Vision Integration
Uses Claude's vision capabilities to identify Magic cards from images
"""

import anthropic
import base64
import os
import logging
from typing import List, Dict, Any, Optional
import json
import re

logger = logging.getLogger(__name__)

# Initialize Anthropic client
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
if not ANTHROPIC_API_KEY:
    logger.warning("ANTHROPIC_API_KEY not set - Claude Vision will not work")

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY) if ANTHROPIC_API_KEY else None


def identify_cards_with_vision(image_data: bytes) -> List[Dict[str, Any]]:
    """
    Use Claude Vision to identify Magic cards in an image

    Args:
        image_data: Raw image bytes

    Returns:
        List of identified cards with name, set, and collector_number
    """
    if not client:
        logger.error("Claude Vision not available - ANTHROPIC_API_KEY not set")
        return []

    try:
        # Encode image to base64
        image_base64 = base64.standard_b64encode(image_data).decode("utf-8")

        # Determine media type (assume JPEG, but could be improved)
        media_type = "image/jpeg"
        if image_data.startswith(b'\x89PNG'):
            media_type = "image/png"
        elif image_data.startswith(b'WEBP'):
            media_type = "image/webp"

        logger.info("Sending image to Claude Vision API...")

        # Call Claude Vision API
        message = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=2048,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": media_type,
                                "data": image_base64,
                            },
                        },
                        {
                            "type": "text",
                            "text": """Identify all Magic: The Gathering cards visible in this image.

For each card you can see, provide:
- Card name (exact name as it appears on the card)
- Set code (3-4 letter code, e.g., "NEO", "MID", "AFR") if visible
- Collector number if visible

Return your response as a JSON array with this exact format:
[
  {
    "name": "Lightning Bolt",
    "set": "LEA",
    "collector_number": "162",
    "confidence": "high"
  }
]

Rules:
- Only include cards you can clearly identify
- If you can't read the set or collector number, omit that field
- Use "confidence": "high", "medium", or "low" based on image quality
- If no Magic cards are visible, return an empty array: []

Return ONLY the JSON array, no other text."""
                        }
                    ],
                }
            ],
        )

        # Extract response text
        response_text = message.content[0].text.strip()
        logger.info(f"Claude Vision response: {response_text}")

        # Parse JSON response
        # Handle potential markdown code blocks
        if "```json" in response_text:
            # Extract JSON from markdown code block
            json_match = re.search(r'```json\s*([\s\S]*?)\s*```', response_text)
            if json_match:
                response_text = json_match.group(1)
        elif "```" in response_text:
            # Extract from generic code block
            json_match = re.search(r'```\s*([\s\S]*?)\s*```', response_text)
            if json_match:
                response_text = json_match.group(1)

        cards = json.loads(response_text)

        if not isinstance(cards, list):
            logger.error(f"Expected list from Claude Vision, got: {type(cards)}")
            return []

        logger.info(f"Claude Vision identified {len(cards)} card(s)")
        return cards

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse Claude Vision response as JSON: {e}")
        logger.error(f"Response was: {response_text}")
        return []
    except Exception as e:
        logger.error(f"Error calling Claude Vision API: {e}", exc_info=True)
        return []


def validate_card_identification(card: Dict[str, Any]) -> bool:
    """
    Validate that a card identification has required fields

    Args:
        card: Card identification dict

    Returns:
        True if valid, False otherwise
    """
    if not isinstance(card, dict):
        return False

    # Name is required
    if "name" not in card or not card["name"]:
        return False

    # Confidence should be present
    if "confidence" not in card:
        card["confidence"] = "medium"

    return True
