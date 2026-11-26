"""
Rate limiting (tiêu chí 7).

Yêu cầu:
  • Mỗi API key tối đa RATE_LIMIT_PER_MINUTE request trong 60 giây (sliding window)
  • Vượt giới hạn → HTTP 429, nên kèm header Retry-After
  • State lưu trong Redis để mọi worker / instance dùng chung và vẫn còn sau khi
    restart agent (script chấm sẽ restart agent để kiểm tra)
"""


import hashlib
import time
import uuid

from fastapi import HTTPException

from app.config import settings
from app.redis_client import r


# Redis chạy toàn bộ đoạn Lua như một thao tác nguyên tử.
RATE_LIMIT_SCRIPT = """
local key = KEYS[1]
local now = tonumber(ARGV[1])
local limit = tonumber(ARGV[2])
local member = ARGV[3]

redis.call("ZREMRANGEBYSCORE", key, "-inf", now - 60)
local count = redis.call("ZCARD", key)

if count >= limit then
    return 0
end

redis.call("ZADD", key, now, member)
redis.call("EXPIRE", key, 60)
return 1
"""


def check_rate_limit(api_key: str) -> None:
    key_hash = hashlib.sha256(api_key.encode()).hexdigest()
    redis_key = f"rate_limit:{key_hash}"

    allowed = r.eval(
        RATE_LIMIT_SCRIPT,
        1,
        redis_key,
        time.time(),
        settings.rate_limit_per_minute,
        uuid.uuid4().hex,
    )

    if not allowed:
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded",
            headers={"Retry-After": "60"},
        )