"""
Multi-provider vision API integration with parallel validation
"""
import asyncio
import logging
from typing import List, Dict, Any
from claude_vision import identify_cards_with_vision as identify_with_claude
from openai_vision import identify_cards_with_openai
from gemini_vision import identify_cards_with_gemini

logger = logging.getLogger(__name__)

def identify_cards_pro(image_data: bytes) -> List[Dict[str, Any]]:
    """
    Pro Scan: Use Claude, OpenAI, and Gemini Vision APIs in parallel and validate results

    Strategy:
    1. Call all three APIs simultaneously
    2. Compare card names - if majority agrees, high confidence
    3. Collect all set/number combinations as alternatives
    4. If only one provider succeeds, use that result

    Args:
        image_data: Raw image bytes

    Returns:
        List of identified cards with validated data
    """
    logger.info("Starting Pro Scan with parallel validation (Claude + OpenAI + Gemini)...")

    # Call all three APIs in parallel
    import concurrent.futures

    claude_results = []
    openai_results = []
    gemini_results = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        # Submit all three tasks
        claude_future = executor.submit(identify_with_claude, image_data)
        openai_future = executor.submit(identify_cards_with_openai, image_data)
        gemini_future = executor.submit(identify_cards_with_gemini, image_data)

        # Wait for all to complete and handle errors
        try:
            claude_results = claude_future.result()
        except Exception as e:
            logger.error(f"Claude Vision failed: {e}")

        try:
            openai_results = openai_future.result()
        except Exception as e:
            logger.error(f"OpenAI Vision failed: {e}")

        try:
            gemini_results = gemini_future.result()
        except Exception as e:
            logger.error(f"Gemini Vision failed: {e}")

    logger.info(f"Claude identified {len(claude_results)} card(s)")
    logger.info(f"OpenAI identified {len(openai_results)} card(s)")
    logger.info(f"Gemini identified {len(gemini_results)} card(s)")

    # Combine and validate results using majority voting
    validated_cards = []

    # Try to match cards from all three providers
    max_cards = max(len(claude_results), len(openai_results), len(gemini_results))

    for i in range(max_cards):
        claude_card = claude_results[i] if i < len(claude_results) else None
        openai_card = openai_results[i] if i < len(openai_results) else None
        gemini_card = gemini_results[i] if i < len(gemini_results) else None

        # Collect all provider results for this card position
        provider_cards = []
        if claude_card:
            provider_cards.append(('Claude', claude_card))
        if openai_card:
            provider_cards.append(('OpenAI', openai_card))
        if gemini_card:
            provider_cards.append(('Gemini', gemini_card))

        if not provider_cards:
            continue

        # Count votes for each card name (case-insensitive)
        name_votes = {}
        for provider_name, card in provider_cards:
            card_name = card.get('name', '').lower().strip()
            if card_name:
                if card_name not in name_votes:
                    name_votes[card_name] = {'count': 0, 'providers': [], 'cards': []}
                name_votes[card_name]['count'] += 1
                name_votes[card_name]['providers'].append(provider_name)
                name_votes[card_name]['cards'].append(card)

        # Find the name with most votes
        if name_votes:
            winning_name = max(name_votes.items(), key=lambda x: x[1]['count'])[0]
            vote_count = name_votes[winning_name]['count']
            winning_providers = name_votes[winning_name]['providers']
            winning_cards = name_votes[winning_name]['cards']

            logger.info(f"✓ {vote_count}/{len(provider_cards)} providers agree on: '{winning_cards[0].get('name')}' ({', '.join(winning_providers)})")

            # Collect all unique set/number combinations
            set_alternatives = []
            primary_set = None
            primary_number = None

            for card in winning_cards:
                card_set = card.get('set')
                card_number = card.get('collector_number')

                if card_set and card_number:
                    if not primary_set:
                        primary_set = card_set
                        primary_number = card_number
                    elif (card_set, card_number) != (primary_set, primary_number):
                        # Different set/number - add as alternative
                        if {'set': card_set, 'collector_number': card_number} not in set_alternatives:
                            set_alternatives.append({
                                'set': card_set,
                                'collector_number': card_number
                            })

            # Determine confidence based on agreement
            if vote_count == len(provider_cards):
                confidence = 'high'  # All providers agree
                validation = 'unanimous'
            elif vote_count >= 2:
                confidence = 'high'  # Majority agrees
                validation = 'majority'
            else:
                confidence = 'medium'  # Only one provider
                validation = 'single_provider'

            validated_cards.append({
                'name': winning_cards[0].get('name'),  # Use original capitalization from first match
                'set': primary_set,
                'collector_number': primary_number,
                'set_alternatives': set_alternatives,
                'confidence': confidence,
                'validation': validation,
                'provider_votes': f"{vote_count}/{len(provider_cards)}"
            })

    logger.info(f"Pro Scan validated {len(validated_cards)} card(s)")
    return validated_cards
