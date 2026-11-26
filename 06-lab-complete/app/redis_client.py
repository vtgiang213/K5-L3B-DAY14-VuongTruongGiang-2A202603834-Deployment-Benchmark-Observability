"""
Kết nối Redis dùng chung cho rate limiter và cost guard.

Yêu cầu:
  • Đọc REDIS_URL từ config
  • App vẫn phải KHỞI ĐỘNG ĐƯỢC khi Redis chưa sẵn sàng (đừng ping Redis lúc import)
  • redis_healthy() dùng cho GET /ready: Redis không kết nối được → False
"""

import redis
from app.config import settings

r = redis.from_url(
    settings.redis_url, 
    decode_responses=True,
    socket_connect_timeout=2,
    socket_timeout=2,
)  # TODO: tạo client, vd redis.from_url(settings.redis_url, decode_responses=True)


def redis_healthy() -> bool:
    # TODO: ping Redis; lỗi kết nối → False
    try:
        return bool(r.ping())
    except redis.RedisError:
        return False
