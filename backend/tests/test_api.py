import io
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from PIL import Image
from app.main import app

def make_jpeg() -> bytes:
    img = Image.new("RGB", (320, 240), color=(100, 150, 200))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()

@pytest.fixture
def anyio_backend():
    return "asyncio"

@pytest.mark.anyio
async def test_health():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"

@pytest.mark.anyio
async def test_roi_unknown_session():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.get("/api/roi?session_id=doesnotexist")
    assert r.status_code == 404

@pytest.mark.anyio
async def test_feed_unknown_session():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.get("/api/feed?session_id=doesnotexist")
    assert r.status_code == 404

@pytest.mark.anyio
async def test_invalid_session_id():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.get("/api/roi?session_id=../../etc/passwd")
    assert r.status_code == 422