import logging
import re
from datetime import datetime, timezone

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import ROIEvent
from app.processor import process_frame
from app.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()

# In-memory store of latest annotated frame per session
_latest_frames: dict[str, bytes] = {}

SESSION_RE = re.compile(r"^[a-zA-Z0-9_-]{1,64}$")

def _validate_session_id(session_id: str) -> str:
    if not SESSION_RE.match(session_id):
        raise HTTPException(status_code=422, detail="Invalid session_id format")
    return session_id


# ── Endpoint 1: Receive video feed via WebSocket ──────────────────────────────
@router.websocket("/ws/stream")
async def stream_endpoint(websocket: WebSocket, db: AsyncSession = Depends(get_db)):
    await websocket.accept()
    session_id = None
    frame_index = 0

    try:
        # First message is the session_id
        session_id = await websocket.receive_text()
        if not SESSION_RE.match(session_id):
            await websocket.close(code=1008, reason="Invalid session_id")
            return

        logger.info(f"Stream started: session={session_id}")

        while True:
            data = await websocket.receive_bytes()

            if (len(data) > settings.MAX_FRAME_BYTES):
                logger.warning(f"Frame too large ({len(data)} bytes), skipping")
                continue

            if frame_index % 30 == 0:
                logger.info(f"Processing frame {frame_index} for session {session_id}")

            annotated, roi = process_frame(data)

            # Store latest frame for /api/feed
            _latest_frames[session_id] = annotated

            # Persist ROI to DB if face detected
            if roi:
                event = ROIEvent(
                    session_id=session_id,
                    frame_index=frame_index,
                    captured_at=datetime.now(timezone.utc),
                    **roi,
                )
                db.add(event)
                await db.commit()

            # Send annotated frame back to client
            await websocket.send_bytes(annotated)
            frame_index += 1

    except WebSocketDisconnect:
        logger.info(f"Client disconnected: session={session_id}")
    except Exception as e:
        logger.error(f"Stream error (session={session_id}): {e}")
    finally:
        _latest_frames.pop(session_id, None)


# ── Endpoint 2: Serve the latest annotated frame ──────────────────────────────
@router.get("/api/feed", tags=["Feed"])
async def get_feed(session_id: str = Query(...)):
    _validate_session_id(session_id)
    frame = _latest_frames.get(session_id)
    if not frame:
        raise HTTPException(status_code=404, detail="No active feed for this session")

    from fastapi.responses import Response
    return Response(content=frame, media_type="image/jpeg")


# ── Endpoint 3: Serve ROI data ────────────────────────────────────────────────
@router.get("/api/roi", tags=["ROI"])
async def get_roi(
    session_id: str = Query(...),
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    _validate_session_id(session_id)

    total_result = await db.execute(
        select(func.count()).where(ROIEvent.session_id == session_id)
    )
    total = total_result.scalar()

    if total == 0:
        raise HTTPException(status_code=404, detail="No ROI data for this session")

    rows = await db.execute(
        select(ROIEvent)
        .where(ROIEvent.session_id == session_id)
        .order_by(ROIEvent.frame_index.desc())
        .limit(limit)
        .offset(offset)
    )
    events = rows.scalars().all()

    return {
        "session_id": session_id,
        "total": total,
        "limit": limit,
        "offset": offset,
        "data": [
            {
                "id": e.id,
                "frame_index": e.frame_index,
                "x": e.x,
                "y": e.y,
                "width": e.width,
                "height": e.height,
                "confidence": round(e.confidence, 4),
                "captured_at": e.captured_at.isoformat(),
            }
            for e in events
        ],
    }