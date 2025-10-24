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

from card_detection import detect_cards_from_image
from card_matching import match_cards, load_card_database
from scryfall_integration import get_card_details, get_card_prices

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

# Global card database
CARD_DATABASE = None


@app.on_event("startup")
async def startup_event():
    """Load card database on startup"""
    global CARD_DATABASE
    logger.info("Loading card database...")
    try:
        CARD_DATABASE = load_card_database()
        logger.info(f"Loaded {len(CARD_DATABASE)} cards into database")
    except Exception as e:
        logger.error(f"Failed to load card database: {e}")
        logger.info("API will continue but card matching may fail")


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
        "database_loaded": CARD_DATABASE is not None,
        "cards_in_database": len(CARD_DATABASE) if CARD_DATABASE else 0,
        "timestamp": datetime.now().isoformat()
    }


@app.post("/scan")
async def scan_cards(file: UploadFile = File(...)) -> Dict[str, Any]:
    """
    Scan an image containing multiple Magic cards
    
    Args:
        file: Image file containing Magic cards
        
    Returns:
        JSON with detected cards and their details
    """
    try:
        # Validate file type
        if not file.content_type.startswith('image/'):
            raise HTTPException(
                status_code=400,
                detail="File must be an image"
            )
        
        logger.info(f"Processing image: {file.filename}")
        
        # Read image data
        image_data = await file.read()
        
        # Step 1: Detect individual cards in the image
        logger.info("Detecting cards in image...")
        detected_cards = detect_cards_from_image(image_data)
        
        if not detected_cards:
            return {
                "success": True,
                "cards_found": 0,
                "cards": [],
                "message": "No cards detected in image"
            }
        
        logger.info(f"Detected {len(detected_cards)} cards")
        
        # Step 2: Match each detected card against database
        if CARD_DATABASE is None:
            raise HTTPException(
                status_code=503,
                detail="Card database not loaded"
            )
        
        logger.info("Matching cards against database...")
        matched_cards = match_cards(detected_cards, CARD_DATABASE)
        
        # Step 3: Get detailed information for matched cards
        logger.info("Fetching card details from Scryfall...")
        results = []
        
        for i, match in enumerate(matched_cards):
            if match['matched']:
                try:
                    # Get full card details from Scryfall
                    card_details = await get_card_details(match['scryfall_id'])
                    
                    # Get current prices
                    prices = await get_card_prices(match['scryfall_id'])
                    
                    results.append({
                        "card_number": i + 1,
                        "matched": True,
                        "confidence": match['confidence'],
                        "name": card_details['name'],
                        "set": card_details['set_name'],
                        "set_code": card_details['set'],
                        "collector_number": card_details.get('collector_number'),
                        "rarity": card_details.get('rarity'),
                        "image_url": card_details.get('image_uris', {}).get('normal'),
                        "scryfall_id": match['scryfall_id'],
                        "prices": prices,
                        "scryfall_uri": card_details.get('scryfall_uri')
                    })
                except Exception as e:
                    logger.error(f"Error fetching details for card {i+1}: {e}")
                    results.append({
                        "card_number": i + 1,
                        "matched": True,
                        "confidence": match['confidence'],
                        "scryfall_id": match['scryfall_id'],
                        "error": "Failed to fetch card details"
                    })
            else:
                results.append({
                    "card_number": i + 1,
                    "matched": False,
                    "message": "Could not identify this card"
                })
        
        return {
            "success": True,
            "cards_found": len(detected_cards),
            "cards_matched": sum(1 for r in results if r.get('matched')),
            "cards": results,
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


@app.get("/database/stats")
async def database_stats():
    """Get statistics about the card database"""
    if CARD_DATABASE is None:
        raise HTTPException(
            status_code=503,
            detail="Card database not loaded"
        )
    
    return {
        "total_cards": len(CARD_DATABASE),
        "status": "loaded",
        "timestamp": datetime.now().isoformat()
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
