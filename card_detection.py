"""
Card Detection Module
Uses OpenCV to detect and extract individual Magic cards from an image
"""

import cv2
import numpy as np
from typing import List, Tuple
import logging

logger = logging.getLogger(__name__)


def detect_cards_from_image(image_data: bytes) -> List[np.ndarray]:
    """
    Detect individual Magic cards from an image containing multiple cards
    
    Args:
        image_data: Raw image bytes
        
    Returns:
        List of numpy arrays, each containing a single card image
    """
    try:
        # Convert bytes to numpy array
        nparr = np.frombuffer(image_data, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if image is None:
            logger.error("Failed to decode image")
            return []
        
        logger.info(f"Image size: {image.shape}")
        
        # Preprocess image
        preprocessed = preprocess_image(image)
        
        # Find card contours
        contours = find_card_contours(preprocessed)
        
        logger.info(f"Found {len(contours)} potential cards")
        
        # Extract and warp each card
        cards = []
        for i, contour in enumerate(contours):
            try:
                card_image = extract_card(image, contour)
                if card_image is not None:
                    cards.append(card_image)
                    logger.info(f"Extracted card {i+1}")
            except Exception as e:
                logger.warning(f"Failed to extract card {i+1}: {e}")
                continue
        
        return cards
        
    except Exception as e:
        logger.error(f"Error in card detection: {e}", exc_info=True)
        return []


def preprocess_image(image: np.ndarray) -> np.ndarray:
    """
    Preprocess image for card detection
    Simple approach focusing on edge detection only

    Args:
        image: Input image

    Returns:
        Preprocessed binary image
    """
    # Convert to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Apply slight blur to reduce noise
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)

    # Use Canny edge detection with moderate settings
    # These values work well for card edges
    edges = cv2.Canny(blurred, 50, 150)

    # MINIMAL morphology - just enough to close small gaps
    # Too much morphology connects everything into one big blob
    kernel = np.ones((3, 3), np.uint8)

    # Dilate edges slightly to connect nearby edges
    dilated = cv2.dilate(edges, kernel, iterations=2)

    # Close small gaps
    closed = cv2.morphologyEx(dilated, cv2.MORPH_CLOSE, kernel, iterations=1)

    logger.info("Preprocessing complete - simple Canny edge detection")

    return closed


def find_card_contours(binary_image: np.ndarray) -> List[np.ndarray]:
    """
    Find contours that likely represent Magic cards

    Args:
        binary_image: Binary preprocessed image

    Returns:
        List of contours representing cards
    """
    # Find contours - use EXTERNAL to avoid nested contours
    # We want the outer border of the card, not inner details
    contours, hierarchy = cv2.findContours(
        binary_image,
        cv2.RETR_EXTERNAL,  # Only outer contours
        cv2.CHAIN_APPROX_SIMPLE
    )

    # Filter contours based on area and shape
    card_contours = []
    image_area = binary_image.shape[0] * binary_image.shape[1]

    logger.info(f"Total contours found: {len(contours)}, Image area: {image_area}")

    for i, contour in enumerate(contours):
        area = cv2.contourArea(contour)

        # Log ALL contours for debugging (limited to first 30)
        if i < 30:
            logger.info(f"Contour {i}: area={area}, area%={area/image_area*100:.2f}%")

        # Filter by area - very lenient to catch cards at various distances
        min_area = image_area * 0.01  # 1% minimum
        max_area = image_area * 0.75  # 75% max - reject "whole image" contours

        if area < min_area or area > max_area:
            if i < 30:
                logger.info(f"Contour {i}: Rejected by area filter (min={min_area:.0f}, max={max_area:.0f})")
            continue

        # Check if contour is approximately rectangular
        peri = cv2.arcLength(contour, True)
        # Tolerant approximation
        approx = cv2.approxPolyDP(contour, 0.04 * peri, True)

        if i < 30:
            logger.info(f"Contour {i}: {len(approx)} corners detected")

        # Magic cards should have 4 corners, but accept 3-8 for flexibility
        # Too many corners means it's not a simple rectangle
        if 3 <= len(approx) <= 8:
            # Check aspect ratio (Magic cards are roughly 2.5:3.5 = 0.71)
            rect = cv2.minAreaRect(contour)
            width, height = rect[1]

            if width == 0 or height == 0:
                continue

            aspect_ratio = min(width, height) / max(width, height)

            if i < 30:
                logger.info(f"Contour {i}: aspect_ratio={aspect_ratio:.2f}, w={width:.0f}, h={height:.0f}")

            # Magic card aspect ratio with tolerance
            # Standard: 63mm x 88mm = 0.716
            # Accept from 0.50 (angled) to 0.90 (nearly square from perspective)
            if 0.50 <= aspect_ratio <= 0.90:
                card_contours.append(contour)
                logger.info(f"Contour {i}: ACCEPTED! area={area:.0f} ({area/image_area*100:.1f}%), ratio={aspect_ratio:.2f}, w={width:.0f}, h={height:.0f}")
            elif i < 30:
                logger.info(f"Contour {i}: Rejected by aspect ratio ({aspect_ratio:.2f} not in range 0.50-0.90)")
        elif i < 30:
            logger.info(f"Contour {i}: Rejected - {len(approx)} corners (need 3-8)")

    # Sort by area (largest first)
    card_contours.sort(key=cv2.contourArea, reverse=True)

    # Limit to maximum 15 cards to avoid false positives
    max_cards = 15
    if len(card_contours) > max_cards:
        logger.info(f"Limiting from {len(card_contours)} to {max_cards} largest contours")
        card_contours = card_contours[:max_cards]

    return card_contours


