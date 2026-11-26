"""
Production AI Agent — Part 6 Final Project (bản khung)

Hoàn thành các TODO để đạt đủ 12 tiêu chí trong README.md, rồi kiểm tra:
    python check_production_ready.py

Bản khung này chạy được (uvicorn app.main:app) nhưng chưa đạt tiêu chí nào.
"""
import logging
import json
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from fastapi.responses import JSONResponse
from app.redis_client import redis_healthy
from app.rate_limiter import check_rate_limit
from app.cost_guard import check_budget, record_cost
from app.redis_client import r
from fastapi import Depends, FastAPI
from pydantic import BaseModel, Field
from app.auth import verify_api_key
from utils.mock_llm import ask as llm_ask

# TODO (tiêu chí 10 — Structured logging):
#   Mỗi dòng log của app phải là 1 JSON object hợp lệ, vd
#   {"ts": "...", "lvl": "INFO", "event": "request", "path": "/ask", "status": 200, "ms": 12.3}
#   Gợi ý: tự viết logging.Formatter dùng json.dumps.
class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_entry = {
            "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "event": record.getMessage()
        }
        return json.dumps(log_entry)

logger = logging.getLogger("agent")
logger.setLevel(logging.INFO)
logger.propagate = False

if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(JSONFormatter())
    logger.addHandler(handler)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("agent_startup")
    yield
    r.close()
    logger.info("agent_shutdown")

app = FastAPI(title="Production AI Agent", lifespan=lifespan)

class AskRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000)


# TODO (tiêu chí 4): GET /health — liveness: luôn trả 200 khi process còn chạy
#                    (kể cả khi Redis chưa kết nối được)
@app.get("/health")
def health():
    return {"status": "ok"}
# TODO (tiêu chí 5): GET /ready  — readiness: 200 khi sẵn sàng, 503 khi Redis không kết nối được
@app.get("/ready")
def ready():
    if not redis_healthy():
        return JSONResponse(
            status_code=503,
            content={"status": "not ready"},
        )
    return {"status": "ready"}

@app.post("/ask")
def ask(body: AskRequest, api_key: str = Depends(verify_api_key)):
    # TODO (tiêu chí 6): bắt buộc header X-API-Key → thêm Depends(verify_api_key)
    # TODO (tiêu chí 7): check_rate_limit(...) → 429 khi vượt giới hạn
    # TODO (tiêu chí 8): check_budget() trước khi gọi LLM, record_cost(...) sau khi gọi → 402 khi hết budget
    check_rate_limit(api_key)
    check_budget()
    answer = llm_ask(body.question)
    input_tokens = max(1, len(body.question.split())*2)
    output_tokens = max(1, len(answer.split())*2)
    record_cost(input_tokens, output_tokens)
    return {"question": body.question, "answer": answer}


# TODO (tiêu chí 11 — Graceful shutdown):
#   Khi nhận SIGTERM: ngừng nhận request mới, xử lý xong request đang chạy rồi thoát (exit code 0).
#   Gợi ý: dùng lifespan của FastAPI để dọn dẹp. Nếu tự đăng ký signal handler cho SIGTERM thì
#   phải gọi lại handler cũ của uvicorn, nếu không process sẽ không bao giờ tắt.
