"""
Google Gemini Vision API integration for card identification
"""
import os
import base64
import json
import logging
from typing import List, Dict, Any
import google.generativeai as genai

logger = logging.getLogger(__name__)

def _get_gemini_client():
    """Lazy initialization of Gemini client"""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable is not set")
    genai.configure(api_key=api_key)
    return genai.GenerativeModel('gemini-2.0-flash-exp')

def identify_cards_with_gemini(image_data: bytes) -> List[Dict[str, Any]]:
    """
    Identify Magic: The Gathering cards using Google Gemini Vision API

    Args:
        image_data: Raw image bytes

    Returns:
        List of identified cards with name, set, collector_number, and confidence
    """
    try:
        logger.info("Sending image to Gemini Vision API...")

        # Get Gemini client (lazy initialization)
        model = _get_gemini_client()

        # Prepare image for Gemini
        import PIL.Image
        import io
        image = PIL.Image.open(io.BytesIO(image_data))

        # Create prompt
        prompt = """You are analyzing a Magic: The Gathering card photo.

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
Confidence should be: "high", "medium", or "low" based on image quality.

Return ONLY the JSON array, no other text."""

        # Call Gemini Vision API
        response = model.generate_content([prompt, image])

        # Parse response
        response_text = response.text
        logger.info(f"Gemini Vision response: {response_text}")

        # Extract JSON from response (might be wrapped in markdown code blocks)
        if "```json" in response_text:
            json_str = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            json_str = response_text.split("```")[1].split("```")[0].strip()
        else:
            json_str = response_text.strip()

        # Parse JSON
        cards = json.loads(json_str)

        logger.info(f"Gemini Vision identified {len(cards)} card(s)")
        return cards

    except Exception as e:
        logger.error(f"Error identifying cards with Gemini Vision: {str(e)}")
        return []
