# TravelBuddy Agent

TravelBuddy là một AI agent nhỏ xây bằng LangGraph để tư vấn chuyến đi trong phạm vi dữ liệu mock. Agent có thể:

- Tìm chuyến bay giữa các thành phố trong dữ liệu mẫu
- Tìm khách sạn theo thành phố và ngân sách mỗi đêm
- Tính tổng chi phí và ngân sách còn lại cho chuyến đi
- Kết hợp nhiều tool trong một cuộc hội thoại để đưa ra gợi ý hoàn chỉnh

Project này bám theo bài lab LangGraph, nhưng đã được refactor để runtime sạch hơn, tool ổn định hơn và dễ test hơn.

## Cấu trúc

- `agent.py`: dựng graph, quản lý hội thoại, gọi model và tool
- `tools.py`: mock data và 3 tool chính
- `system_prompt.txt`: system prompt định hướng hành vi agent
- `test_tools.py`: test cho logic tool và parser
- `.env.example`: mẫu biến môi trường
- `test_results.md`: log các test case của bài lab

## Yêu cầu

- Python 3.11+ khuyến nghị
- OpenAI API key hợp lệ

Thư viện chính:

- `langchain`
- `langchain-openai`
- `langgraph`
- `python-dotenv`
- `pytest`

## Cài đặt

### 1. Tạo môi trường ảo

```powershell
python -m venv venv
.\venv\Scripts\activate
```

### 2. Cài thư viện

```powershell
pip install langchain langchain-openai langgraph python-dotenv pytest
```

### 3. Tạo file `.env`

Copy từ `.env.example`:

```powershell
Copy-Item .env.example .env
```

Điền API key thật vào `.env`:

```env
OPENAI_API_KEY=your_openai_api_key_here
TRAVELBUDDY_MODEL=gpt-4o-mini
TRAVELBUDDY_DEBUG=1
TRAVELBUDDY_RECURSION_LIMIT=8
```

## Chạy project

```powershell
.\venv\Scripts\python.exe agent.py
```

Ví dụ:

```text
Bạn: Tôi ở Hà Nội, muốn đi Phú Quốc 2 đêm, budget 5 triệu. Tư vấn giúp.
```

Agent sẽ tự quyết định có cần gọi:

- `search_flights`
- `search_hotels`
- `calculate_budget`

## Chạy test

```powershell
.\venv\Scripts\python.exe -m pytest -p no:cacheprovider test_tools.py -q
```

`-p no:cacheprovider` được thêm để tránh lỗi cache trên một số môi trường Windows bị hạn chế quyền ghi.

## 3 Tool hiện có

### `search_flights(origin, destination)`

Tra cứu chuyến bay giữa hai thành phố trong dữ liệu mock.

- Sắp xếp kết quả theo giá tăng dần
- Hỗ trợ tham khảo chiều ngược lại nếu không có đúng tuyến
- Chuẩn hóa một số alias tên thành phố phổ biến

### `search_hotels(city, max_price_per_night=99999999)`

Tra cứu khách sạn tại một thành phố.

- Lọc theo ngân sách tối đa mỗi đêm
- Sắp xếp theo rating giảm dần, rồi theo giá tăng dần
- Báo lỗi rõ khi không có dữ liệu hoặc không có lựa chọn phù hợp

### `calculate_budget(total_budget, expenses)`

Tính tổng chi phí và phần ngân sách còn lại.

- Hỗ trợ format `ten_khoan=so_tien` hoặc `ten_khoan:so_tien`
- Hỗ trợ các mẫu nhân như `1.500.000 x 2`, `1500000*2`, `1.500.000 VND × 2`
- Cộng dồn khoản chi trùng tên
- Từ chối format mơ hồ thay vì đoán sai

## Những gì đã cải thiện

### 1. `agent.py` sạch hơn và ít side effect hơn

- Không còn khởi tạo toàn bộ LLM/graph ngay khi import file
- Tách các bước `load_system_prompt`, `create_llm`, `build_graph`, `get_graph`
- Chỉ chèn `SystemMessage` ở entrypoint thay vì sửa message list trong mỗi vòng
- Thêm `recursion_limit` để tránh loop LangGraph quá dài hoặc vô hạn

### 2. Logging rõ hơn

- Tách trace gọi tool khỏi logic xử lý chính
- Có thể bật/tắt trace bằng `TRAVELBUDDY_DEBUG`
- Giữ log dễ đọc cho bài lab, ví dụ:

```text
[Gọi tool: search_flights]({...})
[Trả lời trực tiếp]
```

### 3. Tool đáng tin cậy hơn

- Tách helper normalize, format, parse và validate
- Chuẩn hóa tên thành phố như `ha noi`, `Sài Gòn`, `tp hcm`
- Siết parse chi phí để tránh cộng sai khi chuỗi đầu vào mơ hồ
- Giữ output ổn định hơn để model dễ dựa vào kết quả tool

### 4. Dễ test hơn

- Thêm `test_tools.py`
- Kiểm tra alias thành phố
- Kiểm tra parse phép nhân cho số đêm
- Kiểm tra lỗi format `expenses`
- Kiểm tra thứ tự sắp xếp của flights/hotels

## Biến môi trường

### `OPENAI_API_KEY`

Biến bắt buộc để gọi model OpenAI.

### `TRAVELBUDDY_MODEL`

Model dùng cho agent. Mặc định:

```env
TRAVELBUDDY_MODEL=gpt-4o-mini
```

### `TRAVELBUDDY_DEBUG`

Bật/tắt log trace của agent.

- `1`: hiện log gọi tool
- `0`: ẩn log trace

### `TRAVELBUDDY_RECURSION_LIMIT`

Giới hạn số vòng LangGraph trong một lần chạy agent.

Mục đích:

- Tránh loop `agent -> tools -> agent -> ...` ngoài ý muốn
- Fail sớm khi model hành xử bất thường
- Giữ số vòng chain ở mức hợp lý cho bài lab