# Day 14 Lab — Mission Answers

## Part 1: Localhost vs Production

### Exercise 1.1: Các anti-pattern

1. **Hardcode thông tin nhạy cảm:** `OPENAI_API_KEY` và `DATABASE_URL` được ghi trực tiếp trong `develop/app.py`. Nếu dùng thông tin thật, việc đưa code lên Git có thể làm lộ key và mật khẩu.
2. **Không quản lý cấu hình theo môi trường:** `DEBUG` và `MAX_TOKENS` được gán cố định trong code, khiến việc thay đổi giữa development và production khó khăn và dễ sai sót.
3. **Dùng `print()` để ghi log và in cả API key:** Log khó lọc, theo dõi tập trung; in key còn có nguy cơ làm lộ thông tin nhạy cảm.
4. **Không có health check:** Hệ thống triển khai không có endpoint riêng để kiểm tra ứng dụng còn sống và quyết định xử lý khi ứng dụng gặp sự cố.
5. **Cố định địa chỉ và cổng:** Server bind vào `localhost` và cổng `8000`, nên không thuận tiện để nhận kết nối từ bên ngoài container hoặc dùng cổng do nền tảng cloud cấp.
6. **Bật reload:** `reload=True` phù hợp khi phát triển, nhưng không phù hợp cho production vì server có thể tự khởi động lại khi code thay đổi.

### Exercise 1.2: Chạy bản develop

Đã chạy `python app.py` và gọi:

```bash
curl -X POST "http://localhost:8000/ask?question=Hello"
```

Kết quả thực tế:

```json
{"answer":"Đây là câu trả lời từ AI agent (mock). Trong production, đây sẽ là response từ OpenAI/Anthropic."}
```

### Exercise 1.3: So sánh develop và production

| Thành phần | Develop | Production | Tại sao quan trọng? |
|---|---|---|---|
| Cấu hình | Giá trị được ghi cố định trong code. | `config.py` đọc biến môi trường như `PORT`, `DEBUG` và `AGENT_API_KEY`. | Có thể cấu hình theo môi trường và tránh đưa secret thật vào code. |
| Health check | Không có endpoint health check riêng. | Có `/health` và `/ready`. | Giúp nền tảng biết ứng dụng còn sống và có sẵn sàng nhận request hay không. |
| Logging | Dùng `print()`, bao gồm cả API key. | Dùng `logging` với định dạng JSON và ghi thông tin request thay vì key. | Dễ theo dõi, phân tích log và hạn chế lộ secret. |
| Shutdown | Không có logic cleanup riêng trong ứng dụng. | Có lifecycle `lifespan` với bước shutdown và xử lý SIGTERM trong code mẫu. | Cho phép thực hiện cleanup khi dừng; cần kiểm thử thực tế để xác nhận request đang chạy hoàn tất. |
| Host và port | Bind `localhost:8000` cố định. | Mặc định `0.0.0.0`, port đọc từ `PORT`. | Cho phép container nhận kết nối và thích ứng với cổng do cloud cấp. |
| Debug | `reload=True`. | `reload` phụ thuộc `DEBUG`, mặc định tắt. | Tránh tự reload trong production. |

## Part 2: Docker

### Exercise 2.1: Dockerfile cơ bản

1. Base image: `python:3.11`.
2. Working directory: `/app`.
3. Copy `requirements.txt` trước code để Docker có thể dùng lại cache của bước cài dependency khi chỉ sửa code.
4. `CMD` cung cấp lệnh hoặc đối số mặc định có thể thay khi chạy container; `ENTRYPOINT` xác định chương trình chính của container, còn `CMD` có thể cung cấp đối số mặc định cho chương trình đó.

### Exercise 2.2: Chạy container

Đã build và chạy `my-agent:develop`. Gửi `POST /ask?question=Hello` trả về câu trả lời từ mock agent như ở Exercise 1.2.

### Exercise 2.3: So sánh kích thước image

Kết quả `docker images my-agent`:

| Image | Disk usage | Content size |
|---|---:|---:|
| `my-agent:develop` | 1,67 GB | 426 MB |
| `my-agent:advanced` | 240 MB | 57,4 MB |

Theo disk usage và quy đổi 1 GB = 1.000 MB, image advanced nhỏ hơn khoảng **85,6%**: `(1670 - 240) / 1670 × 100`. Kết quả xấp xỉ vì Docker hiển thị số đã làm tròn. Bản advanced dùng `python:3.11-slim` và multi-stage: công cụ build ở stage builder không được copy toàn bộ sang runtime.

### Exercise 2.4: Docker Compose

Các service cùng nằm trên mạng Docker `internal`:

```text
Client → Nginx (:80) → agent (:8000)
                         ├─ Redis (:6379)
                         └─ Qdrant (:6333)
```

Nginx là reverse proxy; cấu hình agent trỏ tới Redis (cache/session và rate limiting) và Qdrant (vector database), đồng thời đợi hai service này healthy trước khi khởi động. Redis và Qdrant có volume lưu dữ liệu. Đây là các kết nối được cấu hình; việc gọi agent mẫu qua Nginx không tự chứng minh agent đã sử dụng Redis hoặc Qdrant.

