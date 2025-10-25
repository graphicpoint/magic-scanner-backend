"""
OpenAI Vision API integration for card identification
"""
import os
import base64
import json
import logging
from typing import List, Dict, Any, Optional
from openai import OpenAI

logger = logging.getLogger(__name__)

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def identify_cards_with_openai(image_data: bytes) -> List[Dict[str, Any]]:
    """
    Identify Magic: The Gathering cards using OpenAI Vision API

    Args:
        image_data: Raw image bytes

    Returns:
        List of identified cards with name, set, collector_number, and confidence
    """
    try:
        logger.info("Sending image to OpenAI Vision API...")

        # Encode image to base64
        image_base64 = base64.b64encode(image_data).decode('utf-8')

        # Detect image format
        if image_data.startswith(b'\xff\xd8'):
            media_type = "image/jpeg"
        elif image_data.startswith(b'\x89PNG'):
            media_type = "image/png"
        else:
            media_type = "image/jpeg"  # Default fallback

        # Call OpenAI Vision API
        response = client.chat.completions.create(
            model="gpt-4o",  # Latest vision model
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{media_type};base64,{image_base64}"
                            }
                        },
                        {
                            "type": "text",
                            "text": """You are analyzing a Magic: The Gathering card photo.

CRITICAL: Read the EXACT card name from the card itself - do not guess or infer.

For each card visible:
1. Read the card name at the TOP of the card (in the title box)
2. Look for the set symbol (middle-right side of card)
3. Look for the collector number at the BOTTOM of the card (format: 123/456)

Return ONLY a JSON array in this exact format:
[
  {
    "name": "Exact Card Name From Title",
    "set": "SET",
    "collector_number": "123",
    "confidence": "high"
  }
]

If you cannot read the set or collector_number clearly, omit those fields.
Confidence should be: "high", "medium", or "low" based on image quality."""
                        }
                    ],
                }
            ],
            max_tokens=500
        )

        # Parse response
        response_text = response.choices[0].message.content
        logger.info(f"OpenAI Vision response: {response_text}")

        # Extract JSON from response (might be wrapped in markdown code blocks)
        if "```json" in response_text:
            json_str = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            json_str = response_text.split("```")[1].split("```")[0].strip()
        else:
            json_str = response_text.strip()

        # Parse JSON
        cards = json.loads(json_str)

        logger.info(f"OpenAI Vision identified {len(cards)} card(s)")
        return cards

    except Exception as e:
        logger.error(f"Error identifying cards with OpenAI Vision: {str(e)}")
        return []