def extract_card(image: np.ndarray, contour: np.ndarray) -> np.ndarray:
    """
    Extract and warp a card to a rectangular image
    
    Args:
        image: Original image
        contour: Contour of the card
        
    Returns:
        Warped card image
    """
    # Get minimum area rectangle
    rect = cv2.minAreaRect(contour)
    box = cv2.boxPoints(rect)
    box = np.int0(box)
    
    # Order points: top-left, top-right, bottom-right, bottom-left
    pts = order_points(box)
    
    # Calculate target dimensions (standard Magic card aspect ratio)
    # Magic cards: 2.5" x 3.5" = 488 x 680 pixels at 195 DPI
    target_width = 488
    target_height = 680
    
    # Destination points for perspective transform
    dst_pts = np.array([
        [0, 0],
        [target_width - 1, 0],
        [target_width - 1, target_height - 1],
        [0, target_height - 1]
    ], dtype=np.float32)
    
    # Calculate perspective transform matrix
    matrix = cv2.getPerspectiveTransform(pts, dst_pts)
    
    # Warp the card to rectangular shape
    warped = cv2.warpPerspective(image, matrix, (target_width, target_height))
    
    # Check if card is upside down (by checking if top border is darker than bottom)
    # This is a simple heuristic - Magic cards usually have darker artwork at top
    top_strip = warped[:50, :]
    bottom_strip = warped[-50:, :]
    
    top_brightness = np.mean(cv2.cvtColor(top_strip, cv2.COLOR_BGR2GRAY))
    bottom_brightness = np.mean(cv2.cvtColor(bottom_strip, cv2.COLOR_BGR2GRAY))
    
    # If bottom is significantly darker, card might be upside down
    if bottom_brightness < top_brightness - 20:
        warped = cv2.rotate(warped, cv2.ROTATE_180)
    
    return warped


def order_points(pts: np.ndarray) -> np.ndarray:
    """
    Order points in clockwise order: top-left, top-right, bottom-right, bottom-left
    
    Args:
        pts: Array of 4 points
        
    Returns:
        Ordered points
    """
    # Initialize ordered points
    rect = np.zeros((4, 2), dtype=np.float32)
    
    # Sum and difference of coordinates
    s = pts.sum(axis=1)
    diff = np.diff(pts, axis=1)
    
    # Top-left will have smallest sum
    rect[0] = pts[np.argmin(s)]
    
    # Bottom-right will have largest sum
    rect[2] = pts[np.argmax(s)]
    
    # Top-right will have smallest difference
    rect[1] = pts[np.argmin(diff)]
    
    # Bottom-left will have largest difference
    rect[3] = pts[np.argmax(diff)]
    
    return rect


def resize_card_for_matching(card_image: np.ndarray, size: int = 256) -> np.ndarray:
    """
    Resize card to standard size for perceptual hashing
    
    Args:
        card_image: Card image
        size: Target size (width and height will be proportional)
        
    Returns:
        Resized card image
    """
    height, width = card_image.shape[:2]
    aspect_ratio = width / height
    
    if aspect_ratio > 1:
        new_width = size
        new_height = int(size / aspect_ratio)
    else:
        new_height = size
        new_width = int(size * aspect_ratio)
    
    resized = cv2.resize(card_image, (new_width, new_height), interpolation=cv2.INTER_AREA)
    
    return resized