Kết quả chạy thực tế: `docker compose ps` cho thấy bốn service đang chạy, agent, Redis và Qdrant đều healthy. Gọi `GET /health` qua Nginx trả `status: ok`, version `2.0.0`; `POST /ask` với câu hỏi `Explain microservices` trả câu trả lời của mock agent.

## Part 3: Cloud Deployment

Đã deploy agent Part 6 lên Render: https://day14-agent-ijwz.onrender.com. Blueprint tạo web service Docker và Render Key Value. Học viên kiểm tra `/health` và `/ready` trả 200, `POST /ask` không key trả 401 và có key hợp lệ trả 200. Chi tiết trong `DEPLOYMENT.md`; ảnh minh chứng trong `screenshots/`.

Phần so sánh cấu hình Railway / Render và mô tả pipeline Cloud Run: chưa hoàn thành.

## Part 4: API Security

### Exercise 4.1: API key

Đã kiểm tra `POST /ask` trên bản develop:

```text
Không gửi X-API-Key: HTTP/1.1 401 Unauthorized
{"detail":"Missing API key. Include header: X-API-Key: <your-key>"}

Gửi key mẫu hợp lệ: HTTP/1.1 200 OK
{"question":"Hello","answer":"Tôi là AI agent được deploy lên cloud. Câu hỏi của bạn đã được nhận."}
```

### Exercise 4.2–4.4

Đã lấy JWT bằng `POST /auth/token` với tài khoản student và gửi 12 request liên tiếp tới `POST /ask`. Token được giữ trong biến môi trường của terminal và không ghi vào bài.

Kết quả thực tế: request 1–10 trả `HTTP/1.1 200 OK`, số request còn lại giảm từ 9 xuống 0. Request 11 và 12 trả:

```text
HTTP/1.1 429 Too Many Requests
x-ratelimit-limit: 10
x-ratelimit-remaining: 0
retry-after: 59

{"detail":{"error":"Rate limit exceeded","limit":10,"window_seconds":60,"retry_after_seconds":59}}
```

JWT được cấp sau khi xác thực tài khoản và gửi trong `Authorization: Bearer ...`; server kiểm tra chữ ký và thời hạn trước khi xử lý request.

Cost guard bảo vệ ngân sách: với yêu cầu $10/tháng, có thể lưu chi phí theo user và tháng trong Redis, kiểm tra chi phí đã dùng cộng chi phí ước tính trước khi cho gọi LLM, rồi ghi nhận chi phí; sang tháng dùng key mới. Cần thao tác kiểm tra và cập nhật nguyên tử khi có request đồng thời. Rate limit giới hạn tốc độ, còn cost guard giới hạn tiền, nên cần cả hai. Code mẫu Part 4 hiện lưu trong RAM và dùng ngân sách theo ngày ($1/user, $10 tổng), không phải Redis hoặc giới hạn $10/tháng.

## Part 5: Scaling & Reliability

### Exercise 5.4–5.5: Kiểm tra stateless

Đã chạy `python test_stateless.py` với stack scaling. Năm request trong cùng một session được phục vụ bởi ba instance khác nhau; sau đó script đọc được đủ 10 message (5 câu hỏi và 5 câu trả lời) và báo session history được giữ qua Redis. Kết quả này cho thấy lịch sử được chia sẻ giữa các instance trong thử nghiệm; script không kiểm tra việc tắt một instance.

Lệnh `docker compose ps` ban đầu báo `getwd: no such file or directory`. Sau khi `cd` lại vào thư mục production và chạy lại, cả 3 agent và Redis đều ở trạng thái healthy; Nginx đang chạy và ánh xạ cổng 8080.

## Part 6: Production-ready agent

Kết quả `check_production_ready.py` đầy đủ do học viên chạy trong WSL với Docker:

```text
📋 Checklist Deliverable
    ✅ Dockerfile (multi-stage, < 500 MB)
    ✅ docker-compose.yml (agent + redis)
    ✅ .dockerignore
    ✅ Health check endpoint (GET /health)
    ✅ Readiness endpoint (GET /ready)
    ✅ API Key authentication
    ✅ Rate limiting
    ✅ Cost guard
    ✅ Config từ environment variables
    ✅ Structured logging
    ✅ Graceful shutdown
    ✅ Public URL ready (Railway / Render config)
Result: 12/12 tiêu chí đạt · 41/41 checks passed
🎉 PASS 12/12 — PRODUCTION READY!
```

Docker image đo được 273 MB; `docker stop` trả exit code 0 sau 0,7 giây. Cấu hình deploy đã qua kiểm tra, còn URL public phải được triển khai và kiểm tra riêng.

## AI log

- AI hướng dẫn xây dựng Part 6 và chuẩn bị Blueprint Render; học viên tự sửa code, chạy script 12/12, tạo service và kiểm tra bốn mã HTTP public. AI ghi lại các kết quả do học viên cung cấp.

- Đã hỏi AI về yêu cầu lab, cách chuẩn bị môi trường WSL và ghi câu trả lời Part 1.
- AI hỗ trợ phân tích Dockerfile và tính chênh lệch kích thước Part 2 dựa trên kết quả `docker images` do học viên chạy; cần tự đối chiếu và giải thích kết quả.
- AI hỗ trợ giải thích và ghi kết quả kiểm tra xác thực, rate limit cùng cách thiết kế cost guard ở Part 4..
