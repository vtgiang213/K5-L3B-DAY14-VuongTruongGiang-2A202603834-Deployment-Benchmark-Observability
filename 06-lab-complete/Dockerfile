# ============================================================
# TODO (tiêu chí 1): viết lại thành Dockerfile production
#   • Multi-stage build: stage builder cài dependencies, stage runtime chỉ copy kết quả
#   • Base image slim (vd python:3.11-slim) và chạy bằng user non-root
#   • Có HEALTHCHECK gọi GET /health
#   • Image cuối < 500 MB
#   • CMD lắng nghe theo biến PORT (mặc định 8000) và uvicorn phải là PID 1
#     (exec form, hoặc `sh -c "exec uvicorn ..."`) để nhận SIGTERM khi `docker stop`
#
# Bản dưới đây build và chạy được nhưng CHƯA đạt yêu cầu nào ở trên.
# ============================================================
FROM python:3.11-slim AS builder

WORKDIR /app
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

FROM python:3.11-slim AS runtime
WORKDIR /app
RUN groupadd --system appuser \
    && useradd --system --gid appuser --create-home appuser
COPY --from=builder /opt/venv /opt/venv
COPY app/ ./app/
COPY utils/ ./utils/
ENV PATH="/opt/venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1

USER appuser

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:' + __import__('os').getenv('PORT', '8000') + '/health', timeout=3)" || exit 1

CMD ["sh", "-c", "exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]