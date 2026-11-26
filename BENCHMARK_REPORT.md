# Benchmark & Observability Report — Day 14

> Copy file này thành `BENCHMARK_REPORT.md` trong repo của bạn và điền đầy đủ.
> Mọi con số phải lấy từ report JSON / CSV / screenshot thật, không ước lượng.

**Họ tên:** Vương Trường Giang
**Ngày chạy:** 26/11/2026
**Môi trường:** Windows, Ubuntu WSL2, Python 3.12; WSL thấy 12 CPU logic và 7,4 GiB RAM (`nproc`, `free -h`); production chạy Docker Compose.

---

## 1. SLO của agent

| SLI | SLO | Lý do chọn ngưỡng này |
|---|---|---|
| p95 latency `/ask` | ≤ 500 ms | Mức mặc định của load test, đánh giá độ trễ phần lớn request. |
| Error rate `/ask` | ≤ 2% | Mức mặc định của load test, theo dõi tỷ lệ request lỗi. |
| Accuracy trên golden dataset | ≥ 80% | Quality gate mặc định; bài eval cuối nâng yêu cầu lên 100% và không regression. |

---

## 2. Benchmark hiệu năng (develop, `load_test.py`)

### 2.1 Concurrency vs latency (agent v2)

| Concurrency | RPS | p50 (ms) | p95 (ms) | p99 (ms) | Error rate | SLO |
|---|---|---|---|---|---|---|
| 1 | 4,10 | 192,2 | 219,2 | 1688,0 | 0,67% | PASS |
| 10 | 35,92 | 190,1 | 223,6 | 1700,0 | 1,00% | PASS |
| 50 | 107,77 | 198,0 | 346,9 | 1698,9 | 0,33% | PASS |
| 100 | 55,68 | 521,0 | 3312,1 | 3535,6 | 1,00% | FAIL p95 |

**Nhận xét:** RPS có tăng tuyến tính theo concurrency không? Vì sao?

RPS tăng từ 4,10 lên 107,77 khi concurrency tăng từ 1 lên 50, nhưng giảm còn 55,68 ở mức 100; vì vậy kết quả không tăng tuyến tính. Ở mức 100, p95 tăng mạnh và vượt SLO 500 ms, phù hợp với dấu hiệu hệ thống bị quá tải; cần đo thêm để xác định chính xác nút thắt.

### 2.2 Tail latency

| `MOCK_SLOW_RATE` | avg (ms) | p95 (ms) | p99 (ms) |
|---|---|---|---|
| 0 | 191,4 | 219,0 | 230,7 |
| 0.03 (mặc định) | 240,6 | 223,0 | 1705,3 |
| 0.1 | 349,2 | 1696,1 | 1714,5 |

**Nhận xét:** Khi slow rate tăng từ 0 lên 0,03, p99 tăng mạnh từ 230,7 lên 1705,3 ms trong khi p95 chỉ tăng nhẹ. Ở mức 0,1, p95 cũng tăng lên 1696,1 ms và vượt SLO 500 ms. Average che khuất một nhóm request rất chậm; percentile giúp quan sát trải nghiệm ở đuôi phân phối.

---

## 3. Benchmark chất lượng (develop, `eval/run_eval.py`)

| Chỉ số | Agent v1 | Agent v2 | Agent v2 (sau khi sửa KB) |
|---|---|---|---|
| Accuracy | 4,3% (1/23) | 91,3% (21/23) | 100% (23/23) |
| Avg tokens / câu | 57,0 | 108,8 | 112,3 |
| Tổng cost (USD) | 0,000403 | 0,000758 | 0,000779 |
| Cost / câu đúng (USD) | 0,00040335 | 0,00003607 | 0,00003387 |
| Quality gate | FAIL | PASS, không regression so với v1 | PASS, không regression so với v2 |

**Những câu v2 trả lời sai ban đầu và cách bạn sửa:**

