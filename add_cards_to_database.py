"""
Add Specific Cards to Database
Utility script to add individual cards to the hash database
"""

import asyncio
import httpx
from pathlib import Path
import logging
from PIL import Image
from io import BytesIO
import imagehash
import re

from card_matching import load_card_database, save_card_database

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def extract_card_info_from_url(url: str) -> dict:
    """
    Extract set code and collector number from Scryfall URL

    Args:
        url: Scryfall card URL (e.g., https://scryfall.com/card/neo/123/card-name)

    Returns:
        Dict with set and collector_number
    """
    # Pattern: https://scryfall.com/card/{set}/{collector_number}/{name}
    pattern = r'scryfall\.com/card/([^/]+)/([^/]+)'
    match = re.search(pattern, url)

    if not match:
        raise ValueError(f"Invalid Scryfall URL format: {url}")

    return {
        'set': match.group(1),
        'collector_number': match.group(2)
    }


async def fetch_card_from_scryfall(set_code: str, collector_number: str) -> dict:
    """
    Fetch card data from Scryfall API

    Args:
        set_code: Set code (e.g., 'neo')
        collector_number: Collector number

    Returns:
        Card data from Scryfall
    """
    url = f"https://api.scryfall.com/cards/{set_code}/{collector_number}"

    async with httpx.AsyncClient() as client:
        response = await client.get(url, timeout=10.0)
        response.raise_for_status()
        return response.json()


async def download_card_image(url: str) -> Image.Image:
    """
    Download card image from URL

    Args:
        url: Image URL

    Returns:
        PIL Image
    """
    async with httpx.AsyncClient() as client:
        response = await client.get(url, timeout=30.0)
        response.raise_for_status()

        img = Image.open(BytesIO(response.content))
        return img


async def add_card_by_url(url: str, hash_size: int = 16) -> dict:
    """
    Add a card to the database using its Scryfall URL

    Args:
        url: Scryfall card URL
        hash_size: Hash size for perceptual hash

    Returns:
        Card info that was added
    """
    logger.info(f"Processing URL: {url}")

    # Extract card info from URL
    url_info = extract_card_info_from_url(url)
    logger.info(f"Extracted: set={url_info['set']}, number={url_info['collector_number']}")

    # Fetch card data from Scryfall
    logger.info("Fetching card data from Scryfall...")
    card_data = await fetch_card_from_scryfall(
        url_info['set'],
        url_info['collector_number']
    )

    scryfall_id = card_data['id']
    card_name = card_data['name']

    logger.info(f"Found card: {card_name} (ID: {scryfall_id})")

    # Get image URL
    if 'image_uris' in card_data:
        # Single-faced card
        image_url = card_data['image_uris']['normal']
    elif 'card_faces' in card_data and len(card_data['card_faces']) > 0:
        # Multi-faced card - use front face
        if 'image_uris' in card_data['card_faces'][0]:
            image_url = card_data['card_faces'][0]['image_uris']['normal']
        else:
            raise ValueError(f"No image found for {card_name}")
    else:
        raise ValueError(f"No image URL found for {card_name}")

    # Download image
    logger.info("Downloading card image...")
    img = await download_card_image(image_url)

    # Create perceptual hash
    logger.info("Creating perceptual hash...")
    card_hash = imagehash.phash(img, hash_size=hash_size)

    # Prepare card info
    card_info = {
        'hash': card_hash,
        'name': card_name,
        'set': card_data.get('set'),
        'set_name': card_data.get('set_name'),
        'collector_number': card_data.get('collector_number'),
        'rarity': card_data.get('rarity')
    }

    logger.info(f"Successfully processed: {card_name}")

    return {
        'scryfall_id': scryfall_id,
        'card_info': card_info
    }


async def add_cards_to_database(urls: list, hash_size: int = 16):
    """
    Add multiple cards to the database

    Args:
        urls: List of Scryfall card URLs
        hash_size: Hash size for perceptual hash
    """
    logger.info(f"Adding {len(urls)} cards to database...")

    # Load existing database
    database = load_card_database()
    initial_count = len(database)
    logger.info(f"Current database has {initial_count} cards")

    # Add each card
    added = 0
    skipped = 0
    failed = 0

    for url in urls:
        try:
            result = await add_card_by_url(url, hash_size)
            scryfall_id = result['scryfall_id']
            card_info = result['card_info']

            # Check if card already exists
            if scryfall_id in database:
                logger.warning(f"Card {card_info['name']} already in database, skipping")
                skipped += 1
            else:
                # Add to database
                database[scryfall_id] = card_info
                added += 1
                logger.info(f"Added {card_info['name']} to database")

            # Small delay to be nice to Scryfall
            await asyncio.sleep(0.1)

        except Exception as e:
            logger.error(f"Failed to add card from {url}: {e}")
            failed += 1
            continue

    # Save updated database
    if added > 0:
        logger.info("Saving updated database...")
        save_card_database(database)
        logger.info(f"Database saved with {len(database)} cards")

    # Summary
    logger.info("=" * 60)
    logger.info("Summary:")
    logger.info(f"  Cards added: {added}")
    logger.info(f"  Cards skipped (already in DB): {skipped}")
    logger.info(f"  Cards failed: {failed}")
    logger.info(f"  Total cards in database: {len(database)} (was {initial_count})")
    logger.info("=" * 60)


async def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="Add specific cards to the hash database")
    parser.add_argument(
        'urls',
        nargs='*',
        help='Scryfall card URLs to add'
    )
    parser.add_argument(
        '--file',
        type=str,
        help='File containing URLs (one per line)'
    )
    parser.add_argument(
        '--hash-size',
        type=int,
        default=16,
        help='Perceptual hash size (default: 16)'
    )

    args = parser.parse_args()

    # Collect URLs from arguments or file
    urls = []

    if args.urls:
        urls.extend(args.urls)

    if args.file:
        with open(args.file, 'r') as f:
            file_urls = [line.strip() for line in f if line.strip() and not line.startswith('#')]
            urls.extend(file_urls)

    if not urls:
        logger.error("No URLs provided. Use positional arguments or --file")
        return

    # Add cards
    await add_cards_to_database(urls, hash_size=args.hash_size)


if __name__ == "__main__":
    asyncio.run(main())
