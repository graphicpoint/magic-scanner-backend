"""
Image comparison utilities for matching photographed cards with Scryfall images
"""
import os
import base64
import logging
from typing import List, Dict, Any, Optional
import httpx
from anthropic import Anthropic

logger = logging.getLogger(__name__)


async def download_image(url: str) -> Optional[bytes]:
    """
    Download an image from a URL

    Args:
        url: Image URL

    Returns:
        Image bytes or None if download fails
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=10.0)
            response.raise_for_status()
            return response.content
    except Exception as e:
        logger.error(f"Failed to download image from {url}: {e}")
        return None


def compare_cards_with_vision(
    user_image: bytes,
    candidate_cards: List[Dict[str, Any]]
) -> Optional[Dict[str, Any]]:
    """
    Use Claude Vision to compare user's photo with candidate Scryfall images
    and select the best match

    Args:
        user_image: User's photographed card (bytes)
        candidate_cards: List of candidate card objects from Scryfall

    Returns:
        Best matching card object or None
    """
    try:
        logger.info(f"Comparing user image with {len(candidate_cards)} candidate cards using Claude Vision...")

        # Get Anthropic client
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            logger.error("ANTHROPIC_API_KEY not set")
            return None

        client = Anthropic(api_key=api_key)

        # Encode user image
        user_image_base64 = base64.b64encode(user_image).decode('utf-8')

        # Detect image format
        if user_image.startswith(b'\xff\xd8'):
            media_type = "image/jpeg"
        elif user_image.startswith(b'\x89PNG'):
            media_type = "image/png"
        else:
            media_type = "image/jpeg"

        # Build prompt with candidate descriptions
        candidates_text = "\n".join([
            f"{i+1}. {card['set_name']} ({card['set'].upper()}) #{card.get('collector_number', '?')} - {card.get('rarity', 'unknown')} - Released: {card.get('released_at', 'unknown')}"
            for i, card in enumerate(candidate_cards)
        ])

        prompt = f"""You are comparing a photographed Magic: The Gathering card with potential matches from Scryfall.

I will show you the photographed card first, then describe the candidate matches.

Your task: Identify which candidate card BEST matches the photographed card based on:
1. Visual appearance (artwork, frame style, colors)
2. Set symbol (if visible)
3. Collector number (if visible at bottom of card)
4. Card frame/border style
5. Special treatments (foil, showcase, borderless, etc.)

Photographed card is shown in the first image.

Candidate cards:
{candidates_text}

Return ONLY a JSON object with this format:
{{
  "best_match_index": <number 1-{len(candidate_cards)}>,
  "confidence": "<high|medium|low>",
  "reasoning": "<brief explanation of why this match was chosen>"
}}

If none of the candidates match well, return best_match_index: 0 with low confidence."""

        # Create message content with user image
        message_content = [
            {
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": media_type,
                    "data": user_image_base64,
                },
            },
            {
                "type": "text",
                "text": prompt
            }
        ]

        # Call Claude Vision
        response = client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=500,
            messages=[
                {
                    "role": "user",
                    "content": message_content
                }
            ],
        )

        response_text = response.content[0].text
        logger.info(f"Claude Vision comparison response: {response_text}")

        # Parse JSON response
        import json

        # Extract JSON from response
        if "```json" in response_text:
            json_str = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            json_str = response_text.split("```")[1].split("```")[0].strip()
        else:
            json_str = response_text.strip()

        result = json.loads(json_str)

        best_match_index = result.get('best_match_index', 0)
        confidence = result.get('confidence', 'low')
        reasoning = result.get('reasoning', '')

        if best_match_index > 0 and best_match_index <= len(candidate_cards):
            selected_card = candidate_cards[best_match_index - 1]
            logger.info(f"✓ Selected card {best_match_index}/{len(candidate_cards)}: {selected_card['set'].upper()}/{selected_card.get('collector_number')} - Confidence: {confidence}")
            logger.info(f"Reasoning: {reasoning}")
            return selected_card
        else:
            logger.info(f"No confident match found (best_match_index={best_match_index}, confidence={confidence})")
            return None

    except Exception as e:
        logger.error(f"Error in vision-based comparison: {e}")
        return None
