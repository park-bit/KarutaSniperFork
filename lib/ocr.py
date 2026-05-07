# ocr.py — fully in-memory image processing, zero temp-file disk I/O
# Original crop logic credit: https://github.com/riccardolunardi/KarutaBotHack
import io
import numpy as np
import cv2
from PIL import Image


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _load_bytes(data: bytes) -> np.ndarray:
    """Decode image bytes → BGR numpy array (no disk write)."""
    arr = np.frombuffer(data, dtype=np.uint8)
    return cv2.imdecode(arr, cv2.IMREAD_COLOR)


def _gray(img: np.ndarray) -> np.ndarray:
    return cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)


def _to_pil(arr: np.ndarray) -> Image.Image:
    """Convert a grayscale numpy array to a PIL Image for pytesseract."""
    return Image.fromarray(arr)


# ---------------------------------------------------------------------------
# card width detection (replaces filelength)
# ---------------------------------------------------------------------------

def get_card_count(image_bytes: bytes) -> int:
    """Return 3 or 4 depending on the drop image width."""
    img = _load_bytes(image_bytes)
    width = img.shape[1]
    # original logic: width == 836 → 3 cards, else → 4
    return 3 if width == 836 else 4


# ---------------------------------------------------------------------------
# Karuta — in-memory slicing, returns PIL Images ready for pytesseract
# ---------------------------------------------------------------------------

_CARD_W = 278
_CARD_H = 414

def karuta_get_char_top(image_bytes: bytes, n: int) -> Image.Image:
    """Character name strip (top label) for card n (0-indexed)."""
    img = _load_bytes(image_bytes)
    card = img[0:_CARD_H, n * _CARD_W:(n + 1) * _CARD_W]
    crop = card[65:105, 45:230]
    return _to_pil(_gray(crop))


def karuta_get_char_bottom(image_bytes: bytes, n: int) -> Image.Image:
    """Anime name strip (bottom label) for card n (0-indexed)."""
    img = _load_bytes(image_bytes)
    card = img[0:_CARD_H, n * _CARD_W:(n + 1) * _CARD_W]
    crop = card[310:365, 45:235]
    return _to_pil(_gray(crop))


def karuta_get_print(image_bytes: bytes, n: int) -> Image.Image:
    """Print number strip for card n (0-indexed)."""
    img = _load_bytes(image_bytes)
    card = img[0:_CARD_H, n * _CARD_W:(n + 1) * _CARD_W]
    # Crop the bottom right area where print # sits
    crop = card[365:405, 130:265]
    
    # Pre-processing for absolute accuracy:
    # 1. High-scale Resize (4x)
    crop = cv2.resize(crop, None, fx=4, fy=4, interpolation=cv2.INTER_CUBIC)
    # 2. Grayscale
    gray = _gray(crop)
    # 3. Slight Blur to remove card grain
    blur = cv2.GaussianBlur(gray, (3,3), 0)
    # 4. Adaptive Threshold (Handles both light and dark card bars)
    thresh = cv2.adaptiveThreshold(blur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 11, 2)
    
    return _to_pil(thresh)


# ---------------------------------------------------------------------------
# Tofu — in-memory slicing
# ---------------------------------------------------------------------------

_TOFU_CARD_W = 313
_TOFU_CARD_H = 480

def tofu_get_char_top(image_bytes: bytes, n: int) -> Image.Image:
    img = _load_bytes(image_bytes)
    card = img[0:_TOFU_CARD_H, n * _TOFU_CARD_W:(n + 1) * _TOFU_CARD_W]
    crop = card[27:77, 54:259]
    return _to_pil(_gray(crop))


def tofu_get_char_bottom(image_bytes: bytes, n: int) -> Image.Image:
    img = _load_bytes(image_bytes)
    card = img[0:_TOFU_CARD_H, n * _TOFU_CARD_W:(n + 1) * _TOFU_CARD_W]
    crop = card[400:452, 55:260]
    return _to_pil(_gray(crop))


def tofu_get_print(image_bytes: bytes, n: int) -> Image.Image:
    img = _load_bytes(image_bytes)
    card = img[0:_TOFU_CARD_H, n * _TOFU_CARD_W:(n + 1) * _TOFU_CARD_W]
    crop = card[350:405, 170:295]
    
    # Same scaling/thresholding for Tofu
    crop = cv2.resize(crop, None, fx=3, fy=3, interpolation=cv2.INTER_CUBIC)
    gray = _gray(crop)
    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    
    return _to_pil(thresh)
