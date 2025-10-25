"""
MagicScanner Backend API
FastAPI server for Magic card detection and recognition
"""

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import List, Dict, Any
import logging
from datetime import datetime

from claude_vision import identify_cards_with_vision
from multi_vision import identify_cards_pro
from scryfall_integration import get_card_details, get_card_prices, search_card_by_name, get_card_details_by_set

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="MagicScanner API",
    description="API for detecting and recognizing Magic: The Gathering cards",
    version="1.0.0"
)

# CORS middleware - allow requests from mobile app
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your app's domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    """Startup event"""
    logger.info("MagicScanner API starting up...")
    logger.info("Using Claude Vision for card identification")


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "online",
        "service": "MagicScanner API",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    }


@app.get("/health")
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "vision_enabled": True,
        "timestamp": datetime.now().isoformat()
    }


@app.post("/scan")
async def scan_cards(
    file: UploadFile = File(...),
    scan_mode: str = "default"
) -> Dict[str, Any]:
    """
    Scan an image containing Magic cards using AI Vision

    Args:
        file: Image file containing Magic cards
        scan_mode: "default" (Claude only) or "pro" (Claude + OpenAI parallel validation)

    Returns:
        JSON with identified cards and their details
    """
    try:
        # Validate file type
        if not file.content_type.startswith('image/'):
            raise HTTPException(
                status_code=400,
                detail="File must be an image"
            )

        # Validate scan_mode
        if scan_mode not in ["default", "pro"]:
            raise HTTPException(
                status_code=400,
                detail="scan_mode must be 'default' or 'pro'"
            )

        logger.info(f"Processing image: {file.filename} (mode: {scan_mode})")

        # Read image data
        image_data = await file.read()

        # Step 1: Identify cards using selected mode
        if scan_mode == "pro":
            logger.info("Using Pro Scan (Claude + OpenAI parallel validation)...")
            identified_cards = identify_cards_pro(image_data)
        else:
            logger.info("Using Default Scan (Claude Vision only)...")
            identified_cards = identify_cards_with_vision(image_data)

        if not identified_cards:
            return {
                "success": True,
                "cards_found": 0,
                "cards": [],
                "message": "No cards identified in image"
            }

        logger.info(f"Vision API identified {len(identified_cards)} card(s)")

        # Step 2: Get detailed information for each identified card
        logger.info("Fetching card details from Scryfall...")
        results = []

        for i, card_info in enumerate(identified_cards):
            try:
                card_name = card_info.get('name')
                set_code = card_info.get('set')
                collector_number = card_info.get('collector_number')
                confidence = card_info.get('confidence', 'medium')

                # Clean up collector number
                if collector_number:
                    # Remove format like "048/168" -> just keep "48"
                    if '/' in collector_number:
                        collector_number = collector_number.split('/')[0]
                    # Remove leading zeros (Scryfall uses "483" not "0483")
                    if collector_number.isdigit():
                        collector_number = str(int(collector_number))

                logger.info(f"Looking up card: {card_name} (set: {set_code}, number: {collector_number})")

                # Search for card on Scryfall
                card_details = None

                # If we have set and collector number, try specific lookup first
                if set_code and collector_number:
                    card_details = await get_card_details_by_set(set_code, collector_number)

                    # Validate that the found card matches the identified name
                    if card_details:
                        found_name = card_details.get('name', '')
                        if found_name.lower() != card_name.lower():
                            logger.info(f"Set/number lookup found '{found_name}' but Claude identified '{card_name}' - name mismatch, falling back to name search")
                            card_details = None
                    else:
                        logger.info(f"Set/number lookup failed, falling back to name search")

                # Fallback to name search if specific lookup failed or wasn't possible
                if not card_details:
                    card_details = await search_card_by_name(card_name, None)  # Don't use set_code since it might be wrong

                if card_details:
                    # Get current prices
                    prices = await get_card_prices(card_details['id'])

                    results.append({
                        "card_number": i + 1,
                        "matched": True,
                        "confidence": confidence,
                        "name": card_details['name'],
                        "set": card_details['set_name'],
                        "set_code": card_details['set'],
                        "collector_number": card_details.get('collector_number'),
                        "rarity": card_details.get('rarity'),
                        "image_url": card_details.get('image_uris', {}).get('normal'),
                        "scryfall_id": card_details['id'],
                        "prices": prices,
                        "scryfall_uri": card_details.get('scryfall_uri')
                    })
                else:
                    results.append({
                        "card_number": i + 1,
                        "matched": False,
                        "identified_name": card_name,
                        "message": "Card identified but not found in Scryfall"
                    })

            except Exception as e:
                logger.error(f"Error processing card {i+1} ({card_name}): {e}")
                results.append({
                    "card_number": i + 1,
                    "matched": False,
                    "identified_name": card_name,
                    "error": str(e)
                })

        return {
            "success": True,
            "cards_found": len(identified_cards),
            "cards_matched": sum(1 for r in results if r.get('matched')),
            "cards": results,
            "scan_mode": scan_mode,
            "method": "pro_scan" if scan_mode == "pro" else "claude_vision",
            "timestamp": datetime.now().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing image: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error processing image: {str(e)}"
        )


@app.post("/identify-single")
async def identify_single_card(file: UploadFile = File(...)) -> Dict[str, Any]:
    """
    Identify a single card from an image
    Useful for testing or single card lookups
    """
    try:
        if not file.content_type.startswith('image/'):
            raise HTTPException(
                status_code=400,
                detail="File must be an image"
            )
        
        image_data = await file.read()
        
        # Detect cards (should be just one)
        detected_cards = detect_cards_from_image(image_data)
        
        if not detected_cards:
            return {
                "success": False,
                "message": "No card detected in image"
            }
        
        if len(detected_cards) > 1:
            logger.warning(f"Multiple cards detected ({len(detected_cards)}), using first one")
        
        # Match the first (or only) card
        matched_cards = match_cards([detected_cards[0]], CARD_DATABASE)
        match = matched_cards[0]
        
        if not match['matched']:
            return {
                "success": False,
                "message": "Could not identify card"
            }
        
        # Get full details
        card_details = await get_card_details(match['scryfall_id'])
        prices = await get_card_prices(match['scryfall_id'])
        
        return {
            "success": True,
            "confidence": match['confidence'],
            "card": {
                "name": card_details['name'],
                "set": card_details['set_name'],
                "set_code": card_details['set'],
                "collector_number": card_details.get('collector_number'),
                "rarity": card_details.get('rarity'),
                "image_url": card_details.get('image_uris', {}).get('normal'),
                "scryfall_id": match['scryfall_id'],
                "prices": prices,
                "scryfall_uri": card_details.get('scryfall_uri')
            }
        }
        
    except Exception as e:
        logger.error(f"Error identifying card: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error identifying card: {str(e)}"
        )




if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
