"""
Build Card Hash Database
Downloads all Magic cards from Scryfall and creates perceptual hashes

This script should be run ONCE to build the initial database,
and periodically to update with new card releases.

WARNING: This takes a long time (several hours) and downloads ~100MB of data
plus all card images. Make sure you have good internet and disk space.
"""

import asyncio
import httpx
from pathlib import Path
import logging
from tqdm import tqdm
import imagehash
from PIL import Image
from io import BytesIO
import sys

from card_matching import save_card_database
from scryfall_integration import download_all_cards

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def download_card_image(url: str, session: httpx.AsyncClient) -> Image.Image:
    """
    Download a card image from URL
    
    Args:
        url: Image URL
        session: HTTP session
        
    Returns:
        PIL Image
    """
    try:
        response = await session.get(url, timeout=30.0)
        response.raise_for_status()
        
        img = Image.open(BytesIO(response.content))
        return img
        
    except Exception as e:
        logger.error(f"Error downloading image from {url}: {e}")
        raise


async def build_database(
    limit: int = None,
    hash_size: int = 16,
    skip_tokens: bool = True
):
    """
    Build the complete card hash database
    
    Args:
        limit: Optional limit on number of cards (for testing)
        hash_size: Size of perceptual hash
        skip_tokens: Whether to skip token cards
    """
    logger.info("Starting card database build...")
    
    # Step 1: Download all card data from Scryfall
    logger.info("Downloading card data from Scryfall...")
    all_cards = await download_all_cards()
    
    logger.info(f"Downloaded {len(all_cards)} cards")
    
    # Step 2: Filter cards
    cards_to_process = []
    
    for card in all_cards:
        # Skip tokens if requested
        if skip_tokens and card.get('layout') == 'token':
            continue
        
        # Skip cards without images
        if 'image_uris' not in card and 'card_faces' not in card:
            continue
        
        cards_to_process.append(card)
    
    logger.info(f"Will process {len(cards_to_process)} cards")
    
    if limit:
        cards_to_process = cards_to_process[:limit]
        logger.info(f"Limited to {limit} cards for testing")
    
    # Step 3: Download images and create hashes
    database = {}
    failed_cards = []
    
    async with httpx.AsyncClient() as session:
        for i, card in enumerate(tqdm(cards_to_process, desc="Processing cards")):
            try:
                scryfall_id = card['id']
                card_name = card['name']
                
                # Get image URL
                if 'image_uris' in card:
                    # Single-faced card
                    image_url = card['image_uris']['normal']
                elif 'card_faces' in card and len(card['card_faces']) > 0:
                    # Multi-faced card - use front face
                    if 'image_uris' in card['card_faces'][0]:
                        image_url = card['card_faces'][0]['image_uris']['normal']
                    else:
                        logger.warning(f"No image for {card_name}")
                        continue
                else:
                    logger.warning(f"No image URL for {card_name}")
                    continue
                
                # Download image
                img = await download_card_image(image_url, session)
                
                # Create perceptual hash
                card_hash = imagehash.phash(img, hash_size=hash_size)
                
                # Store in database
                database[scryfall_id] = {
                    'hash': card_hash,
                    'name': card_name,
                    'set': card.get('set'),
                    'set_name': card.get('set_name'),
                    'collector_number': card.get('collector_number'),
                    'rarity': card.get('rarity')
                }
                
                # Periodic save (every 1000 cards)
                if (i + 1) % 1000 == 0:
                    save_card_database(database)
                    logger.info(f"Saved checkpoint at {i+1} cards")
                
                # Rate limiting
                await asyncio.sleep(0.1)
                
            except Exception as e:
                logger.error(f"Error processing card {card.get('name', 'unknown')}: {e}")
                failed_cards.append(card['id'])
                continue
    
    # Final save
    save_card_database(database)
    
    logger.info(f"Database build complete!")
    logger.info(f"Successfully processed: {len(database)} cards")
    logger.info(f"Failed cards: {len(failed_cards)}")
    
    if failed_cards:
        logger.info("Failed card IDs (first 10):")
        for card_id in failed_cards[:10]:
            logger.info(f"  {card_id}")


async def build_test_database(num_cards: int = 100):
    """
    Build a small test database for development
    
    Args:
        num_cards: Number of cards to include
    """
    logger.info(f"Building test database with {num_cards} cards...")
    await build_database(limit=num_cards)


async def update_database():
    """
    Update existing database with new cards
    This is faster than rebuilding from scratch
    """
    logger.info("Database update not yet implemented")
    logger.info("Please rebuild the full database")


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Build MagicScanner card hash database")
    parser.add_argument(
        '--test',
        action='store_true',
        help='Build small test database (100 cards)'
    )
    parser.add_argument(
        '--limit',
        type=int,
        help='Limit number of cards to process'
    )
    parser.add_argument(
        '--hash-size',
        type=int,
        default=16,
        help='Perceptual hash size (default: 16)'
    )
    parser.add_argument(
        '--include-tokens',
        action='store_true',
        help='Include token cards'
    )
    
    args = parser.parse_args()
    
    if args.test:
        logger.info("Building TEST database...")
        asyncio.run(build_test_database())
    else:
        logger.info("Building FULL database...")
        logger.warning("This will take several hours and download many GB of data!")
        
        response = input("Continue? (yes/no): ")
        if response.lower() != 'yes':
            logger.info("Cancelled")
            sys.exit(0)
        
        asyncio.run(build_database(
            limit=args.limit,
            hash_size=args.hash_size,
            skip_tokens=not args.include_tokens
        ))


if __name__ == "__main__":
    main()
