"""
Card Matching Module
Uses perceptual hashing to match detected cards against Scryfall database
"""

import imagehash
from PIL import Image
import numpy as np
import cv2
from typing import List, Dict, Any, Optional
import logging
import pickle
import os
from pathlib import Path

logger = logging.getLogger(__name__)

# Cache file for card hashes
CACHE_DIR = Path(__file__).parent / "cache"
HASH_CACHE_FILE = CACHE_DIR / "card_hashes.pkl"


def load_card_database() -> Dict[str, Dict[str, Any]]:
    """
    Load or build the card hash database
    
    Returns:
        Dictionary mapping scryfall_id to card info including hash
    """
    # Check if cache exists
    if HASH_CACHE_FILE.exists():
        logger.info(f"Loading card database from cache: {HASH_CACHE_FILE}")
        try:
            with open(HASH_CACHE_FILE, 'rb') as f:
                database = pickle.load(f)
            logger.info(f"Loaded {len(database)} cards from cache")
            return database
        except Exception as e:
            logger.error(f"Failed to load cache: {e}")
            logger.info("Will build new database")
    
    # Build new database
    logger.warning("No card hash database found!")
    logger.info("You need to run build_card_database.py to create the hash database")
    logger.info("For now, returning empty database")
    
    # Return empty database (API will still work, but won't match cards)
    return {}


def build_hash_for_card(card_image: np.ndarray, hash_size: int = 16) -> imagehash.ImageHash:
    """
    Create perceptual hash for a card image
    
    Args:
        card_image: Card image as numpy array
        hash_size: Size of the hash (default 16 for good balance)
        
    Returns:
        ImageHash object
    """
    # Convert BGR to RGB
    if len(card_image.shape) == 3:
        card_image_rgb = cv2.cvtColor(card_image, cv2.COLOR_BGR2RGB)
    else:
        card_image_rgb = card_image
    
    # Convert to PIL Image
    pil_image = Image.fromarray(card_image_rgb)
    
    # Create perceptual hash
    # We use phash (perceptual hash) as it's robust to minor changes
    card_hash = imagehash.phash(pil_image, hash_size=hash_size)
    
    return card_hash


def match_cards(
    detected_cards: List[np.ndarray],
    database: Dict[str, Dict[str, Any]],
    threshold: int = 10
) -> List[Dict[str, Any]]:
    """
    Match detected cards against the database
    
    Args:
        detected_cards: List of card images
        database: Card hash database
        threshold: Maximum hash distance for a match (lower = stricter)
        
    Returns:
        List of match results
    """
    results = []
    
    for i, card_image in enumerate(detected_cards):
        logger.info(f"Matching card {i+1}/{len(detected_cards)}")
        
        try:
            # Create hash for detected card
            card_hash = build_hash_for_card(card_image)
            
            # Find best match in database
            match = find_best_match(card_hash, database, threshold)
            
            if match:
                results.append({
                    'matched': True,
                    'scryfall_id': match['scryfall_id'],
                    'confidence': match['confidence'],
                    'distance': match['distance']
                })
                logger.info(f"Card {i+1} matched with distance {match['distance']}")
            else:
                results.append({
                    'matched': False,
                    'reason': 'No close match found'
                })
                logger.warning(f"Card {i+1} could not be matched")
                
        except Exception as e:
            logger.error(f"Error matching card {i+1}: {e}")
            results.append({
                'matched': False,
                'reason': f'Error: {str(e)}'
            })
    
    return results


def find_best_match(
    card_hash: imagehash.ImageHash,
    database: Dict[str, Dict[str, Any]],
    threshold: int = 10
) -> Optional[Dict[str, Any]]:
    """
    Find the best matching card in the database
    
    Args:
        card_hash: Hash of the card to match
        database: Card database
        threshold: Maximum acceptable distance
        
    Returns:
        Match information or None
    """
    if not database:
        logger.warning("Database is empty, cannot match cards")
        return None
    
    best_match = None
    best_distance = float('inf')
    
    # Compare against all cards in database
    for scryfall_id, card_info in database.items():
        db_hash = card_info['hash']
        
        # Calculate Hamming distance
        distance = card_hash - db_hash
        
        if distance < best_distance:
            best_distance = distance
            best_match = {
                'scryfall_id': scryfall_id,
                'distance': distance,
                'card_info': card_info
            }
    
    # Check if match is good enough
    if best_match and best_distance <= threshold:
        # Calculate confidence score (0-100)
        # Lower distance = higher confidence
        confidence = max(0, 100 - (best_distance * 10))
        
        return {
            'scryfall_id': best_match['scryfall_id'],
            'distance': best_distance,
            'confidence': confidence
        }
    
    return None


def save_card_database(database: Dict[str, Dict[str, Any]]) -> None:
    """
    Save card database to cache file
    
    Args:
        database: Card database to save
    """
    try:
        # Create cache directory if it doesn't exist
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        
        # Save database
        with open(HASH_CACHE_FILE, 'wb') as f:
            pickle.dump(database, f)
        
        logger.info(f"Saved {len(database)} cards to cache: {HASH_CACHE_FILE}")
        
    except Exception as e:
        logger.error(f"Failed to save database: {e}")


def calculate_hash_statistics(database: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calculate statistics about the hash database
    Useful for tuning matching parameters
    
    Args:
        database: Card database
        
    Returns:
        Statistics dictionary
    """
    if not database:
        return {"error": "Database is empty"}
    
    # Sample some cards and calculate distances
    sample_size = min(100, len(database))
    sample_ids = list(database.keys())[:sample_size]
    
    distances = []
    for i, id1 in enumerate(sample_ids):
        for id2 in sample_ids[i+1:]:
            hash1 = database[id1]['hash']
            hash2 = database[id2]['hash']
            distance = hash1 - hash2
            distances.append(distance)
    
    return {
        "total_cards": len(database),
        "sample_size": sample_size,
        "min_distance": min(distances) if distances else 0,
        "max_distance": max(distances) if distances else 0,
        "avg_distance": sum(distances) / len(distances) if distances else 0,
        "recommended_threshold": 10  # Based on testing
    }
