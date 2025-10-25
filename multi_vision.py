"""
Multi-provider vision API integration with parallel validation
"""
import asyncio
import logging
from typing import List, Dict, Any
from claude_vision import identify_cards_with_vision as identify_with_claude
from openai_vision import identify_cards_with_openai

logger = logging.getLogger(__name__)

def identify_cards_pro(image_data: bytes) -> List[Dict[str, Any]]:
    """
    Pro Scan: Use both Claude and OpenAI Vision APIs in parallel and validate results

    Strategy:
    1. Call both APIs simultaneously
    2. Compare card names - if both agree, high confidence
    3. Use Claude's set/number as primary, but validate against name
    4. If only one provider succeeds, use that result

    Args:
        image_data: Raw image bytes

    Returns:
        List of identified cards with validated data
    """
    logger.info("Starting Pro Scan with parallel validation (Claude + OpenAI)...")

    # Call both APIs in parallel using asyncio
    import concurrent.futures

    claude_results = []
    openai_results = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        # Submit both tasks
        claude_future = executor.submit(identify_with_claude, image_data)
        openai_future = executor.submit(identify_cards_with_openai, image_data)

        # Wait for both to complete and handle errors
        try:
            claude_results = claude_future.result()
        except Exception as e:
            logger.error(f"Claude Vision failed: {e}")

        try:
            openai_results = openai_future.result()
        except Exception as e:
            logger.error(f"OpenAI Vision failed: {e}")
            # If OpenAI fails (e.g., API key not set), continue with Claude only

    logger.info(f"Claude identified {len(claude_results)} card(s)")
    logger.info(f"OpenAI identified {len(openai_results)} card(s)")

    # Combine and validate results
    validated_cards = []

    # Try to match cards from both providers
    for i in range(max(len(claude_results), len(openai_results))):
        claude_card = claude_results[i] if i < len(claude_results) else None
        openai_card = openai_results[i] if i < len(openai_results) else None

        if claude_card and openai_card:
            # Both providers found a card - validate
            claude_name = claude_card.get('name', '').lower().strip()
            openai_name = openai_card.get('name', '').lower().strip()

            if claude_name == openai_name:
                # Perfect match - high confidence!
                logger.info(f"✓ Both providers agree on card name: '{claude_card.get('name')}'")

                # Return both set/number options for main.py to try
                # This handles cases where one provider reads the set/number correctly
                validated_cards.append({
                    'name': claude_card.get('name'),  # Use Claude's capitalization
                    'set': claude_card.get('set'),
                    'collector_number': claude_card.get('collector_number'),
                    'set_alternatives': [{
                        'set': openai_card.get('set'),
                        'collector_number': openai_card.get('collector_number')
                    }] if openai_card.get('set') != claude_card.get('set') or openai_card.get('collector_number') != claude_card.get('collector_number') else [],
                    'confidence': 'high',  # Both agreed
                    'validation': 'both_agree'
                })
            else:
                # Names differ - trust the one with more complete data
                logger.warning(f"⚠ Providers disagree: Claude='{claude_card.get('name')}' vs OpenAI='{openai_card.get('name')}'")

                # Prefer the one with set + collector number
                if claude_card.get('set') and claude_card.get('collector_number'):
                    logger.info(f"Using Claude result (has set/number)")
                    validated_cards.append({
                        **claude_card,
                        'confidence': 'medium',
                        'validation': 'claude_preferred'
                    })
                elif openai_card.get('set') and openai_card.get('collector_number'):
                    logger.info(f"Using OpenAI result (has set/number)")
                    validated_cards.append({
                        **openai_card,
                        'confidence': 'medium',
                        'validation': 'openai_preferred'
                    })
                else:
                    # Neither has complete data - use Claude as default
                    logger.info(f"Using Claude result (default)")
                    validated_cards.append({
                        **claude_card,
                        'confidence': 'low',
                        'validation': 'claude_default'
                    })

        elif claude_card:
            # Only Claude found a card
            logger.info(f"Only Claude found card: '{claude_card.get('name')}'")
            validated_cards.append({
                **claude_card,
                'confidence': 'medium',
                'validation': 'claude_only'
            })

        elif openai_card:
            # Only OpenAI found a card
            logger.info(f"Only OpenAI found card: '{openai_card.get('name')}'")
            validated_cards.append({
                **openai_card,
                'confidence': 'medium',
                'validation': 'openai_only'
            })

    logger.info(f"Pro Scan validated {len(validated_cards)} card(s)")
    return validated_cards
