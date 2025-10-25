"""
Scryfall API Integration
Handles all communication with Scryfall API
"""

import httpx
from typing import Dict, Any, Optional
import logging
import asyncio

logger = logging.getLogger(__name__)

# Scryfall API base URL
SCRYFALL_API_BASE = "https://api.scryfall.com"

# Rate limiting (Scryfall allows 10 requests per second)
REQUEST_DELAY = 0.1  # 100ms between requests


class ScryfallClient:
    """Async client for Scryfall API with rate limiting"""
    
    def __init__(self):
        self.last_request_time = 0
    
    async def _rate_limit(self):
        """Ensure we don't exceed Scryfall's rate limits"""
        current_time = asyncio.get_event_loop().time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < REQUEST_DELAY:
            await asyncio.sleep(REQUEST_DELAY - time_since_last)
        
        self.last_request_time = asyncio.get_event_loop().time()
    
    async def get(self, endpoint: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Make GET request to Scryfall API
        
        Args:
            endpoint: API endpoint (without base URL)
            params: Query parameters
            
        Returns:
            JSON response
        """
        await self._rate_limit()
        
        url = f"{SCRYFALL_API_BASE}{endpoint}"
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                url,
                params=params,
                headers={
                    "User-Agent": "MagicScanner/1.0",
                    "Accept": "application/json"
                },
                timeout=30.0
            )
            response.raise_for_status()
            return response.json()


# Global client instance
_client = ScryfallClient()


async def get_card_details(scryfall_id: str) -> Dict[str, Any]:
    """
    Get full card details from Scryfall by ID
    
    Args:
        scryfall_id: Scryfall UUID for the card
        
    Returns:
        Card object from Scryfall
    """
    try:
        endpoint = f"/cards/{scryfall_id}"
        card_data = await _client.get(endpoint)
        
        return card_data
        
    except httpx.HTTPError as e:
        logger.error(f"Error fetching card details for {scryfall_id}: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error fetching card: {e}")
        raise


async def get_card_prices(scryfall_id: str) -> Dict[str, Optional[str]]:
    """
    Get current prices for a card
    
    Args:
        scryfall_id: Scryfall UUID for the card
        
    Returns:
        Dictionary of prices (usd, usd_foil, eur, tix)
    """
    try:
        card_data = await get_card_details(scryfall_id)
        
        prices = card_data.get('prices', {})
        
        return {
            'usd': prices.get('usd'),
            'usd_foil': prices.get('usd_foil'),
            'eur': prices.get('eur'),
            'tix': prices.get('tix')
        }
        
    except Exception as e:
        logger.error(f"Error fetching prices for {scryfall_id}: {e}")
        return {
            'usd': None,
            'usd_foil': None,
            'eur': None,
            'tix': None
        }


async def get_card_details_by_set(set_code: str, collector_number: str) -> Optional[Dict[str, Any]]:
    """
    Get card details by set code and collector number

    Args:
        set_code: Set code (e.g., "NEO")
        collector_number: Collector number

    Returns:
        Card object or None
    """
    try:
        endpoint = f"/cards/{set_code}/{collector_number}"
        card_data = await _client.get(endpoint)

        return card_data

    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            logger.info(f"Card not found: {set_code}/{collector_number}")
            return None
        logger.error(f"Error fetching card {set_code}/{collector_number}: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error fetching card: {e}")
        raise


async def search_card_by_name(card_name: str, set_code: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Search for a card by name
    
    Args:
        card_name: Name of the card
        set_code: Optional set code to narrow search
        
    Returns:
        Card object or None
    """
    try:
        # Build search query
        query = f'!"{card_name}"'  # Exact name match
        
        if set_code:
            query += f' set:{set_code}'
        
        endpoint = "/cards/search"
        params = {
            'q': query,
            'unique': 'prints'
        }
        
        result = await _client.get(endpoint, params)
        
        if result.get('total_cards', 0) > 0:
            # Return first result
            return result['data'][0]
        
        return None
        
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            logger.info(f"Card not found: {card_name}")
            return None
        logger.error(f"Error searching for card {card_name}: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error searching for card: {e}")
        raise


async def get_bulk_data_info() -> Dict[str, Any]:
    """
    Get information about available bulk data downloads
    
    Returns:
        Bulk data information
    """
    try:
        endpoint = "/bulk-data"
        bulk_data = await _client.get(endpoint)
        
        return bulk_data
        
    except Exception as e:
        logger.error(f"Error fetching bulk data info: {e}")
        raise


async def get_default_cards_bulk_url() -> str:
    """
    Get the download URL for the default cards bulk data file
    
    Returns:
        Download URL
    """
    try:
        bulk_info = await get_bulk_data_info()
        
        # Find "Default Cards" bulk data
        for item in bulk_info.get('data', []):
            if item.get('type') == 'default_cards':
                return item.get('download_uri')
        
        raise ValueError("Default cards bulk data not found")
        
    except Exception as e:
        logger.error(f"Error getting bulk data URL: {e}")
        raise


async def download_all_cards() -> list:
    """
    Download all cards from Scryfall bulk data
    
    Returns:
        List of all card objects
    """
    try:
        # Get bulk data URL
        download_url = await get_default_cards_bulk_url()
        
        logger.info(f"Downloading all cards from: {download_url}")
        
        # Download the JSON file (can be large, ~100MB)
        async with httpx.AsyncClient() as client:
            response = await client.get(
                download_url,
                timeout=300.0  # 5 minute timeout for large download
            )
            response.raise_for_status()
            
            cards = response.json()
            
            logger.info(f"Downloaded {len(cards)} cards")
            
            return cards
        
    except Exception as e:
        logger.error(f"Error downloading bulk data: {e}")
        raise


async def get_set_info(set_code: str) -> Dict[str, Any]:
    """
    Get information about a Magic set
    
    Args:
        set_code: Three-letter set code
        
    Returns:
        Set information
    """
    try:
        endpoint = f"/sets/{set_code}"
        set_data = await _client.get(endpoint)
        
        return set_data
        
    except Exception as e:
        logger.error(f"Error fetching set info for {set_code}: {e}")
        raise


# Synchronous wrapper for FastAPI compatibility
def get_card_details_sync(scryfall_id: str) -> Dict[str, Any]:
    """Synchronous wrapper for get_card_details"""
    return asyncio.run(get_card_details(scryfall_id))


def get_card_prices_sync(scryfall_id: str) -> Dict[str, Optional[str]]:
    """Synchronous wrapper for get_card_prices"""
    return asyncio.run(get_card_prices(scryfall_id))
