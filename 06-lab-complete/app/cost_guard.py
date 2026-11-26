"""
Cost guard (tiêu chí 8).

Yêu cầu:
  • Cộng dồn chi phí LLM (tính theo token) vào Redis
  • Tổng chi phí vượt DAILY_BUDGET_USD (hoặc MONTHLY_BUDGET_USD) → HTTP 402
"""

# Giá USD / 1K tokens (tham khảo gpt-4o-mini)
from datetime import datetime, timezone

from fastapi import HTTPException

from app.config import settings
from app.redis_client import r

# Giá giả lập USD / 1.000 token
PRICE_INPUT_PER_1K = 0.00015
PRICE_OUTPUT_PER_1K = 0.0006


def budget_key() -> str:
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    return f"agent:cost:{today}"


def check_budget() -> None:
    current_cost = float(r.get(budget_key()) or 0)

    if current_cost >= settings.daily_budget_usd:
        raise HTTPException(
            status_code=402,
            detail="Daily budget exceeded",
        )


def record_cost(input_tokens: int, output_tokens: int) -> float:
    cost = (
        input_tokens * PRICE_INPUT_PER_1K / 1000
        + output_tokens * PRICE_OUTPUT_PER_1K / 1000
    )

    key = budget_key()
    r.incrbyfloat(key, cost)
    r.expire(key, 2 * 24 * 60 * 60)
    return cost