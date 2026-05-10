import io
import logging
from PIL import Image, ImageDraw
from app.detector import detect_face
from app.config import settings

logger = logging.getLogger(__name__)

def process_frame(jpeg_bytes: bytes) -> tuple[bytes, dict | None]:
    """
    Decodes JPEG bytes with Pillow, detects face, draws ROI rectangle.
    Returns (annotated_jpeg_bytes, roi_dict | None).
    No OpenCV used anywhere.
    """
    try:
        image = Image.open(io.BytesIO(jpeg_bytes))
    except Exception as e:
        logger.error(f"Failed to decode frame: {e}")
        return jpeg_bytes, None

    roi = detect_face(image)

    if roi:
        draw = ImageDraw.Draw(image)
        x, y, w, h = roi["x"], roi["y"], roi["width"], roi["height"]
        thickness = settings.ROI_THICKNESS
        color = settings.ROI_COLOR

        # Draw axis-aligned minimal bounding box — no OpenCV
        for t in range(thickness):
            draw.rectangle(
                [x - t, y - t, x + w + t, y + h + t],
                outline=color
            )

    output = io.BytesIO()
    image.save(output, format="JPEG", quality=settings.JPEG_QUALITY)
    return output.getvalue(), roi