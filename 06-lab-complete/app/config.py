"""
Config — 12-Factor: mọi cấu hình đọc từ biến môi trường.

TODO (tiêu chí 9 — Config từ environment variables):
  • Đọc các biến sau từ môi trường, có giá trị mặc định hợp lý khi chạy local:
      PORT, ENVIRONMENT, AGENT_API_KEY, REDIS_URL,
      RATE_LIMIT_PER_MINUTE, DAILY_BUDGET_USD (hoặc MONTHLY_BUDGET_USD)
  • Không hard-code secret (API key thật, mật khẩu...) trong code.
  • Liệt kê đủ các biến này trong .env.example.
"""
import os
from dataclasses import dataclass, field


@dataclass
class Settings:
    # TODO: thay các giá trị cố định bên dưới bằng giá trị đọc từ biến môi trường
    api_key: str = field(default_factory=lambda: os.getenv("AGENT_API_KEY", ""))
    redis_url: str = field(
        default_factory=lambda: os.getenv("REDIS_URL", "redis://localhost:6379/0")
    )
    rate_limit_per_minute: int = field(
        default_factory=lambda: int(os.getenv("RATE_LIMIT_PER_MINUTE", "10"))
    )
    daily_budget_usd: float = field(
        default_factory=lambda: float(os.getenv("DAILY_BUDGET_USD", "10"))
    )
    port: int = field(default_factory=lambda: int(os.getenv("PORT", "8000")))
    environment: str = field(
        default_factory=lambda: os.getenv("ENVIRONMENT", "development")
    )


settings = Settings()