| ID | Keyword bị thiếu | Bạn đã sửa gì |
|---|---|---|
| security-02 | token, hết hạn, chữ ký | Thêm kiến thức về JWT và so sánh API key. |
| scaling-03 | CPU, memory, custom metrics | Thêm kiến thức về chỉ số Kubernetes HPA dùng để scale. |

**Nhận xét về trade-off chất lượng / chi phí / latency giữa v1 và v2:**

Trong hai lần eval đầu, v2 đạt accuracy 91,3% so với 4,3% của v1, nhưng dùng nhiều token hơn (108,8 so với 57,0 token/câu), tổng cost tăng từ $0,000403 lên $0,000758 và p95 tăng từ 187,3 lên 214,1 ms. Sau khi sửa knowledge base, v2 đạt 100% không regression trong lần chạy kiểm tra.

Chạy v1 với baseline v2 cho thấy 20 câu regression; quality gate FAIL và trả exit code 1. Trong CI có thể chạy `run_eval.py --baseline <baseline>` với agent đang chạy: exit code khác 0 làm bước kiểm tra thất bại và có thể được đặt thành điều kiện bắt buộc trước khi merge.

---

## 4. Observability stack (production)

### 4.1 Screenshot

- [x] Dashboard Grafana khi đang có tải: `screenshots/grafana-dashboard.png`
- [x] Một trace chậm trong Jaeger: `screenshots/jaeger-slow-trace.png`
- [x] Một trace lỗi trong Jaeger có event `exception`: `screenshots/jaeger-error-trace.png`
- [x] Trang Alerts của Prometheus với hai alert cùng **firing**: `screenshots/prometheus-alert-firing.png`

**Exercise 7.4:**

1. Tại thời điểm Grafana hiển thị 17:09:35 ngày 26/11, avg là 248 ms, p95 là 296 ms và p99 là 1,87 s. P95 cao hơn avg 48 ms; khoảng cách lớn giữa p99 và average cho thấy một nhóm request bị chậm hơn nhiều. Đây là giá trị của panel tại thời điểm chụp, khác với số tổng hợp Locust trong mục 5.
2. Panel Requests/s theo instance cho thấy ba đường sát nhau, mỗi instance xấp xỉ 6 req/s tại thời điểm chụp; tải được chia tương đối đều trong lần quan sát này.
3. Input gồm system prompt, câu hỏi và context truy xuất, nhưng không nhất thiết lớn hơn output: ảnh Grafana ở lần quan sát này cho thấy output/s cao hơn input/s; tỷ lệ phụ thuộc độ dài prompt và câu trả lời.
4. `GET /metrics` qua Nginx (`localhost:8080`) trả `404 Not Found`; cấu hình proxy không công khai endpoint metrics. Prometheus scrape metrics trực tiếp qua mạng nội bộ.

### 4.2 Thí nghiệm "phá hệ thống"

| # | Thay đổi | Alert nào firing | Thời gian từ lúc đổi → firing | Panel nào phản ánh rõ nhất |
|---|---|---|---|---|
| A | `MOCK_ERROR_RATE=0.2` | `AgentHighErrorRate` | Đổi cấu hình khoảng 16:53, chạy lại tải khoảng 16:56, thấy firing lúc 16:58. Khoảng 5 phút từ khi đổi cấu hình; không xác định thời điểm bắt đầu firing chính xác. | Trang Alerts |
| B | `MOCK_SLOW_RATE=0.3` | `AgentHighLatencyP95` | Đổi cấu hình khoảng 16:53, chạy lại tải khoảng 16:56, thấy firing lúc 16:58. Khoảng 5 phút từ khi đổi cấu hình; không xác định thời điểm bắt đầu firing chính xác. | Trang Alerts |
| C | `LLM_MODEL=mock-llm-large` | Chưa thực hiện | — | — |
| D | `docker pause` 1 instance | Chưa thực hiện | — | — |
| E | `AGENT_VERSION=v1` | Chưa thực hiện | — | — |

