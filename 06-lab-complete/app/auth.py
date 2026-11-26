"""
API Key authentication (tiêu chí 6).

Yêu cầu:
  • Client gửi header  X-API-Key: <key>
  • Key phải trùng biến môi trường AGENT_API_KEY
  • Thiếu hoặc sai key → HTTP 401 (không phải 403 hay 422)
"""

import secrets

from fastapi import HTTPException, Security
from fastapi.security import APIKeyHeader

from app.config import settings

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

def verify_api_key(api_key: str | None = Security(api_key_header)) -> str:
    """Dependency cho FastAPI — dùng trong /ask: Depends(verify_api_key)."""
    # TODO: đọc header X-API-Key (gợi ý: fastapi.security.APIKeyHeader),
    #       so sánh với settings.agent_api_key; thiếu/sai → raise HTTPException(status_code=401)
    if not settings.api_key or not api_key:
        raise HTTPException(status_code=401, detail="Missing or invalid API key")

    if not secrets.compare_digest(api_key, settings.api_key):
        raise HTTPException(status_code=401, detail="Missing or invalid API key")

    return api_key
    raise NotImplementedError("TODO: verify_api_key")
