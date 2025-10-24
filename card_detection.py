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
    Preprocess image for better card detection

    Args:
        image: Input image

    Returns:
        Preprocessed binary image
    """
    # Convert to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Increase contrast using CLAHE (Contrast Limited Adaptive Histogram Equalization)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    gray = clahe.apply(gray)

    # Apply Gaussian blur to reduce noise
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)

    # Try multiple threshold methods and combine them

    # Method 1: Adaptive threshold (INVERTED for dark cards on light background)
    thresh1 = cv2.adaptiveThreshold(
        blurred,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY_INV,  # Inverted so cards are white
        21,
        5
    )

    # Method 2: Canny edge detection for clear edges
    edges = cv2.Canny(blurred, 50, 150)

    # Method 3: Otsu's thresholding
    _, thresh2 = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

    # Combine methods - if any method finds an edge, use it
    combined = cv2.bitwise_or(cv2.bitwise_or(thresh1, edges), thresh2)

    # Apply morphological operations to fill gaps and remove noise
    kernel = np.ones((5, 5), np.uint8)
    combined = cv2.morphologyEx(combined, cv2.MORPH_CLOSE, kernel, iterations=3)
    combined = cv2.morphologyEx(combined, cv2.MORPH_OPEN, kernel, iterations=1)

    # Dilate slightly to ensure card edges are connected
    combined = cv2.dilate(combined, kernel, iterations=1)

    logger.info("Preprocessing complete - using combined threshold methods")

    return combined


def find_card_contours(binary_image: np.ndarray) -> List[np.ndarray]:
    """
    Find contours that likely represent Magic cards

    Args:
        binary_image: Binary preprocessed image

    Returns:
        List of contours representing cards
    """
    # Find contours - use TREE to get all hierarchy levels
    contours, hierarchy = cv2.findContours(
        binary_image,
        cv2.RETR_TREE,  # Get all contours including nested ones
        cv2.CHAIN_APPROX_SIMPLE
    )

    # Filter contours based on area and shape
    card_contours = []
    image_area = binary_image.shape[0] * binary_image.shape[1]

    logger.info(f"Total contours found: {len(contours)}, Image area: {image_area}")

    for i, contour in enumerate(contours):
        area = cv2.contourArea(contour)

        # Log first few contours for debugging
        if i < 10:
            logger.info(f"Contour {i}: area={area}, area%={area/image_area*100:.2f}%")

        # Filter by area - MEGET tolerant
        # Min: 0.1% af billedet, Max: 98% (næsten hele billedet er OK hvis det er et tæt crop)
        min_area = image_area * 0.001
        max_area = image_area * 0.98

        if area < min_area or area > max_area:
            if i < 10:
                logger.info(f"Contour {i}: Rejected by area filter (min={min_area}, max={max_area})")
            continue

        # Check if contour is approximately rectangular
        peri = cv2.arcLength(contour, True)
        # Meget tolerant approximation
        approx = cv2.approxPolyDP(contour, 0.05 * peri, True)

        if i < 10:
            logger.info(f"Contour {i}: {len(approx)} corners detected")

        # Magic cards should have 4 corners, but accept 3-20 for flexibility
        if len(approx) >= 3:
            # Check aspect ratio (Magic cards are roughly 2.5:3.5 = 0.71)
            rect = cv2.minAreaRect(contour)
            width, height = rect[1]

            if width == 0 or height == 0:
                continue

            aspect_ratio = min(width, height) / max(width, height)

            if i < 10:
                logger.info(f"Contour {i}: aspect_ratio={aspect_ratio:.2f}, w={width:.0f}, h={height:.0f}")

            # MEGET bredt interval - accepter næsten alt rektangulært
            # Magic cards er ~0.71, men med perspektiv kan det variere meget
            if 0.4 <= aspect_ratio <= 0.95:
                card_contours.append(contour)
                logger.info(f"Contour {i}: ACCEPTED as card candidate!")
            elif i < 10:
                logger.info(f"Contour {i}: Rejected by aspect ratio")

    # Sort by area (largest first)
    card_contours.sort(key=cv2.contourArea, reverse=True)

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