**Thí nghiệm E không làm alert nào firing. Bạn sẽ phát hiện loại sự cố này trong production bằng cách nào?**

Theo dõi chất lượng bằng eval trên golden dataset, so sánh với baseline và chặn triển khai khi accuracy giảm hoặc xuất hiện regression; có thể bổ sung đánh giá trên mẫu traffic thực tế. Metrics hạ tầng đơn thuần không đo được câu trả lời có đúng hay không.

### 4.3 Debug bằng trace

Chọn 1 trace chậm nhất bạn tìm được:

- `trace_id`: `c616e62825e2db9580441bbb6d2c93e5`
- Tổng thời gian: 1715,1 ms theo log HTTP (Jaeger hiển thị khoảng 1,7 s).
- Span chiếm nhiều thời gian nhất: `chat mock-llm-small`; log ghi thời gian LLM 1688,2 ms, khoảng 98,4% thời gian request.
- Dòng log tương ứng (grep theo `trace_id`):

```json
{"ts":"2026-11-26T09:46:04.410877+00:00","level":"INFO","service":"observable-agent","instance":"0a47d60261e9","event":"llm_call","trace_id":"c616e62825e2db9580441bbb6d2c93e5","span_id":"e8b295f89d9692ff","request_id":"550a7ae2101f","model":"mock-llm-small","agent_version":"v2","input_tokens":83,"output_tokens":44,"cost_usd":0.000039,"llm_ms":1688.2}
```

Trace lỗi riêng: `1c2d906a590b1420cfc0345fa2a5d618`, tổng thời gian 941 ms, span `chat mock-llm-small` 842 ms; event `exception` ghi nhận lỗi upstream 503 giả lập. Dòng log có cùng trace ID:

```json
{"ts":"2026-11-26T09:45:37.375586+00:00","level":"INFO","service":"observable-agent","instance":"8a77bb1f0c7f","event":"llm_error","trace_id":"1c2d906a590b1420cfc0345fa2a5d618","span_id":"818578323f95708c","request_id":"3cbfda14eda1","error":"Upstream LLM error: 503 Service Unavailable (mock)"}
```

---

## 5. Benchmark scaling (production, Locust headless, 100 users, 2 phút)

| Số instance | RPS | p50 (ms) | p95 (ms) | p99 (ms) | Failures |
|---|---|---|---|---|---|
| 1 | 59,02 | 200 | 530 | 1700 | 85/7023 (1,21%) |
| 3 | 60,09 | 190 | 250 | 1700 | 79/7137 (1,11%) |

**Giải thích kết quả:** Scale có cải thiện p95 không? Nút thắt nằm ở đâu?

Số liệu trong bảng lấy từ dòng `POST /ask` của Locust CSV. CSV được ghi trước khi Locust kết thúc hoàn toàn nên có thể khác số tổng kết cuối trong terminal. Khi tăng từ 1 lên 3 instance, p95 giảm từ 530 xuống 250 ms, trong khi throughput chỉ tăng nhẹ từ 59,02 lên 60,09 req/s và p99 giữ ở khoảng 1700 ms. Điều này gợi ý scale giúp giảm độ trễ phần lớn request, nhưng các request ở đuôi vẫn có thể bị chi phối bởi độ trễ giả lập của LLM; cần xem trace để xác nhận.

---

## 6. Kết luận

- 3 điều rút ra từ bài đo: percentile giúp thấy request chậm mà average che khuất; quality gate phát hiện hồi quy câu trả lời; trace và log có cùng trace ID giúp tìm bước gây chậm hoặc lỗi.
- Khi triển khai thật, có thể bổ sung synthetic check từ phía người dùng, metric lỗi tại load balancer, và alert về chất lượng câu trả lời hoặc tỷ lệ retrieval không tìm được kết quả.
