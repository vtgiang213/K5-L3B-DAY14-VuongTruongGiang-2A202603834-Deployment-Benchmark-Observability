# Deployment Information

## Public URL

https://day14-agent-ijwz.onrender.com

## Platform

Render Web Service (Docker) và Render Key Value (Redis-compatible), cấu hình trong `06-lab-complete/render.yaml`.

## Kết quả kiểm tra

| Kiểm tra | HTTP |
|---|---:|
| `GET /health` | 200 |
| `GET /ready` | 200 |
| `POST /ask` không có key | 401 |
| `POST /ask` với key hợp lệ | 200 |

```bash
BASE="https://day14-agent-ijwz.onrender.com"
curl -sS -o /dev/null -w '%{http_code}\n' "$BASE/health"
curl -sS -o /dev/null -w '%{http_code}\n' "$BASE/ready"
curl -sS -o /dev/null -w '%{http_code}\n' -X POST "$BASE/ask" \
  -H 'Content-Type: application/json' -d '{"question":"Hello"}'

# Nhập key từ Render mà không hiển thị trên terminal.
read -s -p 'AGENT_API_KEY: ' AGENT_API_KEY
echo
curl -sS -o /dev/null -w '%{http_code}\n' -X POST "$BASE/ask" \
  -H 'Content-Type: application/json' -H "X-API-Key: $AGENT_API_KEY" \
  -d '{"question":"Hello"}'
unset AGENT_API_KEY
```

## Biến môi trường

`AGENT_API_KEY` do Render tạo; `REDIS_URL` lấy từ Key Value qua Blueprint. Các biến khác gồm `RATE_LIMIT_PER_MINUTE`, `DAILY_BUDGET_USD`, `ENVIRONMENT` và `PORT` do Render cấp. Không ghi giá trị secret vào repo.

## Ảnh minh chứng

- [Dashboard deploy](screenshots/dashboard.png)
- [Service đang chạy](screenshots/running.png)
- [Kết quả kiểm tra](screenshots/test.png)
